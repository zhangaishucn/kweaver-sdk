# Agent 命令参考

Decision Agent 管理与对话。

## 命令

```bash
kweaver agent list [--keyword <kw>] [--status published|draft] [--category-id <id>] [--offset 0] [--limit 50] [-v]
kweaver agent get <agent_id> [-v]
kweaver agent chat <agent_id> -m '<message>' [--conversation-id <id>]
kweaver agent sessions <agent_id>
kweaver agent history <conversation_id> [--limit <n>]
```

## 端到端示例

```bash
# 列出已发布的 Agent
kweaver agent list --status published

# 单轮对话
kweaver agent chat ag-123 -m "分析最近的库存数据"

# 多轮对话
CONV_ID=$(kweaver agent chat ag-123 -m "你能做什么？" --format json | jq -r '.conversation_id')
kweaver agent chat ag-123 -m "分析库存风险" --conversation-id "$CONV_ID"
kweaver agent chat ag-123 -m "给出改进建议" --conversation-id "$CONV_ID"

# 查看历史
kweaver agent history "$CONV_ID"
```
