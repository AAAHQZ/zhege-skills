#!/bin/bash
# 验证 ingest Step 1 的 JSON 输出格式
# 用法：bash validate-step1.sh <json_file>
# 返回：0 = 格式正确，1 = 格式有问题（触发回退）

JSON_FILE="$1"

# 参数检查
[ -z "$1" ] && { echo "ERROR: usage: validate-step1.sh <json_file>"; exit 1; }

# 检查 jq 是否可用（必需依赖）
command -v jq >/dev/null 2>&1 || { echo "ERROR: jq not found. Run: brew install jq"; exit 1; }

# 检查文件是否存在
[ -f "$JSON_FILE" ] || { echo "ERROR: file not found: $JSON_FILE"; exit 1; }

# 检查是否是有效 JSON
jq empty "$JSON_FILE" 2>/dev/null || { echo "ERROR: invalid JSON format"; exit 1; }

# 检查必需字段存在且类型正确
jq -e '.entities | type == "array"' "$JSON_FILE" >/dev/null 2>&1 || { echo "ERROR: 'entities' must be an array"; exit 1; }
jq -e '.topics | type == "array"' "$JSON_FILE" >/dev/null 2>&1 || { echo "ERROR: 'topics' must be an array"; exit 1; }
jq -e '.connections | type == "array"' "$JSON_FILE" >/dev/null 2>&1 || { echo "ERROR: 'connections' must be an array"; exit 1; }
jq -e '.contradictions | type == "array"' "$JSON_FILE" >/dev/null 2>&1 || { echo "ERROR: 'contradictions' must be an array"; exit 1; }
jq -e '.new_vs_existing | type == "object"' "$JSON_FILE" >/dev/null 2>&1 || { echo "ERROR: 'new_vs_existing' must be an object"; exit 1; }

# 检查每个 entity 的 confidence 值是否有效
INVALID=$(jq -r '.entities[]? | (.confidence // "MISSING")' "$JSON_FILE" 2>/dev/null | \
    grep -v -E "^(EXTRACTED|INFERRED|AMBIGUOUS|UNVERIFIED)$" | head -3)
if [ -n "$INVALID" ]; then
    echo "ERROR: invalid confidence value(s): $INVALID"
    echo "       Valid values: EXTRACTED | INFERRED | AMBIGUOUS | UNVERIFIED"
    exit 1
fi

echo "OK: Step 1 JSON validation passed"
exit 0
