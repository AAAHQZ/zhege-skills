# zhege-llm-wiki 安装指南

## 安装自己

如果你在 Hermes Agent 中，直接说：

```
安装 zhege-llm-wiki 技能
```

或手动执行：

```bash
hermes skills add zhege-llm-wiki
```

---

## 这是什么

zhege-llm-wiki 是你的**个人知识库构建系统**（基于 Karpathy 的 llm-wiki 方法论）。让 AI 持续构建和维护你的知识库，支持批量导入、增量更新、智能检索。

**核心能力**：批量导入文章/网页/视频字幕 → 自动提取结构化知识 → 支持 AI 持续追问

## 环境要求

| 要求 | 说明 | 必选 |
|------|------|------|
| Hermes Agent | 技能运行环境 | 是 |
| Bash | 脚本执行 | 是 |
| Chrome 远程调试 | 网页内容抓取（用于 baoyu-url-to-markdown） | 否 |

> 依赖技能缺失时，核心功能仍可正常使用（手动粘贴文本即可），Chrome 仅用于自动网页抓取。

---

## 安装步骤

### 第一步：安装依赖技能

```bash
# 查看当前已安装技能
hermes skills list

# 安装可选依赖技能（根据需要）
hermes skills add baoyu-url-to-markdown   # 网页/X/知乎提取
hermes skills add wechat-article-to-markdown  # 微信公众号提取
hermes skills add youtube-transcript      # YouTube 字幕提取
```

### 第二步：运行依赖检查

```bash
cd ~/.hermes/skills/zhege-llm-wiki
bash scripts/setup.sh
```

脚本检查内容：
- 依赖技能是否已安装
- 必要命令是否可用
- Chrome 调试端口状态（仅当检测到 `baoyu-url-to-markdown` 时）

### 第三步：配置 Chrome 远程调试（可选）

仅当需要自动抓取网页内容时才需要配置：

```bash
# macOS
open -na "Google Chrome" --args --remote-debugging-port=9222

# Linux / WSL
google-chrome --remote-debugging-port=9222
# 或在 Windows WSL 中
wsl.exe -e google-chrome --remote-debugging-port=9222
```

### 第四步：验证安装

```bash
# 检查技能状态
hermes skills status zhege-llm-wiki
```

验证通过后，说 **"帮我初始化一个知识库"** 即可开始使用。

---

## 目录结构

```
~/.hermes/skills/zhege-llm-wiki/
├── SKILL.md              # 技能定义
├── INSTALL.md            # 本安装指南
├── references/
│   └── AGENT.md          # Wiki Schema 参考
├── templates/            # Wiki 页面模板
└── scripts/              # 工具脚本
    ├── setup.sh          # 依赖检查
    ├── init-wiki.sh      # 初始化知识库
    ├── source-registry.sh
    ├── adapter-state.sh
    ├── cache.sh
    └── lint-runner.sh
```

---

## 快速开始

1. **初始化知识库**（只需一次）
   ```
   帮我初始化一个知识库存到 /mnt/d/MyLibrary/
   ```

2. **导入内容**
   - 粘贴文本：`把这段文字加入知识库`
   - 导入 URL：`帮我把这个链接的内容加入知识库`
   - 批量导入：`把这几个链接都加入知识库`

3. **检索和追问**
   - `在知识库里找关于 xxx 的内容`
   - `最近加了哪些关于 AI 的内容？`

---

## 故障排除

| 问题 | 解决方法 |
|------|---------|
| 提示"依赖技能缺失" | 运行 `bash ~/.hermes/skills/zhege-llm-wiki/scripts/setup.sh` 检查 |
| 网页提取失败 | 确认 Chrome 已启动且调试端口 9222 开放 |
| 脚本执行报错 | 确认 `scripts/` 目录完整，尝试重新安装技能 |
| 知识库初始化失败 | 检查目标路径是否可写，磁盘空间是否充足 |

---

安装完成后，说**"帮我初始化一个知识库"**即可开始使用。
