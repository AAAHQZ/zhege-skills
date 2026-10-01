# Runtime 适配表

技能的核心流程是纯文本操作，任何 agent 都能执行。本文件只记录**三处 runtime 相关的差异**：读会话、逐条确认、写长期记忆，外加技能安装位置。

**验证状态标记**（重要，不要跳过）：

| 标记 | 含义 |
|------|------|
| ✅ | 在本机（Windows + MiniMax Code 桌面端）实际跑过并确认 |
| 📄 | 来自官方文档或社区一致报道，本机未验证 |
| ❓ | 位置/行为未确认，用前先探测，**不要盲写进存档** |

探测命令（跨 runtime 通用的思路）：先 `glob` 候选目录 → `bash` 查存在性 → 命中才用。

---

## A · 读会话历史

### A0 · 通用首选：当前上下文（所有 runtime，无需探测）

刚聊完的会话就在上下文里。**这是默认路径，优先于任何工具。** 只有需要跨会话、或上下文被压缩截断时才往下走。

### A1 · MiniMax Code / mavis ✅

```jsonc
mavis({ command: "session get",      args: { session_id: "me" } })   // → session.sessionId / title / workspaceDir / createdAt / updatedAt
mavis({ command: "session messages", args: { session_id: "me", limit: 20 } })
mavis({ command: "session list",     args: { limit: 20 } })            // 找别的会话 id
```

- `session messages` 返回结构：`messages[]`，每条含 `role` / `msg_content` / `thinking_content` / `tool_calls[]` / `timestamp` / `turn_id`；`tool_calls[]` 含 `tool_name` / `tool_call_args` / `tool_call_status`（经验值 2 成功、3 失败）/ `tool_call_result_data`。
- **`tool_call_result_data` 是上下文炸弹**——`read` 一个文件就会把整份文件内容塞进来。只在需要时取，绝不整段进存档。
- 翻页：把 `nextCursor` 填进下一次调用的 `before`，倒序翻到 `hasMore: false` ✅ 实测。
- 没有 per-command help：`mavis session messages help` 会报 `Unknown mavis command`，用 `mavis session help` 看全组参数。
- 记忆读写也是这个工具家族：`memory({ target, operation })`，详见 persistence-playbook。

### A2 · Claude Code ✅（目录已确认，字段未逐项验证）

| 路径 | 内容 | 备注 |
|------|------|------|
| `~/.claude/projects/<cwd-slug>/<session-uuid>.jsonl` | **全量会话转录** | 本机 18 个 jsonl；slug 把 `D:\Hqz\madou` 转成 `D--Hqz-madou`（反斜杠和冒号都变连字符） |
| `~/.claude/transcripts/ses_<id>.jsonl` | 另一份转录库 | 文件名带 `ses_` 前缀，与 projects 下的 uuid 不是同一套命名 |
| `~/.claude/history.jsonl` | **只有用户输入** | 每行 `{"display": "...", "pastedContents": {}, "timestamp": 1770732181472, "project": "D:\\...", "sessionId": "..."}` ✅ 字段已确认 |
| `~/.claude/todos/`、`plans/`、`shell-snapshots/` | 任务与快照 | 不是会话正文，别当历史读 |

**推荐用法**：`history.jsonl` 当索引（按 `sessionId` / `project` / 时间戳定位这次会话用户问了什么），再按需读对应的 `projects/<slug>/<uuid>.jsonl` 拿全文。

**注意**：Claude Code 自己的当前会话**本来就在上下文里**，通常不需要读文件。

### A3 · Codex CLI 📄

- 全局个人指令：`~/.codex/AGENTS.md`（跨所有仓库生效，官方支持）。
- 会话历史落盘位置：未确认 ❓。优先用 A0；必要时 `glob ~/.codex/**` 探测再决定。

### A4 · Hermes 📄

- 技能目录 `~/.hermes/skills/`（本仓库 README 的约定）；本机**未安装** Hermes，无从验证 ❓。
- 会话历史位置 ❓，用 A0 兜底。

### A5 · 自建 harness / 裸 LLM API 📄

会话就是一个数组（OpenAI `messages` / Anthropic `messages`）。自己实现的话直接遍历当前 messages 数组即可——这就是 A0 的代码形态。同理，跨会话持久化就是把这套 `T1→T2→T3` 阶梯接到自己的存储上。

---

## B · 逐条确认

| 手段 | 条件 | 备注 |
|------|------|------|
| **纯文本候选表**（SKILL.md 步骤 4 方式 B） | 任何支持 Markdown 的对话 | ✅ 通用兜底，无依赖 |
| `ask_user` | mavis / MiniMax Code ✅ | 单次最多 4 个 step，1–4 个选项；`requiresExplicitResponse` 用于最终动作确认；调用后**结束当前 turn** |
| Cursor 计划 / 提问类工具 | Cursor | 📄 各家工具名不同，名字会变，按"有没有结构化问卷"判断 |
| 终端交互提示 | CLI 类 agent | 📄 能跑交互式 CLI 时可用，但**非交互 shell 下会挂住**，慎用 |

