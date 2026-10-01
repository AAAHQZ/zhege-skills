# llm-wiki 脚本移植契约表（bash → Python）

本文件是 **bash → Python 移植的逐字节行为契约**。父会话改 `SKILL.md` / `INSTALL.md` / `AGENTS.md` 时以本表为准。

- 基线：原 10 个 `.sh`（不是 12 个；`source-registry.tsv` / `source-record-contract.tsv` 是数据文件，内容零改动）
- 目标：**9 个 `.py`**（`shared-config.sh` 无独立逻辑，内联进 `adapter-state.py` 后删除），仅依赖标准库，Windows / macOS / Linux 通吃
- 实测环境：Windows 11 + PowerShell 5.1 + Python 3.13.0
- 通用约定（所有脚本）：
  - shebang `#!/usr/bin/env python3`
  - 读 `.tsv` / `.json` / `.md` 一律 `encoding="utf-8-sig"`（Windows BOM 兜底）
  - 写文本一律 `encoding="utf-8", newline="\n"`
  - 入口处 `sys.stdout.reconfigure(encoding="utf-8", errors="replace", newline="\n")`
    - `encoding/errors` 防 Windows GBK 控制台 `UnicodeEncodeError`
    - **`newline="\n"` 同样关键**：Windows 的 `sys.stdout` 默认把 `\n` 翻成 `\r\n`，会让每个字段行末列多一个 `\r`。强制 LF 后 stdout 与 Linux/bash 原版逐字节一致
  - **`usage()` 帮助文本在 bash 里是 `cat <<EOF` 写到 stdout（不是 stderr）**，退出码 1。本移植保持一致

---

## 1. `init-wiki.py`

**调用**：`python ${SKILL_DIR}/scripts/init-wiki.py <wiki_root> [topic] [language]`

| 位置参数 | 默认值 | 说明 |
|---|---|---|
| 1 `<wiki_root>` | `$HOME/Documents/我的知识库` | 知识库根目录 |
| 2 `[topic]` | `我的知识库` | 主题 |
| 3 `[language]` | `中文` | 精确等于 `English` 时用 `purpose-en-template.md`，否则用 `purpose-template.md` |

| 项 | 契约 |
|---|---|
| stdout | 纯人类可读进度文案（`正在创建知识库...` / `   路径：…` / `[完成] 目录结构已创建` / `知识库创建完成！` + 目录树），**SKILL.md 不解析** |
| 退出码 | 0 成功；非 0 = 任一步失败（`set -e` 语义） |
| 日期 | `{{DATE}}` 用**本地日期** `%Y-%m-%d`（不是 UTC） |
| 模板变量 | `{{TOPIC}}` `{{DATE}}` `{{WIKI_ROOT}}` `{{LANGUAGE}}` 全局替换（逐字） |
| SKILL_DIR | `scripts/..`（即 skill 根），模板在 `SKILL_DIR/templates/` |

**创建的目录**（必须一字不差）：
```
raw/{articles,tweets,wechat,xiaohongshu,zhihu,pdfs,notes,assets}
wiki/{entities,topics,sources,comparisons,synthesis,synthesis/sessions,queries}
```

**创建的文件**：`.gitignore`（内容 `.wiki-tmp/`）、`.wiki-schema.md`、`index.md`、`log.md`、`wiki/overview.md`、`purpose.md`、`.wiki-cache.json`（`{"version": 1, "entries": {}}`）

---

## 2. `source-registry.py`

**调用**：`python ${SKILL_DIR}/scripts/source-registry.py <子命令> [参数]`

