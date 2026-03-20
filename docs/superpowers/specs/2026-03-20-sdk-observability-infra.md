# SDK 可观测基础设施设计

**Date:** 2026-03-20
**Status:** Draft

---

## 1 背景

kweaver-sdk 通过 `HttpClient` 向多个后端服务发送请求（BKN、Vega、Agent 等）。当前可观测能力仅有：

- `log_requests=True`：打印 method + URL（`_http.py:80`）
- `trace_id` 捕获：从错误响应 header 提取（`_errors.py:17`）

这对开发调试和生产排障远远不够。本文档设计一套 **公共可观测 middleware**，在 HTTP 层统一实现，对所有 Resource（BKN、Vega、Agent 等）透明生效。

### 与其他文档的关系

- **`2026-03-20-bkn-read-observability-design.md`** §5.1 引用本文档
- **`2026-03-20-vega-read-observability-design.md`** 的可观测部分同样依赖本文档
- 本文档定义的能力对所有 `HttpClient` 实例生效，不区分 BKN 还是 Vega

---

## 2 设计原则

| 原则 | 说明 |
|------|------|
| 零侵入 | Resource 层不感知 middleware 存在，所有逻辑在 HTTP 层完成 |
| 零依赖 | 仅使用 Python 标准库；OpenTelemetry 为可选依赖 |
| 渐进启用 | 所有能力默认关闭，通过 `KWeaverClient` 构造参数或 CLI flag 开启 |
| 可组合 | 多个 middleware 可叠加，顺序固定，互不干扰 |

---

## 3 Middleware 链架构

当前 `HttpClient._request()` 是一个平铺的方法，直接调用 httpx。重构为 middleware 链：

```python
from typing import Any, Callable, Protocol

class RequestContext:
    """Encapsulates a single HTTP request."""
    method: str
    path: str
    kwargs: dict[str, Any]    # json, data, params, headers, timeout, ...
    # kwargs["json"] = JSON body (default)
    # kwargs["data"] = form-encoded body (e.g. PromQL endpoints)
    # 两者互斥；middleware 需兼容两种 body 类型（如 AuditLog 计算 request_size）

RequestHandler = Callable[[RequestContext], Any]

class Middleware(Protocol):
    def wrap(self, handler: RequestHandler) -> RequestHandler: ...
```

```python
class HttpClient:
    def __init__(self, ..., middlewares: list[Middleware] | None = None) -> None:
        self._middlewares = middlewares or []

    def _request(self, method: str, path: str, **kwargs) -> Any:
        ctx = RequestContext(method=method, path=path, kwargs=kwargs)
        handler = self._do_request       # 最内层：实际 httpx 调用
        for mw in reversed(self._middlewares):
            handler = mw.wrap(handler)
        return handler(ctx)
```

### Middleware 顺序（从外到内）

```
Metrics → AuditLog → TracePropagation → Debug → DryRun → Auth + Retry (existing)
```

- **Metrics** 最外层：测量包含所有 middleware 开销的端到端延迟
- **DryRun** 最内层（Auth 之前）：拦截写请求，不发送到服务端

### 自动组装

`KWeaverClient.__init__()` 根据参数自动构建 middleware 列表：

```python
middlewares = []
if metrics:
    middlewares.append(MetricsMiddleware(collector))
if audit_log:
    middlewares.append(AuditLogMiddleware(writer))
if trace_propagation:
    middlewares.append(TracePropagationMiddleware(propagator))
if debug:
    middlewares.append(DebugMiddleware())
if dry_run:
    middlewares.append(DryRunMiddleware())
```

---

## 4 KWeaverClient 接口变更

```python
class KWeaverClient:
    def __init__(
        self,
        base_url: str | None = None,
        *,
        # Auth (existing)
        token: str | None = None,
        auth: AuthProvider | None = None,

        # Observability (new)
        metrics: bool = False,
        audit_log: str | Path | bool = False,      # True = ~/.kweaver/audit.jsonl, str = custom path
        trace_propagation: bool | str = False,      # True = standalone, "otel" = OpenTelemetry
        debug: bool = False,
        dry_run: bool = False,

        # Existing
        business_domain: str | None = None,
        timeout: float = 30.0,
        log_requests: bool = False,                 # 保留向后兼容，debug=True 时自动启用
    ) -> None: ...

    # Observability accessor
    @property
    def metrics(self) -> MetricsCollector | None:
        """Returns MetricsCollector if metrics=True, else None."""
        ...
```

