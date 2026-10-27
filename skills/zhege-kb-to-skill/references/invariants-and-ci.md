# 不变量 → 断言 → CI

> 校验器的价值不在于「跑起来报了多少错」，在于**它拦住过一次真实事故**。
> 所以最后一步自检永远是：**故意造一个错，看它报不报。**

---

## 一、把不变量翻译成断言

不变量是给人看的规矩，断言是给机器跑的判据。翻译表：

| 不变量 | 断言（机器能判） | `kb_lint.py` 检查项 |
|---|---|---|
| 元数据格式合法 | frontmatter 能解析 | `fm` |
| 必填字段齐全 | 每个条目都有 id/title/category/sources | `fm` |
| id 全局唯一 | 集合去重后长度不变 | `id-unique` |
| 文件名 == id | 逐条比对 | `id-filename` |
| 分类与目录一致 | 剥掉 `NN-` 前缀后相等 | `category-dir` |
| 条目够厚 | `len(body) >= 阈值` | `thickness` |
| 结构完整 | 必需小节逐个 `in body` | `sections` |
| 索引与正文同步 | 索引里的 id 集合 ⊇ 磁盘条目集合 | `index-sync` |
| 交叉引用不悬空 | 正文裸写的 id 必须真实存在 | `deadlink` |
| 机器标签可用 | 每个条目有标签行且可解析 | `label` |
| 条号不重复占用 | 同一章内条号唯一 | `chapter-no` |

**翻译时的两个坑**：

1. **「分类与目录一致」不能直接比。** 目录常带序号前缀（`01-方法与效率`）而
   元数据写裸值（`方法与效率`）。两种写法都常见，**这类差异必须做成配置开关**，
   不要硬编码一种约定然后在别的仓库上满屏误报。
   `category_strip_numeric_prefix` 打开时会先剥掉 `NN-`。
2. **per-chapter 布局下 `fm` 和 `id-unique` 要改判据。** 章节文件常常整份没有
   frontmatter（元数据在文件名和条目标题里），所以只要求「写了就必须能解析」；
   条号唯一性由 `chapter-no` 保证。**不要强行套同一套判据。**

---

## 二、行为契约：格式守不住，句子能守住

lint 能守「YAML 能解析」，守不住「路由判据还在不在」。后者要靠
**断言具体句子存在**的测试来守。

```python
def test_labor_rights_routing_boundary(self):
    # 09 与 07 的分界必须写明，否则"被裁了该不该走"会全被吸进 07
    self.assertIn("09 与 07 的分界", SKILL)
    self.assertIn("权益主张", SKILL)

def test_judgement_conflict_priority_order_is_written(self):
    # 回归测试：补充判据 vs 另一条判据的冲突
    self.assertIn("判据之间打架时，按这个优先序", SKILL)
    self.assertIn("压过", SKILL)

def test_dual_channel_matching(self):
    for phrase in ("用户会怎么问", "判断", "signals", "逐字", "强命中"):
        self.assertIn(phrase, SKILL)
```

**做法**：

- 断言**承载关键判据的那句话还在**，而不是断言整段文档
- 每个用例的注释写清**它防的是哪次真实失败**
- 同时用 `assertNotIn` 断言**过时的东西已经消失**
  （例：断言新版写法在、旧版写法不在）

**为什么值得花这个力气**：这些判据是踩坑踩出来的。写文档时顺手删一句
「看起来啰嗦」的话，就等于把那个坑重新挖开。而这些句子在文档里读起来完全正常——
**没有任何 lint 会报错**。

---

## 三、事故回归：把「坏掉的样本」本身存成测试

**通用脚本改散文时，历史上出过两类事故**：

- **A · 标记被吃掉一半**：清理规则用「至多 N 个符号」收尾，只吃掉闭合那一半，
  留下孤立的加粗符号或引号；重复词规则的捕获组能匹配**纯标点**，
  于是「\*\*技能\*\* / \*\*影响力\*\*」里的「\*\* / \*\*」被当成重复词一起删掉
- **B · 缩写被误译**：无视白名单，把后文还要引用的缩写定义删了

对应的测试写法——**用具体样本回归，不靠抽象判断**：

```python
def test_clean_keeps_paired_markers(self):
    cases = [
        # A：斜杠两侧是标记、不是重复词
        ("**技能** / **影响力** / **客户**", "**技能** / **影响力** / **客户**"),
        ('"主动示好" / "多联系圈外朋友"',  '"主动示好" / "多联系圈外朋友"'),
        # B：包裹成对标记一起带过来
        ("**Prepare to be wrong**（准备犯错）", "**准备犯错**"),
        # B：白名单里的缩写不译——后文还要引用它
        ('"某缩写"（展开解释）', '"某缩写"（展开解释）'),
        # 原本就要处理的场景仍然要工作
        ("沟通 / 沟通", "沟通"),
    ]
    for src, want in cases:
        assert clean(src) == want, f"被改坏了：{src}"
```