| 子命令 | 参数个数 | stdout | 退出码 |
|---|---|---|---|
| `fields` | 1（无额外） | 先校验契约表，再**原样输出** `source-record-contract.tsv` 全文（含表头行） | 0 / 1 |
| `list` | 1（无额外） | 先校验总表，再**原样输出** `source-registry.tsv` 全文（含表头行） | 0 / 1 |
| `get <source_id>` | 2 | 命中：该来源的 1 行数据（**不含表头**）；未命中：无输出 | 0 命中 / **1 未命中** |
| `match-url <url>` | 2 | 命中的 1 行数据（不含表头，10 列） | 0 命中 / **1 无命中** |
| `match-file <path>` | 2 | 命中的 1 行数据（不含表头，10 列） | 0 命中 / **1 无命中** |
| `list-by-category <cat>` | 2 | 该分类全部数据行（不含表头） | 0（无匹配也返回 0，空输出） |
| `unique-dependencies <type>` | 2 | 该 `dependency_type` 下非 `-` 的 `dependency_name`，**去重 + 字典序** | 0 |
| `validate` | 1（无额外） | 无输出；错误全走 stderr | 0 / 1 |

参数个数不对 → 打印 `usage()` 到 **stdout** + 退出 1。未知子命令 → 同上。

**10 列（tab 分隔，顺序固定，`fields`/`list` 首行是表头）**：
```
1 source_id   2 source_label   3 source_category   4 input_mode   5 match_rule
6 raw_dir     7 adapter_name   8 dependency_name  9 dependency_type  10 fallback_hint
```

**匹配规则**：
- `match-url`：先剥 `://` 之前 → 剥到第一个 `@` → 砍掉第一个 `/` 之后 → 砍掉 `?` / `#` / `:` 之后 → 转小写得 host。逐行找 `input_mode == url` 且 `match_rule` 形如 `url_host:<逗号分隔>` 的行；`host == 模式` 或 `host` 以 `.<模式>` 结尾即命中，**首个命中即返回 0**。若整表扫完没命中，用**最后一行** `url_host:*` 作为兜底返回；连兜底都没有 → 退出 1
- `match-file`：path 转小写，逐行找 `input_mode == file` 且 `file_ext:<逗号分隔>`，path 以该扩展名**结尾**即命中，首个命中即返回 0；无命中 → 退出 1

**`validate` 校验项**（任一失败 → stderr 逐条输出 + 退出 1）：

`source-record-contract.tsv`：表头必须严格等于 `field_name\trequiredness\tfilled_by\tvalue_rule`；第 2 行起前 4 列不得为空；`source_id / source_label / source_category / input_mode / raw_dir / original_ref / ingest_text / adapter_name / fallback_hint` 这 9 个字段**必须各出现且仅出现 1 次**。

`source-registry.tsv`：表头必须严格等于 10 列名；第 2 行起 `$1..$6` 与 `$10` 不得为空；`source_category ∈ {core_builtin, optional_adapter, manual_only}`；`input_mode ∈ {url, file, text, asset}`；`url→url_host:` / `file→file_ext:` / `text→text:` / `asset→asset:` 规则前缀必须对应；`raw_dir` 必须以 `raw/` 开头；`source_id` 不得重复；三类 `source_category` 必须各至少出现一次；`optional_adapter` 必须声明非 `-` 的 `dependency_name` / `dependency_type != none`；**非** `optional_adapter` 必须 `adapter_name == "-"` 且 `dependency_name == "-"` 且 `dependency_type == "none"`

---

## 3. `adapter-state.py`

**调用**：`python ${SKILL_DIR}/scripts/adapter-state.py [--skill-root <path>] <子命令> [参数]`

`--skill-root` 是**前置可选 flag**（只认子命令之前的位置），传 1 个值。

| 子命令 | 参数个数 | stdout | 退出码 |
|---|---|---|---|
| `check <source_id>` | 2 | **表头行 + 1 行状态**（各 8 列） | 0 / 1 |
| `summary` | 1（无额外） | **表头行 + N 行状态**（N = 总表里 `optional_adapter` + `manual_only` 的行数，按总表顺序） | 0 / 1 |
| `summary-human` | 1（无额外） | 人类可读多行文本（见下） | 0 / 1 |
| `classify-run <source_id> <exit_code> <output_path>` | 4 | **表头行 + 1 行状态**（各 8 列） | 0 / 1 |

