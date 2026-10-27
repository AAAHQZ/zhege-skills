#!/usr/bin/env python3
"""统一来源总表读取与验证脚本。

权威数据文件：source-registry.tsv（来源定义）、source-record-contract.tsv（字段契约）。

用法：
    python source-registry.py fields
    python source-registry.py list
    python source-registry.py get <source_id>
    python source-registry.py match-url <url>
    python source-registry.py match-file <path>
    python source-registry.py list-by-category <core_builtin|optional_adapter|manual_only>
    python source-registry.py unique-dependencies <bundled|install_time|none>
    python source-registry.py validate

退出码：
    0  正常（get / match-url / match-file 未命中时为 1）
    1  用法错误、表头不匹配、校验失败、或查找未命中
"""

from __future__ import annotations

import pathlib
import sys

if hasattr(sys.stdout, "reconfigure"):
    # Windows 控制台默认 GBK 且会把 \n 翻译成 \r\n；统一 UTF-8 + LF，
    # 保证 stdout 字节与 Linux/bash 原版一致（末列不会多出 \r）
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", newline="\n")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", newline="\n")

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
CONTRACT_FILE = SCRIPT_DIR / "source-record-contract.tsv"
REGISTRY_FILE = SCRIPT_DIR / "source-registry.tsv"

REGISTRY_HEADER = (
    "source_id\tsource_label\tsource_category\tinput_mode\tmatch_rule"
    "\traw_dir\tadapter_name\tdependency_name\tdependency_type\tfallback_hint"
)
CONTRACT_HEADER = "field_name\trequiredness\tfilled_by\tvalue_rule"

VALID_CATEGORIES = ("core_builtin", "optional_adapter", "manual_only")
VALID_INPUT_MODES = ("url", "file", "text", "asset")

REQUIRED_CONTRACT_FIELDS = (
    "source_id",
    "source_label",
    "source_category",
    "input_mode",
    "raw_dir",
    "original_ref",
    "ingest_text",
    "adapter_name",
    "fallback_hint",
)

USAGE = """用法：
  python scripts/source-registry.py fields
  python scripts/source-registry.py list
  python scripts/source-registry.py get <source_id>
  python scripts/source-registry.py match-url <url>
  python scripts/source-registry.py match-file <path>
  python scripts/source-registry.py list-by-category <core_builtin|optional_adapter|manual_only>
  python scripts/source-registry.py unique-dependencies <bundled|install_time|none>
  python scripts/source-registry.py validate
"""


def usage_exit() -> int:
    sys.stdout.write(USAGE)
    return 1


def read_rows(path: pathlib.Path) -> list[list[str]]:
    """按 tab 切分数据行（跳过表头与空行）；缺列补空串，语义同 awk -F '\\t'。"""
    rows: list[list[str]] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        fields = line.split("\t")
        fields += [""] * (10 - len(fields))
        rows.append(fields)
    return rows


def field(row: list[str], index: int) -> str:
    """1 起始的 awk 风格取值。"""
    return row[index - 1] if len(row) >= index else ""


def require_file(path: pathlib.Path) -> None:
    if not path.is_file():
        print(f"缺少文件：{path}", file=sys.stderr)
        raise SystemExit(1)


def expect_header(path: pathlib.Path, expected: str) -> None:
    actual = path.read_text(encoding="utf-8-sig").splitlines()[0] if path.read_text(encoding="utf-8-sig").strip() else ""
    if actual != expected:
        print(f"表头不匹配：{path}", file=sys.stderr)
        print(f"期望：{expected}", file=sys.stderr)
        print(f"实际：{actual}", file=sys.stderr)
        raise SystemExit(1)


