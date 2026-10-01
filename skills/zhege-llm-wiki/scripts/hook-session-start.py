#!/usr/bin/env python3
"""SessionStart hook：会话开始时注入 wiki 上下文（只触发一次）。

用法：
    python hook-session-start.py

输出（一行 JSON）：
    有 wiki  {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "..."}}
    无 wiki  {}

退出码：恒为 0
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

if hasattr(sys.stdout, "reconfigure"):
    # Windows 控制台默认 GBK 且会把 \n 翻译成 \r\n；统一 UTF-8 + LF
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", newline="\n")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", newline="\n")

WIKI_PATH_FILE = ".llm-wiki-path"
SCHEMA_FILENAME = ".wiki-schema.md"


def resolve_wiki_path() -> str:
    wiki_path = ""

    pointer = pathlib.Path.home() / WIKI_PATH_FILE
    if pointer.is_file():
        # bash 的 $(cat ...) 会去掉结尾换行，这里只去行尾
        wiki_path = pointer.read_text(encoding="utf-8-sig").rstrip("\r\n")

    if not wiki_path and (pathlib.Path.cwd() / SCHEMA_FILENAME).is_file():
        wiki_path = str(pathlib.Path.cwd())

    return wiki_path


def main() -> int:
    wiki_path = resolve_wiki_path()

    if not wiki_path or not (pathlib.Path(wiki_path) / SCHEMA_FILENAME).is_file():
        print("{}")
        return 0

    real_path = os.path.realpath(wiki_path)
    message = f"[llm-wiki] 检测到知识库: {real_path}/index.md，回答问题时优先查阅 wiki 内容获取上下文"

    print(json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": message,
            }
        },
        ensure_ascii=False,
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
