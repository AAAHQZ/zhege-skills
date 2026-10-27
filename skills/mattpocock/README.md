# mattpocock 技能包（vendored 副本）

这是 [mattpocock/skills](https://github.com/mattpocock/skills.git) 的逐字副本，**MIT 授权**，共 25 个技能。

**不是本仓库自有的技能**，不遵循仓库的技能约定：无 `INSTALL.md`、无 `## 来源` 段、
无 `zhege-` 前缀、不进根 `README.md` 的「快速索引」表。

## 维护

- **不要手改副本内容。** 要改就改上游，或在本仓库另建技能。
- 需要更新时**手动整体替换**目录内容，保持与上游逐字节一致。
- `LICENSE` 是副本的一部分，**不能删**。
- 本 README 是本仓库自己写的说明，不属于上游，替换副本时保留。

## 与仓库硬约束的冲突（照实记录，不「顺手修好」）

- 副本含 `.sh` 脚本（如 `diagnosing-bugs/scripts/hitl-loop.template.sh`、`wizard/template.sh`），
  与本仓库「脚本一律 Python、不用 bash」的跨平台硬约束冲突。**保持上游原样。**
- 这些技能的运行环境要求以各自 `SKILL.md` 为准，本仓库不为它们背书。

## 使用

技能目录名与 `SKILL.md` 文件名一致即可被 runtime 发现。安装路径见根 `README.md`。
注意 **`code-review` 与本仓库或内置技能同名时会遮蔽**。

`brainstorming` 的下游 `to-spec`、可选拷问 `grilling` / `grill-with-docs` 均来自本副本。