**8 列（tab 分隔，顺序固定）** —— SKILL.md 读 `state`、`detail`、`recovery_action`、`install_hint`、`fallback_hint`：
```
1 source_id   2 source_label   3 state   4 state_label
5 detail      6 recovery_action   7 install_hint   8 fallback_hint
```

**表头行字面量**（`check` / `summary` / `classify-run` 首行）：
```
source_id	source_label	state	state_label	detail	recovery_action	install_hint	fallback_hint
```

**`state` 取值与 `state_label` 映射**：
| state | state_label |
|---|---|
| `available` | 可用 |
| `not_installed` | 未安装 |
| `env_unavailable` | 环境不满足 |
| `runtime_failed` | 运行失败 |
| `unsupported` | 不支持自动提取 |
| `empty_result` | 结果为空 |

**`summary-human` 每条的输出格式**（4 行，最后两行按条件）：
```
- {source_label}：{state_label}。{detail}。
  下一步：{recovery_action}。
  安装提示：{install_hint}。        ← 仅当 install_hint != "-"
  回退方式：{fallback_hint}。
```

**依赖判定**：
| dependency_type | 判定 |
|---|---|
| `bundled` | `{skill_root}/{dependency_name}` 是目录 |
| `install_time` | PATH 上能找到 `{dependency_name}` |
| `none` | 恒为已安装 |
| 其他 | 恒为未安装 |

- `skill_root` 默认 = `scripts/../..`（即 `skills/` 目录）；`--skill-root` 可覆盖
- `uv` 判定 = PATH 上能否找到 `uv`
- **Chrome 调试端口 9222 判定 = Python `socket.create_connection(("127.0.0.1", 9222), timeout=1)` 能否连上**（原 bash 是 `lsof -i :9222 -sTCP:LISTEN`，Linux/macOS 专属，Windows 无 `lsof`）

**`classify-run` 判定顺序**：
1. `exit_code` 非整数 → stderr `exit_code 必须是整数，收到：<x>` + 退出 1
2. 预检 state ≠ `available` → 原样输出预检那一行，退出 0
3. `exit_code != 0` → `runtime_failed`
4. `output_path` 不存在，或内容全是空白 → `empty_result`
5. 否则 → `available`（detail `自动提取已拿到有效正文`）

**`check`/`classify-run`/`summary` 传未知 source_id** → stderr `未知来源：<id>` + 退出 1。

**内置 install_hint 文案**（一字不改）：
- `web_article` / `x_twitter` / `zhihu_article` / `youtube_video`：`重新运行当前平台的 llm-wiki 安装命令，确认 {adapter_name} 已准备到技能目录`
- `wechat_article`：`先安装 uv，再执行：uv tool install {WECHAT_TOOL_URL}`，其中 `WECHAT_TOOL_URL` = `git+https://github.com/jackwener/wechat-article-to-markdown.git`（原 `shared-config.sh` 的唯一内容，已内联）
- 其他：`-`

**env_install_hint 文案**（已按平台分流，见下文「移植后追加修复」）：
- `web_article` / `x_twitter` / `zhihu_article`：按 `sys.platform` 给出对应平台的
  Chrome 调试端口启动命令（macOS `open -na` / Linux `google-chrome` / Windows `chrome.exe`）
- `wechat_article` / `youtube_video`：按 `sys.platform` 给出对应的 uv 安装命令
  （macOS `brew` / Linux `curl | sh` / Windows `irm | iex`）
- 其他：`-`

---

## 4. `cache.py`

**调用**：`python ${SKILL_DIR}/scripts/cache.py <子命令> [参数]`