`log_requests` 保留向后兼容。当 `debug=True` 时，`log_requests` 自动生效。

---

## 5 各 Middleware 详细设计

### 5.1 Metrics — 客户端请求级指标采集

拦截每个请求/响应，记录延迟、状态码、重试次数。

```python
from pydantic import BaseModel

class RequestMetric(BaseModel):
    method: str
    path_template: str       # 模板化: /api/.../knowledge-networks/:kn_id/object-types
    status_code: int
    duration_ms: float
    retries: int
    timestamp: float

class MetricsCollector:
    """Thread-safe request metrics collector with sliding window."""

    def record(self, metric: RequestMetric) -> None: ...
    def summary(self) -> MetricsSummary: ...
    def reset(self) -> None: ...

class MetricsSummary(BaseModel):
    total_requests: int
    total_errors: int           # 4xx + 5xx
    total_retries: int
    by_endpoint: dict[str, EndpointMetrics]
    elapsed_seconds: float      # 自 reset/创建 以来

class EndpointMetrics(BaseModel):
    count: int
    error_count: int
    latency_p50_ms: float | None    # None when samples < 2
    latency_p95_ms: float | None
    latency_p99_ms: float | None
```

**路径模板化**：将 `/knowledge-networks/kn-abc123/object-types` 归一化为 `/knowledge-networks/:kn_id/object-types`，避免高基数。规则：
- UUID 格式（32 位 hex 或 8-4-4-4-12 格式）→ `:id`
- 已知路径段（`knowledge-networks`、`object-types`、`catalogs`）后紧跟的路径段 → `:kn_id`、`:ot_id`、`:cat_id` 等

**实现要点**：
- 延迟分位数：使用 `statistics` 标准库的 `quantiles()`，保留最近 1000 个样本的滑动窗口
- 小样本处理：样本数 < 2 时分位数返回 `None`（避免 `statistics.StatisticsError`），由 `EndpointMetrics` 用 `float | None` 类型表达
- 线程安全：`threading.Lock` 保护写入
- 内存控制：每个 endpoint 最多保留 1000 个延迟样本，超出时淘汰最旧的

**启用**：

```python
client = KWeaverClient(auth=ConfigAuth(), metrics=True)
# ... 使用 SDK ...
print(client.metrics.summary())
```

### 5.2 Audit Log — 结构化请求审计

每次 API 调用写一行 JSON 到本地文件，用于事后排查和合规。

```python
import json
from pathlib import Path

class AuditLogWriter:
    """Append-only JSONL audit log. Thread-safe."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path).expanduser()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def write(self, entry: AuditEntry) -> None:
        line = json.dumps(entry.model_dump(), ensure_ascii=False, default=str) + "\n"
        with self._lock:
            with open(self._path, "a") as f:
                f.write(line)

class AuditEntry(BaseModel):
    timestamp: str              # ISO 8601
    method: str
    url: str
    status_code: int
    duration_ms: float
    request_size: int           # bytes
    response_size: int          # bytes
    trace_id: str | None = None # 从 response header x-trace-id 提取
    error: str | None = None
    account_id: str | None = None
```

**安全要点**：
- 不记录请求/响应 body（可能含敏感数据）
- 不记录 Authorization header 值
- `account_id` 从 `x-account-id` header 提取

**启用**：

```python
client = KWeaverClient(auth=ConfigAuth(), audit_log="~/.kweaver/audit.jsonl")
# 或
client = KWeaverClient(auth=ConfigAuth(), audit_log=True)  # 使用默认路径
```

**默认路径**：`~/.kweaver/audit.jsonl`

### 5.3 Trace Context 传播

将客户端 trace 上下文注入 HTTP 请求 header，打通 SDK → 服务端的全链路追踪。BKN 和 Vega 均使用 OpenTelemetry + W3C Trace Context。

