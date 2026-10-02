# AGENTS.md

zhege-skills —— 面向 AI Agent（MiniMax Code / Claude Code / Codex 等）的技能仓库。每个技能是一个自带触发条件与工作流的 Markdown 目录，可直接安装到各 runtime 的 skills 目录。

## 仓库性质（先读这段）

这是**内容仓库，不是代码项目**：没有 package.json / pyproject.toml，没有 CI，没有测试套件，没有 linter 配置。唯一的"代码"是各技能自带的少量辅助脚本（**全部是 Python**）。

所以：

- 不要发明 `npm test` / `pytest` / CI 步骤 —— 它们不存在
- 改动主体是 Markdown；评审重点是**触发条件是否准确、工作流是否可执行**
- 没有自动化校验兜底，**改完必须自己按下面的命令跑一遍**

## 跨平台是硬约束（先读这段，再写任何代码）

**本仓库的技能必须能在 Windows / macOS / Linux 上原样运行。** 这不是锦上添花，是准入条件。

违反这一条的写法一律不允许进仓库：

| ❌ 不允许 | ✅ 应该 |
|----------|---------|
| `/mnt/d/MyLibrary`、`/tmp/xxx.html`、`C:\Users\某人\` | 由用户指定，或 `~/` / `%USERPROFILE%\` / `tempfile` |
| `~/.hermes/skills/...` 之类的 runtime 绝对路径 | `${SKILL_DIR}` 占位符 + 一张 runtime 目录表 |
| `bash xxx.sh`、`lsof -i :9222`、`diff`、`sed -i` | Python 标准库实现；agent 自带的文件工具 |
| 文档里写死 `python3` 或 `python` | 先探测（Unix 多为 `python3`，Windows 多为 `python`/`py`） |
| `hermes skills add` 之类的单一 runtime CLI | 「列出同级 skills 目录」这种 runtime 无关的探测方式 |
| `export FOO=bar` | 占位符 `${FOO}`，并注明 PowerShell 是 `$env:FOO` |
| shell 重定向 `> out.md` 落盘 | 脚本打到 stdout，agent 用文件写入工具捕获（顺带避免 BOM） |

**理由**：这些写法在作者本机的某个平台上恰好能跑，换台机器就静默失败——`/tmp` 在
Windows 上解析成 `D:\tmp\`（通常不存在，于是走"没找到→重新抓取"这种**不报错但结果不对**
的分支），`bash` 在 PowerShell 下直接命令找不到。**静默失败比崩溃更难查。**

> 历史上本仓库是面向 WSL / Hermes 写的（`~/.hermes/skills/`、`/mnt/d/...`），
> 因此积累了一批上述问题。**现在起不再接受**；改到旧技能时顺手清理。

## 编码与行尾：统一 UTF-8（硬约束）

**所有文本文件必须是 UTF-8 无 BOM + LF 换行。**

这不是审美偏好。中文 Windows 上的坏文件**肉眼看不出来**——在编辑器里打开中文显示得好好的——
但会让下游静默出错：

| 坏编码 | 怎么产生的 | 后果 |
|--------|-----------|------|
| UTF-8 **带 BOM** | PowerShell 5.1 `Set-Content -Encoding UTF8`、记事本、部分编辑器 | `.tsv` 的 BOM 混进表头 → 字段名多一个 `﻿`，不报错，只是每行都多一列 |
| **GBK**（系统 ANSI） | 中文 Windows 默认码页上的老工具 | 脚本读它直接抛 `UnicodeDecodeError`；混进 JSON 配置则整份拒绝服务 |
| **CRLF** | `core.autocrlf=true` 检出 | `.tsv` 每行末尾多 `\r`；shebang 后跟 `\r` 时 Unix 报 `bad interpreter` |

### 三道闸门（缺一道就迟早会漏）

1. **`.editorconfig`** — `charset = utf-8` / `end_of_line = lf`。编辑器侧，让默认值就是对的
2. **`.gitattributes`** — `* text=auto eol=lf` + 显式声明文本扩展名。**注意 git 没有 encoding 属性，强制不了编码**，它只管行尾和「别把中文文件误判成 binary」
3. **`scripts/check_encoding.py`** — 仓库侧，只查不改

```bash
"$PY" scripts/check_encoding.py                 # 检查整个仓库
"$PY" scripts/check_encoding.py --root <目录>   # 检查指定目录
"$PY" scripts/check_encoding.py --only utf8,bom
```

退出码 **0 通过 / 1 有问题 / 2 配置或用法错误**。2 和 1 必须分得开：
配置写错导致根本没扫到文件时是 2，不是静默通过。

### 脚本里的读写策略（两套，别搞混）

| 方向 | 用什么 | 为什么 |
|------|--------|--------|
| **读**外部文件 | `encoding="utf-8-sig"` | **容忍** BOM。用户的配置/语料可能是编辑器另存过的，严格 `utf-8` 会整份拒绝服务 |
| **写**文件 | `encoding="utf-8"`，且不用 PowerShell 的 `Set-Content -Encoding UTF8` | 不制造新的 BOM |
| 读 `.tsv` | `encoding="utf-8-sig"` | 同上，且 BOM 会混进表头导致「表头不匹配」误报 |
| 打印到控制台 | `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` | Windows 控制台默认 GBK，`print` 中文/emoji 会抛 `UnicodeEncodeError` |

**"用 utf-8-sig 读" 不等于 "允许 BOM 存在"** —— 读要容忍，写要避免，检查器要拦住。三件事各管一头。

## 本地校验（无 CI，手动跑）

```bash
"$PY" scripts/check_encoding.py                  # 编码 / BOM / 行尾 / 末尾换行
"$PY" -m py_compile skills/*/scripts/*.py         # Python 语法检查
```

```powershell
$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'; [Console]::OutputEncoding=[Text.Encoding]::UTF8
python scripts\check_encoding.py
Get-ChildItem skills -Recurse -Filter *.py | ForEach-Object { python -m py_compile $_.FullName }
```

改动 SKILL.md 结构后，人工核对两件事：frontmatter 是否完整、根 `README.md` 索引表是否同步。

**改了脚本还要在 PowerShell 里实跑一次**——`py_compile` 只过语法，
`bash` / `lsof` / `/tmp` / BOM 这类问题它一个都查不出来。

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
- Python（**唯一允许的脚本语言**）：仅标准库，不引第三方依赖；`#!/usr/bin/env python3` + 模块 docstring 写清"用法:" + 函数带类型注解与中文 docstring
- 入口加输出编码兜底，否则 Windows 控制台（默认 GBK）打印中文会抛 `UnicodeEncodeError`：
  ```python
  if hasattr(sys.stdout, "reconfigure"):
      sys.stdout.reconfigure(encoding="utf-8", errors="replace")
      sys.stderr.reconfigure(encoding="utf-8", errors="replace")
  ```
- 读文件 / 写文件的 encoding 策略见上面「编码与行尾」，别在这里重复推导
- 路径：只用 `pathlib` / `os.path`，**不拼字符串路径**，不假设分隔符
- 详见上面「跨平台是硬约束」

## 最重要的设计原则：可移植性

**不要把技能绑死在单一 runtime 上。** 这是本仓库的核心约定
- 核心流程用任何 agent 都能执行的纯文本动作表述，不写死某个工具名
- 依赖 runtime 能力的环节（读会话、问卷交互、写长期记忆）写成"增强路径 + 通用兜底"两栏，**缺能力只降级、不阻塞**
- 落点先定**语义层**（项目层 / 用户层 / agent 层），具体文件路径由各 adapter 决定
- 跨工具写项目指令用 `AGENTS.md`（AAIF 标准，20+ 工具原生读）；⚠️ Claude Code 不读它，需要在 `CLAUDE.md` 里写 `@AGENTS.md`
- **OS 维度同理**：绑定 OS 比绑定 runtime 更糟，因为用户换 OS 不会改配置，只会发现技能不工作了

写新技能或改现有技能前，先自查两遍：
1. 有没有把"本机碰巧有的工具"当成流程必经步骤？
2. 有没有把"本机碰巧有的路径"写死？

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