| 子命令 | 参数个数 | stdout（**单个单词 + 换行**） | 退出码 |
|---|---|---|---|
| `check <file>` | 2 | `HIT` 或 `MISS` | 0 / 1 |
| `update <file> <source_page>` | 3 | `UPDATED` | 0 / 1 |
| `invalidate <file>` | 3→2 | `INVALIDATED` | 0 / 1 |

**知识库根定位**：从 `dirname(file)` 逐级向上，找到第一个含 `.wiki-cache.json` **或** `.wiki-schema.md` 的目录即为止。找不到 → stderr `未找到知识库根目录：<file>` + 退出 1。

**`check` 判定链**（任一不满足即 `MISS`）：
1. 缓存文件 `.wiki-cache.json` 不存在 → `MISS`
2. `entries[相对路径]` 不存在 → `MISS`
3. `entry.hash` ≠ 当前哈希 → `MISS`
4. `entry.source_page` 为空 → `MISS`
5. `source_page` 指向的文件不存在 → `MISS`
6. 否则 → `HIT`

**文件哈希**（与 bash 版逐字节一致，缓存升级**不可**改）：`"sha256:" + sha256(相对路径 UTF-8 字节 + b"\0" + 文件原始字节).hexdigest()`，相对路径 = `os.path.relpath(realpath(file), realpath(wiki_root))`

**`check`/`update` 需文件存在**：不存在 → stderr `文件不存在：<path>` + 退出 1。
**`invalidate` 不要求文件存在**（级联删除场景），只按路径删缓存条目。

**`source_page` 归一化**（`update` 用）：
- 空 → 空串
- 绝对路径（**用 `os.path.isabs()` 判，Windows `C:\...` 也算**，原 bash `case /*)` 只认 POSIX）：`realpath` 两边求 `commonpath`，等于 wiki_root 则写相对路径，否则**原样写回入参**
- 相对路径 → 原样

**缓存 JSON 写入**：`{"version": 1, "entries": {相对路径: {"hash":…, "ingested_at":…, "source_page":…}}}`，`ensure_ascii=False, indent=2`，末尾补 `\n`，先写 `.tmp` 再 `os.replace` 原子替换。时间戳 `ingested_at` = **UTC** `%Y-%m-%dT%H:%M:%SZ`。

---

## 5. `lint-runner.py`

**调用**：`python ${SKILL_DIR}/scripts/lint-runner.py <wiki_root>`（缺省 `.`）

| 项 | 契约 |
|---|---|
| stdout | 固定结构化文本报告（SKILL.md **不解析字段**，但版式固定） |
| 退出码 | 0 = 报告跑完；1 = `wiki/` 不存在 或 `index.md` 不存在 |
| 时间行 | `时间：{本地时间 %Y-%m-%d %H:%M}` |

**报告版式**：
```
=== llm-wiki lint 报告 ===
时间：<local>
检查路径：<wiki_root>/wiki

--- 孤立页面（entities/ 下没有被其他页面引用） ---
  孤立: <name>            ← 每个孤立实体一行
  （无孤立页面）           ← 仅当 0 个时输出这一行

--- 断链（被链接但不存在的页面） ---
  断链: [[<link>]]
  （无断链）

--- index 一致性（index.md 有记录但文件缺失） ---
  index 有但文件缺失: <entry>
  （index 与文件一致）

=== 机械检查完成。矛盾检测、交叉引用、置信度抽查由 AI 继续执行 ===
```