```python
class TracePropagator:
    """Inject W3C Trace Context headers into outgoing requests."""

    def __init__(self, mode: str = "standalone") -> None:
        self._mode = mode   # "standalone" | "otel"

    def inject_headers(self, headers: dict[str, str]) -> dict[str, str]:
        if self._mode == "otel":
            return self._inject_otel(headers)
        return self._inject_standalone(headers)

    def _inject_standalone(self, headers: dict[str, str]) -> dict[str, str]:
        import os, uuid
        trace_id = uuid.uuid4().hex                    # 32 hex chars
        span_id = os.urandom(8).hex()                  # 16 hex chars
        headers["traceparent"] = f"00-{trace_id}-{span_id}-01"
        return headers

    def _inject_otel(self, headers: dict[str, str]) -> dict[str, str]:
        try:
            from opentelemetry import context, trace
            from opentelemetry.trace.propagation import TraceContextTextMapPropagator
            propagator = TraceContextTextMapPropagator()
            propagator.inject(headers)
        except ImportError:
            # Fallback to standalone if opentelemetry not installed
            return self._inject_standalone(headers)
        return headers
```

**两种模式**：

| 模式 | 依赖 | 说明 |
|------|------|------|
| `standalone`（默认） | 无 | SDK 自行生成 trace_id + span_id |
| `otel` | `opentelemetry-api` | 从调用方的 OTEL span context 继承 trace_id |

**`traceparent` 格式**：`00-{32位trace_id}-{16位span_id}-01`

**启用**：

```python
# 独立模式
client = KWeaverClient(auth=ConfigAuth(), trace_propagation=True)

# OTEL 模式
client = KWeaverClient(auth=ConfigAuth(), trace_propagation="otel")
```

### 5.4 Debug — 完整请求/响应诊断

增强现有 `log_requests`，提供完整的 HTTP 交互诊断输出。

**输出格式**：

```
──── REQUEST ────────────────────────────────────
GET https://platform.example.com/api/ontology-manager/v1/knowledge-networks/kn-123/object-types
Headers:
  Authorization: Bearer ey...***
  x-business-domain: default
  traceparent: 00-abcdef1234567890abcdef1234567890-1234567890abcdef-01

──── RESPONSE (200 OK, 45ms) ───────────────────
Headers:
  x-trace-id: tr-abc123
  content-type: application/json
Body (2.3 KB):
  {"entries": [...]}

──── CURL ──────────────────────────────────────
curl -X GET 'https://platform.example.com/api/ontology-manager/v1/knowledge-networks/kn-123/object-types' \
  -H 'Authorization: Bearer ey...***' \
  -H 'x-business-domain: default'
```

**实现要点**：
- 输出到 `stderr`（不干扰 stdout 的 JSON 输出）
- Authorization header 值截断 + `***` 掩码
- Body 超过 4KB 时截断显示
- 自动生成等价 curl 命令

**启用**：

```python
client = KWeaverClient(auth=ConfigAuth(), debug=True)
```

### 5.5 Dry-run — 写操作拦截

对写操作（POST/PUT/DELETE），只构建并展示请求，不实际发送。GET 请求正常执行。

**输出格式**：

```
[DRY RUN] Would send:
POST https://platform.example.com/api/ontology-manager/v1/knowledge-networks/kn-123/object-types
Body:
  {"name": "Pod", "branch": "main", "data_source": {...}, ...}
```

**实现**：

DryRun 通过抛出 `DryRunIntercepted` 异常短路请求，而非返回空 dict（空 dict 会导致 Pydantic 解析 required 字段时抛 `ValidationError`）。CLI 层 catch 此异常并打印 `[DRY RUN]` 信息；SDK 调用方可按需 catch 或让异常透传。

```python
class DryRunIntercepted(KWeaverError):
    """Raised when a write request is intercepted by dry-run mode."""
    def __init__(self, method: str, url: str, body: Any = None) -> None:
        self.method = method
        self.url = url
        self.body = body
        super().__init__(f"[DRY RUN] {method} {url}")

class DryRunMiddleware:
    def wrap(self, handler: RequestHandler) -> RequestHandler:
        def wrapper(ctx: RequestContext) -> Any:
            if ctx.method.upper() in ("GET", "HEAD", "OPTIONS"):
                return handler(ctx)
            # 拦截写操作，打印诊断信息后抛异常
            _print_dry_run(ctx)
            raise DryRunIntercepted(ctx.method, ctx.path, ctx.kwargs.get("json"))
        return wrapper
```

**CLI 层处理**：

```python
# cli/_helpers.py — 在命令入口处统一 catch
try:
    result = sdk_call(...)
except DryRunIntercepted as e:
    click.echo(str(e), err=True)
    return   # 正常退出，不报错
```

**启用**：

```python
client = KWeaverClient(auth=ConfigAuth(), dry_run=True)
```

