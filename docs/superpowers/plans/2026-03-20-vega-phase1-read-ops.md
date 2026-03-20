# Vega Phase 1: Read Operations + Query + Inspect

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add complete Vega read operations via `client.vega.*` namespace — catalogs, resources, 6 model types (generic), query engines (DSL/PromQL/execute), tasks, health/stats/inspect.

**Architecture:** VegaNamespace owns a separate HttpClient pointing at `vega_url`. Uses VegaModelResource\<T\> generic base for 6 model resources. All under `resources/vega/` sub-package. KWeaverClient gets `vega_url` param and lazy `vega` property.

**Tech Stack:** Python 3.10+, httpx, pydantic, click. Zero new dependencies.

**Spec:** `docs/superpowers/specs/2026-03-20-vega-read-observability-design.md`

**Depends on:** Infra Phase 1 (complete)

---

## File Structure

### New Files

| File | Responsibility |
|------|---------------|
| `src/kweaver/resources/vega/__init__.py` | VegaNamespace class, exports |
| `src/kweaver/resources/vega/_base.py` | VegaModelResource\<T\> generic base |
| `src/kweaver/resources/vega/catalogs.py` | CatalogsResource (list, get, health_status, health_report, test_connection, discover, resources) |
| `src/kweaver/resources/vega/resources.py` | ResourcesResource (list, get, data, preview) |
| `src/kweaver/resources/vega/connector_types.py` | ConnectorTypesResource (list, get) |
| `src/kweaver/resources/vega/models.py` | All 6 model resources via VegaModelResource subclasses |
| `src/kweaver/resources/vega/query.py` | VegaQueryResource (dsl, promql, execute, metric_model, data_view, events) |
| `src/kweaver/resources/vega/tasks.py` | TasksResource (list_discover, get_discover, wait_discover, get_metric) |
| `src/kweaver/resources/vega/inspect.py` | health(), stats(), inspect() methods |
| `tests/unit/test_vega.py` | All Vega SDK tests (parameterized for models) |

### Modified Files

| File | Changes |
|------|---------|
| `src/kweaver/types.py` | Add all Vega* types + VegaError hierarchy |
| `src/kweaver/_errors.py` | Add VegaError, VegaQueryError, VegaConnectionError, VegaDiscoverError |
| `src/kweaver/_client.py` | Add vega_url param, lazy vega property |
| `tests/conftest.py` | Add make_vega_client() helper |

---

## Task 1: Vega Types + Error Hierarchy

**Files:**
- Modify: `packages/python/src/kweaver/types.py`
- Modify: `packages/python/src/kweaver/_errors.py`
- Test: `packages/python/tests/unit/test_vega_types.py`

- [ ] **Step 1: Write tests**