**判定细节**：
- **孤立页面**：遍历 `wiki/entities/*.md`，若 `wiki/` 下（**递归、含 index.md 以外的一切，不含 wiki 根外的 index.md**）没有任何**其他**文件包含字面量 `[[<basename>]]` → 孤立。注意：`index.md` 在 wiki 根、**不在** `wiki/` 下，所以它不算引用来源
- **断链**：抓 `wiki/` 下所有 `[[...]]`（正则 `\[\[[^\]]+\]\]`，**至少 1 个非 `]` 字符**），去掉 `[[` `]]`、按 `|` 截断取别名前半、**去重并按字典序**；若 `wiki/` 下任何层级的文件名都不等于 `<link>.md` → 断链
- **index 一致性**：同上，但只扫 `index.md`，命中时输出 `index 有但文件缺失: <entry>`（不带 `[[]]`）
- 原 bash 用 `grep`/`find` 外部命令；本移植用 `pathlib.rglob("*.md")` + 读文件判断包含，**不调外部 grep**
- `wiki/entities/` 不存在 → 视为 0 个孤立页面

---

## 6. `validate-step1.py`

**调用**：`python ${SKILL_DIR}/scripts/validate-step1.py <json_file>`

| 项 | 契约 |
|---|---|
| stdout（成功） | `OK: Step 1 JSON validation passed`，退出 0 |
| 退出码 | 0 = 通过；1 = 任一校验失败 |
| ⚠️ 错误流 | **原 bash 的 `echo "ERROR: ..."` 没有 `>&2`，错误信息走 stdout**。本移植**照搬**（保真优先）。退出码 1 是调用方唯一判据（SKILL.md 第 380 行只靠退出码触发回退） |

**校验顺序与错误文案**：
1. 无参数 → `ERROR: usage: validate-step1.py <json_file>`
2. 文件不存在 → `ERROR: file not found: <path>`
3. 非法 JSON → `ERROR: invalid JSON format`
4. `.entities` 非 array → `ERROR: 'entities' must be an array`
5. `.topics` 非 array → `ERROR: 'topics' must be an array`
6. `.connections` 非 array → `ERROR: 'connections' must be an array`
7. `.contradictions` 非 array → `ERROR: 'contradictions' must be an array`
8. `.new_vs_existing` 非 object → `ERROR: 'new_vs_existing' must be an object`
9. 遍历 `.entities`，`.confidence` 取值必须 ∈ `{EXTRACTED, INFERRED, AMBIGUOUS, UNVERIFIED}`。缺失 / `null` 记作 `MISSING`（视为非法）。**最多列出前 3 个非法值**，换行分隔：
   ```
   ERROR: invalid confidence value(s): <v1>
   <v2>
   <v3>
          Valid values: EXTRACTED | INFERRED | AMBIGUOUS | UNVERIFIED
   ```

**已知契约收窄**：原脚本第 12 行有 `command -v jq` 依赖检查（缺 jq → 退出 1）。Python 用标准库 `json`，**该失败模式消失**。这是**去掉一个依赖**，不是给调用方加约束。

---

## 7. `delete-helper.py`

**调用**：`python ${SKILL_DIR}/scripts/delete-helper.py scan-refs <wiki_root> <素材文件名>`

| 项 | 契约 |
|---|---|
| 参数个数 | 3（`scan-refs` + 2），否则 `usage()` 到 stdout + 退出 1 |
| stdout | **每行一个相对 wiki_root 的相对路径**，`wiki/` 下所有 `*.md` 中含该字面量（`grep -F` 语义，**含子串、大小写敏感、跨行亦可**）的文件；按 realpath 去重，按 realpath 字典序排列 |
| 退出码 | 0（包括零命中，零命中即空输出） |
| 错误 | 素材文件名为空 → stderr `素材文件名不能为空` + 退出 1；`{wiki_root}/wiki` 不是目录 → stderr `知识库目录不存在：<path>` + 退出 1 |

---

## 8. `wiki-compat.py`

**调用**：`python ${SKILL_DIR}/scripts/wiki-compat.py <子命令> [参数]`

| 子命令 | 参数个数 | stdout | 退出码 |
|---|---|---|---|
| `inspect <wiki_root>` | 2 | 8 行 `key=value`（见下） | 0 / 1 |
| `validate <wiki_root>` | 2 | **无输出**（inspect 结果丢弃，只留退出码） | 0 / 1 |
| `ensure-source-dir <wiki_root> <source_id>` | 3 | 创建后的绝对/相对目录路径 `"{wiki_root}/{raw_dir}"` 一行 | 0 / 1 |

