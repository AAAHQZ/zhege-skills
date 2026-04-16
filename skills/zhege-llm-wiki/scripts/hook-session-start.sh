#!/bin/bash
# SessionStart hook: 会话开始时注入 wiki 上下文（只触发一次）

set -euo pipefail

WIKI_PATH=""

if [ -f "$HOME/.llm-wiki-path" ]; then
  WIKI_PATH="$(cat "$HOME/.llm-wiki-path")"
fi

if [ -z "$WIKI_PATH" ] && [ -f .wiki-schema.md ]; then
  WIKI_PATH="$(pwd)"
fi

if [ -z "$WIKI_PATH" ] || [ ! -f "$WIKI_PATH/.wiki-schema.md" ]; then
  printf '{}\n'
  exit 0
fi

python3 - "$WIKI_PATH" <<'PY'
import json
import os
import sys

wiki_path = os.path.realpath(sys.argv[1])
message = f"[llm-wiki] 检测到知识库: {wiki_path}/index.md，回答问题时优先查阅 wiki 内容获取上下文"

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": message,
    }
}, ensure_ascii=False))
PY
