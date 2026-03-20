# Action 命令参考

Action Type 查询与执行。**`execute` 有副作用，执行前向用户确认。**

## 命令

```bash
kweaver action query <kn_id> <action_type_id>
kweaver action execute <kn_id> [<action_type_id>] [--action-name <name>] [--params '<json>'] [--wait/--no-wait] [--timeout 300]
kweaver action logs <kn_id> [--limit 20]
kweaver action log <kn_id> <log_id>
```

### BKN 层命令（等价）

```bash
kweaver bkn action-type list <kn_id>
kweaver bkn action-log list <kn_id> [--offset 0] [--limit 20] [--sort create_time] [--direction desc]
kweaver bkn action-log get <kn_id> <log_id>
kweaver bkn action-log cancel <kn_id> <log_id> [--yes/-y]
kweaver bkn action-execution get <kn_id> <execution_id> [--wait/--no-wait] [--timeout 300]
```

## 说明

- `execute` 支持按名称查找 action：`--action-name "sync_data"` 会自动通过 `kn_search` 解析为 ID
- `--params` 传 JSON 格式执行参数
- `--wait`（默认 True）会轮询直到执行完成或超时

## 端到端示例

```bash
# 查看可用 action
kweaver bkn action-type list kn-1

# 按名称执行（自动解析 ID）
kweaver action execute kn-1 --action-name "sync_inventory" --wait

# 带参数执行
kweaver action execute kn-1 at-123 --params '{"source": "erp", "mode": "incremental"}'

# 查看执行日志
kweaver action logs kn-1
kweaver action log kn-1 log-456
```
