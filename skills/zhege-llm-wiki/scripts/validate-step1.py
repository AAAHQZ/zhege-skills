#!/usr/bin/env python3
"""验证 ingest Step 1 的 JSON 输出格式。

用法：
    python validate-step1.py <json_file>

返回：0 = 格式正确，1 = 格式有问题（触发回退）

⚠️ 输出流说明：原 bash 版的 `echo "ERROR: ..."` 没有重定向到 stderr，
   错误信息与成功信息一样走 stdout，调用方（SKILL.md）只靠退出码判断。
   本移植保持一致，不要单独改动。
"""

from __future__ import annotations

import json
import pathlib
import sys

if hasattr(sys.stdout, "reconfigure"):
    # Windows 控制台默认 GBK 且会把 \n 翻译成 \r\n；统一 UTF-8 + LF
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", newline="\n")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", newline="\n")

VALID_CONFIDENCE = ("EXTRACTED", "INFERRED", "AMBIGUOUS", "UNVERIFIED")


def fail(*lines: str) -> int:
    for line in lines:
        print(line)
    return 1


def jq_render(value) -> str:
    """近似 `jq -r` 的标量渲染，仅用于打印 confidence 非法值。"""
    if value is None or value is False:
        return "MISSING"
    if value is True:
        return "true"
    if isinstance(value, (int, float)):
        return json.dumps(value)
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def main(argv: list[str]) -> int:
    if not argv or not argv[0]:
        return fail("ERROR: usage: validate-step1.py <json_file>")

    json_path = pathlib.Path(argv[0])
    if not json_path.is_file():
        return fail(f"ERROR: file not found: {json_path}")

    try:
        with open(json_path, "r", encoding="utf-8-sig") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return fail("ERROR: invalid JSON format")
    except OSError:
        return fail(f"ERROR: file not found: {json_path}")

    if not isinstance(data, dict):
        return fail("ERROR: 'entities' must be an array")

    for key in ("entities", "topics", "connections", "contradictions"):
        if not isinstance(data.get(key), list):
            return fail(f"ERROR: '{key}' must be an array")

    if not isinstance(data.get("new_vs_existing"), dict):
        return fail("ERROR: 'new_vs_existing' must be an object")

    invalid: list[str] = []
    for entity in data.get("entities", []):
        if not isinstance(entity, dict):
            # 原 jq 在非对象元素上会中断整条管道；这里跳过，不误报
            continue
        value = jq_render(entity.get("confidence"))
        if value not in VALID_CONFIDENCE:
            invalid.append(value)
        if len(invalid) >= 3:
            break

    if invalid:
        return fail(
            "ERROR: invalid confidence value(s): " + "\n".join(invalid),
            "       Valid values: EXTRACTED | INFERRED | AMBIGUOUS | UNVERIFIED",
        )

    print("OK: Step 1 JSON validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
