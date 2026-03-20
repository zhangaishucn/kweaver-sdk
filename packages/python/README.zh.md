# KWeaver Python SDK

KWeaver 平台的 Python SDK + CLI — 支持 BKN（Business Knowledge Network）、Vega 数据管理和 Decision Agent。

[English](README.md)

## 安装

```bash
pip install kweaver-sdk          # 仅 SDK
pip install kweaver-sdk[cli]     # SDK + CLI
```

需要 **Python >= 3.10**。

## 快速上手

### 搜索与对话（最简路径）

```python
import kweaver

kweaver.configure(
    url="https://kweaver.example.com",
    token="my-token",
    bkn_id="supply-chain-bkn-id",
    agent_id="supply-chain-agent-id",
)

# 语义搜索
results = kweaver.search("供应链有哪些关键风险？")
for concept in results.concepts:
    print(concept.concept_name, concept.rerank_score)

# 与 Agent 对话
reply = kweaver.chat("帮我分析一下今年的库存风险")
print(reply.content)

# 流式输出
for chunk in kweaver.chat("给我生成一份风险报告", stream=True):
    print(chunk.delta, end="", flush=True)
```

### Client API（完全控制）

```python
from kweaver import KWeaverClient, ConfigAuth

client = KWeaverClient(
    auth=ConfigAuth(),           # 读取 ~/.kweaver/ 凭证
    debug=True,                  # 打印请求/响应诊断
    vega_url="http://vega:13014", # 可选：连接 Vega
)

# BKN — 知识网络
kns = client.knowledge_networks.list()
report = client.knowledge_networks.inspect("kn-123")  # 一站式诊断

# BKN — Schema 管理
ots = client.object_types.list("kn-123")
ot = client.object_types.get("kn-123", "ot-456")      # 含完整 data_properties
cgs = client.concept_groups.list("kn-123")
jobs = client.jobs.list("kn-123")

# Vega — 数据平台
catalogs = client.vega.catalogs.list()
resources = client.vega.resources.list(catalog_id="cat-1", category="table")
models = client.vega.metric_models.list()

# Vega — 查询
result = client.vega.query.dsl(body={"query": {"match_all": {}}, "size": 10})
result = client.vega.query.execute(tables=[...], output_fields=["*"], limit=20)

# Vega — 诊断
info = client.vega.health()
report = client.vega.inspect()
```

### 可观测能力

```python
# Debug 模式 — 打印完整 HTTP 诊断 + curl 命令到 stderr
client = KWeaverClient(auth=ConfigAuth(), debug=True)

# Dry-run — 拦截写操作，不实际发送到服务端
client = KWeaverClient(auth=ConfigAuth(), dry_run=True)
```

---

## CLI

```bash
pip install kweaver-sdk[cli]
```

### 上下文与状态

```bash
kweaver auth login https://kweaver.example.com   # 浏览器 OAuth 登录
kweaver use kn-abc123                             # 设置默认 KN 上下文

kweaver bkn                                       # KN 概览（= inspect）
kweaver vega                                      # Vega 平台概览
```

### BKN 命令

```bash
kweaver bkn object-type list                      # 使用 'kweaver use' 设置的上下文
kweaver bkn object-type get ot-456 -v             # 详细模式：含 data_properties
kweaver bkn concept-group list
kweaver bkn job list --status running
kweaver bkn inspect --full
```

### Vega 命令

```bash
kweaver vega catalog list
kweaver vega catalog health --all
kweaver vega resource list --category table
kweaver vega model list --type metric
kweaver vega query dsl -d '{"query": {"match_all": {}}, "size": 5}'
kweaver vega health
kweaver vega inspect
```

### 全局选项

```bash
kweaver --debug bkn list           # 完整请求/响应诊断
kweaver --dry-run bkn concept-group create kn-1 --name test   # 预览不发送
kweaver --format json vega catalog list   # JSON 输出（默认 Markdown）
```

---

## SDK 资源一览

### BKN（知识网络）

| 资源 | 访问方式 | 方法 |
|------|---------|------|
| 知识网络 | `client.knowledge_networks` | `list`, `get`, `create`, `update`, `delete`, `build`, `export`, `inspect` |
| 对象类 | `client.object_types` | `list`, `get`, `create`, `update`, `delete` |
| 关系类 | `client.relation_types` | `list`, `get`, `create`, `update`, `delete` |
| Action 类 | `client.action_types` | `list`, `execute`, `cancel` |
| 概念组 | `client.concept_groups` | `list`, `get`, `create`, `update`, `delete`, `add_members`, `remove_members` |
| 任务 | `client.jobs` | `list`, `get_tasks`, `delete`, `wait` |
| 查询 | `client.query` | `semantic_search`, `instances`, `instances_iter`, `kn_search`, `subgraph` |
| Agent | `client.agents` | `list`, `get` |
| 对话 | `client.conversations` | `send_message`, `list_messages` |

### Vega（数据平台）

| 资源 | 访问方式 | 方法 |
|------|---------|------|
| Catalog | `client.vega.catalogs` | `list`, `get`, `health_status`, `health_report`, `test_connection`, `discover`, `resources` |
| 数据资源 | `client.vega.resources` | `list`, `get`, `data`, `preview` |
| 连接器类型 | `client.vega.connector_types` | `list`, `get` |
| 指标模型 | `client.vega.metric_models` | `list`, `get` |
| 事件模型 | `client.vega.event_models` | `list`, `get` |
| 调用链模型 | `client.vega.trace_models` | `list`, `get` |
| 数据视图 | `client.vega.data_views` | `list`, `get` |
| 数据字典 | `client.vega.data_dicts` | `list`, `get` |
| 目标模型 | `client.vega.objective_models` | `list`, `get` |
| 查询 | `client.vega.query` | `execute`, `dsl`, `dsl_count`, `promql`, `promql_instant`, `events` |
| 任务 | `client.vega.tasks` | `list_discover`, `get_discover`, `wait_discover`, `get_metric` |
| 命名空间 | `client.vega` | `health`, `stats`, `inspect` |

### 配置

```python
KWeaverClient(
    base_url="https://...",          # KWeaver 平台 URL
    auth=ConfigAuth(),               # 或 TokenAuth("...") 或 PasswordAuth(...)
    vega_url="http://vega:13014",    # 可选：Vega 数据平台 URL
    debug=False,                     # 打印请求/响应诊断
    dry_run=False,                   # 拦截写操作
)
```

| 环境变量 | 说明 |
|---------|------|
| `KWEAVER_BASE_URL` | 平台 URL |
| `KWEAVER_TOKEN` | Bearer Token |
| `KWEAVER_VEGA_URL` | Vega 后端 URL |
| `KWEAVER_DEBUG` | 启用 debug 模式（`true`） |
| `KWEAVER_FORMAT` | CLI 输出格式（`md`/`json`/`yaml`） |

---

## 相关链接

- [GitHub](https://github.com/kweaver-ai/kweaver-sdk)
- [TypeScript SDK on npm](https://www.npmjs.com/package/@kweaver-ai/kweaver-sdk)

## 许可证

MIT
