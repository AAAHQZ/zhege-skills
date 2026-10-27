# zhege-kb-to-skill 安装指南

## 这是什么

把一份知识语料（书籍、文档集、法规库、课程笔记）改造成一个**能长期维护的 agent
skill** 的方法与工具。产出是五件套：内容 / 检索层 / 消费契约 / 生产规则 /
校验闸门与变更台账。

## 环境要求

| 要求 | 说明 | 必选 |
|---|---|---|
| Python ≥ 3.9 | 只跑 `scripts/kb_lint.py` 时需要 | 是 |
| PyYAML | **可选**。装了会用它做更严的 frontmatter 解析；没装自动退回内置极简解析 | 否 |
| Git | 校验器不碰 git | 否 |

> 校验器**只用标准库**。装得上 PyYAML 就用，报错信息更准；装不上也能跑。

## 安装

技能目录名与 `SKILL.md` 文件名一致即可被各自的 skill 机制发现。

| Runtime | 技能目录 |
|---------|----------|
| MiniMax Code / mavis | `%USERPROFILE%\.minimax\skills\zhege-kb-to-skill\` |
| Claude Code | `~/.claude/skills/zhege-kb-to-skill/` |
| Codex CLI | `~/.codex/skills/zhege-kb-to-skill/` |
| 其他 | 该 agent 的 skills 目录，结构同 `SKILL.md` + `scripts/` + `references/` |

> **历史约定 `~/.hermes/skills/` 已废弃**，不要再用。

**Linux / macOS：**

```bash
SKILLS="$HOME/.minimax/skills"        # 按上表换成目标 runtime 的目录
cp -r skills/zhege-kb-to-skill "$SKILLS/"
```

**Windows PowerShell：**

```powershell
$SKILLS = "$env:USERPROFILE\.minimax\skills"
Copy-Item -Path skills\zhege-kb-to-skill -Destination $SKILLS -Recurse -Force
```

**本 skill 没有任何外部依赖，也不需要网络。** 纯方法 + 一个只用标准库的校验脚本，装到哪都能用。

### 解释器名

`python3` / `python` / `py` 各平台不同，调用前先探测：

```bash
command -v python3 >/dev/null && PY=python3 || PY=python
```

```powershell
if (Get-Command python -ErrorAction SilentlyContinue) { $PY = "python" }
elseif (Get-Command py -ErrorAction SilentlyContinue)    { $PY = "py" }
else { $PY = "python3" }
```

## 目录结构

```
skills/zhege-kb-to-skill/
├── SKILL.md                      # 主入口：五件套 + 七步工作流
├── INSTALL.md                    # 本文件
├── references/
│   ├── corpus-layouts.md         # 正文按条目切还是按章节切
│   ├── retrieval-layer.md        # 索引怎么建、判据怎么现场取
│   ├── answer-contract.md        # 路由判据 / 追问 / 输出骨架 / 边界
│   ├── change-ledger.md          # append-only 台账 + 贡献入口
│   ├── invariants-and-ci.md      # 不变量→断言→CI + 事故回归测试
│   └── parallelism.md            # 按主题簇切分（并行蒸馏）
├── scripts/
│   └── kb_lint.py                # 通用校验器，只查不改
└── templates/
    ├── consumer-skill.md         # 消费侧 skill 骨架
    └── entry.md                  # 条目模板（两种布局两版）
```

## 校验器用法

```bash
# 从默认配置起步
"$PY" scripts/kb_lint.py --init-config

# 全量校验（只查不改，退出码 0/1/2）
"$PY" scripts/kb_lint.py --repo <库根>

# 只跑某几项
"$PY" scripts/kb_lint.py --repo <库根> --only id-unique,index-sync

# 生成规范索引到 stdout，人工比对后再落盘
"$PY" scripts/kb_lint.py --repo <库根> --emit-index

