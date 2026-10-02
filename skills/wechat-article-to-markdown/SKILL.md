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

## 跨平台约定（动手前先读这一节）

本技能**不写死任何盘符、系统临时目录或 shell**。Windows / macOS / Linux 通用。

**① 定位 skill 目录**（脚本路径都从这里拼，不要写绝对路径）：

```bash
# Linux / macOS
SKILL_DIR=~/.minimax/skills/wechat-article-to-markdown        # 本 runtime
# SKILL_DIR=~/.claude/skills/wechat-article-to-markdown     # Claude Code
```

```powershell
# Windows PowerShell
$SKILL_DIR = "$env:USERPROFILE\.minimax\skills\wechat-article-to-markdown"
```

> 换 runtime 就换这一行。仓库里的原路径 `~/.hermes/skills/productivity/...`
> 是历史约定，**已废弃**，按上表选当前 agent 的技能目录。

**② 定位 Python 解释器**（`python3` / `python` / `py` 三个名字各平台不一样）：

```bash
command -v python3 >/dev/null && PY=python3 || PY=python
```

```powershell
if (Get-Command python -ErrorAction SilentlyContinue) { $PY = "python" }
elseif (Get-Command py -ErrorAction SilentlyContinue)    { $PY = "py" }
else { $PY = "python3" }
```

**③ 输出目录**：必须由用户指定，或设环境变量。**不要**写死 `/mnt/d/MyLibrary`
这类路径——那是某台 WSL 机器的约定，在 Windows 上会解析成当前盘符根下的
`D:\mnt\d\MyLibrary`，在其他机器上也不存在。

```bash
export SAVE_DIR="${WECHAT_SAVE_DIR:-$HOME/WeChatArticles}"
```

```powershell
$SAVE_DIR = if ($env:WECHAT_SAVE_DIR) { $env:WECHAT_SAVE_DIR } else { "$env:USERPROFILE\WeChatArticles" }
```

**④ 外部工具一律可选，用前先探测**：`defuddle` 和 `curl` 都不是必需依赖。
脚本自身会用标准库 `urllib` 抓取。缺哪个都不阻塞流程。

## 工作流程

### 方式一：一条命令（推荐）

脚本会自己抓取 HTML，**这是唯一不需要任何外部工具的路径**：

```bash
ARTICLE_URL="https://mp.weixin.qq.com/s/ARTICLE_ID"
"$PY" "${SKILL_DIR}/scripts/wechat_to_markdown.py" "${ARTICLE_URL}" "${SAVE_DIR}"
```

```powershell
$PY "${SKILL_DIR}\scripts\wechat_to_markdown.py" $ARTICLE_URL $SAVE_DIR
```

### 方式二：先下载 HTML 再转换（需要调试或换抓取工具时）

如果想自己控制抓取（比如换 UA、抓下来的 HTML 要人工检查），先存成文件再传第三个参数：

```bash
"$PY" -c "import sys,urllib.request as u; open(sys.argv[2],'wb').write(u.urlopen(urllib.request.Request(sys.argv[1],headers={'User-Agent':'Mozilla/5.0','Accept-Language':'zh-CN,zh;q=0.9'}),timeout=20).read())" \
  "${ARTICLE_URL}" "${HTML_FILE}"
"$PY" "${SKILL_DIR}/scripts/wechat_to_markdown.py" "${ARTICLE_URL}" "${SAVE_DIR}" "${HTML_FILE}"
```

```powershell
Invoke-WebRequest -Uri $ARTICLE_URL -OutFile $HTML_FILE -Headers @{ "Accept-Language" = "zh-CN,zh;q=0.9" }
$PY "${SKILL_DIR}\scripts\wechat_to_markdown.py" $ARTICLE_URL $SAVE_DIR $HTML_FILE
```

> 用 `python -c` / `Invoke-WebRequest` 而不是 `curl`，是因为 curl 在 Windows 上
> 不一定有（Win10 1803+ 才内置 `curl.exe`），而上面两个在三个平台都自带。
> 已有 HTML 时跳过这步直接调脚本。

### 步骤 3：确认结果

```bash
# 生成的 Markdown 和本地图集
ls -1 "${SAVE_DIR}" | grep '_image_'
head -5 "${SAVE_DIR}/文章标题.md"
grep -c "image_" "${SAVE_DIR}/文章标题.md"   # 确认图片引用的是本地文件
```

```powershell
Get-ChildItem "$SAVE_DIR" -Filter *_image_* | Select-Object -ExpandProperty Name
Get-Content "$SAVE_DIR\文章标题.md" -TotalCount 5 -Encoding UTF8
(Select-String -Path "$SAVE_DIR\文章标题.md" -Pattern "image_").Count
```

> PowerShell 读中文文件必须带 `-Encoding UTF8`，否则控制台按 GBK 显示成乱码。
> **那是显示层问题，不代表文件坏了**——用文件读取工具打开同一个文件就是正常中文。

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

生成的目录结构（`${SAVE_DIR}` 由用户指定，不写死）：
```
<SAVE_DIR>/
├── AIAgent工程实践_image_001.jpg  ← 文章图片 1（带文章名前缀）
├── AIAgent工程实践_image_002.png  ← 文章图片 2
├── AIAgent工程实践_image_003.webp ← 文章图片 3
└── AIAgent工程实践.md              ← 最终 Markdown
```

## 关键经验

| 情况 | 解决方案 |
|------|----------|
| 脚本自己抓就够了 | **默认走这条**，零外部依赖，三平台通用 |
| 想换抓取工具 / 调试 HTML | 用方式二先存 HTML，再传第三个参数 |
| `python3` 命令不存在 | Windows 上是 `python` 或 `py`，见「跨平台约定」② |
| 图片下载失败 | 降级为原 CDN URL 引用，文章仍可读 |
| 重复运行同一篇文章 | 图片已存在则跳过，Markdown 追加 `_2` 后缀 |
| 标题为空 | 备用：从 `var msg_title` 全局变量中提取 |
| 内容提取失败 | 检查正则中 `\s+` 和 `\s*` 是否匹配实际空格 |
| PowerShell 终端显示 `��` | 终端编码问题，**文件是好的**，用文件读取工具确认 |
| 浏览器打开微信文章被拦截 | 正常，脚本走 `urllib` 直接抓，无需浏览器 |
