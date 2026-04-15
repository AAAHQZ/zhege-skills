# zhege-skills

> zhege-skills

## 简介

这个 skills 仓库是 zhege 的技能仓库，面向 Hermes Agent 提供实用的能力。所有技能以 Markdown 编写，包含触发条件、工作流程和使用说明，可直接安装到 `~/.hermes/skills/` 使用。

## 快速索引

| 技能 | 描述 | 触发词 |
|------|------|--------|
| wechat-article-to-markdown | 微信公众号文章转 Markdown | 微信文章转markdown |
| zhege-llm-wiki | 个人知识库构建与维护 | 创建知识库 / 查询知识库 / 摄入知识 |

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
