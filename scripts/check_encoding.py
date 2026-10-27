#!/usr/bin/env python3
"""编码与行尾检查器（只查不改）。

本仓库的文本文件统一 **UTF-8 无 BOM + LF 换行**。这不是审美偏好，是硬约束：

    Windows 上 PowerShell 5.1 的 Set-Content -Encoding UTF8、记事本、部分编辑器
    默认写 UTF-8 **带 BOM**；中文 Windows 的系统 ANSI 码页是 GBK。
    这些坏文件**肉眼看不出来**——在编辑器里打开中文显示得好好的——
    只有脚本读它的时候才炸，或者更糟：`.tsv` 的 BOM 混进表头，
    解析出一个名字带 `` 的字段，不报错，只是每行都多一列。

    git 没有 encoding 属性，强制不了编码；编辑器侧靠 .editorconfig，
    仓库侧就靠这个脚本。两道闸门缺一道，迟早会漏进来。

检查项:
    utf8     文件能按 UTF-8 解码
    bom      文件不以 UTF-8 BOM 开头
    crlf     不含 CRLF（.gitattributes 已保证 eol=lf，这里兜底工作区副本）
    eof      以换行结尾

用法:
    python check_encoding.py                      # 检查整个仓库
    python check_encoding.py --root <目录>        # 检查指定目录
    python check_encoding.py --quiet              # 只输出结果，不逐条列问题
    python check_encoding.py --list-checks        # 列出全部检查项

跨平台:
    只用标准库，Windows / macOS / Linux 通用。
    退出码 0 通过 / 1 有问题 / 2 配置或用法错误（2 与 1 必须分得开：
    配置写错导致根本没扫到文件时是 2，不是静默通过）。

只读保证:
    本脚本永远不写任何被检查的文件。修复动作是人工的，或者靠
    编辑器遵守 .editorconfig —— 不提供 --fix。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, Iterator, NamedTuple

ALL_CHECKS = ("utf8", "bom", "crlf", "eof")

# 这些扩展名视为文本，需要检查
TEXT_SUFFIXES = frozenset(
    {".md", ".py", ".tsv", ".txt", ".json", ".yml", ".yaml", ".sh", ".cfg", ".ini"}
)

# 这些文件名（无扩展名或特殊）也需要检查
TEXT_NAMES = frozenset(
    {".gitattributes", ".gitignore", ".editorconfig", "LICENSE", "Makefile"}
)

# 不扫描的目录名
SKIP_DIRS = frozenset(
    {".git", "__pycache__", ".venv", "venv", "node_modules", ".idea", ".vscode", ".pytest_cache"}
)

UTF8_BOM = b"\xef\xbb\xbf"


class Problem(NamedTuple):
    """一条检查失败记录。"""

    path: Path
    check: str
    detail: str

    def format(self, root: Path) -> str:
        try:
            rel = self.path.relative_to(root)
        except ValueError:
            rel = self.path
        return f"  [{self.check}] {rel} — {self.detail}"


def is_text_candidate(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES or path.name in TEXT_NAMES


def iter_files(root: Path, suffixes: frozenset[str], names: frozenset[str]) -> Iterator[Path]:
    """遍历 root 下的候选文件，跳过版本控制与构建目录。"""
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if SKIP_DIRS & set(path.parts):
            continue
        if path.suffix.lower() in suffixes or path.name in names:
            yield path


def check_file(path: Path, enabled: Iterable[str]) -> Iterator[Problem]:
    """对单个文件跑启用的检查项。"""
    enabled = set(enabled)
    try:
        data = path.read_bytes()
    except OSError as exc:
        yield Problem(path, "utf8", f"读取失败：{exc}")
        return

    if "bom" in enabled and data.startswith(UTF8_BOM):
        # 用具体成因指路：Windows 上多半是 Set-Content -Encoding UTF8 写的
        yield Problem(
            path,
            "bom",
            "带 UTF-8 BOM。Windows 上通常是 Set-Content -Encoding UTF8 或记事本写的；"
            "改用文件写入工具落盘，或让编辑器遵守 .editorconfig",
        )

    if "utf8" in enabled:
        # 容错解码也算失败——坏字节会让下游解析静默出错，必须显式报出来
        try:
            data.decode("utf-8")
        except UnicodeDecodeError as exc:
            # 常见成因：GBK/Big5 等双字节编码，或 latin-1 误存
            guess = _guess_encoding(data)
            yield Problem(
                path,
                "utf8",
                f"非 UTF-8：第 {exc.start} 字节处解码失败（{exc.reason}）{guess}",
            )

    if "crlf" in enabled and b"\r\n" in data:
        count = data.count(b"\r\n")
        yield Problem(
            path, "crlf", f"含 {count} 处 CRLF。应存为 LF（.gitattributes 已设 eol=lf）"
        )
    elif "crlf" in enabled and b"\r" in data:
        # 单独的 \r：老 Mac 换行或混合换行
        yield Problem(path, "crlf", f"含 {data.count(chr(13).encode())} 处裸 CR，疑似混合换行符")

    if "eof" in enabled and data and not data.endswith(b"\n"):
        yield Problem(path, "eof", "文件末尾缺少换行符")


def _guess_encoding(data: bytes) -> str:
    """对常见双字节编码给个提示，省得对着乱码猜半天。"""
    probes = {
        "gb18030": "GBK/GB18030（中文 Windows 常用）",
        "big5": "Big5（繁体中文）",
        "shift_jis": "Shift-JIS（日文）",
        "cp1252": "Windows-1252（西欧）",
    }
    for enc, label in probes.items():
        try:
            data.decode(enc)
        except UnicodeDecodeError:
            continue
        # 能完整解码且确实不是合法 UTF-8，才提示
        return f"，疑似 {label}"
    return ""


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(
        description="编码与行尾检查器（只查不改）",
        epilog="退出码：0 通过 / 1 有问题 / 2 配置或用法错误",
    )
    ap.add_argument("--root", default=".", help="要检查的仓库根目录（默认当前目录）")
    ap.add_argument("--only", help=f"只跑这些检查，逗号分隔。可选：{', '.join(ALL_CHECKS)}")
    ap.add_argument("--suffix", help="只检查这些扩展名，逗号分隔（覆盖默认）")
    ap.add_argument("--quiet", action="store_true", help="只输出汇总，不逐条列问题")
    ap.add_argument("--list-checks", action="store_true", help="列出全部检查项")
    args = ap.parse_args(argv)

    if args.list_checks:
        for name in ALL_CHECKS:
            print(name)
        return 0

    # --- 配置校验：出错必须是退出码 2，不能和「扫了但有问题」的 1 混在一起 ---
    enabled = set(ALL_CHECKS)
    if args.only:
        enabled = {c.strip() for c in args.only.split(",") if c.strip()}
        unknown = enabled - set(ALL_CHECKS)
        if unknown:
            print(
                f"[check_encoding] 未知检查项：{', '.join(sorted(unknown))}；"
                f"可选：{', '.join(ALL_CHECKS)}",
                file=sys.stderr,
            )
            return 2

    suffixes = TEXT_SUFFIXES
    names = TEXT_NAMES
    if args.suffix:
        raw = [s.strip() for s in args.suffix.split(",") if s.strip()]
        if not raw:
            print("[check_encoding] --suffix 给了空值", file=sys.stderr)
            return 2
        suffixes = frozenset(s if s.startswith(".") else f".{s}" for s in raw)

    root = Path(args.root).expanduser()
    if not root.is_dir():
        print(f"[check_encoding] 目录不存在：{root}", file=sys.stderr)
        return 2

    files = sorted(iter_files(root, suffixes, names))
    if not files:
        # 一个文件都没扫到 = 配置有问题，不能当成「通过」
        print(
            f"[check_encoding] 没扫到任何候选文件：{root}\n"
            f"  检查 --suffix / root 是否写错，或是否被忽略规则整个排除了。",
            file=sys.stderr,
        )
        return 2

    problems: list[Problem] = []
    for path in files:
        problems.extend(check_file(path, enabled))

    if problems:
        by_check: dict[str, int] = {}
        for p in problems:
            by_check[p.check] = by_check.get(p.check, 0) + 1
        print(f"[check_encoding] ✗ {len(problems)} 个问题 / 扫描 {len(files)} 个文件")
        for name in ALL_CHECKS:
            if name in by_check:
                print(f"  {name}: {by_check[name]}")
        if not args.quiet:
            print()
            for p in problems:
                print(p.format(root))
        return 1

    print(f"[check_encoding] ✓ 全部通过（{len(files)} 个文件，{'/'.join(sorted(enabled))}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
