# 查询命令参考

知识网络查询：语义搜索、实例查询、子图遍历、schema 搜索。

## 命令

```bash
kweaver query search <kn_id> <query> [--max-concepts 10]
kweaver query instances <kn_id> <ot_id> [--condition '<json>'] [--limit 20]
kweaver query subgraph <kn_id> --start-type <ot_name> --start-condition '<json>' --path <rt1,rt2>
kweaver query kn-search <kn_id> <query> [--only-schema]
```

## 参数说明

### condition JSON 格式

```json
{"field": "name", "operation": "==", "value": "Pod-123"}
```

支持的 operation: `==`, `!=`, `>`, `<`, `>=`, `<=`, `in`, `not_in`, `match`

### subgraph --path 格式

逗号分隔的关系类名称，表示多跳路径：

```bash
kweaver query subgraph kn-1 --start-type Pod --start-condition '{"field":"name","operation":"match","value":"web"}' --path "runs_on,hosts"
```

## 端到端示例

```bash
# 搜索 schema
kweaver query kn-search kn-1 "Pod"

# 查询实例
kweaver query instances kn-1 ot-pod --condition '{"field":"status","operation":"==","value":"Running"}' --limit 5

# 子图遍历：Pod → Node
kweaver query subgraph kn-1 --start-type Pod --start-condition '{"field":"name","operation":"match","value":"web"}' --path "runs_on"
```
