---
name: wechat-article-to-markdown
description: 将微信公众号文章提取为 Markdown 并保存到本地，图片同步下载本地化，永久可访问
triggers:
  - 微信文章转markdown
  - wechat article to markdown
  - 提取微信公众号内容
  - 微信文章格式
  - 微信公众号图片本地化
---

# WeChat Article to Markdown（图片本地化版）

将微信公众号文章转换为 Markdown，**图片下载到本地目录**，避免微信 CDN 链接过期导致图片无法显示。

## 核心改进：图片本地化

- 扫描文章中所有 `<img>`（优先 `data-src` 属性）
- 下载到 Markdown 同目录，命名为 `文章名_image_001.jpg`、`文章名_image_002.png` …
- 自动跳过微信小头像占位图（`w < 100px`）
- 下载失败时降级保留原 CDN URL
- 避免重复下载（已存在则跳过）

## 工作流程

### 方式一：一条命令（推荐）

`defuddle` 负责抓取和格式转换，再由本脚本下载图片：

```bash
ARTICLE_URL="https://mp.weixin.qq.com/s/ARTICLE_ID"
SAVE_DIR="/mnt/d/MyLibrary"

# 1. 用 defuddle 提取内容
defuddle parse "${ARTICLE_URL}" --md -o /tmp/wechat_article.md

# 2. 爬取完整 HTML（含图片 URL）
curl -s -L \
  -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
  -H "Accept-Language: zh-CN,zh;q=0.9" \
  "${ARTICLE_URL}" -o /tmp/wechat_article.html

# 3. 运行脚本（下载图片 + 生成 Markdown）
python ~/.hermes/skills/productivity/wechat-article-to-markdown/scripts/wechat_to_markdown.py \
  "${ARTICLE_URL}" \
  "${SAVE_DIR}"
```

> **注：** 步骤 1（defuddle）和步骤 2（curl）可二选一。curl 保留完整 HTML 结构，适合需要手动调试的场景；defuddle 更快更干净。

### 方式二：自动抓取（无需手动 curl）

脚本内部可自动抓取 HTML，跳过步骤 2：

```bash
python ~/.hermes/skills/productivity/wechat-article-to-markdown/scripts/wechat_to_markdown.py \
  "https://mp.weixin.qq.com/s/ARTICLE_ID" \
  "/mnt/d/MyLibrary"
```

### 步骤 3：确认结果

```bash
# 查看生成的 Markdown 和本地图集
ls -lh /mnt/d/MyLibrary/文章名_image_*.{jpg,png,webp,gif} 2>/dev/null
head -5 /mnt/d/MyLibrary/文章标题.md
grep "image_" /mnt/d/MyLibrary/文章标题.md  # 确认图片引用的是本地文件
```

## 保留的格式

| HTML 元素 | Markdown 格式 |
|-----------|---------------|
| `<strong>`/`<b>` | **加粗** |
| `<em>`/`<i>` | *斜体* |
| `<a href="...">` | [文字](链接) |
| `<img>`（data-src） | ![图片](文章名_image_001.jpg)（**本地路径**） |
| `<img>`（src 下载失败） | ![图片](https://原CDN链接)（降级保留） |
| `<blockquote>` | > 引用块 |
| `<pre>`/`<code>` | ```代码块``` / `行内代码` |
| `<ul>`+`<li>` | 无序列表 |
| `<ol>`+`<li>` | 有序列表 |
| `<h1>`-`<h6>` | #~###### 标题 |
| `<p>` | 段落（空行分隔） |
| `<br>` | 换行 |

## 图片本地化规则

| 情况 | 处理方式 |
|------|----------|
| `data-src` 属性存在 | 优先下载 `data-src` 地址 |
| 只有 `src` 属性 | 下载 `src` 地址 |
| 图片 `w < 100px` | 判定为小头像占位符，**跳过下载** |
| 图片 < 2KB | 判定为占位符，**跳过下载** |
| 下载超时/失败 | 保留原始 URL 作为 fallback |
| 文件已存在 | **跳过**（不重复下载） |
| 无扩展名或未知扩展名 | 默认为 `.jpg` |
| 请求频率 | 每张图片间隔 0.3 秒（防封禁） |

## 输出示例

```markdown
> 原文链接：https://mp.weixin.qq.com/s/XXXXXXXX

# 文章标题

![img](文章名_image_001.jpg)

正文内容，**加粗**和*斜体*都保留了。

> 引用块内容

- 列表项 1
- 列表项 2

```代码块内容
```

正文继续...
```

生成的目录结构：
```
/mnt/d/MyLibrary/
├── AIAgent工程实践_image_001.jpg  ← 文章图片 1（带文章名前缀）
├── AIAgent工程实践_image_002.png  ← 文章图片 2
├── AIAgent工程实践_image_003.webp ← 文章图片 3
└── AIAgent工程实践.md              ← 最终 Markdown
```

## 关键经验

| 情况 | 解决方案 |
|------|----------|
| defuddle 可用 | 优先使用，自动保留格式；再跑本脚本下载图片 |
| defuddle 失败/不可用 | 用 curl 爬取 HTML，再跑本脚本 |
| 图片下载失败 | 降级为原 CDN URL 引用，文章仍可读 |
| 重复运行同一篇文章 | 图片已存在则跳过，Markdown 追加 `_2` 后缀 |
| 标题为空 | 备用：从 `var msg_title` 全局变量中提取 |
| 内容提取失败 | 检查正则中 `\s+` 和 `\s*` 是否匹配实际空格 |
| browser_navigate 遇到验证 | 用 defuddle 或 curl 可以绕过，无需浏览器 |
