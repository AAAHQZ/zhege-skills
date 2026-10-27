# zhege-handoff 安装指南

## 简介

复盘并归档当前会话：读取会话历史 → 生成存档 Markdown 到 workspace → 把值得长期保留的决策**逐条**确认后写进项目指令文件（`AGENTS.md` / `CLAUDE.md` 等）或长期记忆。

纯流程型技能，**无脚本、无运行时依赖、无特定 agent 绑定**。只有 Markdown 文件。核心动作（读上下文、写 Markdown、列条目、逐条确认、写文件）任何 agent 都能执行；缺能力时按 `references/runtime-adapters.md` 的通用兜底降级。

## 依赖

- 任意能读写 Markdown 文件、执行基础工具调用的 agent
- **可选增强**（有则更好用，无则降级，不阻塞）：
  - 会话读取工具（mavis `session messages` / 其他 runtime 的转录文件）
  - 结构化问卷工具（mavis `ask_user` 等）
  - 记忆工具（mavis `memory`；无则写纯文本指令文件）
- 无 Python / Node 依赖

## 文件清单

```
zhege-handoff/
├── SKILL.md                              # 主工作流（可移植性原则 + 步骤 0-5）
├── INSTALL.md                            # 本文件
└── references/
    ├── runtime-adapters.md               # 各 runtime 的会话/记忆/问卷/安装路径 + 验证状态
    ├── archive-template.md               # 存档文档章节模板 + 写作规则
    ├── extraction-rubric.md              # 三问法 / 证据分级 / 排除清单 / 正反例
    └── persistence-playbook.md           # 落点映射、AGENTS.md 与 memory 写法、回读验证
```

## 跨 runtime 安装

技能目录名与 `SKILL.md` 文件名一致即可被各自的 skill 机制发现。frontmatter 只需 `name` + `description`，多余的 `triggers` / `argument-hint` 留着无害。

| Runtime | 用户级技能目录 | 状态 |
|---------|---------------|------|
| MiniMax Code | `~/.minimax/skills/<name>/SKILL.md` | ✅ 目录已存在（Windows 上即 `%USERPROFILE%\.minimax\skills\`） |
| Claude Code | `~/.claude/skills/<name>/SKILL.md` | ✅ 目录已存在 |
| Codex CLI | `~/.codex/skills/<name>/SKILL.md` | 📄 未验证 |
| 其他 | 查该 agent 的 skills/plugins 目录，结构同 `SKILL.md` + `references/` | 📄 |

> `~/` 是跨平台记号：Unix 展开为 `/home/<user>` 或 `/Users/<user>`，Windows 展开为 `C:\Users\<user>`。
> **不要**把它硬展开成某一台机器的绝对路径。`~/.hermes/skills/` 是**已废弃**的历史约定。

**通用安装命令**：

```bash
# Linux / macOS
cp -r skills/zhege-handoff "$HOME/.minimax/skills/"
```

```powershell
# Windows
$src = "D:\MiniMaxWork\zhege-skills\skills\zhege-handoff"
$dst = "$env:USERPROFILE\.minimax\skills\zhege-handoff"
New-Item -ItemType Directory -Force -Path "$dst\references" | Out-Null
Copy-Item "$src\SKILL.md"       -Destination $dst -Force
Copy-Item "$src\references\*"  -Destination "$dst\references" -Force
```

> 装完可能需要重启或新开会话，技能才会出现在该 agent 的可用技能列表里。

### 若目标 runtime 是 Claude Code（额外一步）

Claude Code 不原生读 `AGENTS.md`。本技能会往 `AGENTS.md` 写项目层条目，所以仓库里需要补一行导入，否则 Claude Code 侧等于没写：

```markdown
<!-- CLAUDE.md -->
@AGENTS.md
```

或者 `ln -s AGENTS.md CLAUDE.md`（Windows 无 symlink 权限时用 @import）。详见 `references/persistence-playbook.md` 第二节。

## 验证

### 1. 结构校验

```bash
# Linux / macOS
PYTHONUTF8=1 python3 <skill-creator>/scripts/quick_validate.py "skills/zhege-handoff"
```

```powershell
# Windows
$env:PYTHONUTF8='1'   # 必须，否则校验器在中文 SKILL.md 上崩
python "$env:USERPROFILE\.claude\skills\skill-creator\scripts\quick_validate.py" "skills\zhege-handoff"
# 期望输出：Skill is valid!
```

> ⚠️ `quick_validate.py` 用 `Path.read_text()` 且不指定 encoding，Windows 中文环境下按 GBK 解码会抛
> `UnicodeDecodeError: 'gbk' codec can't decode byte ...`。这是校验器自身的问题（仓库里其他中文技能
> 同样会崩），设 `PYTHONUTF8=1` 即可，不要去改 SKILL.md 的编码。

