#!/usr/bin/env python3
"""wiki 机械健康检查（lint）。

用法：
    python lint-runner.py <wiki_root>

输出：结构化文本报告（供 AI 后续分析使用），不做任何写入。
退出码：
    0  运行完成
    1  脚本错误（wiki 目录不存在、index.md 不存在）

原实现依赖 grep / find / mktemp 等外部命令；本移植改用 pathlib 递归遍历，
不调用任何外部命令，跨平台行为一致。
"""

from __future__ import annotations

import datetime
import pathlib
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    # Windows 控制台默认 GBK 且会把 \n 翻译成 \r\n；统一 UTF-8 + LF
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", newline="\n")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", newline="\n")

WIKI_LINK_RE = re.compile(r"\[\[[^\]]+\]\]")


def read_text(path: pathlib.Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return ""


def markdown_files(root: pathlib.Path) -> list[pathlib.Path]:
    """递归收集 *.md（替代 grep -r --include='*.md'）。"""
    if not root.is_dir():
        return []
    return [p for p in root.rglob("*.md") if p.is_file()]


def link_targets(text: str) -> set[str]:
    """抽取 [[X]] / [[X|alias]] 里的 X（替代 grep -ohE + sed + sort -u）。"""
    targets = set()
    for match in WIKI_LINK_RE.findall(text):
        inner = match[2:-2]
        targets.add(inner.split("|", 1)[0])
    targets.discard("")
    return targets


def page_names(wiki_dir: pathlib.Path) -> set[str]:
    """等价 find <wiki_dir> -name 'X.md'：任意层级只看文件名，先收一次避免重复遍历。"""
    return {p.stem for p in markdown_files(wiki_dir)}


def report_orphans(wiki_dir: pathlib.Path) -> None:
    entities_dir = wiki_dir / "entities"
    candidates = sorted(p for p in entities_dir.glob("*.md") if p.is_file()) if entities_dir.is_dir() else []
    contents = {p.resolve(): read_text(p) for p in markdown_files(wiki_dir)}

    orphans = 0
    for entity in candidates:
        needle = "[[" + entity.stem + "]]"
        entity_real = entity.resolve()
        # 原逻辑：grep -rlF 的结果里排除自己（grep -vxF "$f"）
        referenced = any(
            other_real != entity_real and needle in text for other_real, text in contents.items()
        )
        if not referenced:
            print(f"  孤立: {entity.stem}")
            orphans += 1

    if orphans == 0:
        print("  （无孤立页面）")
    print("")


def report_broken_links(wiki_dir: pathlib.Path) -> None:
    targets: set[str] = set()
    for path in markdown_files(wiki_dir):
        targets |= link_targets(read_text(path))

    known = page_names(wiki_dir)
    broken = [target for target in sorted(targets) if target not in known]
    for target in broken:
        print(f"  断链: [[{target}]]")
    if not broken:
        print("  （无断链）")
    print("")


def report_index_consistency(wiki_dir: pathlib.Path, index_file: pathlib.Path) -> None:
    targets = link_targets(read_text(index_file))
    known = page_names(wiki_dir)

    missing = [target for target in sorted(targets) if target not in known]
    for target in missing:
        print(f"  index 有但文件缺失: {target}")
    if not missing:
        print("  （index 与文件一致）")
    print("")


def main(argv: list[str]) -> int:
    wiki_root = pathlib.Path(argv[0]) if len(argv) >= 1 and argv[0] else pathlib.Path(".")
    wiki_dir = wiki_root / "wiki"
    index_file = wiki_root / "index.md"

    if not wiki_dir.is_dir():
        print(f"ERROR: wiki 目录不存在：{wiki_dir}", file=sys.stderr)
        print("       请确认路径正确，或先运行 init 工作流初始化知识库。", file=sys.stderr)
        return 1
    if not index_file.is_file():
        print(f"ERROR: index.md 不存在：{index_file}", file=sys.stderr)
        return 1

    print("=== llm-wiki lint 报告 ===")
    print(f"时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"检查路径：{wiki_dir}")
    print("")

    report_orphans(wiki_dir)
    report_broken_links(wiki_dir)
    report_index_consistency(wiki_dir, index_file)

    print("=== 机械检查完成。矛盾检测、交叉引用、置信度抽查由 AI 继续执行 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
