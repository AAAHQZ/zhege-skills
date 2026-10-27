#!/usr/bin/env python3
"""旧知识库兼容脚本：惰性默认、目录检查、按需创建。

原则：migration_required=no，只有确实无法兼容时才引入显式迁移。

用法：
    python wiki-compat.py inspect <wiki_root>
    python wiki-compat.py validate <wiki_root>
    python wiki-compat.py ensure-source-dir <wiki_root> <source_id>

退出码：
    0  正常
    1  用法错误、知识库不存在、布局校验失败、未知来源
"""

from __future__ import annotations

import pathlib
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    # Windows 控制台默认 GBK 且会把 \n 翻译成 \r\n；统一 UTF-8 + LF，
    # 保证 stdout 字节与 Linux/bash 原版一致（末列不会多出 \r）
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", newline="\n")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", newline="\n")

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
REGISTRY_FILE = SCRIPT_DIR / "source-registry.tsv"

LEGACY_REQUIRED_RAW_DIRS = (
    "raw/articles",
    "raw/tweets",
    "raw/wechat",
    "raw/pdfs",
    "raw/notes",
    "raw/assets",
)

REQUIRED_PATHS = (
    ".wiki-schema.md",
    "index.md",
    "log.md",
    "raw",
    "wiki",
    "wiki/entities",
    "wiki/topics",
    "wiki/sources",
    "wiki/comparisons",
    "wiki/synthesis",
    "wiki/overview.md",
)

REGISTRY_HEADER = [
    "source_id",
    "source_label",
    "source_category",
    "input_mode",
    "match_rule",
    "raw_dir",
    "adapter_name",
    "dependency_name",
    "dependency_type",
    "fallback_hint",
]
VALID_CATEGORIES = ("core_builtin", "optional_adapter", "manual_only")
VALID_INPUT_MODES = ("url", "file", "text", "asset")

USAGE = """用法：
  python scripts/wiki-compat.py inspect <wiki_root>
  python scripts/wiki-compat.py validate <wiki_root>
  python scripts/wiki-compat.py ensure-source-dir <wiki_root> <source_id>
"""


def usage_exit() -> int:
    sys.stdout.write(USAGE)
    return 1


def field(row: list[str], index: int) -> str:
    """1 起始的 awk 风格取值。"""
    return row[index - 1] if len(row) >= index else ""


def validate_registry() -> list[list[str]]:
    """复刻 source-registry.sh 的总表校验（错误文案逐字一致）。"""
    if not REGISTRY_FILE.is_file():
        print(f"缺少文件：{REGISTRY_FILE}", file=sys.stderr)
        raise SystemExit(1)

    lines = REGISTRY_FILE.read_text(encoding="utf-8-sig").splitlines()
    if not lines or lines[0] != "\t".join(REGISTRY_HEADER):
        print(f"表头不匹配：{REGISTRY_FILE}", file=sys.stderr)
        print("期望：" + "\t".join(REGISTRY_HEADER), file=sys.stderr)
        print(f"实际：{lines[0] if lines else ''}", file=sys.stderr)
        raise SystemExit(1)

    failed = False
    seen_ids: set[str] = set()
    category_seen: set[str] = set()

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

    rows = []
    for line in lines[1:]:
        if not line.strip():
            continue
        cells = line.split("\t")
        cells += [""] * (10 - len(cells))
        rows.append(cells)
    return rows


def require_wiki_root(wiki_root: str) -> None:
    if not wiki_root:
        raise SystemExit(usage_exit())
    if not pathlib.Path(wiki_root).is_dir():
        print(f"知识库不存在：{wiki_root}", file=sys.stderr)
        raise SystemExit(1)


def schema_field_value(wiki_root: str, field_name: str, default_value: str) -> str:
    schema_path = pathlib.Path(wiki_root) / ".wiki-schema.md"
    if not schema_path.is_file():
        return default_value

    match_re = re.compile(r"^-\s*" + re.escape(field_name) + r"[：:]")
    strip_re = re.compile(r"^-\s*" + re.escape(field_name) + r"[：:]\s*")

    for line in schema_path.read_text(encoding="utf-8-sig").splitlines():
        if match_re.match(line):
            return strip_re.sub("", line, count=1).strip() or default_value

    return default_value