---

## 6 CLI 全局 Flag 与约定

### 6.1 全局 Flag

所有 CLI 命令共享以下全局 flag，在 `cli/main.py` 中定义：

```
kweaver [--debug] [--dry-run] [--audit-log <path>] [--format md|json|yaml] <command> ...
```

| Flag | 环境变量 | 默认值 | 说明 |
|------|---------|--------|------|
| `--debug` | `KWEAVER_DEBUG` | `false` | 打印完整请求/响应 + curl 命令 |
| `--dry-run` | — | `false` | 写操作只展示不执行 |
| `--audit-log` | `KWEAVER_AUDIT_LOG` | 关闭 | 审计日志文件路径 |
| `--format` | `KWEAVER_FORMAT` | `md` | 输出格式：`md`（Markdown 表格，默认）、`json`、`yaml` |

> `--format` 默认 `md`，不做 TTY 自动检测。AI Agent 需要 JSON 时显式传 `--format json`。理由：md 是面向人类的主格式，自动检测引入不可预测行为，Agent 应该显式声明意图。

### 6.2 `kweaver use` — 上下文锁定

BKN 命令几乎都需要 `<kn_id>`，重复输入成本高。`kweaver use` 设置当前上下文，后续命令自动继承：

```bash
kweaver use <kn_id>                    # 锁定 KN 上下文
kweaver use --clear                    # 清除
kweaver use                            # 显示当前上下文
```

上下文存储在 `~/.kweaver/context.json`：

```json
{"kn_id": "kn-abc123", "set_at": "2026-03-20T10:30:00Z"}
```

**解析优先级**：显式位置参数 > `context.json` > 报错提示。

```bash
kweaver use kn-abc123
kweaver bkn object-type list                  # 使用 kn-abc123
kweaver bkn object-type list kn-other456      # 显式覆盖，使用 kn-other456
```

> Vega 命令不需要 kn_id，因此 `kweaver use` 仅影响 BKN 命令族。

### 6.3 默认行为：命令组 = 数据总览

**命令组不带子命令时，展示当前数据状态，而非帮助文档。** 让用户先看到全貌，再决定下一步。

| 输入 | 行为 | 等价于 |
|------|------|--------|
| `kweaver` | 平台总览（BKN + Vega 健康 + 活跃 KN） | `kweaver status` |
| `kweaver bkn` | 当前 KN 概览（OT/RT/AT 数量 + 最近 job） | `kweaver bkn inspect`（需 `use` 上下文） |
| `kweaver bkn object-type` | 列出 Object Types | `kweaver bkn object-type list` |
| `kweaver bkn concept-group` | 列出 Concept Groups | `kweaver bkn concept-group list` |
| `kweaver vega` | Vega 平台概览 | `kweaver vega inspect` |
| `kweaver vega catalog` | 列出 Catalogs + 健康摘要 | `kweaver vega catalog list` |
| `kweaver vega model` | 列出各类型模型数量摘要 | `kweaver vega model list` |

**缺少必要上下文时**（如 BKN 命令无 `kweaver use` 也无位置参数），显示帮助 + 引导：

```
需要指定 Knowledge Network。用法：

  kweaver use <kn_id>                    设置默认 KN
  kweaver bkn object-type list <kn_id>   或直接指定

可用的 Knowledge Networks：
  kn-abc123  k8s-topology   (5 OTs, 3 RTs)
  kn-def456  cmdb-assets    (12 OTs, 8 RTs)
```

**输出末尾附引导提示**，告诉用户下一步可做什么：

```
3 object types. Run 'kweaver bkn object-type get <id>' for details.
```

### 6.4 顶层快捷命令

减少记忆负担，提供高频操作的统一入口：

```bash
kweaver status                         # 一站式状态：BKN inspect + Vega inspect + health
kweaver status --bkn                   # 仅 BKN
kweaver status --vega                  # 仅 Vega

kweaver find "Pod"                     # 跨域搜索：BKN schema + Vega resources + Vega models
kweaver find "Pod" --scope bkn         # 仅 BKN
kweaver find "cpu_usage" --scope vega  # 仅 Vega

kweaver health                         # 聚合健康检查（BKN + Vega）
```

> `status` 是面向人类和 Agent 的"发生了什么"入口。`find` 是"找到某个东西"入口。两者是最高频操作，不应该要求用户知道数据在 BKN 还是 Vega。