**`inspect` 8 行（顺序固定，`=` 分隔）**：
```
wiki_root={入参原样}
schema_version={.wiki-schema.md 的「版本」字段，默认 1.0}
language=zh|en
legacy_mode=yes|no
migration_required=no            ← 字面常量，永不改变
missing_optional_raw_dirs=-      ← 或逗号分隔列表
purpose_file=present|missing
cache_file=present|missing
```

**`language`**：`.wiki-schema.md` 中 `- 语言:` 值为 `English` / `english` / `EN` / `en` 之一 → `en`，否则（含字段缺失）→ `zh`

**`legacy_mode=yes` 的条件**（任一成立）：`schema_version == "1.0"` **或** `missing_optional_raw_dirs != "-"` **或** `purpose_file == "missing"` **或** `cache_file == "missing"`；否则 `no`

**`missing_optional_raw_dirs`**：取总表第 6 列 `raw_dir` → 去重 + 字典序 → 排除这 6 个 legacy 必需目录（`raw/articles` `raw/tweets` `raw/wechat` `raw/pdfs` `raw/notes` `raw/assets`）→ 剩下不存在的按字典序**逗号拼接**；一个都不缺 → `-`

**`validate` 布局校验**（`inspect` / `validate` / `ensure-source-dir` 都先跑，失败则 stderr 逐条 + 退出 1）：
- 必须**存在**（`-e`）：`.wiki-schema.md`、`index.md`、`log.md`、`raw`、`wiki`、`wiki/entities`、`wiki/topics`、`wiki/sources`、`wiki/comparisons`、`wiki/synthesis`、`wiki/overview.md` → 缺失文案 `缺少必要路径：<path>`
- 必须是**目录**（`-d`）：`raw/articles`、`raw/tweets`、`raw/wechat`、`raw/pdfs`、`raw/notes`、`raw/assets` → 缺失文案 `缺少必要旧目录：<path>`
- `wiki_root` 为空 → `usage()` 到 stdout + 退出 1；不是目录 → stderr `知识库不存在：<path>` + 退出 1

**`ensure-source-dir` 额外错误**：未知 `source_id` → stderr `未知来源：<id>` + 退出 1。目录不存在则创建（`mkdir(parents=True, exist_ok=True)`）。

---

## 9. `hook-session-start.py`

**调用**：`python ${SKILL_DIR}/scripts/hook-session-start.py`（**无参数、无子命令**）

| 场景 | stdout | 退出码 |
|---|---|---|
| 无 wiki | `{}\n` | 0 |
| 有 wiki | `{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "[llm-wiki] 检测到知识库: {realpath}/index.md，回答问题时优先查阅 wiki 内容获取上下文"}}`（`ensure_ascii=False`，**末尾带换行**） | 0 |

**wiki 路径解析顺序**：
1. 读 `{HOME}/.llm-wiki-path` 的内容（非空则用，去掉尾随换行）
2. 仍为空且**当前工作目录**下有 `.wiki-schema.md` → 用当前工作目录
3. 仍为空，或 `{路径}/.wiki-schema.md` 不存在 → 输出 `{}`
4. 否则用 `os.path.realpath` 后的绝对路径

---

## 10. `shared-config.sh` → 已删除

只有 204 字节，唯一内容是 `WECHAT_TOOL_URL="git+https://github.com/jackwener/wechat-article-to-markdown.git"`。已**内联进 `adapter-state.py`**（见第 3 节 install_hint 文案），原文件删除，不单独移植成 `.py`。

---

## 移植进度与实测记录

**移植完成度：9/9 个 `.py` + 10/10 个 `.sh` 已删除。实测环境：Windows 11 + PowerShell 5.1.26100 + Python 3.13.0。**