**通用原则**：问卷只是体验优化，不是依赖。只要能把候选列成带编号的表，并让用户用一句话回复编号，就满足"一条条确认"。

---

## C · 写长期记忆

### C1 · 项目层：`AGENTS.md`（跨工具事实标准）📄

- 仓库根的纯 Markdown，**无 frontmatter、无 schema、无校验**，60k+ 开源仓库在用，Linux Foundation 下的 Agentic AI Foundation 治理。
- 优先级（官方）：用户当前 prompt > 离被编辑文件最近的 AGENTS.md > 父目录 > 仓库根 > agent 默认。支持 monorepo 嵌套。
- 原生读取：Codex CLI（参考实现）、GitHub Copilot、Cursor、Gemini CLI / Jules、Aider、Zed、Warp、goose、opencode、Factory、Devin/Windsurf、JetBrains Junie、Amp、RooCode、Kilo Code 等。
- **⚠️ 唯一重要例外：Claude Code 不原生读 `AGENTS.md`**（自动加载 `CLAUDE.md`）。同时用 Claude Code 时二选一：
  - `CLAUDE.md` 写一行 `@AGENTS.md`（Claude Code 展开 @import）—— **Windows 推荐，无 symlink 权限问题**
  - `ln -s AGENTS.md CLAUDE.md`（Git 追踪这条 symlink 即可）
  - 静默失败是最坑的形态：只有 AGENTS.md 的仓库在 Claude Code 里等于零项目指令，不报错。

### C2 · 用户层 / agent 层

| Runtime | 项目层 | 用户层（跨项目） | agent 层（经验） |
|---------|--------|----------------|-----------------|
| MiniMax Code / mavis ✅ | `AGENTS.md` | `memory({target:"user"})` | `memory({target:"main"})` |
| Claude Code 📄 | `CLAUDE.md`（+ `@AGENTS.md`） | `~/.claude/CLAUDE.md` | 无内建机制，用文件 |
| Codex CLI 📄 | `AGENTS.md` | `~/.codex/AGENTS.md` | 无 |
| Gemini CLI 📄 | `AGENTS.md` + `GEMINI.md` | `~/.gemini/GEMINI.md` | 无 |
| Cursor 📄 | `AGENTS.md` + `.cursor/rules/*.mdc` | 用户级 rules | 无 |
| Copilot 📄 | `AGENTS.md` + `.github/copilot-instructions.md` | — | 无 |

**没有对应机制时的正确行为**：不要为了填坑硬造 `MEMORY.md` 之类文件。把条目留在存档文档的「确认结果」里，并在报告里明说"本条在本 runtime 无处可写"。凭空造文件的下一次会话不会有人去读。

---

## D · 技能安装位置

| Runtime | 用户级技能目录 | 状态 |
|---------|---------------|------|
| MiniMax Code | `C:\Users\HW\.minimax\skills\<name>\SKILL.md` | ✅ 目录存在（现含 `folder-cleanup-assistant`、`pptx-generator`） |
| Claude Code | `~/.claude/skills/<name>/SKILL.md` | ✅ 目录存在（现含 `skill-creator`、`life-decision-guide`） |
| Hermes | `~/.hermes/skills/...` | 📄 本仓库 README 约定，本机未安装 |
| 官方插件形态 | `<dataDir>/v2/plugin-cache/official/...` | ✅ 官方插件是服务端整包下推，**不可就地改**，要改就走用户级目录 |

**通用**：SKILL.md 的 frontmatter 只需 `name`（`^[a-z0-9-]+$`）+ `description`（不含尖括号）。多余的 `triggers` / `argument-hint` 各家行为不一，但留着无害。

---

## E · 环境坑（跨 runtime 通用）

| 坑 | 表现 | 处理 |
|----|------|------|
| Windows 控制台默认 GBK | Python 脚本 `print` emoji/中文 → `UnicodeEncodeError` | `$env:PYTHONIOENCODING='utf-8'` + `[Console]::OutputEncoding=[Text.Encoding]::UTF8` |
| Python 读文件未指定 encoding | `quick_validate.py` 读中文 SKILL.md → `UnicodeDecodeError: 'gbk'` | `$env:PYTHONUTF8='1'` |
| PowerShell `Set-Content -Encoding UTF8` | 写出 UTF-8 BOM，文件头多 `ï»¿` | 用 `write` 工具写文件 |
| 终端显示乱码 ≠ 文件损坏 | `Get-Content` 打印中文成 `��` | 用 `read` 工具读，别信控制台 |