```python
# tests/unit/test_vega_types.py
"""Tests for Vega type definitions."""
from kweaver.types import (
    VegaServerInfo, VegaCatalog, VegaResource, VegaResourceProperty,
    VegaConnectorType, VegaMetricModel, VegaEventModel, VegaTraceModel,
    VegaDataView, VegaDataDict, VegaDataDictItem, VegaObjectiveModel,
    VegaDiscoverTask, VegaMetricTask, VegaSpan,
    VegaQueryResult, VegaDslResult, VegaPromqlResult,
    VegaHealthReport, VegaPlatformStats, VegaInspectReport,
)
from kweaver._errors import VegaError, VegaQueryError, VegaConnectionError, VegaDiscoverError, KWeaverError


def test_vega_server_info():
    info = VegaServerInfo(server_name="VEGA", server_version="1.0", language="Go", go_version="1.22", go_arch="amd64")
    assert info.server_name == "VEGA"

def test_vega_catalog_defaults():
    c = VegaCatalog(id="c-1", name="prod", type="physical", connector_type="mysql", status="active")
    assert c.health_status is None

def test_vega_resource_with_properties():
    r = VegaResource(id="r-1", name="users", catalog_id="c-1", category="table", status="active",
                     properties=[VegaResourceProperty(name="id", type="integer")])
    assert len(r.properties) == 1

def test_vega_model_types():
    """All 6 model types should instantiate."""
    VegaMetricModel(id="mm-1", name="cpu")
    VegaEventModel(id="em-1", name="alert")
    VegaTraceModel(id="tm-1", name="traces")
    VegaDataView(id="dv-1", name="view1")
    VegaDataDict(id="dd-1", name="status_codes")
    VegaObjectiveModel(id="om-1", name="sla")

def test_vega_discover_task():
    t = VegaDiscoverTask(id="dt-1", catalog_id="c-1", status="running")
    assert t.progress is None

def test_vega_query_results():
    VegaQueryResult(entries=[{"a": 1}], total_count=1)
    VegaDslResult(hits=[{"a": 1}], total=1, took_ms=5)
    VegaPromqlResult(status="success", result_type="vector")

def test_vega_inspect_report():
    info = VegaServerInfo(server_name="V", server_version="1", language="Go", go_version="1.22", go_arch="amd64")
    report = VegaInspectReport(server_info=info, catalog_health=VegaHealthReport())
    assert report.active_tasks == []

def test_vega_error_hierarchy():
    assert issubclass(VegaError, KWeaverError)
    assert issubclass(VegaQueryError, VegaError)
    assert issubclass(VegaConnectionError, VegaError)
    assert issubclass(VegaDiscoverError, VegaError)

def test_vega_query_error_attrs():
    e = VegaQueryError("fail", query_type="dsl")
    assert e.query_type == "dsl"
```

- [ ] **Step 2: Run to confirm failure**
- [ ] **Step 3: Add types to types.py and errors to _errors.py**

Add all Vega* model classes to types.py. Add VegaError hierarchy to _errors.py:
```python
class VegaError(KWeaverError):
    """Base for all Vega errors."""

class VegaConnectionError(VegaError):
    def __init__(self, message: str, *, catalog_id: str = "", connector_type: str = "", **kw):
        super().__init__(message, **kw)
        self.catalog_id = catalog_id
        self.connector_type = connector_type

class VegaQueryError(VegaError):
    def __init__(self, message: str, *, query_type: str = "", **kw):
        super().__init__(message, **kw)
        self.query_type = query_type

class VegaDiscoverError(VegaError):
    def __init__(self, message: str, *, catalog_id: str = "", task_id: str = "", **kw):
        super().__init__(message, **kw)
        self.catalog_id = catalog_id
        self.task_id = task_id
```

- [ ] **Step 4: Run tests, verify all pass**
- [ ] **Step 5: Commit**
```bash
git commit -m "feat: add Vega type definitions and error hierarchy"
```

---

## Task 2: VegaModelResource Generic Base + 6 Model Resources

**Files:**
- Create: `packages/python/src/kweaver/resources/vega/__init__.py`
- Create: `packages/python/src/kweaver/resources/vega/_base.py`
- Create: `packages/python/src/kweaver/resources/vega/models.py`
- Test: `packages/python/tests/unit/test_vega.py` (parameterized)

- [ ] **Step 1: Write parameterized tests**