def validate_contract() -> None:
    require_file(CONTRACT_FILE)
    expect_header(CONTRACT_FILE, CONTRACT_HEADER)

    failed = False
    seen: dict[str, int] = {}
    lines = CONTRACT_FILE.read_text(encoding="utf-8-sig").splitlines()

    for number, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        cells = line.split("\t")
        cells += [""] * (4 - len(cells))
        if not cells[0] or not cells[1] or not cells[2] or not cells[3]:
            print(f"source-record-contract.tsv 第 {number} 行存在空字段", file=sys.stderr)
            failed = True
        seen[cells[0]] = seen.get(cells[0], 0) + 1

    for name in REQUIRED_CONTRACT_FIELDS:
        if seen.get(name, 0) != 1:
            print(f"source-record-contract.tsv 缺少或重复字段：{name}", file=sys.stderr)
            failed = True

    if failed:
        raise SystemExit(1)


def validate_registry() -> None:
    require_file(REGISTRY_FILE)
    expect_header(REGISTRY_FILE, REGISTRY_HEADER)

    failed = False
    seen_ids: set[str] = set()
    category_seen: set[str] = set()
    lines = REGISTRY_FILE.read_text(encoding="utf-8-sig").splitlines()

    for number, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        row = line.split("\t")
        row += [""] * (10 - len(row))

        source_id = field(row, 1)
        source_category = field(row, 3)
        input_mode = field(row, 4)
        match_rule = field(row, 5)
        raw_dir = field(row, 6)
        adapter_name = field(row, 7)
        dependency_name = field(row, 8)
        dependency_type = field(row, 9)

        if any(field(row, i) == "" for i in (1, 2, 3, 4, 5, 6, 10)):
            print(f"source-registry.tsv 第 {number} 行存在空字段", file=sys.stderr)
            failed = True

        if source_category not in VALID_CATEGORIES:
            print(f"source-registry.tsv 第 {number} 行存在未知分类：{source_category}", file=sys.stderr)
            failed = True

        if input_mode not in VALID_INPUT_MODES:
            print(f"source-registry.tsv 第 {number} 行存在未知输入模式：{input_mode}", file=sys.stderr)
            failed = True

        if input_mode == "url" and not match_rule.startswith("url_host:"):
            print(f"source-registry.tsv 第 {number} 行 URL 来源必须声明 url_host 规则：{match_rule}", file=sys.stderr)
            failed = True

        if input_mode == "file" and not match_rule.startswith("file_ext:"):
            print(f"source-registry.tsv 第 {number} 行文件来源必须声明 file_ext 规则：{match_rule}", file=sys.stderr)
            failed = True

        if input_mode == "text" and not match_rule.startswith("text:"):
            print(f"source-registry.tsv 第 {number} 行文本来源必须声明 text 规则：{match_rule}", file=sys.stderr)
            failed = True

        if input_mode == "asset" and not match_rule.startswith("asset:"):
            print(f"source-registry.tsv 第 {number} 行附件来源必须声明 asset 规则：{match_rule}", file=sys.stderr)
            failed = True

        if not raw_dir.startswith("raw/"):
            print(f"source-registry.tsv 第 {number} 行 raw_dir 必须位于 raw/ 下：{raw_dir}", file=sys.stderr)
            failed = True

        if source_id in seen_ids:
            print(f"source-registry.tsv source_id 重复：{source_id}", file=sys.stderr)
            failed = True
        seen_ids.add(source_id)

        category_seen.add(source_category)

        if source_category == "optional_adapter":
            if adapter_name == "-" or dependency_name == "-" or dependency_type == "none":
                print(f"source-registry.tsv 第 {number} 行 optional_adapter 缺少依赖信息", file=sys.stderr)
                failed = True
        elif adapter_name != "-" or dependency_name != "-" or dependency_type != "none":
            print(f"source-registry.tsv 第 {number} 行非外挂来源不应声明依赖", file=sys.stderr)
            failed = True

    for category in VALID_CATEGORIES:
        if category not in category_seen:
            print(f"source-registry.tsv 缺少 {category} 来源", file=sys.stderr)
            failed = True

    if failed:
        raise SystemExit(1)


