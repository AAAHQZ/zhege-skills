#!/usr/bin/env python3
"""知识库校验器（只查不改）。

把两个真实知识库各自手写的 lint 收敛成一个可配置的通用版本，支持两种正文布局：

    per-entry    一个 .md 一个条目，frontmatter + 固定小节
                  例：<分类>/<id>.md
    per-chapter  一个 .md 多条条目，条目是 `### N. 标题` + 机器标签行
                  例：<节号>-<节名>.md

设计约定（照抄两个仓库共同踩出来的结论）：

    只查不改。CI 与本地跑同一份代码、同一份判据，不会和本地生成物分叉。
    索引要重建时用 --emit-index 把规范索引打到 stdout，自己比对或落盘。
    这两个仓库的 CI 都把「索引/统计是否与正文同步」做成独立只读 job，
    就是因为「让 CI 往 main 推提交」会和本地分叉。

用法:
    python kb_lint.py --repo <知识库仓库根> [--config kb-lint.json]
    python kb_lint.py --repo <root> --only id-unique,index-sync
    python kb_lint.py --repo <root> --emit-index
    python kb_lint.py --init-config

跨平台约定:
    解释器名各平台不同：Unix 是 python3，Windows 常是 python 或 py。调用方先探测。
    --emit-index / --init-config 打到 stdout，**不要用 shell 重定向落盘**（`> file`
    在不同 shell 行为不同，且 /tmp 在 Windows 上不存在）。用文件写入工具捕获
    stdout 的内容再落盘，跨平台且不会写出 BOM。
    退出码: 0 通过 / 1 有问题 / 2 配置或用法错误。

检查项（--only 可点名，逗号分隔）:
    fm            frontmatter 能解析、必填字段齐全
    id-pattern    id 命名规范
    id-unique     id 全局唯一
    id-filename   文件名 == id（仅 per-entry）
    category-dir  frontmatter 的 category 与所在目录一致（仅 per-entry）
    sections      必需正文小节齐全
    thickness     条目不过薄
    label         机器标签行存在且可解析（仅 per-chapter）
    chapter-no    条目条号在章内唯一且不重复占用（仅 per-chapter）
    index-sync    索引与正文同步（配合 --emit-index 比对）
    deadlink      正文里裸写的条目 id 必须真实存在

退出码:
    0  全部通过（或没有启用任何检查）
    1  有检查未通过
    2  配置或用法错误
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional

CONFIG_NAME = "kb-lint.json"

DEFAULT_CONFIG: dict[str, Any] = {
    "layout": "per-entry",
    # 下面三个 glob 是占位默认值，指向一种中性布局。首次使用请按你自己的正文
    # 位置改掉——它们不匹配时会以退出码 2 报「没扫到任何语料文件」，
    # 而不是静默通过。
    "corpus_globs": ["references/**/*.md"],
    "exclude_globs": [
        "**/_index/**",
        "**/00-index.md",
        "**/README.md",
        "**/SKILL.md",
        "**/INSTALL.md",
        "**/backup/**",
    ],
    "index_globs": ["references/00-index.md"],
    "required_frontmatter": ["id", "title", "category", "sources"],
    "required_body_sections": [],
    "sources_heading": "## 来源",
    "category_field": "category",
    "category_strip_numeric_prefix": True,
    "id_pattern": r"^[a-z][a-z0-9]*(-[a-z0-9]+)+$",
    "min_body_chars": 0,
    "chapter_entry_pattern": r"^###\s+(\d+)\.\s*(.+?)\s*$",
    "chapter_id_pattern": "",
    "label_pattern": r"^<!--\s*([^>]+?)\s*-->\s*$",
    "deadlink_pattern": r"(?<![A-Za-z0-9\-])[a-z][a-z0-9]*(?:-[a-z0-9]+){1,4}(?![A-Za-z0-9\-])",
    "deadlink_ignore": [r"`[^`\n]*`", r"《[^》\n]*》", r"^\s*\|.*\|\s*$"],
    "disabled_checks": [],
}

ALL_CHECKS = [
    "fm", "id-pattern", "id-unique", "id-filename", "category-dir",
    "sections", "thickness", "label", "chapter-no", "index-sync", "deadlink",
]

PER_ENTRY_ONLY = {"id-filename", "category-dir"}
PER_CHAPTER_ONLY = {"label", "chapter-no"}


# --------------------------------------------------------------------------- #
# 极简 YAML（PyYAML 存在就用它，否则退回这个）
# --------------------------------------------------------------------------- #

def _scalar(v: str) -> Any:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    if v.startswith("[") and v.endswith("]"):
        return [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
    return v


def _mini_yaml(text: str) -> dict:
    """只认 frontmatter 里真实会出现的形态：标量、内联列表、块标量、列表。

    不追求完整 YAML。frontmatter 校验只需要「能不能读出 key 和它有没有值」。
    装得上 PyYAML 时走 PyYAML，报错信息更准。
    """
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(text)
        return data if isinstance(data, dict) else {}
    except ImportError:
        pass
    except Exception as exc:  # PyYAML 在但解析失败：按失败处理，不静默放过
        raise ValueError(f"YAML 解析失败: {exc}") from exc

    data: dict = {}
    key: Optional[str] = None
    block: Optional[list] = None

    def flush() -> None:
        nonlocal key, block
        if key is not None and block is not None:
            data[key] = "\n".join(ln.strip() for ln in block).strip()
        key, block = None, None

    for raw in text.splitlines():
        if block is not None:
            if not raw.strip() or raw[:1] in (" ", "\t"):
                block.append(raw)
                continue
            flush()
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        item = re.match(r"^\s*-\s+(.*)$", line)
        if item and key is not None:
            if not isinstance(data.get(key), list):
                data[key] = []
            data[key].append(_scalar(item.group(1)))
            continue
        pair = re.match(r"^([A-Za-z0-9_.\-]+)\s*:\s*(.*)$", line)
        if pair:
            key = pair.group(1)
            val = pair.group(2).strip()
            if val in ("|", ">", "|-", ">-"):
                block = []
            elif val == "":
                data[key] = []
            else:
                data[key] = _scalar(val)
    flush()
    return data


def split_frontmatter(text: str) -> tuple[Optional[dict], str, str, str]:
    """返回 (frontmatter dict 或 None, 正文, frontmatter 原文, 错误信息)。

    错误信息区分两种情况：压根没写 frontmatter（""），和写了但解析不了（原因）。
    调用方要自己区分——per-chapter 布局下章节文件常常整份没有 frontmatter，
    那不是错。
    """
    if not text.startswith("---"):
        return None, text, "", ""
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, text, "", "frontmatter 起始了但没有闭合的 ---"
    raw = parts[1]
    try:
        fm = _mini_yaml(raw)
    except ValueError as exc:
        return None, parts[2], raw, str(exc)
    return fm, parts[2], raw, ""


# --------------------------------------------------------------------------- #
# 语料发现
# --------------------------------------------------------------------------- #

@dataclass
class Entry:
    """一个可被检索的条目。两种布局共用。"""
    eid: str                      # per-entry: frontmatter.id；per-chapter: 章号
    title: str
    path: Path
    category: str
    body: str
    fm: dict = field(default_factory=dict)
    labels: list = field(default_factory=list)
    fm_error: str = ""


@dataclass
class Corpus:
    root: Path
    cfg: dict
    entries: list = field(default_factory=list)
    index_files: list = field(default_factory=list)
    files_seen: int = 0


def _rel(root: Path, p: Path) -> str:
    return p.relative_to(root).as_posix()


def _match_any(path: str, pats: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(path, pat) for pat in pats)


def _glob_repo(root: Path, pat: str) -> list:
    """把 'skills/*/references/**/*.md' 这类模式转成对 root 的扫描。

    不用 Path.glob：它不支持 ** 且对 Windows 大小写不友好。
    直接按段判断：'**' 匹配任意多层，'*' 匹配一段。
    """
    parts = pat.split("/")
    stack: list = [root]
    for i, seg in enumerate(parts):
        last = i == len(parts) - 1
        nxt: list = []
        if seg == "**":
            for d in stack:
                nxt.extend([d, *[p for p in sorted(d.iterdir()) if p.is_dir()]])
            # 允许 '**' 吸收零层
            stack = nxt
            continue
        for d in stack:
            if not d.is_dir():
                continue
            if last:
                for p in sorted(d.glob(seg)):
                    if p.is_file():
                        nxt.append(p)
            else:
                for p in sorted(d.glob(seg)):
                    if p.is_dir():
                        nxt.append(p)
        stack = nxt
    return stack


def load_corpus(root: Path, cfg: dict) -> Corpus:
    corpus = Corpus(root=root, cfg=cfg)
    layout = cfg["layout"]

    files: dict = {}
    for pat in cfg["corpus_globs"]:
        for p in _glob_repo(root, pat):
            files[p.resolve()] = p

    excludes = cfg.get("exclude_globs") or []
    for idx_pat in cfg.get("index_globs") or []:
        for p in _glob_repo(root, idx_pat):
            corpus.index_files.append(p)
            files.pop(p.resolve(), None)

    selected = []
    for rp in files.values():
        rel = _rel(root, rp)
        if _match_any(rel, excludes):
            continue
        selected.append(rp)
    selected.sort()
    corpus.files_seen = len(selected)

    if layout == "per-entry":
        for p in selected:
            entry = _read_entry_file(p, root, cfg)
            if entry is not None:
                corpus.entries.append(entry)
    else:
        for p in selected:
            corpus.entries.extend(_read_chapter_file(p, root, cfg))
    return corpus


def _read_entry_file(path: Path, root: Path, cfg: dict) -> Optional[Entry]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    fm, body, _raw, err = split_frontmatter(text)
    return Entry(
        eid=str((fm or {}).get("id") or path.stem),
        title=str((fm or {}).get("title") or ""),
        path=path,
        category=str((fm or {}).get(cfg["category_field"]) or path.parent.name),
        body=body,
        fm=fm or {},
        fm_error=err,
    )


def _read_chapter_file(path: Path, root: Path, cfg: dict) -> list:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    head, body, _raw, _err = split_frontmatter(text)
    err = "" if head is not None else ("" if _err == "" else _err)
    if text.startswith("---") and head is None and _err:
        err = _err
    out: list = []
    marks = list(re.finditer(cfg["chapter_entry_pattern"], body, re.M))
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(body)
        chunk = body[m.end():end]
        cut = chunk.find(cfg.get("sources_heading") or "\0")
        if cut > 0:
            chunk = chunk[:cut]
        labels = [x.strip() for x in re.findall(cfg["label_pattern"], chunk, re.M)]
        cat = str((head or {}).get(cfg["category_field"]) or path.stem)
        out.append(Entry(
            eid=f"{path.stem}#{m.group(1)}",
            title=m.group(2),
            path=path,
            category=cat,
            body=chunk,
            fm=head or {},
            labels=labels,
            fm_error=err,
        ))
    return out


# --------------------------------------------------------------------------- #
# 检查
# --------------------------------------------------------------------------- #

class Report:
    def __init__(self) -> None:
        self.items: list = []
        self.checks_run: set = set()

    def add(self, check: str, where: str, msg: str) -> None:
        self.items.append((check, where, msg))

    def fail(self) -> bool:
        return bool(self.items)


def _enabled(cfg: dict, only: Optional[set]) -> set:
    enabled = set(ALL_CHECKS) - set(cfg.get("disabled_checks") or [])
    if only:
        enabled &= only
    layout = cfg["layout"]
    if layout == "per-entry":
        enabled -= PER_CHAPTER_ONLY
    elif layout == "per-chapter":
        enabled -= PER_ENTRY_ONLY
    return enabled


def check_fm(corpus: Corpus, cfg: dict, rep: Report) -> None:
    """per-entry：每个条目都要有 frontmatter 且必填字段齐全。

    per-chapter：frontmatter 是「章」的元数据，而且常常整份不存在——
    元数据在文件名的节号里、条目的元数据在标签行里。所以这里只守一件事：
    写了就必须能解析。没写不算错。
    """
    req = cfg.get("required_frontmatter") or []
    seen: set = set()

    if cfg["layout"] == "per-chapter":
        for e in corpus.entries:
            if e.path in seen:
                continue
            seen.add(e.path)
            if e.fm_error:
                rep.add("fm", _rel(corpus.root, e.path), e.fm_error)
        return

    for e in corpus.entries:
        where = _rel(corpus.root, e.path)
        if e.fm_error:
            rep.add("fm", where, e.fm_error)
            continue
        if e.fm is None and not e.fm:
            rep.add("fm", where, "缺 frontmatter（per-entry 布局下每个条目都要有）")
            continue
        for k in req:
            v = e.fm.get(k)
            if v is None or v == "" or v == []:
                rep.add("fm", where, f"缺必填字段 `{k}`")


def check_id_pattern(corpus: Corpus, cfg: dict, rep: Report) -> None:
    """per-entry 校验条目 id；per-chapter 校验章号（配 chapter_id_pattern）。"""
    if cfg["layout"] == "per-chapter":
        pat_src = cfg.get("chapter_id_pattern") or ""
        if not pat_src:
            return
        pat = re.compile(pat_src)
        seen: set = set()
        for e in corpus.entries:
            if e.path in seen:
                continue
            seen.add(e.path)
            if not pat.match(e.path.stem):
                rep.add("id-pattern", _rel(corpus.root, e.path),
                        f"章节名 `{e.path.stem}` 不符合 {pat_src}")
        return

    pat = re.compile(cfg["id_pattern"])
    for e in corpus.entries:
        if not pat.match(e.eid):
            rep.add("id-pattern", _rel(corpus.root, e.path),
                    f"id `{e.eid}` 不符合 {cfg['id_pattern']}")


def check_id_unique(corpus: Corpus, cfg: dict, rep: Report) -> None:
    """per-entry 下 id 必须全局唯一。

    per-chapter 下条号唯一性由 chapter-no 保证（`章号#条号` 按构造唯一），
    这里不重复报。
    """
    if cfg["layout"] == "per-chapter":
        return
    seen: dict = {}
    for e in corpus.entries:
        if e.eid in seen:
            rep.add("id-unique", _rel(corpus.root, e.path),
                    f"id `{e.eid}` 与 {seen[e.eid]} 重复")
        else:
            seen[e.eid] = _rel(corpus.root, e.path)


def check_id_filename(corpus: Corpus, cfg: dict, rep: Report) -> None:
    for e in corpus.entries:
        want = f"{e.eid}.md"
        if e.path.name != want:
            rep.add("id-filename", _rel(corpus.root, e.path),
                    f"文件名应为 `{want}`，实际 `{e.path.name}`")


def check_category_dir(corpus: Corpus, cfg: dict, rep: Report) -> None:
    """frontmatter 里的分类值必须与所在目录一致。

    目录常带序号前缀（`01-方法与效率`）而 frontmatter 写裸值（`方法与效率`），
    这是两个真实知识库都在用的写法。category_strip_numeric_prefix 打开时，
    比对前把目录名的 `NN-` 去掉。
    """
    field_ = cfg["category_field"]
    strip = bool(cfg.get("category_strip_numeric_prefix"))
    for e in corpus.entries:
        if e.fm.get(field_) is None:
            continue  # 已由 fm 报过
        dirname = e.path.parent.name
        if strip:
            dirname = re.sub(r"^\d+[-_]", "", dirname)
        if str(e.fm[field_]) != dirname:
            rep.add("category-dir", _rel(corpus.root, e.path),
                    f"{field_}={e.fm[field_]!r} 与目录 `{e.path.parent.name}` 不符")


def check_sections(corpus: Corpus, cfg: dict, rep: Report) -> None:
    req = cfg.get("required_body_sections") or []
    if not req:
        return
    for e in corpus.entries:
        where = _rel(corpus.root, e.path)
        for sec in req:
            if sec not in e.body:
                rep.add("sections", where, f"缺小节 `{sec}`")


def check_thickness(corpus: Corpus, cfg: dict, rep: Report) -> None:
    floor = int(cfg.get("min_body_chars") or 0)
    if floor <= 0:
        return
    thin = [f"{_rel(corpus.root, e.path)}（{len(e.body)}）" for e in corpus.entries
            if len(e.body) < floor]
    if thin:
        rep.add("thickness", f"{len(thin)} 个条目",
                f"正文短于 {floor} 字符：" + "、".join(thin[:10])
                + ("…" if len(thin) > 10 else ""))


def check_label(corpus: Corpus, cfg: dict, rep: Report) -> None:
    for e in corpus.entries:
        where = f"{_rel(corpus.root, e.path)} 条 {e.eid}"
        if not e.labels:
            rep.add("label", where, "缺机器标签行（`<!-- key: 值 -->`）")
            continue
        for line in e.labels:
            if ":" not in line and "=" not in line:
                rep.add("label", where, f"标签行无法解析：{line[:60]}")


def check_chapter_no(corpus: Corpus, cfg: dict, rep: Report) -> None:
    seen: dict = {}
    for e in corpus.entries:
        stem, _, no = e.eid.partition("#")
        key = (stem, no)
        if key in seen:
            rep.add("chapter-no", _rel(corpus.root, e.path),
                    f"条号 {no} 与 {seen[key]} 重复")
        else:
            seen[key] = _rel(corpus.root, e.path)


def check_index_sync(corpus: Corpus, cfg: dict, rep: Report) -> None:
    """索引必须覆盖磁盘上全部条目；per-chapter 布局允许索引只列章文件名。

    反向检查（索引多写了磁盘上没有的）默认开，但当索引是给人看的长文档
    （README、正文汇总）时噪声极大，用 index_check_reverse 关掉。
    """
    known = {e.eid for e in corpus.entries}
    plain = _plain_ids(known)
    reverse = bool(cfg.get("index_check_reverse", True))

    for idx in corpus.index_files:
        text = idx.read_text(encoding="utf-8-sig", errors="replace")
        where = _rel(corpus.root, idx)
        # 索引里的条目可能写成 `id`、也可能写成 markdown 链接 [标题](book/01-x.md)。
        # 两种都要认，否则拿 README 当索引的仓库会全线误报。
        listed = set(re.findall(r"`([^`\n]+)`", text))
        listed |= set(re.findall(r"\]\(([^)\s]+)\)", text))
        listed_stems = {x.split("#", 1)[0] for x in listed} | {
            Path(x).stem for x in listed if "/" in x or "\\" in x or "." in x}

        for e in corpus.entries:
            if e.eid in listed:
                continue
            if cfg["layout"] == "per-chapter" and (
                    e.path.stem in listed_stems or e.path.name in listed):
                continue
            rep.add("index-sync", where, f"索引漏了 `{e.eid}`")

        if not reverse:
            continue
        for token in sorted(listed):
            if token.startswith(("http", "#")) or "/" in token or "." in token:
                continue
            if token in plain or token in listed_stems:
                continue
            rep.add("index-sync", where, f"索引里有磁盘上找不到的 `{token}`")


def check_deadlink(corpus: Corpus, cfg: dict, rep: Report) -> None:
    pat = re.compile(cfg["deadlink_pattern"])
    ignores = [re.compile(p) for p in cfg.get("deadlink_ignore") or []]
    known = {e.eid for e in corpus.entries}
    if not known:
        return
    for e in corpus.entries:
        scope = e.body
        head = cfg.get("sources_heading") or ""
        if head:
            i = scope.find(head)
            if i > 0:
                scope = scope[:i]
        for ig in ignores:
            scope = ig.sub(" ", scope)
        for m in pat.finditer(scope):
            tok = m.group()
            if tok in known or tok in _plain_ids(known):
                continue
            rep.add("deadlink", f"{_rel(corpus.root, e.path)} 条 {e.eid}",
                    f"指向不存在的 id `{tok}`")


def _plain_ids(known: set) -> set:
    out = set()
    for k in known:
        out.add(k.split("#", 1)[0])
        out.add(k.split("#", 1)[-1])
    return out


# --------------------------------------------------------------------------- #
# 索引输出（只打印，不写盘）
# --------------------------------------------------------------------------- #

def emit_index(corpus: Corpus, cfg: dict) -> str:
    by_cat: dict = {}
    for e in sorted(corpus.entries, key=lambda x: (x.category, x.eid)):
        by_cat.setdefault(e.category, []).append(e)
    lines = [f"# 索引（由 kb_lint.py --emit-index 生成，共 "
             f"{len(corpus.entries)} 条，扫描 {corpus.files_seen} 个文件）", ""]
    for cat in sorted(by_cat):
        lines.append(f"## {cat}（{len(by_cat[cat])}）")
        lines.append("")
        for e in by_cat[cat]:
            if cfg["layout"] == "per-chapter":
                lines.append(f"- `{e.eid}` {e.title}")
            else:
                lines.append(f"- `{e.eid}` {e.title}  →  {e.path.name}")
        lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# 入口
# --------------------------------------------------------------------------- #

def load_config(repo: Path, explicit: Optional[str]) -> dict:
    cfg = dict(DEFAULT_CONFIG)
    path = Path(explicit) if explicit else repo / CONFIG_NAME
    if path.is_file():
        try:
            # utf-8-sig：Windows 上 PowerShell 5.1 的 Set-Content -Encoding UTF8、
            # 记事本、部分编辑器都会写 BOM，直接用 utf-8 读会整个报
            # "Unexpected UTF-8 BOM"。配置文件不是程序，没必要因此拒绝服务。
            user = json.loads(path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"[kb_lint] 配置不是合法 JSON: {path} — {exc}")
        cfg.update(user)
    if cfg["layout"] not in ("per-entry", "per-chapter"):
        raise SystemExit(f"[kb_lint] layout 只能是 per-entry / per-chapter，"
                         f"当前 {cfg['layout']!r}")
    unknown = set(cfg.get("disabled_checks") or []) - set(ALL_CHECKS)
    if unknown:
        raise SystemExit(f"[kb_lint] disabled_checks 里有不存在的检查: {sorted(unknown)}")
    return cfg


CHECK_FUNCS = {
    "fm": check_fm,
    "id-pattern": check_id_pattern,
    "id-unique": check_id_unique,
    "id-filename": check_id_filename,
    "category-dir": check_category_dir,
    "sections": check_sections,
    "thickness": check_thickness,
    "label": check_label,
    "chapter-no": check_chapter_no,
    "index-sync": check_index_sync,
    "deadlink": check_deadlink,
}


def main(argv: Optional[list] = None) -> int:
    # Windows 控制台默认 GBK，打印中文报错可能抛 UnicodeEncodeError。
    # 兜底只保证不崩；终端显示乱码是显示层问题，不代表语料文件坏了。
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(
        description="知识库校验器（只查不改）",
        epilog="退出码：0 通过 / 1 有检查未过 / 2 配置或用法错误")
    ap.add_argument("--repo", help="知识库仓库根目录（默认当前目录）")
    ap.add_argument("--config", help=f"配置文件路径（默认 <repo>/{CONFIG_NAME}）")
    ap.add_argument("--only", help="只跑这些检查，逗号分隔。可选：" + ", ".join(ALL_CHECKS))
    ap.add_argument("--emit-index", action="store_true",
                    help="把规范索引打到 stdout（不写盘）")
    ap.add_argument("--init-config", action="store_true",
                    help="打印一份带注释的默认配置到 stdout")
    ap.add_argument("--list-checks", action="store_true", help="列出全部检查项")
    args = ap.parse_args(argv)

    if args.list_checks:
        print("\n".join(ALL_CHECKS))
        return 0

    if args.init_config:
        print(json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2))
        print(f"\n# 存成 {CONFIG_NAME} 放在知识库仓库根；"
              f"required_body_sections / min_body_chars 等按你自己的 schema 填。",
              file=sys.stderr)
        return 0

    root = Path(args.repo).expanduser().resolve() if args.repo else Path.cwd()
    if not root.is_dir():
        print(f"[kb_lint] 仓库目录不存在: {root}", file=sys.stderr)
        return 2

    only = {s.strip() for s in args.only.split(",") if s.strip()} if args.only else None
    if only:
        bad = only - set(ALL_CHECKS)
        if bad:
            print(f"[kb_lint] 不存在的检查项: {sorted(bad)}\n"
                  f"可用: {', '.join(ALL_CHECKS)}", file=sys.stderr)
            return 2

    cfg = load_config(root, args.config)
    corpus = load_corpus(root, cfg)

    if args.emit_index:
        print(emit_index(corpus, cfg))
        return 0

    if corpus.files_seen == 0:
        print(f"[kb_lint] 没扫到任何语料文件。检查 corpus_globs（当前 "
              f"{cfg['corpus_globs']}）与 exclude_globs。", file=sys.stderr)
        return 2

    enabled = _enabled(cfg, only)
    rep = Report()
    for name in ALL_CHECKS:
        if name in enabled:
            rep.checks_run.add(name)
            CHECK_FUNCS[name](corpus, cfg, rep)

    layout_note = ("per-entry：一文件一条目" if cfg["layout"] == "per-entry"
                   else "per-chapter：一文件多条目")
    print(f"[kb_lint] {root}")
    print(f"[kb_lint] 布局 {layout_note}｜语料 {corpus.files_seen} 文件 / "
          f"{len(corpus.entries)} 条｜索引 {len(corpus.index_files)} 个｜"
          f"检查 {len(rep.checks_run)} 项：{', '.join(sorted(rep.checks_run))}")

    if not rep.fail():
        print("[kb_lint] 全部通过。")
        return 0

    grouped: dict = {}
    for check, where, msg in rep.items:
        grouped.setdefault(check, []).append((where, msg))
    print()
    for check in ALL_CHECKS:
        rows = grouped.get(check)
        if not rows:
            continue
        print(f"── {check}：{len(rows)} 处")
        for where, msg in rows[:25]:
            print(f"   {where}\n     {msg}")
        if len(rows) > 25:
            print(f"   …另有 {len(rows) - 25} 处")
        print()
    print(f"[kb_lint] 共 {len(rep.items)} 处未通过。")
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