```python
# tests/unit/test_vega.py
"""Tests for Vega SDK resources."""
from __future__ import annotations
import httpx
import pytest
from kweaver._auth import TokenAuth
from kweaver._http import HttpClient
from kweaver.types import (
    VegaMetricModel, VegaEventModel, VegaTraceModel,
    VegaDataView, VegaDataDict, VegaObjectiveModel,
)

def _make_vega_http(handler):
    transport = httpx.MockTransport(handler)
    return HttpClient(base_url="http://vega-mock:13014", auth=TokenAuth("tok"), transport=transport)


# ── Parameterized model tests ──────────────────────────────────────

MODEL_RESOURCES = [
    ("metric_models",    "/api/mdl-data-model/v1/metric-models",    VegaMetricModel,    {"id": "mm-1", "name": "cpu"}),
    ("event_models",     "/api/mdl-data-model/v1/event-models",     VegaEventModel,     {"id": "em-1", "name": "alert"}),
    ("trace_models",     "/api/mdl-data-model/v1/trace-models",     VegaTraceModel,     {"id": "tm-1", "name": "traces"}),
    ("data_views",       "/api/mdl-data-model/v1/data-views",       VegaDataView,       {"id": "dv-1", "name": "view1"}),
    ("data_dicts",       "/api/mdl-data-model/v1/data-dicts",       VegaDataDict,       {"id": "dd-1", "name": "codes"}),
    ("objective_models", "/api/mdl-data-model/v1/objective-models",  VegaObjectiveModel, {"id": "om-1", "name": "sla"}),
]


@pytest.mark.parametrize("attr,path,model_cls,sample", MODEL_RESOURCES)
def test_model_list(attr, path, model_cls, sample):
    def handler(req):
        return httpx.Response(200, json={"entries": [sample]})
    from kweaver.resources.vega import VegaNamespace
    ns = VegaNamespace(_make_vega_http(handler))
    result = getattr(ns, attr).list()
    assert len(result) == 1
    assert isinstance(result[0], model_cls)


@pytest.mark.parametrize("attr,path,model_cls,sample", MODEL_RESOURCES)
def test_model_get(attr, path, model_cls, sample):
    def handler(req):
        return httpx.Response(200, json=sample)
    from kweaver.resources.vega import VegaNamespace
    ns = VegaNamespace(_make_vega_http(handler))
    result = getattr(ns, attr).get(sample["id"])
    assert isinstance(result, model_cls)
    assert result.id == sample["id"]
```

- [ ] **Step 2: Run to confirm failure**
- [ ] **Step 3: Create vega sub-package**

`packages/python/src/kweaver/resources/vega/_base.py`:
```python
"""Generic model resource for mdl-data-model services."""
from __future__ import annotations
from typing import Any, Callable, Generic, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from kweaver._http import HttpClient

T = TypeVar("T")

class VegaModelResource(Generic[T]):
    def __init__(self, http: HttpClient, path: str, parse_fn: Callable[[dict], T]) -> None:
        self._http = http
        self._path = path
        self._parse = parse_fn

    def list(self, *, limit: int = 20, offset: int = 0, **params) -> list[T]:
        params.update({"limit": limit, "offset": offset})
        data = self._http.get(self._path, params=params)
        entries = data.get("entries", data.get("data", [])) if isinstance(data, dict) else data
        return [self._parse(e) for e in entries]

    def get(self, id: str) -> T:
        data = self._http.get(f"{self._path}/{id}")
        if isinstance(data, dict) and "entries" in data:
            data = data["entries"][0] if data["entries"] else data
        return self._parse(data)

    def get_batch(self, ids: list[str]) -> list[T]:
        ids_str = ",".join(ids)
        data = self._http.get(f"{self._path}/{ids_str}")
        entries = data.get("entries", data.get("data", [data])) if isinstance(data, dict) else data
        return [self._parse(e) for e in entries]
```

`packages/python/src/kweaver/resources/vega/models.py`:
```python
"""All 6 Vega model resources via VegaModelResource subclasses."""
from __future__ import annotations
from typing import TYPE_CHECKING
from kweaver.resources.vega._base import VegaModelResource
from kweaver.types import (
    VegaMetricModel, VegaEventModel, VegaTraceModel,
    VegaDataView, VegaDataDict, VegaObjectiveModel,
)
if TYPE_CHECKING:
    from kweaver._http import HttpClient

_MDL = "/api/mdl-data-model/v1"

class VegaMetricModelsResource(VegaModelResource[VegaMetricModel]):
    def __init__(self, http: HttpClient):
        super().__init__(http, f"{_MDL}/metric-models", lambda d: VegaMetricModel(**d))

class VegaEventModelsResource(VegaModelResource[VegaEventModel]):
    def __init__(self, http: HttpClient):
        super().__init__(http, f"{_MDL}/event-models", lambda d: VegaEventModel(**d))

class VegaTraceModelsResource(VegaModelResource[VegaTraceModel]):
    def __init__(self, http: HttpClient):
        super().__init__(http, f"{_MDL}/trace-models", lambda d: VegaTraceModel(**d))

class VegaDataViewsResource(VegaModelResource[VegaDataView]):
    def __init__(self, http: HttpClient):
        super().__init__(http, f"{_MDL}/data-views", lambda d: VegaDataView(**d))

class VegaDataDictsResource(VegaModelResource[VegaDataDict]):
    def __init__(self, http: HttpClient):
        super().__init__(http, f"{_MDL}/data-dicts", lambda d: VegaDataDict(**d))

class VegaObjectiveModelsResource(VegaModelResource[VegaObjectiveModel]):
    def __init__(self, http: HttpClient):
        super().__init__(http, f"{_MDL}/objective-models", lambda d: VegaObjectiveModel(**d))
```

