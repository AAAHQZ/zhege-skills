# zhege-skills

> zhege 的 Hermes Agent 技能仓库

## 简介

这个 skills 仓库是 zhege 的技能仓库，面向 Hermes Agent 提供实用的内容提取和转换能力。所有技能以 Markdown 编写，包含触发条件、工作流程和使用说明，可直接安装到 `~/.hermes/skills/` 使用。

## 快速索引

| 技能 | 描述 | 触发词 |
|------|------|--------|
| wechat-article-to-markdown | 微信公众号文章转 Markdown | 微信文章转markdown |

## 技能详情

### wechat-article-to-markdown

将微信公众号文章转换为 Markdown 格式，尽可能保留原文格式（标题、加粗、斜体、链接、图片、引用、代码块、列表等）。

**触发词：** 微信文章转markdown / wechat article to markdown / 提取微信公众号内容

**工作流程：**
1. 用 curl 爬取 HTML 到 `/tmp/wechat_article.html`
2. 用 `wechat_to_markdown.py` 脚本转换为 Markdown
3. 保存到 `/mnt/d/MyLibrary/`

**保留格式：** 加粗、斜体、链接、图片、引用块、代码块、列表、标题
