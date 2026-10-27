# mattpocock 技能包（vendored 副本）

这是 [mattpocock/skills](https://github.com/mattpocock/skills) 的逐字副本，**MIT 授权**，共 **27 个技能**。

**不是本仓库自有的技能**，不遵循仓库的技能约定：无 `INSTALL.md`、无 `## 来源` 段、
无 `zhege-` 前缀、不进根 `README.md` 的「快速索引」表。

## 上游 pin

| 项 | 值 |
|---|---|
| 上游仓库 | <https://github.com/mattpocock/skills.git> |
| pin 到 | `main` 分支 `59db609`（2026-10-27，`Close blank issues and route requests by kind (#1169)`） |
| 大致版本 | 上游 release **1.3.1** 之后、尚未发版的若干修复 commit |
| 上一版 pin | `006a52b`（2026-08-15，`chore: rename repo's own CONTEXT.md to GLOSSARY.md`） |

只取上游已发布的两个 bucket：`skills/engineering/`（20 个）与 `skills/productivity/`（7 个）。
上游的 `in-progress/`、`misc/`、`deprecated/` 三个 bucket **不收**（前两者是未定型的实验技能，
后者是上游自己归档下来的）。

## 目录形态：与上游不同的三处处置

上游是两层结构（`skills/engineering/tdd/SKILL.md`），本仓库**压平成一层**
（`skills/mattpocock/tdd/SKILL.md`），因为 runtime 的 skills 目录只扫一层，安装方式就是
「把整个 `<name>/` 拷进 `~/.claude/skills/`」，两层结构会扫不到。

| 上游 | 本副本 | 为什么 |
|---|---|---|
| `engineering/<skill>/`、`productivity/<skill>/` | 同名目录直接放在本目录下 | 一层可被发现 |
| bucket 级 `README.md`（engineering / productivity 的目录说明） | 不收，压缩成本文件末尾的「技能清单」 | 那两个文件讲的是上游 plugin 怎么打包，不是技能内容 |
| 每个技能里的 `agents/openai.yaml` | **收**（本轮起） | Codex 的 UI/调用策略元数据（`interface.*`、`policy.allow_implicit_invocation`）；缺了它 Codex 侧没有 display name，用户触发的技能也不会被排除在隐式调用之外 |

除上表的搬运之外，每个技能目录内的文件与上游**逐字节一致**（UTF-8 无 BOM + LF）。

## 本次更新（`006a52b` → `59db609`）改了什么

**新增 3 个工程技能**

- `implement-spec`：一次性实现整个 spec。把 tickets 当任务图，在各自 worktree 里并行跑
  implementer subagent，全部落到一条集成分支，最后交 `code-review` 收尾。
- `pr`：PR 正文该有的形状——用最小的可视化（伪代码 / 调用树 / 文件树 / Mermaid / diff）说清变更，
  再给 before-after 证据和「合并危险度」判断（单向门还是双向门 + 爆炸半径）。
- `retro`：复盘一次开发会话，改的是 **agent 的环境**而不是代码（导航指针、自动检查、
  编码规范、steering 文件、工具经济性、信息可达性），并按严重程度排序。

**删除 1 个**

- `resolving-merge-conflicts`：上游 1.3.0 明确移除，**没有替代技能**，冲突处理直接走普通流程。

**重命名（会影响项目里的文件）**

- `domain-modeling/CONTEXT-FORMAT.md` → `domain-modeling/GLOSSARY-FORMAT.md`。
- 上游把领域文档约定从 `CONTEXT.md` / `CONTEXT-MAP.md` 改成了 `GLOSSARY.md` / `GLOSSARY-MAP.md`，
  `domain-modeling`、`grill-with-docs`、`improve-codebase-architecture`、`setup-matt-pocock-skills`、
  `triage`、`tdd`、`diagnosing-bugs`、`code-review`、`codebase-design`、`wait-what`、`pr` 都只认新名字。
  **项目里已有 `CONTEXT.md` 的，`git mv` 改名**，否则技能会当作「没有领域文档」。

**其余实质改动**

- `wizard/template.sh`：readline 行为、`.env` 引号、软链、EOF、打开器告警等一批修复。
- `setup-matt-pocock-skills`：issue tracker 模板命令（`gh` / `glab`）修正、创建 triage 标签、
  兼容遗留 `CONTEXT.md`、仓库可达性检查。
- `code-review` / `tdd` / `diagnosing-bugs` / `teach` / `wayfinder` / `to-tickets` / `implement` /
  `grilling` / `handoff` / `wait-what`：步骤与措辞修正（跨技能调用统一成「call the Skill tool」、
  子 agent 描述去掉 Claude Code 专有名词、`grilling` 每轮之间加 `---` 等）。

完整 changelog 见上游 `CHANGELOG.md`（**不随副本收录**，本目录只放技能本体）。

## 技能清单

「调用方式」照抄上游 bucket README 的分法：**用户触发**的技能模型不会自己调，
**模型触发**的技能模型也能主动用。

### 工程（engineering，20 个）

| 技能 | 调用 | 做什么 |
|---|---|---|
| `ask-matt` | 用户 | 不知道该用哪个技能时问它，用户触发技能的路由表 |
| `grill-with-docs` | 用户 | 拷问式面谈，同时就地打磨领域模型、更新 `GLOSSARY.md` 与 ADR |
| `triage` | 用户 | 按 triage 角色状态机推动 issue |
| `improve-codebase-architecture` | 用户 | 扫描可「加深」的模块，出 HTML 可视化报告，再逐个拷问 |
| `setup-matt-pocock-skills` | 用户 | 每个仓库跑一次：配置 issue tracker、triage 标签、领域文档布局 |
| `to-spec` | 用户 | 把当前会话合成 spec 并发到 issue tracker |
| `to-tickets` | 用户 | 把计划 / spec / 会话拆成 tracer-bullet tickets，并声明阻塞关系 |
| `implement` | 用户 | 按 spec 或 tickets 施工，在约定 seam 上走 `tdd`，收尾 `code-review` |
| `implement-spec` | 用户 | 整个 spec 一次做完：tickets 当任务图并行实现，落一条集成分支 |
| `wayfinder` | 用户 | 把一个超出单次会话容量的大工程规划成 issue tracker 上的决策地图 |
| `retro` | 用户 | 会话复盘：改 agent 环境（导航、检查、规范、steering、工具）而不是代码 |
| `prototype` | 模型 | 做一个一次性原型回答问题：单个可分享 HTML，或几套可切换 UI 变体 |
| `diagnosing-bugs` | 模型 | 硬 bug / 性能回退的诊断循环：先做出会变红的反馈回路，再最小化、假设、埋点、修、回归 |
| `research` | 模型 | 派后台 agent 查一手来源，落成带引用的 Markdown |
| `tdd` | 模型 | 红绿重构，一次一个纵向切片 |
| `domain-modeling` | 模型 | 主动打磨领域模型：挑战术语、用场景压测、就地更新 `GLOSSARY.md` 与 ADR |
| `codebase-design` | 模型 | 深模块设计的共享词汇与纪律：小接口、干净 seam、从接口可测 |
| `code-review` | 模型 | 两轴评审：Standards（仓库规范 + Fowler 坏味道基线）与 Spec（是否忠实实现来源 issue） |
| `pr` | 模型 | PR 正文的形状：最小可视化摘要 + before/after 证据 + 合并危险度判断 |
| `wizard` | 模型 | 生成交互式 bash 向导，带人走只有人能做的步骤（开账号、配密钥、点第三方后台、一次性迁移） |

### 效率（productivity，7 个）

| 技能 | 调用 | 做什么 |
|---|---|---|
| `grill-me` | 用户 | 把自己的计划 / 设计往死里问，直到设计树的每个分支都有结论 |
| `handoff` | 用户 | 把当前会话压缩成交接文档，让另一个 agent 接着干 |
| `teach` | 用户 | 跨多次会话教一个技能 / 概念，用当前目录当有状态的教学工作区 |
| `to-questionnaire` | 用户 | 你一个人答不了的决定，做成一份给「能答的那个人」的 Markdown 问卷 |
| `wait-what` | 用户 | 某句话没听懂时立刻用：agent 用 `GLOSSARY.md` 里的词、补上缺的上下文重讲一遍 |
| `grilling` | 模型 | 拷问式面谈的执行内核（`grill-me` / `grill-with-docs` 共用的那一层） |
| `writing-for-agents` | 模型 | 写给 agent 看的文档：skills、`AGENTS.md` / `CLAUDE.md`、任何靠指针抵达的文档 |

## 维护

- **不要手改副本内容。** 要改就改上游，或在本仓库另建技能。
- 需要更新时**手动整体替换**目录内容，保持与上游逐字节一致，并在上面「上游 pin」表里记下新 pin。
- `LICENSE` 是副本的一部分，**不能删**。
- 本 README 是本仓库自己写的说明，不属于上游，替换副本时保留（并同步更新 pin 与清单）。
- 上游删掉的技能、改名的文档要在这里点名——否则下一个维护者不知道自己的 `CONTEXT.md` 为什么失效。

## 与仓库硬约束的冲突（照实记录，不「顺手修好」）

- 副本含 `.sh` 脚本（`diagnosing-bugs/scripts/hitl-loop.template.sh`、`wizard/template.sh`），
  与本仓库「脚本一律 Python、不用 bash」的跨平台硬约束冲突。**保持上游原样。**
- 这些技能会用到 `gh` / `glab` 等外部 CLI，并要求联网发 issue。
- 这些技能的运行环境要求以各自 `SKILL.md` 为准，本仓库不为它们背书。

## 使用

技能目录名与 `SKILL.md` 里的 `name` 一致即可被 runtime 发现。安装路径见根 `README.md`。

注意 **`code-review` 与本仓库或内置技能同名时会遮蔽**。

`brainstorming` 的下游 `to-spec`、可选拷问 `grilling` / `grill-with-docs` 均来自本副本
（本轮更新后三者仍在，名字与触发条件未变）。