`packages/python/src/kweaver/resources/vega/__init__.py`:
```python
"""VegaNamespace — all Vega resources under one namespace."""
from __future__ import annotations
from typing import TYPE_CHECKING
from kweaver.resources.vega.models import (
    VegaMetricModelsResource, VegaEventModelsResource, VegaTraceModelsResource,
    VegaDataViewsResource, VegaDataDictsResource, VegaObjectiveModelsResource,
)
if TYPE_CHECKING:
    from kweaver._http import HttpClient

class VegaNamespace:
    def __init__(self, http: HttpClient) -> None:
        self._http = http
        self.metric_models = VegaMetricModelsResource(http)
        self.event_models = VegaEventModelsResource(http)
        self.trace_models = VegaTraceModelsResource(http)
        self.data_views = VegaDataViewsResource(http)
        self.data_dicts = VegaDataDictsResource(http)
        self.objective_models = VegaObjectiveModelsResource(http)
```

- [ ] **Step 4: Run tests**
- [ ] **Step 5: Commit**
```bash
git commit -m "feat: add VegaModelResource generic base + 6 model resources"
```

---

## Task 3: Catalogs + Resources + ConnectorTypes

**Files:**
- Create: `packages/python/src/kweaver/resources/vega/catalogs.py`
- Create: `packages/python/src/kweaver/resources/vega/resources.py`
- Create: `packages/python/src/kweaver/resources/vega/connector_types.py`
- Modify: `packages/python/src/kweaver/resources/vega/__init__.py` (register)
- Extend: `packages/python/tests/unit/test_vega.py`

- [ ] **Step 1: Write tests**

Append to `tests/unit/test_vega.py`:
```python
from kweaver.types import VegaCatalog, VegaResource as VegaResourceModel, VegaConnectorType, VegaHealthReport

def test_catalog_list():
    def handler(req):
        return httpx.Response(200, json={"entries": [
            {"id": "c-1", "name": "prod", "type": "physical", "connector_type": "mysql", "status": "active"}
        ]})
    from kweaver.resources.vega import VegaNamespace
    ns = VegaNamespace(_make_vega_http(handler))
    cats = ns.catalogs.list()
    assert len(cats) == 1
    assert isinstance(cats[0], VegaCatalog)

def test_catalog_get():
    def handler(req):
        return httpx.Response(200, json={"id": "c-1", "name": "prod", "type": "physical", "connector_type": "mysql", "status": "active"})
    from kweaver.resources.vega import VegaNamespace
    ns = VegaNamespace(_make_vega_http(handler))
    cat = ns.catalogs.get("c-1")
    assert cat.id == "c-1"

def test_resource_list():
    def handler(req):
        return httpx.Response(200, json={"entries": [
            {"id": "r-1", "name": "users", "catalog_id": "c-1", "category": "table", "status": "active"}
        ]})
    from kweaver.resources.vega import VegaNamespace
    ns = VegaNamespace(_make_vega_http(handler))
    resources = ns.resources.list()
    assert len(resources) == 1

def test_connector_type_list():
    def handler(req):
        return httpx.Response(200, json={"entries": [
            {"type": "mysql", "name": "MySQL", "enabled": True}
        ]})
    from kweaver.resources.vega import VegaNamespace
    ns = VegaNamespace(_make_vega_http(handler))
    types = ns.connector_types.list()
    assert len(types) == 1
    assert types[0].type == "mysql"
```