### 6.5 CLI 约定（BKN / Vega / Audit 共同遵守）

以下约定从现有代码中提取，所有新增命令必须遵守：

| 约定 | 规则 | 现有先例 |
|------|------|---------|
| **动词** | `list`、`get`、`create`、`update`、`delete`（不用 `ls`/`show`/`new`/`rm`） | 全局统一 |
| **名词** | 单数、kebab-case（`object-type`、`concept-group`，不用 `object_type` 或复数） | `bkn object-type` |
| **ID 参数** | 位置参数（positional），不用 `--id` flag | `<kn_id> <ot_id>` |
| **批量 ID** | 逗号分隔的单个位置参数（`<ids>`），不用 `nargs=-1` 可变参数 | `bkn object-type delete <kn_id> <ot_ids>` |
| **删除确认** | 所有 delete/clear 命令必须有 `--yes, -y` 跳过确认提示 | `bkn delete --yes` |
| **分页** | `--offset`（默认 0）+ `--limit`（默认 **20**） | `query instances --limit 20` |
| **异步等待** | `--wait`/`--no-wait` + `--timeout`（默认 300s） | `bkn build --wait --timeout 300` |
| **详细输出** | `-v`/`--verbose` 展示更多字段（与 `--format` 正交） | `bkn list -v`、`agent get -v` |
| **JSON body** | `-d`/`--data` 传递原始 JSON body | `call -d '{...}'` |
| **时间范围** | `--since`/`--before` 支持相对时间（`Nm` 分钟、`Nh` 小时、`Nd` 天）和 ISO 8601 绝对时间 | 新增约定 |
| **默认行为** | 命令组不带子命令 = 展示数据总览（见 §6.3） | 新增约定 |

**`-v` 与 `--format` 的关系**：两者正交。`-v` 控制"展示哪些字段"（如 OT 的 data_properties），`--format` 控制"用什么格式渲染"。组合示例：

```bash
kweaver bkn object-type get <kn_id> <ot_id>           # md 格式，摘要字段
kweaver bkn object-type get <kn_id> <ot_id> -v        # md 格式，全部字段（含 data_properties）
kweaver bkn object-type get <kn_id> <ot_id> --format json    # json 格式，摘要字段
kweaver bkn object-type get <kn_id> <ot_id> -v --format json # json 格式，全部字段
```

**`make_client()` 扩展**：

```python
def make_client(
    *,
    debug: bool = False,
    dry_run: bool = False,
    audit_log: str | None = None,
    vega_url: str | None = None,       # Vega 文档中定义
) -> KWeaverClient:
    # ... existing auth logic ...
    return KWeaverClient(
        base_url=base_url,
        auth=auth,
        business_domain=bd,
        debug=debug or os.environ.get("KWEAVER_DEBUG") == "true",
        dry_run=dry_run,
        audit_log=audit_log or os.environ.get("KWEAVER_AUDIT_LOG") or False,
        vega_url=vega_url or os.environ.get("KWEAVER_VEGA_URL"),
    )
```

### CLI 审计日志查询命令

```
kweaver audit list [--since 1h] [--status error] [--method GET] [--path "*object-types*"] [--limit 20] [--offset 0]
kweaver audit export [--since 24h] [--format jsonl|csv]
kweaver audit clear [--before 7d] [--yes, -y]
```

> `--since`/`--before` 支持相对时间（`30m`、`1h`、`7d`）和 ISO 8601 绝对时间（`2026-03-20T10:00:00Z`）。见 §6.5 CLI 约定。

`audit list` 示例输出：

```
TIMESTAMP            METHOD  PATH                                          STATUS  DURATION  TRACE_ID
2026-03-20 10:30:01  GET     /api/.../knowledge-networks                   200     45ms      tr-abc123
2026-03-20 10:30:02  POST    /api/.../object-types/ot-1                    200     120ms     tr-def456
2026-03-20 10:30:03  POST    /api/.../action-types/at-1/execute            500     3200ms    tr-ghi789
```

---

## 7 文件清单

### 新增文件

