# AGENT.md - LLM Wiki Schema

这是LLM Wiki的配置文件，告诉LLM Agent如何维护wiki的结构和约定。

## Directory Structure

```
vault/
├── raw/                    # 原始来源文件（不可变）
│   ├── articles/          # 文章
│   ├── papers/            # 论文
│   ├── notes/             # 笔记
│   └── assets/            # 图片等资源
├── wiki/                  # LLM生成的wiki页面
│   ├── sources/          # 来源摘要页
│   ├── entities/          # 实体页面
│   ├── concepts/         # 概念页面
│   ├── comparisons/      # 比较页面
│   └── synthesis/        # 综合分析页面
├── index.md               # 内容索引
└── log.md                 # 活动日志
```

## Page Types

### 1. Source Page (wiki/sources/)
记录每个摄入的来源。

Frontmatter:
- type: source
- title: 来源标题
- date: 摄入日期 YYYY-MM-DD
- source: raw/中的原始文件路径
- tags: 标签列表

Content:
- 关键要点 (2-3句话)
- 主要claim (1-2个)
- 重要数据/引用
- 相关实体列表
- 相关概念列表

### 2. Entity Page (wiki/entities/)
记录人物、公司、产品等实体。

Frontmatter:
- type: entity
- name: 实体名称
- tags: 标签列表

Content:
- 一句话描述
- 详细描述
- 出现来源列表（带引用）
- 相关实体
- 相关概念

### 3. Concept Page (wiki/concepts/)
记录想法、主题、理论等概念。

Frontmatter:
- type: concept
- name: 概念名称
- tags: 标签列表

Content:
- 定义
- 详细解释
- 出现来源列表（带引用）
- 相关概念
- 演变（不同来源中的变化）

### 4. Comparison Page (wiki/comparisons/)
比较多个实体或概念。

Content:
- 比较维度表格
- 每个维度的详细分析
- 结论

### 5. Synthesis Page (wiki/synthesis/)
综合多个来源的分析。

Content:
- 主题/问题
- 关键发现
- 来源综合
- 待解决的问题

## Naming Conventions

- 使用kebab-case: `elon-musk.md`, `transformer-model.md`
- 英文优先，保留原语言术语
- 避免特殊字符

## Cross-Referencing

使用Obsidian风格的wikilinks:
- `[[page-name]]` - 链接到wiki页面
- `[[page-name|显示文本]]` - 带显示文本的链接
- `[来源](raw/file.md)` - 链接到原始文件

## Workflows

### Ingest Workflow
1. 读取raw/中的新文件
2. 与用户讨论关键要点
3. 创建source page
4. 更新或创建相关entity pages
5. 更新或创建相关concept pages
6. 更新index.md
7. 记录到log.md

### Query Workflow
1. 读取index.md找到相关页面
2. 读取相关页面
3. 综合答案
4. 标注引用来源
5. 建议是否需要存为新页面

### Lint Workflow
1. 检查矛盾：对比相关页面的声明
2. 检查过时：标记被新来源更新的内容
3. 检查孤立：找出无入链的页面
4. 检查缺失：找出提及但无专页的概念
5. 报告并修复

## Index Format

```markdown
# Index

## Sources
| Page | Summary | Date | Sources |
|------|---------|------|---------|
| [[source-name]] | 一句话摘要 | YYYY-MM-DD | N |

## Entities
| Page | Type | Summary | Sources |
|------|------|---------|---------|
| [[entity-name]] | person/company/product | 一句话摘要 | N |

## Concepts
| Page | Summary | Sources |
|------|---------|---------|
| [[concept-name]] | 一句话摘要 | N |
```

## Log Format

```markdown
# Log

## [YYYY-MM-DD] type | Title
- 操作描述
- 新增/更新的页面列表
```