- [ ] **Step 2: Create resource files**

`catalogs.py`: CatalogsResource with list/get/health_status/health_report/test_connection/discover/resources. Base path: `/api/vega-backend/v1/catalogs`.

`resources.py`: ResourcesResource with list/get/data/preview. Base path: `/api/vega-backend/v1/resources`.

`connector_types.py`: ConnectorTypesResource with list/get. Base path: `/api/vega-backend/v1/connector-types`.

- [ ] **Step 3: Register in VegaNamespace.__init__**
- [ ] **Step 4: Run tests**
- [ ] **Step 5: Commit**
```bash
git commit -m "feat: add Vega catalogs, resources, connector-types"
```

---

## Task 4: Query Resource

**Files:**
- Create: `packages/python/src/kweaver/resources/vega/query.py`
- Modify: `packages/python/src/kweaver/resources/vega/__init__.py`
- Extend: `packages/python/tests/unit/test_vega.py`

- [ ] **Step 1: Write tests**

```python
# append to test_vega.py
from kweaver.types import VegaQueryResult, VegaDslResult, VegaPromqlResult

def test_query_execute():
    def handler(req):
        return httpx.Response(200, json={"entries": [{"a": 1}], "total_count": 1})
    from kweaver.resources.vega import VegaNamespace
    ns = VegaNamespace(_make_vega_http(handler))
    result = ns.query.execute(tables=[{"resource_id": "r-1"}], output_fields=["*"])
    assert isinstance(result, VegaQueryResult)
    assert result.total_count == 1

def test_query_dsl():
    def handler(req):
        return httpx.Response(200, json={"hits": [{"a": 1}], "total": 1, "took_ms": 5})
    from kweaver.resources.vega import VegaNamespace
    ns = VegaNamespace(_make_vega_http(handler))
    result = ns.query.dsl(body={"query": {"match_all": {}}})
    assert isinstance(result, VegaDslResult)
    assert result.total == 1
```

- [ ] **Step 2: Create query.py**

VegaQueryResource with: execute, dsl, dsl_count, dsl_scroll, promql, promql_instant, promql_series, metric_model, data_view, events, event.

Paths:
- execute: POST `/api/vega-backend/v1/query/execute`
- dsl: POST `/api/mdl-uniquery/v1/dsl/{index}/_search` or `/api/mdl-uniquery/v1/dsl/_search`
- promql: POST `/api/mdl-uniquery/v1/promql/query_range` (uses `data=` for form-encoded)

- [ ] **Step 3: Register in VegaNamespace**
- [ ] **Step 4: Run tests**
- [ ] **Step 5: Commit**
```bash
git commit -m "feat: add VegaQueryResource — DSL, PromQL, execute"
```

---

## Task 5: Tasks Resource + health/stats/inspect

**Files:**
- Create: `packages/python/src/kweaver/resources/vega/tasks.py`
- Create: `packages/python/src/kweaver/resources/vega/inspect.py` (as methods on VegaNamespace)
- Modify: `packages/python/src/kweaver/resources/vega/__init__.py`
- Extend: `packages/python/tests/unit/test_vega.py`

- [ ] **Step 1: Write tests**

