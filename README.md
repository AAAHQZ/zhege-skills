# zhege-skills

> zhege-skills

## 简介

这个 skills 仓库是 zhege 的技能仓库，面向各类 AI Agent 提供实用的能力。所有技能以 Markdown 编写，包含触发条件、工作流程和使用说明。

**跨平台**：所有技能都能在 **Windows / macOS / Linux** 上原样运行。
脚本一律是 Python（仅标准库），不依赖任何 shell 或第三方 CLI。
详见 [AGENTS.md](AGENTS.md) 的「跨平台是硬约束」。

## 快速索引

| 技能 | 描述 | 触发词 | 来源 |
|------|------|--------|------|
| brainstorming | 动手前的需求讨论与设计；架构路径产出草稿 spec，交 `to-spec` 定稿 | 头脑风暴 / 需求讨论 / 设计讨论 / 写规格 | 派生自 obra/superpowers；来源见 AGENTS.md「衍生技能来源」 |
| wechat-article-to-markdown | 微信公众号文章转 Markdown（图片本地化） | 微信文章转markdown | 自研（依据微信公开文章页结构） |
| zhege-llm-wiki | 个人知识库构建与维护 | 创建知识库 / 查询知识库 / 摄入知识 | 方法论：Karpathy llm-wiki；实现自研 |
| zhege-handoff | 会话复盘存档 + 决策条目化确认 | 存档这次会话 / 复盘 / 归档会话 | 参考 `mattpocock-skills:handoff`；其余自研 |
| zhege-kb-to-skill | 把知识语料做成可长期维护的 agent skill | 把资料做成 skill / 知识库怎么加内容 / 设计检索层和回答骨架 | 自研 |

每个技能的「来源」详细说明（依据 / 原创部分 / 授权）见其 `SKILL.md` 的 `## 来源` 段；
`brainstorming` 为例外，其来源记录在 `AGENTS.md` 的「衍生技能来源」。
**本仓库未附 LICENSE 文件**，转载或二次分发前请先确认授权。

## 安装到哪个 runtime

技能目录名与 `SKILL.md` 文件名一致即可被发现。

| Runtime | 技能目录 |
|---------|----------|
| MiniMax Code / mavis | `~/.minimax/skills/<name>/` |
| Claude Code | `~/.claude/skills/<name>/` |
| Codex CLI | `~/.codex/skills/<name>/` |
| 其他 | 该 agent 的 skills 目录，结构同 `SKILL.md` + `scripts/` + `references/` |

`~/` 是跨平台记号（Windows 展开为 `C:\Users\<你>`）。
**不要**把路径硬展开成某一台机器的绝对路径。

## 技能详情

### brainstorming

在动手做任何创造性工作之前，先把需求聊清楚、把设计定下来。按工作量分三条路径：**Spike**（可行性问题，只给结论）、**Bounded**（已有代码上的小改动，聊天里给短设计）、**Architectural**（新项目 / 新子系统，产出草稿 spec）。

**触发词：** 头脑风暴 / 需求讨论 / 设计讨论 / 方案设计 / 架构设计 / 写规格

**工作流程（架构路径）：** 探索项目上下文 → 逐个澄清问题 → 提 2-3 个方案 → 分段确认设计 → 写草稿 spec（按 `to-spec` 的章节形状）→ 草稿自审 →（可选）用 `grilling` / `grill-with-docs` 拷问 → 交 `to-spec` 合成并发布。

**与 mattpocock 技能包的关系：** `to-spec` 是本技能的下游（它不提问，只合成会话），`grilling` / `grill-with-docs` 是草稿的可选拷问环节。二者缺失时**只降级不阻塞**：自己写 `docs/specs/` 下的 spec，或按同样轮次手动拷问。

**依赖：** 零依赖（纯 Markdown、无脚本、不联网）。

---

### wechat-article-to-markdown

将微信公众号文章转换为 Markdown 格式，尽可能保留原文格式（标题、加粗、斜体、链接、图片、引用、代码块、列表等），并把图片下载到本地。

**触发词：** 微信文章转markdown / wechat article to markdown / 提取微信公众号内容

**工作流程：**
1. 探测 Python 解释器（`python3` / `python` / `py`）
2. 用 `wechat_to_markdown.py` 直接抓取并转换（**零外部依赖**），或先存 HTML 再传第三个参数
3. 图片下载到 Markdown 同目录

**保留格式：** 加粗、斜体、链接、图片、引用块、代码块、列表、标题

**依赖：** Python ≥ 3.8（仅标准库）。不用 curl / defuddle / 浏览器。

---

### zhege-llm-wiki