def print_contract() -> None:
    validate_contract()
    sys.stdout.write(CONTRACT_FILE.read_text(encoding="utf-8-sig"))


def print_registry() -> None:
    validate_registry()
    sys.stdout.write(REGISTRY_FILE.read_text(encoding="utf-8-sig"))


def get_source(source_id: str) -> None:
    validate_registry()
    for row in read_rows(REGISTRY_FILE):
        if field(row, 1) == source_id:
            sys.stdout.write("\t".join(row[:10]) + "\n")
            return
    raise SystemExit(1)


def extract_url_host(url: str) -> str:
    rest = url
    if "://" in rest:
        rest = rest.split("://", 1)[1]
    if "@" in rest:
        rest = rest.split("@", 1)[1]
    host = rest.split("/", 1)[0]
    for sep in ("?", "#", ":"):
        host = host.split(sep, 1)[0]
    return host.lower()


def host_matches_pattern(host: str, pattern: str) -> bool:
    return host == pattern or host.endswith("." + pattern)


def match_url(url: str) -> None:
    validate_registry()
    host = extract_url_host(url)
    fallback_row: str | None = None

    for row in read_rows(REGISTRY_FILE):
        if field(row, 1) == "source_id" or field(row, 4) != "url":
            continue
        match_rule = field(row, 5)
        line = "\t".join(row[:10])
        if not match_rule.startswith("url_host:"):
            continue
        pattern_list = match_rule[len("url_host:"):]
        if pattern_list == "*":
            fallback_row = line
            continue
        for pattern in pattern_list.replace(",", " ").split():
            if host_matches_pattern(host, pattern):
                sys.stdout.write(line + "\n")
                return

    if fallback_row is None:
        raise SystemExit(1)
    sys.stdout.write(fallback_row + "\n")


def match_file(path: str) -> None:
    validate_registry()
    lowered_path = path.lower()

    for row in read_rows(REGISTRY_FILE):
        if field(row, 1) == "source_id" or field(row, 4) != "file":
            continue
        match_rule = field(row, 5)
        if not match_rule.startswith("file_ext:"):
            continue
        for extension in match_rule[len("file_ext:"):].replace(",", " ").split():
            if lowered_path.endswith(extension):
                sys.stdout.write("\t".join(row[:10]) + "\n")
                return

    raise SystemExit(1)


def list_by_category(category: str) -> None:
    validate_registry()
    for row in read_rows(REGISTRY_FILE):
        if field(row, 3) == category:
            sys.stdout.write("\t".join(row[:10]) + "\n")


def list_unique_dependencies(dependency_type: str) -> None:
    validate_registry()
    names: set[str] = set()
    for row in read_rows(REGISTRY_FILE):
        dependency_name = field(row, 8)
        if field(row, 9) == dependency_type and dependency_name != "-":
            names.add(dependency_name)
    for name in sorted(names):
        sys.stdout.write(name + "\n")


def main(argv: list[str]) -> int:
    if not argv:
        return usage_exit()

    command = argv[0]
    count = len(argv)

    if command == "fields":
        if count != 1:
            return usage_exit()
        print_contract()
    elif command == "list":
        if count != 1:
            return usage_exit()
        print_registry()
    elif command == "get":
        if count != 2:
            return usage_exit()
        get_source(argv[1])
    elif command == "match-url":
        if count != 2:
            return usage_exit()
        match_url(argv[1])
    elif command == "match-file":
        if count != 2:
            return usage_exit()
        match_file(argv[1])
    elif command == "list-by-category":
        if count != 2:
            return usage_exit()
        list_by_category(argv[1])
    elif command == "unique-dependencies":
        if count != 2:
            return usage_exit()
        list_unique_dependencies(argv[1])
    elif command == "validate":
        if count != 1:
            return usage_exit()
        validate_contract()
        validate_registry()
    else:
        return usage_exit()

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
