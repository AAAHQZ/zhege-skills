# wechat-article-to-markdown 安装指南

## 简介

将微信公众号文章提取为 Markdown 并保存到本地。

## 依赖

- `curl`（命令行 HTTP 客户端）
- Python 3（标准库，无需额外包：`re`, `html`, `os`）

## 安装步骤

### 方法一：复制到 Hermes skills 目录

```bash
# 创建技能目录
mkdir -p ~/.hermes/skills/productivity/wechat-article-to-markdown/scripts

# 复制技能文件
cp wechat-article-to-markdown/SKILL.md \
   ~/.hermes/skills/productivity/wechat-article-to-markdown/

# 复制转换脚本
cp wechat-article-to-markdown/scripts/wechat_to_markdown.py \
   ~/.hermes/skills/productivity/wechat-article-to-markdown/scripts/
```

### 方法二：从当前 workspace 同步

```bash
cp wechat-article-to-markdown/SKILL.md \
   ~/.hermes/skills/productivity/wechat-article-to-markdown/

cp wechat-article-to-markdown/scripts/wechat_to_markdown.py \
   ~/.hermes/skills/productivity/wechat-article-to-markdown/scripts/
```

## 验证

技能加载成功后，应能看到以下触发词：

- 微信文章转markdown
- wechat article to markdown
- 提取微信公众号内容

## 使用方法

### 基本用法

用户提供微信公众号文章链接（如 `https://mp.weixin.qq.com/s/xxxx`）后：

1. 用 curl 爬取 HTML
2. 用 Python 正则提取标题和正文
3. 保存为 Markdown 到 `/mnt/d/MyLibrary/`

### 示例

```
用户：请帮我把这篇文章转成 Markdown：https://mp.weixin.qq.com/s/xxxxxxxx
```

Agent 会：
1. 提取 `ARTICLE_ID = xxxxxxxx`
2. 执行 curl 爬取
3. 执行 Python 提取
4. 保存到 `/mnt/d/MyLibrary/文章标题.md`

## 文件格式

```markdown
> 原文链接：https://mp.weixin.qq.com/s/ARTICLE_ID

# 文章标题

正文内容...
```

## 注意事项

| 问题 | 解决方案 |
|------|----------|
| 浏览器打开微信文章被拦截 | 正常，用 curl 可以绕过 |
| execute_code 超时 | 用 terminal 执行 Python 脚本 |
| 文件名冲突 | 自动加 `_2`、`_3` 后缀 |
| 内容提取失败 | 检查正则中 `\s+` 和 `\s*` 是否匹配实际 HTML |