基于 LLM 的增量式个人知识库管理系统。LLM 会主动阅读来源、提取信息、整合到现有 wiki 中、更新交叉引用、标记矛盾之处。

**触发词：** 创建知识库 / 查询知识库 / 摄入知识 / 知识库健康检查 / 我的 wiki

**核心操作：**
- **创建**：建立 wiki 目录结构
- **Ingest**：摄入新来源 → 提取要点 → 更新相关页面 → 记录到 log.md
- **Query**：读取 index.md → 检索相关页面 → 综合答案并标注来源
- **Lint**：检查矛盾、过时声明、孤立页面、缺失交叉引用

**依赖：** Python ≥ 3.8。**全部 12 个工具脚本都是 Python（仅标准库），不再有 `.sh`。**
脚本用 `${PY} ${SKILL_DIR}/scripts/<name>.py` 调用，子命令、参数、输出列、退出码与旧版一致。

---

### zhege-handoff

参考 `mattpocock-skills:handoff` 编写。复盘并归档当前会话，把值得长期保留的决策逐条确认后写进项目指令文件或长期记忆。**不绑定特定 agent**：核心流程纯文本，任何 runtime 都能跑，缺能力时按通用兜底降级。

**触发词：** 存档这次会话 / 复盘 / 归档会话 / 整理本次会话 / 把关键决策记下来 / session archive

**工作流程：**
1. 能力探测 → 采集会话（默认用当前上下文；有会话工具则分页拉全量，`before` + `nextCursor` 倒序翻页，只取正文与工具名，丢弃工具返回全文）
2. 写存档到 `<workspace>/docs/session-archives/session-<id>-<时间戳>.md`：元信息 / 一句话结论 / 时间线 / 关键决策 / 未完成 / 踩坑 / 建议能力 / 引用指针 / 降级说明
3. 三问法提取 3–8 条决策候选（换用户会变？换项目还成立？只是临时状态？），先去重
4. **一条一个**确认落点：问卷工具或纯文本编号回复
5. 落盘并回读验证，输出收尾表

**三条硬规则：** 未经逐条确认不写任何持久化文件；已有产物只引用路径不复制正文；报告"已写入"必须有回读结果支撑。

**可移植性：** 只有三处依赖 runtime（跨会话读取、问卷交互、长期记忆写入），每处都有通用兜底。项目层统一写 `AGENTS.md`（AAIF/Linux Foundation 标准，20+ 工具原生读取）；⚠️ Claude Code 不读 `AGENTS.md`，需在 `CLAUDE.md` 写 `@AGENTS.md`。

**资源：** `references/runtime-adapters.md`（各 runtime 路径 + 验证状态）/ `archive-template.md`（存档模板）/ `extraction-rubric.md`（提取判定）/ `persistence-playbook.md`（落盘与验证）

---

### zhege-kb-to-skill

把一份知识语料（书籍、文档集、法规库、笔记）改造成**能长期维护的 agent skill**。核心是把「内容 / 检索 / 消费契约 / 生产规则 / 闸门与台账」五件事分开落位。零依赖、不联网。

**触发词：** 把资料做成 skill / 建知识库 / 这个 skill 怎么加内容 / 怎么防止索引和正文不同步 / 设计检索层 / 设计回答骨架 / 知识库出过一次事故后怎么补防线

**五件套**（混在一起写，短期省事，长期每件都会拖垮另外四件）：

| 件 | 缺了会怎么死 |
|---|---|
| ① 内容独立成目录，绝不进 SKILL.md | 每次调用全量进上下文 |
| ② 检索层（索引 + 判据现场取） | 要么读完 6MB 才敢答，要么瞎猜 |
| ③ 消费契约（另一个薄 skill） | 每次回答结构都不一样，没法验收 |
| ④ 生产规则独立成文件 | 改数据的规矩和消费侧互相污染 |
| ⑤ 只读闸门进 CI + append-only 台账 | 正文悄悄漂了没人知道，改动不可追溯 |

**工作流程：** 判阶段 → 盘点现状 → 定布局（per-entry / per-chapter）→ 建检索层 → 写消费契约（路由判据**带优先序** / 追问纪律 / 输出骨架 / 边界）→ 配闸门 → 开贡献入口 + 定台账

**自带的：** `scripts/kb_lint.py` 通用校验器（11 项检查、两种布局通用、**只查不改**）——2026-10-01 在两个真实仓库上跑通，并实弹抓到过一次正在发生的索引腐化。

**资源：** `references/corpus-layouts.md` / `retrieval-layer.md` / `answer-contract.md` / `change-ledger.md` / `invariants-and-ci.md` / `parallelism.md` + `templates/`

