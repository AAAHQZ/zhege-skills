#!/bin/bash
# lint-runner.sh — wiki 机械健康检查
# 用法：bash scripts/lint-runner.sh <wiki_root>
# 输出：结构化文本报告（供 AI 后续分析使用）
# 退出码：0 = 运行完成，1 = 脚本错误（路径不存在、wiki 结构不完整）

set -u
shopt -s nullglob

WIKI_ROOT="${1:-.}"
WIKI_DIR="$WIKI_ROOT/wiki"
INDEX_FILE="$WIKI_ROOT/index.md"

if [ ! -d "$WIKI_DIR" ]; then
  echo "ERROR: wiki 目录不存在：$WIKI_DIR" >&2
  echo "       请确认路径正确，或先运行 init 工作流初始化知识库。" >&2
  exit 1
fi
if [ ! -f "$INDEX_FILE" ]; then
  echo "ERROR: index.md 不存在：$INDEX_FILE" >&2
  exit 1
fi

echo "=== llm-wiki lint 报告 ==="
echo "时间：$(date '+%Y-%m-%d %H:%M')"
echo "检查路径：$WIKI_DIR"
echo ""

# 检查 1：孤立页面
# 定义：entities/ 下的页面，除了自己之外没有任何其他 wiki 页面用 [[名称]] 引用它
echo "--- 孤立页面（entities/ 下没有被其他页面引用） ---"
_ORPHANS=0
for f in "$WIKI_DIR"/entities/*.md; do
  [ -f "$f" ] || continue
  BASENAME=$(basename "$f" .md)
  if ! grep -rlF "[[$BASENAME]]" "$WIKI_DIR" 2>/dev/null | grep -vxF "$f" | grep -q .; then
    echo "  孤立: $BASENAME"
    _ORPHANS=$((_ORPHANS + 1))
  fi
done
[ "$_ORPHANS" -eq 0 ] && echo "  （无孤立页面）"
echo ""

# 检查 2：断链
# 定义：wiki/ 下的页面里有 [[X]] 链接（支持 [[X|别名]] 语法），但 wiki/ 任意子目录找不到 X.md
echo "--- 断链（被链接但不存在的页面） ---"
_TMP_BROKEN=$(mktemp)
grep -rohE "\[\[[^]]+\]\]" "$WIKI_DIR" 2>/dev/null | \
  sed -e 's/\[\[//g' -e 's/\]\]//g' -e 's/|.*//' | \
  sort -u | \
  while read -r LINK; do
    [ -z "$LINK" ] && continue
    if ! find "$WIKI_DIR" -name "$LINK.md" 2>/dev/null | grep -q .; then
      echo "  断链: [[$LINK]]"
      echo "$LINK" >> "$_TMP_BROKEN"
    fi
  done
if [ ! -s "$_TMP_BROKEN" ]; then
  echo "  （无断链）"
fi
rm -f "$_TMP_BROKEN"
echo ""

# 检查 3：index 一致性
# 定义：index.md 里有 [[X]] 记录（去掉别名），但 wiki/ 任意子目录都找不到 X.md
echo "--- index 一致性（index.md 有记录但文件缺失） ---"
_TMP_MISSING=$(mktemp)
grep -ohE "\[\[[^]]+\]\]" "$INDEX_FILE" 2>/dev/null | \
  sed -e 's/\[\[//g' -e 's/\]\]//g' -e 's/|.*//' | \
  sort -u | \
  while read -r ENTRY; do
    [ -z "$ENTRY" ] && continue
    if ! find "$WIKI_DIR" -name "$ENTRY.md" 2>/dev/null | grep -q .; then
      echo "  index 有但文件缺失: $ENTRY"
      echo "$ENTRY" >> "$_TMP_MISSING"
    fi
  done
if [ ! -s "$_TMP_MISSING" ]; then
  echo "  （index 与文件一致）"
fi
rm -f "$_TMP_MISSING"
echo ""

echo "=== 机械检查完成。矛盾检测、交叉引用、置信度抽查由 AI 继续执行 ==="
exit 0
