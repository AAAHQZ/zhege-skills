# brainstorming 安装指南

## 这是什么

在动手做任何创造性工作（新功能、新组件、行为变更）**之前**，先把需求聊清楚、
把设计定下来。按工作量分三条路径：

| 路径 | 适用 | 产物 |
|---|---|---|
| Spike | 可行性问题（"能不能…"） | 一个结论，不保留代码 |
| Bounded | 已有代码上的小改动 | 一段聊天里的短设计 |
| Architectural | 新项目 / 新子系统 / 接口重构 | **草稿 spec** → `to-spec` 定稿发布 |

架构路径的草稿可用 `grilling` / `grill-with-docs` 拷问，再交给 mattpocock 的
`to-spec` 合成并发布到 issue tracker。

## 环境要求

| 要求 | 说明 | 必选 |
|---|---|---|
| 纯 Markdown 流程 | 需求讨论、设计、草稿 spec、`to-spec` 交接 | 是 |
| `to-spec` 技能 | mattpocock 技能包之一；缺失时降级为本地写 `docs/specs/` | 否（增强） |
| `grilling` / `grill-with-docs` | 拷问草稿；缺失时可按同样的轮次手动进行 | 否（增强） |

> **本技能零依赖、零脚本、不联网。** 需求讨论、草稿、`to-spec`、`grilling`
> 全部是纯文本动作，在任何 agent、任何 OS 上一致。

## 安装

技能目录名与 `SKILL.md` 文件名一致即可被各自的 skill 机制发现。

| Runtime | 技能目录 |
|---------|----------|
| MiniMax Code / mavis | `%USERPROFILE%\.minimax\skills\brainstorming\` |
| Claude Code | `~/.claude/skills/brainstorming/` |
| Codex CLI | `~/.codex/skills/brainstorming/` |
| 其他 | 该 agent 的 skills 目录，结构同 `SKILL.md` |

**Linux / macOS：**

```bash
SKILLS="$HOME/.minimax/skills"        # 按上表换成目标 runtime 的目录
cp -r skills/brainstorming "$SKILLS/"
```

**Windows PowerShell：**

```powershell
$SKILLS = "$env:USERPROFILE\.minimax\skills"
Copy-Item -Path skills\brainstorming -Destination $SKILLS -Recurse -Force
```

## 目录结构

```
skills/brainstorming/
├── SKILL.md                          # 主入口：三路径 + 工作流
├── INSTALL.md                        # 本文件
└── spec-document-reviewer-prompt.md  # 草稿 spec 的独立 reviewer 提示词
```

## 与 `to-spec` / `grilling` 的关系

- **`to-spec`（mattpocock）** 是本技能架构路径的**下游**：它不提问，只把当前会话
  合成 spec 并发布到 issue tracker。所以需求访谈必须在本技能里做完。
- `to-spec` 依赖 issue tracker 与 triage 标签词表。未配置时提示用户运行
  `/setup-matt-pocock-skills`。
- **`grilling` / `grill-with-docs`（mattpocock）** 是草稿的**可选拷问**环节：
  `grilling` 做不留情面的设计树访谈；`grill-with-docs` 额外产出 ADR 与 glossary。
- 两个 mattpocock 技能缺失时**只降级不阻塞**：`to-spec` 缺 → 自己写
  `docs/specs/YYYY-MM-DD-<topic>-design.md`；grilling 缺 → 按同样的轮次手动拷问。

## 验证

改完 `SKILL.md` 后人工核对：

1. frontmatter 的 `name` 与目录名一致
2. `triggers` 覆盖中文触发词
3. 架构路径的终态是「交给 `to-spec`」，没有残留的 implementation plan 步骤
4. 根 `README.md` 的「快速索引」表已同步

本技能不带脚本，无需 `py_compile` 或运行验证。

## 故障排除

| 现象 | 原因 / 处理 |
|---|---|
| 不知道走哪条路径 | 拿不准就选更重的那条；中途发现隐藏复杂度只升级不降级 |
| 用户已给足约束还在追问 | 直接把理解回写请对方确认，不要重复问已知信息 |
| `to-spec` 找不到 | 正常降级：自己写 `docs/specs/` 下的 spec，再请用户 review |
| `to-spec` 报 issue tracker 未配置 | 让用户运行 `/setup-matt-pocock-skills` |
| 草稿越聊越大 | 触发 scope check，拆成子项目，各自走 spec → `to-spec` → 实现 |

## 来源

来源信息记录在仓库根 `AGENTS.md` 的「衍生技能来源」一节，不放在 `SKILL.md`。