```
packages/python/src/kweaver/
├── _middleware/
│   ├── __init__.py          # Middleware protocol, RequestContext
│   ├── metrics.py           # MetricsCollector + MetricsMiddleware
│   ├── audit.py             # AuditLogWriter + AuditMiddleware
│   ├── trace.py             # TracePropagator + TraceMiddleware
│   ├── debug.py             # DebugMiddleware
│   └── dry_run.py           # DryRunMiddleware
├── cli/
│   ├── audit.py             # kweaver audit list/export/clear
│   ├── use.py               # kweaver use <kn_id> 上下文管理
│   ├── status.py            # kweaver status 聚合状态
│   └── find.py              # kweaver find 跨域搜索
```

```
packages/typescript/src/
├── middleware/
│   ├── index.ts             # Middleware interface
│   ├── metrics.ts
│   ├── audit.ts
│   ├── trace.ts
│   ├── debug.ts
│   └── dry-run.ts
├── commands/
│   ├── audit.ts
│   ├── use.ts
│   ├── status.ts
│   └── find.ts
```

### 修改文件

| 文件 | 变更 |
|------|------|
| `_http.py` | 重构 `_request()` 为 middleware 链 |
| `_client.py` | 新增 `metrics`/`audit_log`/`trace_propagation`/`debug`/`dry_run` 构造参数 |
| `cli/main.py` | 注册全局 flag + `audit`/`use`/`status`/`find` 命令组；命令组默认行为（§6.3） |
| `cli/_helpers.py` | `make_client()` 接受可观测参数 + `output()` 多格式函数 + `resolve_kn_id()` 上下文解析 + `hint()` 引导提示 |

---

## 8 测试计划

### 8.1 单元测试

| 测试文件 | 覆盖范围 |
|---------|---------|
| `test_middleware_metrics.py` | 路径模板化、延迟采集、分位数计算、滑动窗口淘汰、线程安全 |
| `test_middleware_audit.py` | JSONL 写入格式、字段完整性、敏感信息不泄露（无 body/token） |
| `test_middleware_trace.py` | traceparent 格式正确、standalone 模式生成、otel fallback |
| `test_middleware_debug.py` | 输出包含 method/url/headers/body/timing/curl、token 掩码 |
| `test_middleware_dry_run.py` | GET 正常发送、POST/PUT/DELETE 被拦截返回空 |
| `test_middleware_chain.py` | 多 middleware 组合顺序、metrics 测量包含完整链路 |

### 8.2 CLI 集成测试

```python
def test_debug_flag(cli_runner, mock_transport):
    result = cli_runner.invoke(cli, ["--debug", "bkn", "list"])
    assert "REQUEST" in result.output or "REQUEST" in result.stderr

def test_dry_run_blocks_write(cli_runner, mock_transport):
    result = cli_runner.invoke(cli, ["--dry-run", "bkn", "concept-group", "create", "kn-123", "--name", "test"])
    assert result.exit_code == 0
    assert "[DRY RUN]" in result.output

def test_audit_list(cli_runner, tmp_path):
    # Prepare audit.jsonl with sample entries
    ...
    result = cli_runner.invoke(cli, ["audit", "list", "--since", "1h"])
    assert result.exit_code == 0

def test_format_json_yaml(cli_runner, mock_transport):
    for fmt in ["json", "yaml"]:
        result = cli_runner.invoke(cli, ["--format", fmt, "bkn", "list"])
        assert result.exit_code == 0
```

### 8.3 E2E 验证

在真实环境验证 middleware 不破坏正常请求，并验证端到端集成行为：

```python
# tests/e2e/layer/test_observability.py
pytestmark = pytest.mark.e2e

def test_audit_log_written(tmp_path, kweaver_client_factory):
    """audit_log should contain JSONL entries after SDK calls."""
    audit_path = tmp_path / "audit.jsonl"
    client = kweaver_client_factory(audit_log=str(audit_path))
    client.knowledge_networks.list()
    lines = audit_path.read_text().strip().splitlines()
    assert len(lines) >= 1
    entry = json.loads(lines[0])
    assert "method" in entry
    assert "status_code" in entry
    assert "duration_ms" in entry

def test_metrics_collector(kweaver_client_factory):
    """metrics=True should accumulate request counts."""
    client = kweaver_client_factory(metrics=True)
    client.knowledge_networks.list()
    summary = client.metrics.summary()
    assert summary.total_requests >= 1
    assert summary.total_errors == 0

def test_debug_does_not_break_requests(kweaver_client_factory):
    """debug=True should not affect request/response correctness."""
    client = kweaver_client_factory(debug=True)
    kns = client.knowledge_networks.list()
    assert isinstance(kns, list)

def test_trace_propagation_sends_header(kweaver_client_factory):
    """trace_propagation=True should send traceparent (verify via audit)."""
    import json
    from pathlib import Path
    audit_path = Path("/tmp/trace_test_audit.jsonl")
    client = kweaver_client_factory(trace_propagation=True, audit_log=str(audit_path))
    client.knowledge_networks.list()
    # traceparent injection is verified at unit level;
    # e2e just confirms no error when both features are enabled
```

