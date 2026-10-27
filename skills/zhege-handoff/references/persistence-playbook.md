# 落盘手册：项目指令文件与长期记忆

用户逐条确认之后才会执行本手册。**没确认的一律不写。**

原则：**优先写纯文本指令文件**（任何 runtime 都能读、可 diff、可进 git），有记忆工具时再用记忆工具（可分层、可检索）。反过来做会把知识锁死在一个工具里。

---

## 一、语义层 → 物理落点

先定"这条知识的作用域"，再查 `runtime-adapters.md` C 节把它映射到当前 runtime 的具体文件。

| 语义层 | 判据 | 跨工具默认落点 | 本 runtime 的实现 |
|--------|------|--------------|----------------|
| **项目层** | 只在本仓库成立 | `<workspace>/AGENTS.md` | 同左；Claude Code 另需 `CLAUDE.md` 里 `@AGENTS.md` |
| **用户层** | 换项目仍成立、对任何 agent 都适用 | 用户级指令文件 | mavis: `memory(target=user)`；Claude Code: `~/.claude/CLAUDE.md`；Codex: `~/.codex/AGENTS.md` |
| **agent 层** | 与具体用户无关的经验教训 | 无跨工具标准 | mavis: `memory(target=main)`；**其他 runtime 不要硬造文件，见第五节** |

---

## 二、项目层：`AGENTS.md`

### 为什么是 AGENTS.md

纯 Markdown、无 frontmatter、无 schema，60k+ 仓库在用，Linux Foundation 下的 Agentic AI Foundation 治理，Codex / Cursor / Copilot / Gemini CLI / Aider / Zed / opencode / goose / Warp / Devin / Junie / Amp / Windsurf 等 20+ 工具原生读取，支持 monorepo 嵌套（离被编辑文件最近的优先）。

### ⚠️ Claude Code 例外

Claude Code **不原生读 `AGENTS.md`**，只自动加载 `CLAUDE.md`，且**不报错**——只有 AGENTS.md 的仓库在 Claude Code 里等于零项目指令。

同时用 Claude Code 时二选一：

```
# 方案 1（推荐，Windows 无 symlink 权限问题）：CLAUDE.md 写一行
@AGENTS.md

# 方案 2：符号链接，进 git
ln -s AGENTS.md CLAUDE.md
git add AGENTS.md CLAUDE.md && git commit -m "one instruction file for every agent"
```

**若当前 runtime 就是 Claude Code 且仓库还没有 AGENTS.md**：直接写 `CLAUDE.md`；如果仓库已在用 `AGENTS.md` 承载跨工具约定，就补 `@AGENTS.md` 导入，别把同一份约定抄成两份会漂移的文件。

### 写之前

1. `glob` 找根指令文件：`glob(pattern="AGENTS.md", path="<workspace>")`；Claude Code 环境同时 `glob` 一下 `CLAUDE.md`。
2. 找不到 → `write` 新建最小骨架（见下）。
3. 找到了 → `read` 一遍看清现有小节结构，**用 `edit` 追加或插入，绝不整体重写**（重写会毁掉别人写的注释与结构，也会让 diff 无法审阅）。
4. 嵌套项目：离目标目录更近的 AGENTS.md 优先级更高，条目该写近的那份。

### 不存在时的最小骨架

```markdown
# AGENTS.md

<项目名>。给 AI agent 看的项目约定。

## 目录约定

- <条目>

## 工作流约定

- <条目>

## 参考

- <指向 references/ 或 topic 文件的链接，避免 AGENTS.md 无限膨胀>
```

### 小节命名

| 内容类型 | 小节 |
|---------|------|
| 目录结构、文件放哪 | 目录约定 |
| 命令、脚本、必须怎么做 | 工作流约定 |
| 代码风格、命名、格式 | 代码风格 |
| 环境、依赖、平台坑 | 环境约束 |
| 负向约束（不要做什么） | Never / 不要 |
| 指向详细文档 | 参考 |

> 跨项目经验证过的经验：**负向约束往往比正向描述更值钱**（"不要自动发布""不要用 PowerShell 改文件"能挡住最贵的错误），所以给它们独立小节。

条目超过 ~200 行就把同类挪进 `references/<topic>.md`，AGENTS.md 只留一行指针。

---

## 三、用户层 / agent 层：记忆工具

### 三层归属

| target | 存什么 | 判据 |
|--------|--------|------|
| `user` | 这个人的偏好、纠正、硬约束 | 换项目、换场景依然成立 |
| `main` | 这个 agent 的经验教训、工作方式 | 换项目成立、与具体用户无关 |
| `topic` | 某主题下成组的事实 | 需要独立命名的一组内容 |

**有记忆工具时，只能通过 `memory` 工具访问。** 禁止用 `bash` / `read` / `grep` 碰记忆文件路径——那是运行时拥有的数据，绕过工具会拿到不一致的视图。没有记忆工具的 runtime 直接看第四节。

### 合法调用形态