- [x] `init-wiki.py` —— `py_compile` 通过；真实跑通，目录树 15 项 + 7 个文件全对，模板占位符零残留，`{{DATE}}` 为本地日期
- [x] `source-registry.py` —— `py_compile` 通过；8 个子命令全测；`list` / `fields` 的 stdout 与源 TSV **逐字节相同**（1626 / 783 字节完全一致）
- [x] `adapter-state.py` —— `py_compile` 通过；`check` / `summary` / `summary-human` / `classify-run` 全测，**每行均 8 列**
- [x] `cache.py` —— `py_compile` 通过；`MISS → UPDATED → MISS → HIT → INVALIDATED` 生命周期全对
- [x] `lint-runner.py` —— `py_compile` 通过；孤立页 / 断链 / index 不一致三段报告全对
- [x] `validate-step1.py` —— `py_compile` 通过；11 个 JSON 用例（含 4 个非法 confidence、head -3 截断）全对
- [x] `delete-helper.py` —— `py_compile` 通过；命中 / 零命中 / 中文 needle / 大小写敏感 / 空 needle / 目录缺失全对
- [x] `wiki-compat.py` —— `py_compile` 通过；`inspect` / `validate` / `ensure-source-dir` 全对
- [x] `hook-session-start.py` —— `py_compile` 通过；5 个场景（含 BOM、无 wiki、CWD 命中、指针文件命中）全对
- [x] `shared-config.sh` 删除（`WECHAT_TOOL_URL` 已内联进 `adapter-state.py`）
- [x] 10 个 `.sh` 全部删除
- [x] 零第三方依赖（只用 `pathlib` / `json` / `socket` / `shutil` / `hashlib` / `datetime` / `re` / `os` / `sys`）

### 关键实测证据

| 验证项 | 方法 | 结果 |
|---|---|---|
| `source-registry list/fields` 保真 | Python subprocess 比对 stdout 字节 vs 源 TSV 字节 | **完全一致**（1626 / 783） |
| 10 列契约 | 每个返回行做 tab 切分计数 | 全部 10 列 |
| 8 列契约 | `check` / `summary` / `classify-run` 每行计数 | 全部 8 列，含表头行 |
| host 后缀匹配 | `match-url https://sub.twitter.com/...` | 命中 `x_twitter`（`.twitter.com` 规则生效） |
| `url_host:*` 兜底 | `match-url https://www.example.com/a` | 命中 `web_article`，退出 0 |
| Windows 路径 | `match-file C:\tmp\a.PDF` | 命中 `local_pdf`（大小写不敏感） |
| 缓存哈希 | 同一文件 `update` → `check` | `UPDATED` → `HIT` |
| Windows 绝对路径归一化 | `update <file> C:\...\wiki\wiki\sources\x.md` | 落盘为相对路径 `wiki\sources\x.md` |
| 跨盘符/越界路径 | `update <file> D:\...\outside.md` | 保持绝对路径原样 |
| socket 探端口 | 造假 bundled 依赖目录 → `check x_twitter` | `env_unavailable` / `Chrome 调试端口 9222 未监听`（1s 超时，不挂起） |
| `classify-run` 三态 | 退出码非 0 / 空文件 / 无效输出 / 正常 | `runtime_failed` / `empty_result` / `empty_result` / `available` |
| 校验失败文案 | 临时副本注入未知分类、错 `raw_dir`、重复 id、错 `url_host` 前缀、错表头 | 5 条错误文案逐字一致，退出 1，stdout 为空 |
| `validate-step1` head -3 | 4 个非法 confidence | 只列前 3 个 |
| BOM 读取 | `utf-8-sig` 读 `.tsv` / `.json` / `.md` / hook 指针文件 | 全部正常，无 `UnicodeDecodeError` |

### 与 bash 版的已知差异（均为有意为之，调用方无感或仅更宽松）

