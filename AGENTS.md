# AGENTS.md

zhege-skills —— 面向 AI Agent（Hermes / Claude Code / Codex 等）的技能仓库。每个技能是一个自带触发条件与工作流的 Markdown 目录，可直接安装到各 runtime 的 skills 目录。

## 仓库性质（先读这段）

这是**内容仓库，不是代码项目**：没有 package.json / pyproject.toml，没有 CI，没有测试套件，没有 linter 配置。唯一的"代码"是各技能自带的少量辅助脚本（1 个 Python + 若干 Bash）。

所以：

- 不要发明 `npm test` / `pytest` / CI 步骤 —— 它们不存在
- 改动主体是 Markdown；评审重点是**触发条件是否准确、工作流是否可执行**
- 没有自动化校验兜底，**改完必须自己按下面的命令跑一遍**

## 本地校验（无 CI，手动跑）

```bash
bash -n skills/*/scripts/*.sh                # Bash 语法检查
python -m py_compile skills/*/scripts/*.py   # Python 语法检查
```

改动 SKILL.md 结构后，人工核对两件事：frontmatter 是否完整、根 `README.md` 索引表是否同步。

## 技能目录约定

每个技能 = `skills/<kebab-case-name>/`：

| 路径 | 必需 | 说明 |
|---|---|---|
| `SKILL.md` | ✅ | 主入口：frontmatter + 工作流步骤 |
| `INSTALL.md` | ✅ | 依赖、安装路径、验证方法、故障排查表 |
| `references/*.md` | 选 | 拆出去的细则（模板、判定标准、adapter 清单） |
| `scripts/*` | 选 | 辅助脚本；纯流程型技能可以完全不带脚本 |
| `templates/*.md` | 选 | 生成物模板 |

frontmatter 必填 `name` 与 `description`；`triggers`（触发词列表）建议写全，`argument-hint` 仅在支持参数时加。个人技能统一 `zhege-` 前缀。

## Code style

- **文档与注释一律中文**，命令、路径、专有名词保持原样不翻译
- Bash：`#!/bin/bash` + 顶部注释写清用途与用法 + `set -euo pipefail`（确需容忍未定义变量时降为 `set -u`）+ `usage()` heredoc + 显式退出码并在文件头说明含义
- Python：仅标准库，不引第三方依赖；`#!/usr/bin/env python3` + 模块 docstring 写清"用法:" + 函数带类型注解与中文 docstring
- 路径：文档与脚本面向 **WSL / Hermes** 环境（`~/.hermes/skills/`、`/mnt/d/...`），而本仓库在 Windows 上开发 —— 写路径前先想清楚是给谁用的

## 最重要的设计原则：可移植性

**不要把技能绑死在单一 runtime 上。** 这是本仓库的核心约定
- 核心流程用任何 agent 都能执行的纯文本动作表述，不写死某个工具名
- 依赖 runtime 能力的环节（读会话、问卷交互、写长期记忆）写成"增强路径 + 通用兜底"两栏，**缺能力只降级、不阻塞**
- 落点先定**语义层**（项目层 / 用户层 / agent 层），具体文件路径由各 adapter 决定
- 跨工具写项目指令用 `AGENTS.md`（AAIF 标准，20+ 工具原生读）；⚠️ Claude Code 不读它，需要在 `CLAUDE.md` 里写 `@AGENTS.md`
写新技能或改现有技能前，先自查：有没有把"本机碰巧有的工具"当成流程必经步骤。

## Testing instructions
无自动化测试。改动后按上面「本地校验」跑一遍，并至少手工走一次技能工作流的关键步骤（`zhege-llm-wiki` 的 init/lint、`wechat-article-to-markdown` 的抓取转换）。

## PR & commit conventions
- 从 `main` 切分支，不要直接推 `main`
- Conventional Commits，描述用中文：`feat(wechat): 图片下载到本地` / `docs: update README` / `fix(wiki): 修正 ingest 路径`
- **新增或重命名技能，必须同步更新根 `README.md` 的「快速索引」表和「技能详情」章节** —— 那是目前唯一的索引来源
- 合并前确认 README 索引与 `skills/` 实际目录一致

## Security
- 不提交密钥、token、cookie；`.env` 等本地配置不入库
- 技能脚本会抓取外部网页（curl / urllib）：只做公开内容的 GET 读取，不绕过登录态，不写入用户凭据
- 生成物（抓取的 HTML、下载的图片、缓存、session archives）不入库，仓库只提交技能定义本身