```jsonc
// 读（user 层可能还不存在，也要先读一次确认）
memory({ target: "user", operation: "read" })

// 读全文——去重的可靠做法（记忆文件 KB 级，直接读出来自己比对）
memory({ target: "main", operation: "read" })

// 搜（⚠️ 可能静默返回空，只用来缩小范围，不作为"不存在"的证据）
memory({ target: "main", operation: "search", query: "派子 agent 增量落盘" })

// 追加到 user 层：必须带 reason
memory({
  target: "user",
  operation: "append",
  reason: "用户在本次会话中明确纠正了发布行为，换项目同样适用，属于稳定操作偏好",
  content: "### 发布物默认不公开（2026-10-01）\nType: preference\n默认只落本地，不调用 website_deploy。\n\n**Why:** …\n**How to apply:** …"
})

// 追加到 main 层
memory({ target: "main", operation: "append", content: "### …\nType: lesson\n…" })

// 改已有条目：必须用 edit，append 不去重
memory({ target: "main", operation: "edit", oldString: "<原文>", newString: "<新文>" })
```

### 三条硬规则

1. **`append` 不去重。** 写之前先把已有条目**完整读出来**逐条比对；要修正已有内容用 `operation: "edit"` 配 `oldString` / `newString`。
2. **不要拿 `search` 的空结果当"确认不存在"。** 本机实测 `memory(operation=search)` 无论怎么换关键词都返回 `[]`，而 `read` 能读出全部条目——`search` 静默失效。空结果只能说明"没搜到"，不能说明"不存在"。记忆文件通常不大（KB 级），**直接 `read` 全文自己比对**才是可靠做法。
3. **`user` 层 `append` 必须带 `reason`**，写清"为什么这条值得跨项目保留"。
4. **条目语言跟文件里已有条目保持一致**（中文库写中文，英文库写英文）。代码标识符、路径、命令行保持原样不翻译。

### 条目内部结构

```
### <主题>（<日期>）
Type: preference | lesson | project | reference | environment
<压缩成一句话的结论>

**Why:** <证据 / 根因>
**How to apply:** <以后什么时候按它做>
```

只写 **Why → How to apply**，不写事故时间线、不写完整复盘。

### 绝对不要存

密钥、token、密码、私钥；无关的个人隐私；纯推测；一次性参数；临时任务状态；仓库里本来就有的事实；官方文档能查到的东西；与现有条目重复的内容。

---

## 四、没有记忆工具的 runtime：写纯文本指令文件

没有 `memory` 工具时，**不要为了填坑硬造 `MEMORY.md` 之类文件**——下一次会话不会有人去读它。正确做法是按 runtime 选用户级指令文件：

| Runtime | 用户层落点 |
|---------|-----------|
| Claude Code | `~/.claude/CLAUDE.md` |
| Codex CLI | `~/.codex/AGENTS.md` |
| Gemini CLI | `~/.gemini/GEMINI.md` |
| Cursor | 用户级 rules |
| 其他 | 见 `runtime-adapters.md` C2；确实没有就执行第五节 |

写法与记忆条目一致（`### 主题（日期）` + `Type:` + `Why` / `How to apply`），照样先读后写、用 `edit` 修正而不 `append` 重复。

---

## 五、真的无处可写时

agent 层知识在某些 runtime 里没有落点。**正确行为是把条目留在存档文档的「确认结果」里，并在报告里明说"本条在本 runtime 无处可写，仅存于存档"**。

凭空造一个没人读的文件，比不写更糟：它制造了"已经记住了"的假象。

---

## 六、写完必须回读验证

写完不等于成功。逐个目标回读一次：

```jsonc
read({ path: "<workspace>/AGENTS.md" })       // 确认 edit 落在了正确小节
memory({ target: "user", operation: "read" }) // 确认 append 内容完整
```

对照用户确认的结论**逐字**检查：

- 用户给了改写文案 → 落盘必须是**用户的文案**，不是自己拟的版本
- 用户选了"跳过" → 目标文件里**没有**这条
- 落点层次选错（该进用户层的进了项目层）→ 报告里明说，不要静默
- 目标 runtime 是否有 `@AGENTS.md` 导入 → 没有就提醒，否则 Claude Code 侧等于没写

---

## 七、收尾汇报格式

```
| 条目 | 结论 | 落点 | 状态 |
|------|------|------|------|
| D1 | 交付物默认不公开 | 用户层（mavis memory user） | ✅ 已写入，回读确认 |
| D3 | 引用要给出处 | — | ⏭ 用户跳过 |
| D5 | PowerShell 写中文会带 BOM | agent 层 | ✅ 已存在，未重复写入 |
| D6 | 技能只放仓库 | AGENTS.md「目录约定」 | ❌ 该条已在仓库中，未改动 |

降级情况：本次走的是 T1（当前上下文），无跨会话读取；确认走问卷工具。
跨工具提醒：仓库有 AGENTS.md 但无 CLAUDE.md，Claude Code 侧需要补 @AGENTS.md。
存档文档：<workspace>/docs/session-archives/session-xxxx-YYYYMMDD-HHMM.md
是否 commit？（由用户决定，不自动提交）
```

汇报里每一个"✅ 已写入"都必须有回读结果支撑。没回读就写"已写入"是本技能最严重的失败模式。
