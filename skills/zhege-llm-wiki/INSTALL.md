# zhege-llm-wiki 安装指南

## 环境要求

- **Hermes Agent** — 技能运行环境
- **Bash** — 脚本执行需要
- **Chrome**（可选）— 用于 baoyu-url-to-markdown 网页提取

## 安装步骤

### 1. 安装依赖技能

本技能依赖以下技能，建议提前安装：

```bash
# 查看已安装技能
hermes skills list

# 安装所需依赖技能（如果缺失）
hermes skills add baoyu-url-to-markdown
hermes skills add wechat-article-to-markdown
hermes skills add youtube-transcript
```

> 即使依赖技能缺失，核心功能仍可通过手动粘贴文本使用。

### 2. 运行依赖检查

首次使用前，运行检查脚本确认环境就绪：

```bash
cd ~/.hermes/skills/zhege-llm-wiki
bash scripts/setup.sh
```

该脚本会检查：
- 依赖技能是否已安装
- 必要命令是否可用
- Chrome 调试端口状态（如需网页提取）

### 3. 配置 Chrome 远程调试（可选，仅网页提取需要）

如果使用 `baoyu-url-to-markdown` 进行网页提取，需要配置 Chrome 远程调试：

```bash
# macOS
open -na "Google Chrome" --args --remote-debugging-port=9222

# Linux / WSL
google-chrome --remote-debugging-port=9222
# 或
wsl.exe -e google-chrome --remote-debugging-port=9222
```

### 4. 验证安装

```bash
# 检查技能状态
hermes skills status zhege-llm-wiki

# 或直接说"帮我初始化一个知识库"开始使用
```

## 目录结构

技能安装后目录结构：

```
~/.hermes/skills/zhege-llm-wiki/
├── SKILL.md              # 技能定义
├── INSTALL.md            # 本安装指南
├── references/
│   └── AGENT.md          # Wiki Schema 参考
├── templates/            # Wiki 页面模板
└── scripts/              # 工具脚本
    ├── setup.sh          # 依赖检查脚本
    ├── init-wiki.sh      # 初始化知识库
    ├── source-registry.sh
    ├── adapter-state.sh
    ├── cache.sh
    ├── lint-runner.sh
    └── ...
```

## 依赖清单

| 依赖 | 类型 | 用途 | 必装 |
|------|------|------|------|
| baoyu-url-to-markdown | 技能 | 网页/X/Twitter/知乎提取 | 否 |
| wechat-article-to-markdown | 技能 | 微信公众号提取 | 否 |
| youtube-transcript | 技能 | YouTube 字幕提取 | 否 |
| Chrome 远程调试 | 环境 | 网页内容抓取 | 否 |

## 故障排除

| 问题 | 解决方法 |
|------|---------|
| 提示"依赖技能缺失" | 运行 `setup.sh` 或手动安装缺失技能 |
| 网页提取失败 | 确认 Chrome 调试端口 `9222` 已打开 |
| 脚本执行报错 | 检查 `scripts/` 目录是否完整 |

---

安装完成后，说"帮我初始化一个知识库"即可开始使用。