```python
# append to test_vega.py
from kweaver.types import VegaDiscoverTask, VegaServerInfo, VegaPlatformStats, VegaInspectReport

def test_tasks_list_discover():
    def handler(req):
        return httpx.Response(200, json={"entries": [
            {"id": "dt-1", "catalog_id": "c-1", "status": "running"}
        ]})
    from kweaver.resources.vega import VegaNamespace
    ns = VegaNamespace(_make_vega_http(handler))
    tasks = ns.tasks.list_discover()
    assert len(tasks) == 1
    assert isinstance(tasks[0], VegaDiscoverTask)

def test_health():
    def handler(req):
        return httpx.Response(200, json={
            "server_name": "VEGA", "server_version": "1.0",
            "language": "Go", "go_version": "1.22", "go_arch": "amd64"
        })
    from kweaver.resources.vega import VegaNamespace
    ns = VegaNamespace(_make_vega_http(handler))
    info = ns.health()
    assert isinstance(info, VegaServerInfo)
    assert info.server_name == "VEGA"

def test_inspect():
    call_count = {"n": 0}
    def handler(req):
        call_count["n"] += 1
        url = str(req.url)
        if "/health" in url:
            return httpx.Response(200, json={
                "server_name": "V", "server_version": "1", "language": "Go", "go_version": "1.22", "go_arch": "amd64"
            })
        if "/catalogs" in url:
            return httpx.Response(200, json={"entries": []})
        if "/discover-tasks" in url:
            return httpx.Response(200, json={"entries": []})
        return httpx.Response(200, json={"entries": []})
    from kweaver.resources.vega import VegaNamespace
    ns = VegaNamespace(_make_vega_http(handler))
    report = ns.inspect()
    assert isinstance(report, VegaInspectReport)
```

- [ ] **Step 2: Create tasks.py, add health/stats/inspect to VegaNamespace**

tasks.py: VegaTasksResource with list_discover, get_discover, wait_discover (exponential backoff), get_metric.

health/stats/inspect as methods directly on VegaNamespace (in __init__.py or a separate inspect.py imported by __init__).

- [ ] **Step 3: Run tests**
- [ ] **Step 4: Commit**
```bash
git commit -m "feat: add Vega tasks, health, stats, inspect"
```

---

## Task 6: Wire VegaNamespace into KWeaverClient

**Files:**
- Modify: `packages/python/src/kweaver/_client.py`
- Extend: `packages/python/tests/unit/test_vega.py`

- [ ] **Step 1: Write test**

```python
# append to test_vega.py
from kweaver import KWeaverClient

def test_client_vega_property():
    """client.vega should return VegaNamespace when vega_url is set."""
    def handler(req):
        return httpx.Response(200, json={"entries": []})
    transport = httpx.MockTransport(handler)
    client = KWeaverClient(base_url="https://mock", token="tok", transport=transport, vega_url="http://vega:13014")
    from kweaver.resources.vega import VegaNamespace
    assert isinstance(client.vega, VegaNamespace)

def test_client_vega_raises_without_url():
    """client.vega should raise ValueError when vega_url not configured."""
    def handler(req):
        return httpx.Response(200, json={})
    transport = httpx.MockTransport(handler)
    client = KWeaverClient(base_url="https://mock", token="tok", transport=transport)
    with pytest.raises(ValueError, match="vega_url"):
        _ = client.vega
```

- [ ] **Step 2: Add vega_url param and lazy vega property to _client.py**

```python
class KWeaverClient:
    def __init__(self, ..., vega_url: str | None = None) -> None:
        # ... existing ...
        self._vega_url = vega_url
        self._vega: VegaNamespace | None = None
        self._auth = auth  # store for vega HttpClient

    @property
    def vega(self):
        if self._vega is None:
            if not self._vega_url:
                raise ValueError("vega_url not configured. Pass vega_url to KWeaverClient or set KWEAVER_VEGA_URL.")
            from kweaver.resources.vega import VegaNamespace
            vega_http = HttpClient(
                base_url=self._vega_url, auth=self._auth,
                middlewares=self._http._middlewares,  # share middleware chain
            )
            self._vega = VegaNamespace(vega_http)
        return self._vega
```

- [ ] **Step 3: Run ALL tests**
- [ ] **Step 4: Commit**
```bash
git commit -m "feat: wire VegaNamespace into KWeaverClient with lazy vega property"
```

---

## Task 7: Final Regression + Push

- [ ] **Step 1: Run full test suite**
```bash
cd packages/python && python -m pytest tests/unit/ -v --tb=short
```

- [ ] **Step 2: Verify coverage ≥ 65%**
```bash
python -m pytest tests/unit/ --cov=kweaver --cov-report=term-missing 2>&1 | tail -5
```

- [ ] **Step 3: Push**
```bash
git push
```
