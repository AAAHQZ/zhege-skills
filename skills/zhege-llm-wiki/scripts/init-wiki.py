#!/usr/bin/env python3
"""llm-wiki 初始化脚本：自动创建知识库的目录结构。

用法：
    python init-wiki.py <知识库路径> [主题] [语言]

与原 init-wiki.sh 的行为契约：
    - 位置参数与默认值一致（路径默认 $HOME/Documents/我的知识库）
    - 模板变量 {{TOPIC}} {{DATE}} {{WIKI_ROOT}} {{LANGUAGE}} 全局替换
    - 目录 / 文件清单一字不变
    - 进度文案走 stdout，不被 SKILL.md 解析
    - 退出码：0 成功；非 0 = 任一步失败
"""

from __future__ import annotations

import datetime
import pathlib
import sys

if hasattr(sys.stdout, "reconfigure"):
    # Windows 控制台默认 GBK 且会把 \n 翻译成 \r\n；统一 UTF-8 + LF
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", newline="\n")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", newline="\n")

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATES_DIR = SKILL_DIR / "templates"

RAW_DIRS = [
    "articles",
    "tweets",
    "wechat",
    "xiaohongshu",
    "zhihu",
    "pdfs",
    "notes",
    "assets",
]

WIKI_DIRS = [
    "entities",
    "topics",
    "sources",
    "comparisons",
    "synthesis",
    "synthesis/sessions",
    "queries",
]

GITIGNORE_CONTENT = ".wiki-tmp/\n"

CACHE_CONTENT = '{\n  "version": 1,\n  "entries": {}\n}\n'


def replace_vars(input_file: pathlib.Path, output_file: pathlib.Path, values: dict[str, str]) -> None:
    """把模板里的 {{VAR}} 占位符逐字替换后落盘（替代原 perl -pe）。"""
    text = input_file.read_text(encoding="utf-8")
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(text, encoding="utf-8", newline="\n")


def main(argv: list[str]) -> int:
    home = pathlib.Path.home()
    wiki_root = pathlib.Path(argv[0]) if len(argv) >= 1 and argv[0] else home / "Documents" / "我的知识库"
    topic = argv[1] if len(argv) >= 2 and argv[1] else "我的知识库"
    language = argv[2] if len(argv) >= 3 and argv[2] else "中文"
    date_value = datetime.date.today().strftime("%Y-%m-%d")

    values = {
        "TOPIC": topic,
        "DATE": date_value,
        "WIKI_ROOT": str(wiki_root),
        "LANGUAGE": language,
    }

    print("正在创建知识库...")
    print(f"   路径：{wiki_root}")
    print(f"   主题：{topic}")
    print(f"   语言：{language}")
    print("")

    for name in RAW_DIRS:
        (wiki_root / "raw" / name).mkdir(parents=True, exist_ok=True)
    for name in WIKI_DIRS:
        (wiki_root / "wiki" / pathlib.PurePosixPath(name)).mkdir(parents=True, exist_ok=True)

    (wiki_root / ".gitignore").write_text(GITIGNORE_CONTENT, encoding="utf-8", newline="\n")

    print("[完成] 目录结构已创建")

    replace_vars(TEMPLATES_DIR / "schema-template.md", wiki_root / ".wiki-schema.md", values)
    print("[完成] Schema 文件已生成")

    replace_vars(TEMPLATES_DIR / "index-template.md", wiki_root / "index.md", values)
    print("[完成] 索引文件已生成")

    replace_vars(TEMPLATES_DIR / "log-template.md", wiki_root / "log.md", values)
    print("[完成] 日志文件已生成")

    replace_vars(TEMPLATES_DIR / "overview-template.md", wiki_root / "wiki" / "overview.md", values)
    print("[完成] 总览文件已生成")

    if language == "English":
        purpose_template = TEMPLATES_DIR / "purpose-en-template.md"
    else:
        purpose_template = TEMPLATES_DIR / "purpose-template.md"
    replace_vars(purpose_template, wiki_root / "purpose.md", values)
    print("[完成] 研究方向文件已生成")

    (wiki_root / ".wiki-cache.json").write_text(CACHE_CONTENT, encoding="utf-8", newline="\n")
    print("[完成] 缓存文件已生成")

    print("")
    print("知识库创建完成！")
    print("")
    print("目录结构：")
    print(f"   {wiki_root}/")
    print("   ├── raw/        （原始素材）")
    print("   │   ├── articles/     网页文章")
    print("   │   ├── tweets/       X/Twitter")
    print("   │   ├── wechat/       微信公众号")
    print("   │   ├── xiaohongshu/  小红书")
    print("   │   ├── zhihu/        知乎")
    print("   │   ├── pdfs/         PDF")
    print("   │   ├── notes/        笔记")
    print("   │   └── assets/       图片等附件")
    print("   ├── wiki/       （知识库）")
    print("   ├── index.md    （索引）")
    print("   ├── log.md      （日志）")
    print("   ├── purpose.md  （研究方向）")
    print("   ├── .wiki-cache.json （缓存）")
    print("   └── .wiki-schema.md （配置）")
    print("")
    print("下一步：给 agent 一个链接或文件，开始构建知识库！")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