# 列出全部检查项
"$PY" scripts/kb_lint.py --list-checks
```

> `--init-config` 和 `--emit-index` 把结果打到 **stdout**，不写盘。
> **不要用 shell 重定向 `> file` 落盘**——重定向行为各 shell 不同，`/tmp` 在 Windows 上
> 也不存在。正确做法：用文件写入工具捕获 stdout 内容再落盘（顺带避免 PowerShell 5.1 写出 BOM）。

### 检查项

`fm` `id-pattern` `id-unique` `id-filename` `category-dir` `sections`
`thickness` `label` `chapter-no` `index-sync` `deadlink`

按布局自动分流：`per-entry` 生效 `id-filename` / `category-dir`；
`per-chapter` 生效 `label` / `chapter-no`。

### 退出码

| 码 | 含义 |
|---|---|
| 0 | 全部通过 |
| 1 | 有检查未通过 |
| 2 | 配置或用法错误 |

**2 和 1 要分得开** —— 配置写错导致根本没扫到文件时退出码是 2，而不是静默通过。

## 配置要点

两种布局的完整配置示例见 `references/invariants-and-ci.md` 第五节。三个最容易踩的：

| 配置 | 为什么 |
|---|---|
| `category_strip_numeric_prefix` | 目录带 `NN-` 序号而元数据写裸值时，不开会满屏误报 |
| `index_check_reverse` | 索引是长文档（如 README）时关掉反向检查，否则噪声极大 |
| `disabled_checks` | 布局不适用的检查在这里关掉，不要为了消错而放宽判据 |

**通用脚本要做成布局感知、差异可配。** 硬编码一种约定然后在别的仓库上满屏误报，
比没有这个工具更糟——它会让人忽略真正的报错。

## 配置文件的编码

校验器按 **`utf-8-sig`** 读配置和语料，也就是**容忍 BOM**。

这不是过度设计：Windows 上的 PowerShell 5.1、记事本、部分编辑器在保存 JSON/YAML 时
默认会写 BOM。如果校验器用严格的 `utf-8` 读，用户会得到一个完全看不懂的
「Unexpected UTF-8 BOM」错误，而配置文件本身没有任何问题。

## 故障排除

| 现象 | 原因 / 处理 |
|---|---|
| `配置不是合法 JSON` | 检查括号逗号；确认不是被编辑器写坏了 |
| `没扫到任何语料文件` | `corpus_globs` 路径写错，或被 `exclude_globs` 全排除了。退出码 2 |
| `category-dir` 满屏报 | 确认 `category_strip_numeric_prefix: true` |
| `index-sync` 报满屏 | 索引是长文档时设 `index_check_reverse: false` |
| `deadlink` 误报一堆 | 词表没收干净。往 `deadlink_ignore` 加正则（如书名号、表格行） |
| Windows 终端中文乱码 | 终端编码问题，**不是文件坏了**。用文件读取工具确认 |
| 装不上 PyYAML | 不需要。校验器会自动退回内置极简解析 |

## 在 CI 里接

```yaml
- name: 知识库校验（只读）
  run: |
    if command -v python3 >/dev/null; then PY=python3; else PY=python; fi
    "$PY" scripts/kb_lint.py --repo . --config kb-lint.json
```

> 解释器名别写死：GitHub Actions 的 ubuntu 镜像有 `python3`，
> 别的 runner（尤其自建 / Windows runner）可能只有 `python`。一行探测最省事。

三条原则：

1. **只读** —— 校验器永远不写盘，重建动作留给人本地跑。
   让 CI 往主分支推提交会和本地分叉，且 CI 环境常缺本地才有的依赖
2. **独立 job** —— 不要挂在构建 job 上，校验失败不该连累别的产物发布
3. **和本地同代码同判据** —— 不要写一套「CI 专用」的简化版检查

理由见 `references/invariants-and-ci.md` 第四节。

## 首次接入请做一次「故意造错」

跑通之后**务必做一遍**：随便挑两类典型错误（删掉一个必填字段、删掉一行索引），
跑一次校验，确认它**报出来**。再恢复。

**没验证过会报错的闸门等于没有闸门。** 这一步不能跳。

## 什么时候不该用这个 skill

- 只是总结、翻译、点评**某一篇**材料
- 写一个**不依赖知识库**的一次性脚本
- 已有 skill **答错了内容** —— 那是去改那个 skill 的条目或契约，不是重建流水线

最后一条最容易做错：九成的情况是**条目不够**或**索引没同步**，
先跑一遍 `kb_lint.py` 再决定动不动 SKILL.md。

## 维护

本 skill 自身不做自动校验（所在仓库无 CI）。改完跑：

```bash
"$PY" -m py_compile skills/zhege-kb-to-skill/scripts/kb_lint.py
"$PY" skills/zhege-kb-to-skill/scripts/kb_lint.py --list-checks
```

并人工核对 `SKILL.md` 的 frontmatter 是否完整、所在仓库根 `README.md` 的索引表是否同步。
