# BKN 命令参考

知识网络管理：schema CRUD、构建、导出、诊断。

## 概览

```bash
kweaver bkn                          # KN 概览（= inspect）
kweaver bkn list                     # 列出知识网络
kweaver bkn inspect [<kn_id>]        # 一站式诊断
```

## 知识网络

```bash
kweaver bkn list [--name <n>] [--name-pattern <p>] [--tag <t>] [--sort update_time] [--direction desc] [--offset 0] [--limit 50] [-v]
kweaver bkn get <kn_id> [--stats] [--export]
kweaver bkn stats <kn_id>
kweaver bkn export <kn_id>
kweaver bkn create <datasource_id> --name <name> [--tables <t1,t2>] [--build/--no-build] [--timeout 300]
kweaver bkn update <kn_id> [--name <n>] [--description <d>] [--tag <t> ...]
kweaver bkn build <kn_id> [--wait/--no-wait] [--timeout 300]
kweaver bkn delete <kn_id> [--yes]
kweaver bkn inspect [<kn_id>] [--full]
```

## Object Type

```bash
kweaver bkn object-type list <kn_id>
kweaver bkn object-type get <kn_id> <ot_id>                # -v 显示完整 data_properties
kweaver bkn object-type create <kn_id> --name <n> --dataview-id <dv> --primary-key <pk> --display-key <dk> [--property '<json>' ...]
kweaver bkn object-type update <kn_id> <ot_id> [--name <n>] [--display-key <dk>]
kweaver bkn object-type delete <kn_id> <ot_ids> [--yes/-y]
kweaver bkn object-type properties <kn_id> <ot_id> [<body_json>]
```

## Relation Type

```bash
kweaver bkn relation-type list <kn_id>
kweaver bkn relation-type get <kn_id> <rt_id>
kweaver bkn relation-type create <kn_id> --name <n> --source <ot_id> --target <ot_id> [--mapping src:tgt ...]
kweaver bkn relation-type update <kn_id> <rt_id> [--name <n>]
kweaver bkn relation-type delete <kn_id> <rt_ids> [--yes/-y]
```

## Concept Group

```bash
kweaver bkn concept-group list [<kn_id>]
kweaver bkn concept-group get [<kn_id>] <cg_id>
kweaver bkn concept-group create [<kn_id>] --name <name>
kweaver bkn concept-group update [<kn_id>] <cg_id> --name <name>
kweaver bkn concept-group delete [<kn_id>] <cg_ids> [--yes/-y]
kweaver bkn concept-group add-members [<kn_id>] <cg_id> <ot_id1,ot_id2>
kweaver bkn concept-group remove-members [<kn_id>] <cg_id> <ot_id1,ot_id2>
```

> `[<kn_id>]` 可选：省略时使用 `kweaver use` 设置的上下文。

## Job

```bash
kweaver bkn job list [<kn_id>] [--status running|completed|failed]
kweaver bkn job tasks [<kn_id>] <job_id>
kweaver bkn job delete [<kn_id>] <job_ids> [--yes/-y]
kweaver bkn job wait [<kn_id>] <job_id> [--timeout 300]
```

## Action Type / Log / Execution

```bash
kweaver bkn action-type list <kn_id>
kweaver bkn action-log list <kn_id> [--offset 0] [--limit 20] [--sort create_time] [--direction desc]
kweaver bkn action-log get <kn_id> <log_id>
kweaver bkn action-log cancel <kn_id> <log_id> [--yes/-y]
kweaver bkn action-execution get <kn_id> <execution_id> [--wait/--no-wait] [--timeout 300]
```

## 端到端示例

```bash
# 接入数据源 → 创建 KN → 查询
kweaver ds connect mysql db.example.com 3306 erp --account root --password pass
kweaver bkn create <ds_id> --name "erp-kn" --wait
kweaver bkn object-type list <kn_id>
kweaver query kn-search <kn_id> "订单"
```