再加一条**整类事故的不变量**（比逐个样本更能守住）：

```python
def test_clean_preserves_marker_balance_on_corpus(self):
    """不变量：clean() 跑完全库，成对标记的配对不能变。"""
    def balanced(s):
        return (s.count("**") % 2 == 0 and s.count('"') % 2 == 0
                and s.count("“") == s.count("”") and s.count("（") == s.count("）"))
    # 对每篇正文：原来平衡 → 改完也必须平衡
```

**通用化**：脚本改散文时，**只做删减和替换，不做插入**。

理由很具体：曾经有条规则给外文名补一个连接号，结果把「现金流」切成两段、
把「真金白银」切成两段，损坏数百处、横跨全部分类——而**lint 和契约测试都查不出来**，
因为插进去的是「看起来正常的符号」。

所以：**插入类操作一律人工，不用脚本。**

---

## 四、CI 接法

```yaml
- run: pip install pyyaml
- name: 结构校验
  run: python <你的库>/lint.py
- name: 索引同步
  run: python <你的索引重建脚本> --check          # 生成结果与磁盘比对
- name: 契约测试
  run: python -m unittest discover -s skills/<name>/tests
```

本 skill 自带的通用校验器可以替代前两步：

```yaml
- name: 知识库校验（只读）
  run: |
    if command -v python3 >/dev/null; then PY=python3; else PY=python; fi
    "$PY" scripts/kb_lint.py --repo . --config kb-lint.json
```

### 三条原则

1. **只读**：校验器永远不写盘。重建动作留给人本地跑。
   理由是让 CI 往主分支推提交会**和本地分叉**，且 CI 环境常缺本地才有的依赖。
2. **独立 job**：**把只读检查拆成独立 job，不要挂在构建 job 上**。
   校验失败不该连累别的产物发布——锚点没修好和电子书能不能发布是两回事。
   PR 上照样红，主分支该发的还是发出去。
3. **和本地同代码同判据**：不要写一套「CI 专用」的简化版检查。

---

## 五、配置：`kb-lint.json`

```bash
# 从默认配置起步
"$PY" scripts/kb_lint.py --init-config
```

**per-entry 示例**（一文件一条目）：

```json
{
  "layout": "per-entry",
  "corpus_globs": ["skills/*/references/*/*.md"],
  "exclude_globs": ["**/_index/**", "**/00-index.md"],
  "index_globs": ["skills/*/references/00-index.md"],
  "required_frontmatter": ["id", "title", "category", "problem", "signals", "sources"],
  "required_body_sections": ["## 解决的问题", "## 核心判断", "## 机制",
                             "## 诊断信号", "## 实操方法", "## 备选计策",
                             "## 决策规则", "## 反模式", "## 边界",
                             "## 代价与风险提示", "## 来源"],
  "sources_heading": "## 来源",
  "category_strip_numeric_prefix": true,
  "min_body_chars": 4000
}
```

**per-chapter 示例**（一文件多条目）：

```json
{
  "layout": "per-chapter",
  "corpus_globs": ["book/*.md"],
  "index_globs": ["README.md"],
  "index_check_reverse": false,
  "chapter_id_pattern": "^[0-9]{2}-",
  "disabled_checks": ["deadlink", "thickness", "sections"],
  "chapter_entry_pattern": "^###\\s+(\\d+)\\.\\s*(.+?)\\s*$",
  "label_pattern": "^<!--\\s*([^>]+?)\\s*-->\\s*$"
}
```

**常用开关**：

| 开关 | 作用 |
|---|---|
| `--only a,b,c` | 只跑指定检查（调试单条规则时用） |
| `--list-checks` | 列出全部检查项 |
| `--emit-index` | 打印规范索引到 stdout，**不写盘** |
| `index_check_reverse` | 索引「多写了」的检查；索引是长文档（如 README）时关掉，否则噪声极大 |
| `disabled_checks` | 永久关掉不适用的检查 |

---

## 六、退出码

| 码 | 含义 |
|---|---|
| 0 | 全部通过（或没有启用任何检查） |
| 1 | 有检查未通过 |
| 2 | 配置或用法错误（配置不是合法 JSON、目录不存在、扫不到语料、检查项名拼错） |

**2 和 1 要分得开。** 入库闸门通常要求「校验必须全部通过」，
但也要能分辨「报了两处错」和「配置写错导致根本没扫到文件」——
**后者不会报错，只会让检查静默失效**，比前者危险得多。
