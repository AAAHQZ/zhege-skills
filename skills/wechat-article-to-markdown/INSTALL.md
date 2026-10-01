# wechat-article-to-markdown 安装指南

## 简介

将微信公众号文章提取为 Markdown 并保存到本地，图片同步下载本地化。

## 依赖

| 依赖 | 必选 | 说明 |
|---|---|---|
| Python ≥ 3.8 | **是** | 只用标准库：`re` / `html` / `os` / `pathlib` / `tempfile` / `urllib`。无需 pip 装包 |
| 网络 | 是 | 抓取文章 HTML 与图片 |
| 浏览器 / curl / defuddle | **否** | 全部是可选增强，缺了不影响主流程 |

**本技能不依赖任何 shell，也不依赖任何第三方 CLI。** 这是它跨平台的前提。

## 安装步骤

技能目录名与 `SKILL.md` 文件名一致即可被各自的 skill 机制发现。
frontmatter 只需 `name` + `description`，多余的 `triggers` 留着无害。

### 目标目录

| Runtime | 技能目录 | 本机状态 |
|---------|----------|----------|
| MiniMax Code / mavis | `%USERPROFILE%\.minimax\skills\<name>\` | ✅ 已安装 |
| Claude Code | `~/.claude/skills/<name>/` | ✅ 目录存在 |
| Codex CLI | `~/.codex/skills/<name>/` | 📄 未验证 |
| 其他 | 查该 agent 的 skills/plugins 目录，结构同 `SKILL.md` + `scripts/` | 📄 |

> **历史约定 `~/.hermes/skills/productivity/<name>/` 已废弃**，不要再用。

### Linux / macOS

```bash
SKILLS="$HOME/.minimax/skills"          # 按上表换成目标 runtime 的目录
mkdir -p "$SKILLS/wechat-article-to-markdown/scripts"
cp SKILL.md "$SKILLS/wechat-article-to-markdown/"
cp scripts/wechat_to_markdown.py "$SKILLS/wechat-article-to-markdown/scripts/"
```

### Windows PowerShell

```powershell
$SKILLS = "$env:USERPROFILE\.minimax\skills"   # 按上表换成目标 runtime 的目录
New-Item -ItemType Directory -Force -Path "$SKILLS\wechat-article-to-markdown\scripts" | Out-Null
Copy-Item SKILL.md "$SKILLS\wechat-article-to-markdown\" -Force
Copy-Item scripts\wechat_to_markdown.py "$SKILLS\wechat-article-to-markdown\scripts\" -Force
```

> 装完可能需要重启或新开会话，技能才会出现在该 agent 的可用技能列表里。

## 验证

### 1. 结构校验

```bash
PYTHONUTF8=1 python3 <skill-creator>/scripts/quick_validate.py <技能目录>
```

```powershell
$env:PYTHONUTF8='1'    # 必须，否则校验器在中文 SKILL.md 上崩
python "$env:USERPROFILE\.claude\skills\skill-creator\scripts\quick_validate.py" "<技能目录>"
# 期望输出：Skill is valid!
```

> ⚠️ `quick_validate.py` 用 `Path.read_text()` 且不指定 encoding，Windows 中文环境下按 GBK
> 解码会抛 `UnicodeDecodeError: 'gbk' codec can't decode byte ...`。这是校验器自身的问题，
> 设 `PYTHONUTF8=1` 即可，**不要去改 SKILL.md 的编码**。

### 2. 触发词

技能加载后应能命中：

- 微信文章转markdown / wechat article to markdown
- 提取微信公众号内容 / 微信文章格式 / 微信公众号图片本地化

### 3. 跨平台自检

在**当前**平台上确认这四件事成立：

1. **解释器能跑**：`python scripts/wechat_to_markdown.py` 打印用法而不是报「不是内部或外部命令」
2. **默认输出目录可写**：不传 `SAVE_DIR` 时落到 `~/WeChatArticles`（Windows: `C:\Users\<你>\WeChatArticles`）
3. **不碰盘符**：脚本里不应出现 `/mnt/`、`/tmp/`、`C:\` 这类硬编码路径
4. **中文输出不崩**：PowerShell 下执行不抛 `UnicodeEncodeError`

Windows 上终端显示中文乱码是**显示层**问题，不代表文件坏了——
用文件读取工具打开同一个文件确认。

## 使用方法

### 基本用法

```
用户：请帮我把这篇文章转成 Markdown：https://mp.weixin.qq.com/s/xxxxxxxx
```

Agent 会：

1. 探测 Python 解释器（`python3` / `python` / `py`）
2. 确定输出目录：用户指定 > `$WECHAT_SAVE_DIR` > `~/WeChatArticles`
3. 直接抓取 HTML 并转换（不需要先 curl）
4. 下载图片到输出目录，生成 `文章标题.md`

### 显式指定输出目录

```bash
"$PY" scripts/wechat_to_markdown.py "https://mp.weixin.qq.com/s/xxx" "$HOME/MyLibrary"
```

```powershell
$PY "scripts\wechat_to_markdown.py" "https://mp.weixin.qq.com/s/xxx" "$env:USERPROFILE\MyLibrary"
```

### 复用已下载的 HTML（调试用）

第三个参数传 HTML 文件路径，跳过抓取：

```bash
"$PY" scripts/wechat_to_markdown.py "$ARTICLE_URL" "$SAVE_DIR" "/path/to/article.html"
```

## 注意事项

| 问题 | 解决方案 |
|------|----------|
| 换到别的 OS/agent 就跑不起来 | 检查有没有硬编码盘符、`/tmp/`、`~/.hermes/` 绝对路径 |
| Windows 上 `python3` 不存在 | 用 `python` 或 `py`，见 SKILL.md「跨平台约定」② |
| 浏览器打开微信文章被拦截 | 正常，脚本走 `urllib` 直接抓，无需浏览器 |
| 文件名冲突 | 自动加 `_2`、`_3` 后缀 |
| 内容提取失败 | 检查正则中 `\s+` 和 `\s*` 是否匹配实际空格 |
| PowerShell 中文乱码 | 终端编码问题，**不是文件坏了**，用文件读取工具确认 |
| 生成的 Markdown 开头出现 `ï»¿` | 没用 `write` 工具，用了 PowerShell `Set-Content -Encoding UTF8`（会写 BOM） |