1. **`usage()` 帮助文本里的命令名**从 `bash scripts/X.sh …` 改成 `python scripts/X.py …`。`.sh` 已删除，保留旧文案会指向不存在的文件。子命令名与参数顺序未变。
2. **Windows 上 stdout 强制 LF**（`reconfigure(newline="\n")`）。Windows 的 `sys.stdout` 默认会把 `\n` 翻成 `\r\n`，导致每个字段行末列多一个 `\r`；强制 LF 后输出与 Linux/bash 原版逐字节一致。**这是本次移植发现的最容易踩的坑。**
3. **`.tsv` 用 `utf-8-sig` 读**。bash 的 `head -n 1` 会把 BOM 算进表头，导致 `expect_header` 误报「表头不匹配」；Python 剥掉 BOM 后表头校验正常。**属于修复，不是放宽。**
4. **`list` / `fields` 重新以 `\n` 输出**。源文件若是 LF 则与 `cat` 逐字节相同；源文件若是 CRLF，bash `cat` 会原样吐 CRLF，Python 统一为 LF。
5. **`validate-step1.py` 去掉了 `jq` 依赖检查**。原脚本缺 `jq` 时退出 1；Python 用标准库 `json`，该失败模式消失。调用方判据是退出码，不受影响。
6. **`validate-step1.py` 对 `entities` 里的非对象元素跳过**。jq 会在第一个非对象元素上中断整条管道（等于漏检后续）；Python 跳过它并继续检查其余元素，属于更严格的检出。
7. **`cache.py` 的绝对路径判定**从 `case /*)` 改为 `os.path.isabs()`。Windows 的 `C:\…` 现在会被正确识别为绝对路径并归一化——原 bash 在 Windows 上会漏判。
8. **缓存键用平台原生分隔符**（`os.path.relpath`）。同一平台内自洽；知识库在 OS 之间迁移时会 MISS 一次（不会写坏缓存）。
9. **`cache.py` 在文件父目录不存在时静默退出 1**（与 bash `set -e` 在 `cd` 失败时一致，不打印额外信息）。
10. **`adapter-state.py` 用 `socket.create_connection(("127.0.0.1", 9222), timeout=1)` 代替 `lsof`**。`lsof` 在 Windows 上不存在；socket 直连跨平台且无外部命令。语义等价（能否连上 9222）。
11. **`env_install_hint` 已按 `sys.platform` 分平台**（移植后由父会话追加修复）。原 bash 版对所有平台都输出 macOS 专用的 `open -na "Google Chrome" …` 和 `brew install uv`；给 Windows/Linux 用户看等于给了条跑不起来的命令。现在 `_chrome_debug_hint()` / `_uv_install_hint()` 分别返回当前平台可执行的命令，三平台文案均已断言。
12. **`init-wiki.py` 用 `str.replace` 代替 `perl -pe`**，对 4 个占位符语义完全一致。
13. **`lint-runner.py` / `delete-helper.py` 不调外部 `grep` / `find` / `mktemp`**，改用 `pathlib.rglob` + 内容判断。`delete-helper` 用 UTF-8 字节子串查找，与 `grep -F` 对 UTF-8 文件等价。
14. **`source-registry` / `adapter-state` / `wiki-compat` 各自内联了一份总表校验器**（约 40 行 × 3）。这是刻意的：任务要求每个脚本自包含可直接执行，不把 `scripts/` 变成包。代价是改校验规则时三处要同步。

### 父会话待办（我无权修改的文件）

- `SKILL.md:134` 和 `SKILL.md:330` 的散文里仍写着 `adapter-state.sh check`，而同文件其它地方已改成 `${PY} …/adapter-state.py`。建议统一。
- `INSTALL.md` 的目录树已不含 `shared-config`，与实际一致。
- 其余 `.sh` 引用在 `zhege-llm-wiki/` 目录内已无残留。
