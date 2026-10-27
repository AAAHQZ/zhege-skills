#!/usr/bin/env python3
"""llm-wiki 缓存脚本。

用法：
    python cache.py check <file>
    python cache.py update <file> <source_page>
    python cache.py invalidate <file>

stdout 是单个单词 + 换行：
    check       HIT / MISS
    update      UPDATED
    invalidate  INVALIDATED

退出码：
    0  正常
    1  用法错误、文件不存在、或找不到知识库根目录
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import pathlib
import sys

if hasattr(sys.stdout, "reconfigure"):
    # Windows 控制台默认 GBK 且会把 \n 翻译成 \r\n；统一 UTF-8 + LF，
    # 保证 stdout 字节与 Linux/bash 原版一致（末列不会多出 \r）
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", newline="\n")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", newline="\n")

CACHE_FILENAME = ".wiki-cache.json"
SCHEMA_FILENAME = ".wiki-schema.md"
DEFAULT_CACHE_CONTENT = '{\n  "version": 1,\n  "entries": {}\n}\n'

USAGE = """用法：
  python scripts/cache.py check <file>
  python scripts/cache.py update <file> <source_page>
  python scripts/cache.py invalidate <file>
"""


def usage_exit() -> int:
    sys.stdout.write(USAGE)
    return 1


def require_file(file_path: str) -> None:
    if not file_path:
        raise SystemExit(usage_exit())
    if not os.path.isfile(file_path):
        print(f"文件不存在：{file_path}", file=sys.stderr)
        raise SystemExit(1)


def find_wiki_root(file_path: str) -> str:
    """从文件所在目录逐级向上，找到含 .wiki-cache.json 或 .wiki-schema.md 的目录。"""
    current = pathlib.Path(file_path).parent
    if not current.is_dir():
        # 原 bash 行为：cd 失败 -> set -e 直接退出，不打印任何内容
        raise SystemExit(1)

    while True:
        if (current / CACHE_FILENAME).is_file() or (current / SCHEMA_FILENAME).is_file():
            return str(current)
        parent = current.parent
        if parent == current:
            raise SystemExit(1)
        current = parent


def cache_file_path(wiki_root: str) -> str:
    return os.path.join(wiki_root, CACHE_FILENAME)


def ensure_cache_file(cache_file: str) -> None:
    if not os.path.isfile(cache_file):
        with open(cache_file, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(DEFAULT_CACHE_CONTENT)


def relative_path(wiki_root: str, file_path: str) -> str:
    return os.path.relpath(os.path.realpath(file_path), os.path.realpath(wiki_root))


def normalized_source_page(wiki_root: str, source_page: str) -> str:
    """绝对路径且位于知识库内 -> 相对路径；其余原样返回。

    用 os.path.isabs() 而非 bash 的 `case /*)`，这样 Windows 的 C:\\... 也算绝对路径。
    """
    if not source_page:
        return ""

    if not os.path.isabs(source_page):
        return source_page

    root_real = os.path.realpath(wiki_root)
    page_real = os.path.realpath(source_page)
    try:
        common = os.path.commonpath([root_real, page_real])
    except ValueError:
        common = ""
    if common == root_real:
        return os.path.relpath(page_real, root_real)
    return source_page


def file_hash(relative: str, file_path: str) -> str:
    content = pathlib.Path(file_path).read_bytes()
    digest = hashlib.sha256(relative.encode("utf-8") + b"\0" + content).hexdigest()
    return f"sha256:{digest}"


def read_cache(cache_file: str) -> dict:
    with open(cache_file, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def write_cache(cache_file: str, data: dict) -> None:
    tmp_file = cache_file + ".tmp"
    with open(tmp_file, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    os.replace(tmp_file, cache_file)


def cache_check(file_path: str) -> None:
    require_file(file_path)
    wiki_root = find_wiki_root(file_path)
    cache_file = cache_file_path(wiki_root)

    if not os.path.isfile(cache_file):
        print("MISS")
        return

    relative = relative_path(wiki_root, file_path)
    current_hash = file_hash(relative, file_path)

    data = read_cache(cache_file)
    entry = data.get("entries", {}).get(relative)
    if not entry or entry.get("hash") != current_hash:
        print("MISS")
        return

    source_page = entry.get("source_page")
    if not source_page:
        print("MISS")
        return

    source_path = source_page
    if not os.path.isabs(source_path):
        source_path = os.path.join(wiki_root, source_path)

    print("HIT" if os.path.isfile(source_path) else "MISS")


def cache_update(file_path: str, source_page: str) -> None:
    require_file(file_path)
    wiki_root = find_wiki_root(file_path)
    cache_file = cache_file_path(wiki_root)
    ensure_cache_file(cache_file)

    relative = relative_path(wiki_root, file_path)
    current_hash = file_hash(relative, file_path)
    normalized_source = normalized_source_page(wiki_root, source_page)
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    data = read_cache(cache_file)
    entries = data.setdefault("entries", {})
    entries[relative] = {
        "hash": current_hash,
        "ingested_at": timestamp,
        "source_page": normalized_source,
    }
    write_cache(cache_file, data)

    print("UPDATED")


def cache_invalidate(file_path: str) -> None:
    # 不做文件存在性校验：文件可能已被删除（级联删除场景）
    wiki_root = find_wiki_root(file_path)
    cache_file = cache_file_path(wiki_root)

    if not os.path.isfile(cache_file):
        print("INVALIDATED")
        return

    relative = relative_path(wiki_root, file_path)
    data = read_cache(cache_file)
    data.setdefault("entries", {}).pop(relative, None)
    write_cache(cache_file, data)

    print("INVALIDATED")


def main(argv: list[str]) -> int:
    if not argv:
        return usage_exit()

    command = argv[0]
    count = len(argv)

    if command == "check":
        if count != 2:
            return usage_exit()
        cache_check(argv[1])
    elif command == "update":
        if count != 3:
            return usage_exit()
        cache_update(argv[1], argv[2])
    elif command == "invalidate":
        if count != 2:
            return usage_exit()
        cache_invalidate(argv[1])
    else:
        return usage_exit()

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
