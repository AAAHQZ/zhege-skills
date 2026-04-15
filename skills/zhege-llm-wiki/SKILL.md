---
name: llm-wiki-assistant
description: 帮助用户使用LLM维护个人知识库wiki。适用于已有LLM Wiki或想要创建LLM Wiki架构的场景，支持ingest（摄入新来源）、query（查询）、lint（健康检查）等操作。
---

# LLM Wiki Assistant

## Overview

本skill帮助用户使用LLM维护个人知识库wiki。这是一个基于LLM的增量式知识管理系统，LLM会主动阅读来源、提取信息、整合到现有wiki中、更新交叉引用、标记矛盾之处。

## When to Use This Skill

- 用户想要创建新的LLM Wiki架构
- 用户需要将新来源（文章、文档、笔记）摄入到wiki
- 用户需要查询wiki中的知识
- 用户需要检查wiki的健康状态（lint）
- 用户需要维护和更新现有的wiki页面

## Core Operations

### 1. 创建Wiki架构

用户想要从头创建LLM Wiki时，执行以下步骤：

1. **创建目录结构**：
   ```
   vault/
   ├── raw/                    # 原始来源文件（不可变）
   ├── wiki/
   │   ├── sources/           # 来源摘要页
   │   ├── entities/          # 实体页面（人物、产品、公司等）
   │   ├── concepts/          # 概念页面（想法、主题等）
   │   ├── comparisons/      # 比较页面
   │   └── synthesis/         # 综合分析页面
   ├── index.md               # 内容索引
   └── log.md                 # 活动日志
   ```

2. **创建AGENT.md schema文件**：包含wiki的结构规范、页面类型、命名约定、工作流程

3. **创建index.md和log.md**：初始的空索引和日志文件

### 2. Ingest（摄入来源）

当用户添加新来源时：

1. 将源文件放入`raw/`目录
2. 执行ingest流程：
   - 读取源文件内容
   - 与用户讨论关键要点
   - 写入来源摘要页到`wiki/sources/`
   - 更新相关实体页面到`wiki/entities/`
   - 更新相关概念页面到`wiki/concepts/`
   - 更新index.md
   - 在log.md中记录摄入

### 3. Query（查询）

当用户向wiki提问时：

1. 首先读取index.md找到相关页面
2. 读取相关页面获取详细信息
3. 综合答案并标注引用来源
4. 如果答案有价值，建议将其存为新的wiki页面

### 4. Lint（健康检查）

定期执行wiki健康检查：

- 检查页面间的矛盾之处
- 检查已被新来源更新的过时声明
- 检查孤立页面（无入链）
- 检查缺失交叉引用的重要概念
- 检查可以填充的数据空白

## Wiki Schema Conventions

### 页面类型

**来源摘要页 (wiki/sources/)**
```markdown
---
type: source
title: [来源标题]
date: [摄入日期]
source: [原始文件路径]
tags: [标签]
---

## 关键要点
[来源的主要观点]

## 主要 claim
[来源的主要论点]

## 数据/引用
[来源中的重要数据]

## 相关实体
- [[Entity Name]]

## 相关概念
- [[Concept Name]]
```

**实体页面 (wiki/entities/)**
```markdown
---
type: entity
name: [实体名称]
tags: [标签]
---

## 描述
[实体的描述]

## 出现来源
- [[Source Name]] - [出现位置描述]

## 相关信息
[相关实体/概念]
```

**概念页面 (wiki/concepts/)**
```markdown
---
type: concept
name: [概念名称]
tags: [标签]
---

## 定义
[概念的定义]

## 出现来源
- [[Source Name]] - [出现位置描述]

## 相关概念
- [[Related Concept]]

## 演变
[概念在不同来源中的变化]
```

### 索引格式 (index.md)
```markdown
# Wiki Index

## 来源 (Sources)
- [[Source Name]] - [一句话摘要] (来源数量: N)

## 实体 (Entities)
- [[Entity Name]] - [一句话摘要] (来源数量: N)

## 概念 (Concepts)
- [[Concept Name]] - [一句话摘要]
```

### 日志格式 (log.md)
```markdown
# Activity Log

## [2026-04-15] ingest | Article Title
- 摄入来源: raw/article.md
- 新增页面: source-article, entity-person, concept-idea
- 更新页面: index, concept-other

## [2026-04-14] query | Topic Question
- 查询: 关于X的跨来源分析
- 回答见: [引用页面]
```

## Resources

### references/

存放AGENT.md模板和工作流参考文档。

### Tips

- **Obsidian Web Clipper**：浏览器插件，快速将网页文章转为markdown
- **下载图片到本地**：在Obsidian设置中配置附件文件夹路径，便于LLM直接查看
- **使用graph view**：查看wiki的连接结构
- **使用Marp**：从markdown生成幻灯片
- **使用Dataview**：对页面frontmatter进行动态查询

## Implementation Note

具体实现细节应根据用户的偏好和领域进行调整。wiki的结构、命名约定、页面格式都可以定制。核心原则是：LLM负责维护，人负责提供来源和提问。