def resolved_language(wiki_root: str) -> str:
    raw_value = schema_field_value(wiki_root, "语言", "")
    if raw_value in ("English", "english", "EN", "en"):
        return "en"
    return "zh"


def resolved_schema_version(wiki_root: str) -> str:
    return schema_field_value(wiki_root, "版本", "1.0")


def missing_optional_raw_dirs(wiki_root: str) -> str:
    raw_dirs = {field(row, 6) for row in validate_registry()}

    missing = [
        raw_dir
        for raw_dir in sorted(raw_dirs)
        if raw_dir and raw_dir not in LEGACY_REQUIRED_RAW_DIRS and not (pathlib.Path(wiki_root) / raw_dir).is_dir()
    ]
    if not missing:
        return "-"
    return ",".join(missing)


def file_presence(wiki_root: str, relative_path: str) -> str:
    return "present" if (pathlib.Path(wiki_root) / relative_path).exists() else "missing"


def validate_layout(wiki_root: str) -> None:
    require_wiki_root(wiki_root)
    failed = False

    for path in REQUIRED_PATHS:
        if not (pathlib.Path(wiki_root) / path).exists():
            print(f"缺少必要路径：{path}", file=sys.stderr)
            failed = True

    for path in LEGACY_REQUIRED_RAW_DIRS:
        if not (pathlib.Path(wiki_root) / path).is_dir():
            print(f"缺少必要旧目录：{path}", file=sys.stderr)
            failed = True

    if failed:
        raise SystemExit(1)


def source_raw_dir(source_id: str) -> str:
    for row in validate_registry():
        if field(row, 1) == source_id:
            return field(row, 6)
    print(f"未知来源：{source_id}", file=sys.stderr)
    raise SystemExit(1)


def inspect_lines(wiki_root: str) -> list[str]:
    validate_layout(wiki_root)

    schema_version = resolved_schema_version(wiki_root)
    language = resolved_language(wiki_root)
    optional_dirs = missing_optional_raw_dirs(wiki_root)
    purpose_file = file_presence(wiki_root, "purpose.md")
    cache_file = file_presence(wiki_root, ".wiki-cache.json")

    if (
        schema_version == "1.0"
        or optional_dirs != "-"
        or purpose_file == "missing"
        or cache_file == "missing"
    ):
        legacy_mode = "yes"
    else:
        legacy_mode = "no"

    return [
        f"wiki_root={wiki_root}",
        f"schema_version={schema_version}",
        f"language={language}",
        f"legacy_mode={legacy_mode}",
        "migration_required=no",
        f"missing_optional_raw_dirs={optional_dirs}",
        f"purpose_file={purpose_file}",
        f"cache_file={cache_file}",
    ]


def print_inspect(wiki_root: str) -> None:
    sys.stdout.write("\n".join(inspect_lines(wiki_root)) + "\n")


def ensure_source_dir(wiki_root: str, source_id: str) -> None:
    validate_layout(wiki_root)
    raw_dir = source_raw_dir(source_id)
    (pathlib.Path(wiki_root) / raw_dir).mkdir(parents=True, exist_ok=True)
    sys.stdout.write(f"{wiki_root}/{raw_dir}\n")


def main(argv: list[str]) -> int:
    if not argv:
        return usage_exit()

    command = argv[0]
    count = len(argv)

    if command == "inspect":
        if count != 2:
            return usage_exit()
        print_inspect(argv[1])
    elif command == "validate":
        if count != 2:
            return usage_exit()
        # 原 bash 是 `print_inspect "$2" > /dev/null`：只取退出码，不输出
        inspect_lines(argv[1])
    elif command == "ensure-source-dir":
        if count != 3:
            return usage_exit()
        ensure_source_dir(argv[1], argv[2])
    else:
        return usage_exit()

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
