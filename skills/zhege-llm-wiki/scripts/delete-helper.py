#!/usr/bin/env python3
"""llm-wiki 删除辅助脚本。

用法：
    python delete-helper.py scan-refs <wiki_root> <素材文件名>

stdout：每个命中文件一行，路径相对 wiki_root，按 realpath 去重 + 字典序排列。
退出码：
    0  正常（零命中即空输出）
    1  用法错误、素材文件名为空、wiki 目录不存在
"""

from __future__ import annotations

import os
import pathlib
import sys

if hasattr(sys.stdout, "reconfigure"):
    # Windows 控制台默认 GBK 且会把 \n 翻译成 \r\n；统一 UTF-8 + LF
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", newline="\n")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", newline="\n")

USAGE = """用法：
  python scripts/delete-helper.py scan-refs <wiki_root> <素材文件名>
"""


def usage_exit() -> int:
    sys.stdout.write(USAGE)
    return 1


def main(argv: list[str]) -> int:
    # argv = [scan-refs, <wiki_root>, <素材文件名>]
    if len(argv) != 3 or argv[0] != "scan-refs":
        return usage_exit()

    wiki_root = argv[1]
    needle = argv[2]
    wiki_dir = pathlib.Path(wiki_root) / "wiki"

    if not needle:
        print("素材文件名不能为空", file=sys.stderr)
        return 1

    if not wiki_dir.is_dir():
        print(f"知识库目录不存在：{wiki_dir}", file=sys.stderr)
        return 1

    wiki_root_real = os.path.realpath(wiki_root)
    # 等价 grep -rlF：字面量子串、大小写敏感、可跨行
    needle_bytes = needle.encode("utf-8")

    seen: list[str] = []
    for path in sorted(wiki_dir.rglob("*.md")):
        if not path.is_file():
            continue
        try:
            content = path.read_bytes()
        except OSError:
            continue
        if needle_bytes not in content:
            continue
        real_path = os.path.realpath(path)
        if real_path in seen:
            continue
        seen.append(real_path)

    for real_path in sorted(seen):
        print(os.path.relpath(real_path, wiki_root_real))

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
