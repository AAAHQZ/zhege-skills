# zhege-llm-wiki 安装指南

## 这是什么

zhege-llm-wiki 是你的**个人知识库构建系统**（基于 Karpathy 的 llm-wiki 方法论）。让 AI 持续构建和维护你的知识库，支持批量导入、增量更新、智能检索。

**核心能力**：批量导入文章/网页/视频字幕 → 自动提取结构化知识 → 支持 AI 持续追问

## 环境要求

| 要求 | 说明 | 必选 |
|------|------|------|
| Python ≥ 3.8 | **全部脚本仅用标准库**，无第三方依赖 | **是** |
| 任意支持 skill 的 agent | 技能运行环境 | 是 |
| 联网 | 抓取在线素材 | 否（纯本地素材不需要） |
| Chrome 远程调试 | 仅网页自动抓取（baoyu-url-to-markdown） | 否 |

> **本技能不含任何 shell 脚本。** 全部工具是 Python 脚本，跨 Windows / macOS / Linux 通用。
> 唯一的外部依赖是 Python 本身。

## 安装步骤

### 第一步：装到目标 runtime 的技能目录

技能目录名与 `SKILL.md` 文件名一致即可被各自的 skill 机制发现。

| Runtime | 技能目录 |
|---------|----------|
| MiniMax Code / mavis | `%USERPROFILE%\.minimax\skills\zhege-llm-wiki\` |
| Claude Code | `~/.claude/skills/zhege-llm-wiki/` |
| Codex CLI | `~/.codex/skills/zhege-llm-wiki/` |
| 其他 | 该 agent 的 skills 目录 |

> **历史约定 `~/.hermes/skills/` 已废弃**，不要再用。

**Linux / macOS：**

```bash
SKILLS="$HOME/.minimax/skills"        # 按上表换成目标 runtime 的目录
cp -r zhege-llm-wiki "$SKILLS/"
```

**Windows PowerShell：**

```powershell
$SKILLS = "$env:USERPROFILE\.minimax\skills"
Copy-Item -Path zhege-llm-wiki -Destination $SKILLS -Recurse -Force
```

### 第二步：装可选的素材提取 skill

这三个都是**可选增强**，缺任何一个都不阻塞——用户可以手动粘贴文本：

| skill | 用途 | 对应 `source-registry.py` 的 `adapter_name` |
|-------|------|------------------------------------------|
| `wechat-article-to-markdown` | 微信公众号 | `wechat-article-to-markdown` |
| `baoyu-url-to-markdown` | 网页 / X / 知乎 | `baoyu-url-to-markdown` |
| `youtube-transcript` | YouTube 字幕 | `youtube-transcript` |

装法同上——拷到同一个 skills 目录即可。**不要**用某个 runtime 专属的包管理 CLI，
本仓库不假设你装了哪个 agent 的 CLI。

### 第三步：验证安装

```bash
"$PY" "${SKILL_DIR}/scripts/source-registry.py" list
```

期望输出 10 列（`source_id` / `source_label` / `source_category` / `input_mode` /
`match_rule` / `raw_dir` / `adapter_name` / `dependency_name` / `dependency_type` /
`fallback_hint`）且退出码为 0。

> Windows PowerShell 上先设编码，否则打印中文可能崩：
> `$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'`
> 终端仍显示乱码是**显示层**问题，文件本身是好的。

验证通过后，说 **"帮我初始化一个知识库"** 即可开始使用。

### 第四步（可选）：配置 Chrome 远程调试

**仅当**需要自动抓取网页内容（`adapter_name=baoyu-url-to-markdown`）时才需要：

| 平台 | 命令 |
|------|------|
| macOS | `open -na "Google Chrome" --args --remote-debugging-port=9222` |
| Linux | `google-chrome --remote-debugging-port=9222` |
| Windows | `& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222` |

端口探测由 `adapter-state.py check` 完成（Python socket 直连 `127.0.0.1:9222`），
**不用 `lsof`**——那是 Linux/macOS 专属命令。

## 目录结构

```
<skills-dir>/zhege-llm-wiki/
├── SKILL.md              # 技能定义
├── INSTALL.md            # 本安装指南
├── references/
│   └── AGENT.md          # Wiki Schema 参考
├── templates/            # Wiki 页面模板（14 份，含中英双份的 index/log/overview/purpose）
└── scripts/              # 工具脚本（全部 Python 3，仅标准库）
    ├── init-wiki.py                  # 初始化知识库
    ├── lint-runner.py                # 批量 lint 入口
    ├── validate-step1.py             # 单步校验
    ├── source-registry.py            # 来源总表读写
    ├── source-registry.tsv           # 来源总表数据
    ├── source-record-contract.tsv    # 来源记录字段契约
    ├── adapter-state.py              # 外挂状态判定
    ├── cache.py                      # 缓存管理
    ├── delete-helper.py              # 删除辅助
    ├── hook-session-start.py         # 会话启动钩子
    └── wiki-compat.py                # 旧版 wiki 兼容
```

> 早期版本这里是 12 个 `.sh` 脚本。已全部移植为 Python——
> bash 在 Windows PowerShell 下不可用，且 `lsof` / `set -o pipefail` 等是 Linux/macOS 专属。
> 迁移自旧版的用户请改用 `python scripts/xxx.py` 调用，**子命令、参数、输出列、退出码完全一致**。

## 快速开始

1. **初始化知识库**（只需一次）
   ```
   帮我初始化一个知识库
   ```
   知识库路径让用户给，**不要**写死 `/mnt/d/MyLibrary` 之类的机器专属路径。

2. **导入内容**
   - 粘贴文本：`把这段文字加入知识库`
   - 导入 URL：`帮我把这个链接的内容加入知识库`
   - 批量导入：`把这几个链接都加入知识库`

3. **检索和追问**
   - `在知识库里找关于 xxx 的内容`
   - `最近加了哪些关于 AI 的内容？`

## 故障排除

| 现象 | 原因 / 处理 |
|------|-------------|
| `python3: command not found` / `无法将"python3"项识别` | 换 `python` 或 `py`，见 SKILL.md「Script Directory」② |
| 脚本找不到 | `SKILL_DIR` 拼错。用文件读取工具确认 SKILL.md 实际安装位置 |
| 提示"依赖 skill 缺失" | 正常降级路径，按 `fallback_hint` 引导用户手动粘贴内容。**不要**用 runtime 专属 CLI 去"修复" |
| 网页提取失败 | 确认 Chrome 已启动且 9222 端口开放，或直接改用手动粘贴 |
| 打印中文时 `UnicodeEncodeError` | 设 `PYTHONIOENCODING=utf-8`（脚本已内置 reconfigure 兜底，仍报错说明终端配置极端） |
| PowerShell 终端显示 `��` | **终端编码问题，不是文件坏了**。用文件读取工具确认 |
| 知识库初始化失败 | 检查目标路径是否可写，磁盘空间是否充足 |

## 维护

改完脚本后自检：

```bash
"$PY" -m py_compile scripts/*.py
"$PY" scripts/source-registry.py list
"$PY" scripts/adapter-state.py summary-human
```

并人工核对 `SKILL.md` 里引用的脚本名与 `scripts/` 下实际文件名是否一致。