### 2. 触发词

技能加载后应能命中以下说法：

- 存档这次会话 / 复盘 / 归档会话 / 整理本次会话 / 会话存档
- 把关键决策记下来 / session archive
- `/zhege-handoff`

### 3. 降级路径自检

本技能的"通用兜底"是刻意设计的，可以在**任何** runtime 上跑通。验证时确认这三件事成立：

1. 读会话：不给任何会话工具，agent 仍能用**当前上下文**完成复盘（T1 路径）
2. 逐条确认：不给问卷工具，agent 仍能用**纯文本候选表 + 编号回复**完成确认
3. 长期记忆：不给记忆工具，agent 仍能写进**纯文本指令文件**（`AGENTS.md` / `CLAUDE.md`）

三项任一失败，说明实现里混进了对特定工具的硬依赖，需要修。

## 使用方法

### 基本用法

```
用户：/zhege-handoff
用户：把这次会话存档一下，重点看工具选型
```

Agent 会：

1. **能力探测**：确认能不能读会话、有没有问卷工具、有没有记忆工具
2. 采集会话（默认直接用当前上下文；有会话工具则分页拉全量，只取正文与工具名，丢弃工具返回全文）
3. 写存档到 `<workspace>/docs/session-archives/session-<id>-<时间戳>.md`
4. 提取 3–8 条决策候选，每条给出建议落点（项目层 / 用户层 / agent 层）
5. **一条一个**确认：问卷工具或纯文本编号回复
6. 按确认结果落盘，回读验证，给出收尾表 + 降级说明

### 会产出什么

| 产物 | 位置 | 是否需要用户确认 |
|------|------|----------------|
| 存档文档 | `<workspace>/docs/session-archives/session-*.md` | 否 |
| 项目层条目 | `<workspace>/AGENTS.md`（Claude Code 另需 `CLAUDE.md` 里 `@AGENTS.md`） | **是，逐条** |
| 用户层 / agent 层条目 | 有记忆工具则写记忆；否则写该 runtime 的用户级指令文件；都没有则只留在存档里并告知 | **是，逐条** |

## 注意事项

| 问题 | 解决方案 |
|------|---------|
| 换到别的 agent 就跑不起来 | 检查有没有对特定工具的硬依赖；用 INSTALL 第 3 节的三项降级自检定位 |
| 仓库有 `AGENTS.md` 但 Claude Code 没生效 | Claude Code 不读 `AGENTS.md`，需 `CLAUDE.md` 写 `@AGENTS.md` 或 symlink |
| 会话很长，翻页被 runtime 截断 | 把 `limit` 从 20 降到 10 继续翻，不要一次拉完 |
| 上下文被工具结果撑爆 | 只取「字段裁剪」表里的 ✅ 项，丢弃完整工具返回 / token 遥测 / 思考过程 |
| 存档文件开头出现 `ï»¿` | 没用 `write` 工具，用了 PowerShell `Set-Content -Encoding UTF8`（会写 BOM） |
| 用户还没答完就去写文件 | 问卷工具会结束当前 turn；纯文本则必须等下一条消息，必须等 |
| 记忆出现重复条目 | `append` 不去重，先 `search`，修正用 `operation: "edit"` |
| 本 runtime 没有对应记忆层 | 不要硬造 `MEMORY.md`；留在存档「确认结果」里并明说无处可写 |
| 存档里出现密钥 | 脱敏规则见 `references/archive-template.md`，替换为 `***REDACTED***` |
| 存档污染 git 工作区 | 只写 `docs/session-archives/`，是否 commit 由用户决定，技能不自动提交 |
