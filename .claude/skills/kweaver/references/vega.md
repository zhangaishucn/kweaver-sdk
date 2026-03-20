# Vega 命令参考

Vega 数据平台：Catalog 管理、数据资源、模型、查询（DSL/PromQL）、健康巡检。

**前提**: 需要设置 `KWEAVER_VEGA_URL` 环境变量。

## 概览

```bash
kweaver vega                         # 平台概览（= inspect）
kweaver vega health                  # 服务健康
kweaver vega stats                   # 资源统计
kweaver vega inspect [--full]        # 聚合诊断
```

## Catalog

```bash
kweaver vega catalog list [--status healthy|degraded|unhealthy|offline|disabled] [--limit 20]
kweaver vega catalog get <id>
kweaver vega catalog health [<ids>] [--all]
kweaver vega catalog test-connection <id>
kweaver vega catalog discover <id> [--wait]
kweaver vega catalog resources <id> [--category table|index|...]
```

## Resource

```bash
kweaver vega resource list [--catalog-id <id>] [--category table] [--status active] [--limit 20]
kweaver vega resource get <id>
kweaver vega resource data <id> -d '<body>'
```

## Connector Type

```bash
kweaver vega connector-type list
kweaver vega connector-type get <type>
```

## Model（统一入口）

6 种模型通过 `--type` 区分：metric, event, trace, data-view, data-dict, objective。

```bash
kweaver vega model list [--type metric|event|trace|data-view|data-dict|objective] [--limit 20]
kweaver vega model get <id>
kweaver vega model fields <id>         # metric/trace 模型
kweaver vega model levels              # event 模型级别
kweaver vega model items <id>          # data-dict 条目
kweaver vega model groups              # data-view 分组
```

## Query

```bash
# DSL（OpenSearch 兼容）
kweaver vega query dsl [<index>] -d '<body>'
kweaver vega query dsl-count [<index>] -d '<body>'

# PromQL
kweaver vega query promql '<expr>' --start X --end Y --step 15s
kweaver vega query promql-instant '<expr>'
kweaver vega query promql-series --match '<selector>'

# 统一查询
kweaver vega query execute -d '<body>'

# 指标/视图
kweaver vega query metric-model <ids> -d '<body>'
kweaver vega query data-view <ids> -d '<body>'

# Trace/Event
kweaver vega query trace <trace-model-id> <trace-id>
kweaver vega query events -d '<body>'
kweaver vega query event <event-model-id> <event-id>

# 基准测试（CLI only）
kweaver vega query bench [<index>] -d '<body>' --count 10
```

## Task

```bash
kweaver vega task list [--type discover|metric|event] [--status running|pending|completed|failed]
kweaver vega task get <task-id> [--type discover|metric]
```

## Trace 诊断

```bash
kweaver vega trace show <trace-model-id> <trace-id>
kweaver vega trace spans <trace-model-id> <trace-id>
kweaver vega trace span <trace-model-id> <trace-id> <span-id>
kweaver vega trace related-logs <trace-model-id> <trace-id> <span-id>
```

## 端到端示例

```bash
# 巡检
kweaver vega inspect
kweaver vega catalog health --all

# 查询数据
kweaver vega catalog resources cat-1 --category table
kweaver vega query dsl -d '{"query": {"match_all": {}}, "size": 5}' --format json

# 指标查询
kweaver vega query promql-instant 'up'
```
