---
name: wechat-article-to-markdown
description: 将微信公众号文章提取为 Markdown 并保存到本地，保留原文格式
triggers:
  - 微信文章转markdown
  - wechat article to markdown
  - 提取微信公众号内容
  - 微信文章格式
---

# WeChat Article to Markdown

将微信公众号文章转换为 Markdown 格式保存在本地，**尽可能保留原文格式**（标题、加粗、斜体、链接、图片、引用、代码块、列表等）。

## 触发条件

- 用户要求提取微信公众号文章内容并保存为 Markdown

## 工作流程

### 步骤 1：用 curl 爬取 HTML

微信公众号文章可以用 curl 直接爬取，浏览器访问被拦截不代表 API 被拦截。

```bash
ARTICLE_URL="https://mp.weixin.qq.com/s/ARTICLE_ID"
curl -s -L \
  -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
  -H "Accept-Language: zh-CN,zh;q=0.9" \
  "${ARTICLE_URL}" -o /tmp/wechat_article.html
```

### 步骤 2：执行转换脚本

转换逻辑已提取到独立脚本 `scripts/wechat_to_markdown.py`，由 terminal 调用：

```bash
python skills/wechat-article-to-markdown/scripts/wechat_to_markdown.py \
  "https://mp.weixin.qq.com/s/ARTICLE_ID" \
  "/mnt/d/MyLibrary"
```

**脚本参数：**
- `ARTICLE_URL` — 原文链接（必填，用于文件头部）
- `SAVE_DIR` — 保存目录（可选，默认为 `/mnt/d/MyLibrary`）

**注意：** 脚本读取 `/tmp/wechat_article.html` 作为输入，需先完成步骤 1 爬取。

### 步骤 3：确认保存结果

```bash
ls -la /mnt/d/MyLibrary/*.md
head -20 /mnt/d/MyLibrary/文章标题.md  # 确认格式保留
```

## 保留的格式

| HTML 元素 | Markdown 格式 |
|-----------|---------------|
| `<strong>`/`<b>` | **加粗** |
| `<em>`/`<i>` | *斜体* |
| `<a href="...">` | [文字](链接) |
| `<img>` | ![图片](url) |
| `<blockquote>` | > 引用块 |
| `<pre>`/`<code>` | ```代码块``` / `行内代码` |
| `<ul>`+`<li>` | 无序列表 |
| `<ol>`+`<li>` | 有序列表 |
| `<h1>`-`<h6>` | #~###### 标题 |
| `<p>` | 段落（空行分隔） |
| `<br>` | 换行 |

## Markdown 输出格式

```markdown
> 原文链接：https://mp.weixin.qq.com/s/ARTICLE_ID

# 文章标题

段落内容，**加粗**和*斜体*都保留了。

> 引用块内容

![图片](https://example.com/image.jpg)

- 列表项 1
- 列表项 2

```
代码块内容
```

正文继续...
```

## 关键经验

| 情况 | 解决方案 |
|------|----------|
| `browser_navigate` 遇到验证 | 正常，用 curl 可以绕过 |
| `execute_code` 超时 | 用 terminal 执行 Python |
| 图片提取失败 | 检查 `data-src` vs `src` 属性 |
| 内容提取失败 | 检查正则中 `\s+` 和 `\s*` 是否匹配实际空格 |
| 标题为空 | 确认 regex `<h1[^>]*>` 使用了 `re.DOTALL` |
| 文件名冲突 | 自动加 `_2`、`_3` 后缀 |