---

## 9 实施阶段

### Phase 1 — 基础架构 + Debug + DryRun

- `_middleware/__init__.py`（Protocol + RequestContext）
- `HttpClient` 重构为 middleware 链
- `DebugMiddleware` + `DryRunMiddleware`
- CLI 全局 flag（`--debug`、`--dry-run`、`--format`）
- `make_client()` 扩展
- 单元测试

**验收**：`kweaver --debug bkn list` 输出完整请求诊断；`kweaver --dry-run bkn concept-group create ...` 不发送请求。

### Phase 2 — Audit + Metrics

- `AuditLogMiddleware` + `AuditLogWriter`
- `MetricsMiddleware` + `MetricsCollector`
- CLI `audit` 命令组（list/export/clear）
- CLI `--audit-log` 全局 flag
- 单元测试 + e2e 测试

**验收**：`kweaver --audit-log ./audit.jsonl bkn list` 写入审计日志；`client.metrics.summary()` 返回正确统计。

### Phase 3 — Trace 传播

- `TracePropagationMiddleware` + `TracePropagator`
- standalone 模式（无依赖）
- otel 模式（可选依赖）
- 单元测试 + e2e 测试

**验收**：BKN/Vega 服务端日志能关联到 SDK 发出的 trace_id。

---

## 10 折衷与决策记录

| 决策 | 选择 | 备选 | 理由 |
|------|------|------|------|
| Middleware 实现方式 | 函数链（wrap pattern） | httpx Transport/Event Hook | httpx hook 不支持 dry-run 等需要短路的场景 |
| Metrics 存储 | 内存滑动窗口 | Prometheus client | 零依赖原则；SDK 是客户端库，不应强制引入 metrics 框架 |
| Audit 格式 | JSONL | SQLite | JSONL 可 grep、可 tail、无依赖、可追加 |
| Audit 内容 | 不含 body | 含 body | body 可能含敏感业务数据，审计只记录元数据 |
| Trace 传播默认模式 | standalone（无依赖） | 强制 OTEL | 降低安装门槛；OTEL 作为可选增强 |
| Debug 输出目标 | stderr | logger | stderr 不干扰 stdout JSON 管道，且对 CLI 用户可见 |
| 全局 flag 归属 | 全部在 `cli/main.py` | 各命令组各自定义 | 统一入口，BKN/Vega 命令均生效 |
| YAML 输出依赖 | `PyYAML` 为可选依赖 `[yaml]` | 内置实现 | `--format yaml` 未安装时提示 `pip install kweaver[yaml]`；不影响核心功能的零依赖原则 |
| DryRun 拦截方式 | 抛 `DryRunIntercepted` 异常 | 返回空 dict | 空 dict 会导致 Pydantic 解析 required 字段失败；异常方式允许 CLI 和 SDK 调用方各自选择处理策略 |

---

## 11 跨文档实施依赖关系

```
Infra Phase 1 (middleware 链 + Debug + DryRun)
  │
  ├──→ BKN Phase 1 (补齐实体读取 + 深度解析 + inspect)
  │      │
  │      └──→ BKN Phase 2 (高级读取 + import/diff + 多格式输出)
  │
  ├──→ Vega Phase 1 (metadata + models + query + health/stats/inspect)
  │
  └──→ Infra Phase 2 (Audit + Metrics)
         │
         ├──→ BKN/Vega 可观测 e2e 验证
         │
         └──→ Infra Phase 3 (Trace 传播)
```

**关键约束**：
- Infra Phase 1 是所有 BKN/Vega 实施的前置条件（middleware 链重构影响 `HttpClient._request()`）
- BKN Phase 1 和 Vega Phase 1 可并行
- Infra Phase 2/3 与 BKN/Vega 的领域功能可并行，但可观测 e2e 测试需要 Infra Phase 2 完成
- `--format yaml` 功能需要 `PyYAML` 可选依赖就绪（Infra Phase 1 或 BKN Phase 2 时引入）
