# zhege-skills

> zhege-skills

## 简介

这个 skills 仓库是 zhege 的技能仓库，面向 Hermes Agent 提供实用的能力。所有技能以 Markdown 编写，包含触发条件、工作流程和使用说明，可直接安装到 `~/.hermes/skills/` 使用。

## 快速索引

| 技能 | 描述 | 触发词 |
|------|------|--------|
| wechat-article-to-markdown | 微信公众号文章转 Markdown | 微信文章转markdown |
| zhege-llm-wiki | 个人知识库构建与维护 | 创建知识库 / 查询知识库 / 摄入知识 |
| zhege-handoff | 会话复盘存档 + 决策条目化确认 | 存档这次会话 / 复盘 / 归档会话 |

## 技能详情

### wechat-article-to-markdown

将微信公众号文章转换为 Markdown 格式，尽可能保留原文格式（标题、加粗、斜体、链接、图片、引用、代码块、列表等）。

**触发词：** 微信文章转markdown / wechat article to markdown / 提取微信公众号内容

**工作流程：**
1. 用 curl 爬取 HTML 到 `/tmp/wechat_article.html`
2. 用 `wechat_to_markdown.py` 脚本转换为 Markdown
3. 保存到 `/mnt/d/MyLibrary/`

**保留格式：** 加粗、斜体、链接、图片、引用块、代码块、列表、标题

---

### zhege-llm-wiki

基于 LLM 的增量式个人知识库管理系统。LLM 会主动阅读来源、提取信息、整合到现有 wiki 中、更新交叉引用、标记矛盾之处。

**触发词：** 创建知识库 / 查询知识库 / 摄入知识 / 知识库健康检查 / 我的 wiki

**核心操作：**
- **创建**：建立 wiki 目录结构
- **Ingest**：摄入新来源 → 提取要点 → 更新相关页面 → 记录到 log.md
- **Query**：读取 index.md → 检索相关页面 → 综合答案并标注来源
- **Lint**：检查矛盾、过时声明、孤立页面、缺失交叉引用

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
