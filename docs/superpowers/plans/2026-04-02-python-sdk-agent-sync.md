# Python SDK Agent 功能同步与测试补充实现计划

> **For agentic workers:** REQUIRED SUBSKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 Python SDK 中实现与 TypeScript SDK 一致的 Agent 新功能，并为两者补充单元测试。

**Architecture:** 分三个阶段渐进实现：1) Python SDK API 层扩展，2) Python CLI 命令扩展，3) TypeScript SDK 测试补充。

**Tech Stack:** Python 3.12+, click, pytest, httpx; TypeScript 5+, node:test

---

## 文件结构

```
packages/python/
├── src/kweaver/
│   ├── resources/
│   │   └── agents.py          # 新增 4 个方法
│   ├── cli/
│   │   ├── agent.py              # 新增 5 个子命令，1 个增强
│   │   └── _helpers.py         # 新增时间戳路径工具函数
│   └── types/
│       └── __init__.py          # 新增 AgentTemplate, AgentCategory 类型
├── tests/unit/
│   ├── test_agents.py           # 新增 7 个测试用例
│   └── test_cli_agent.py        # 新建文件，新增 10+ 个测试用例

packages/typescript/
├── test/
│   ├── api/
│   │   └── agent-list.test.ts   # 新建文件，新增 6 个 API 测试
│   └── agent-new-commands.test.ts # 新建文件，新增 10+ 个 CLI 测试
```

---

## 阶段 1：Python SDK API 层扩展

### Task 1: 新增类型定义

**Files:**
- Modify: `packages/python/src/kweaver/types/__init__.py`

- [ ] **Step 1: 在 types/__init__.py 中添加 AgentTemplate 类型**

```python
class AgentTemplate(BaseModel):
    """Agent 模板."""
    id: str
    name: str
    description: str
    config: dict[str, Any] | None = None
```

- [ ] **Step 2: 在 types/__init__.py 中添加 AgentCategory 类型**

```python
class AgentCategory(BaseModel):
    """Agent 分类."""
    id: str
    name: str
    description: str = ""
```

- [ ] **Step 3: 导出新类型到 __init__.py**

确保 `__all__` 包含新类型。

- [ ] **Step 4: Commit**

```bash
git add packages/python/src/kweaver/types/__init__.py
git commit -m "feat(python): add AgentTemplate and AgentCategory types"
```

---

### Task 2: 实现 list_personal() API 方法

**Files:**
- Modify: `packages/python/src/kweaver/resources/agents.py`

- [ ] **Step 1: 在 AgentsResource 类中添加 list_personal() 方法**

```python
def list_personal(
    self,
    *,
    keyword: str | None = None,
    pagination_marker: str | None = None,
    publish_status: str | None = None,
    publish_to_be: str | None = None,
    size: int = 48,
) -> list[Agent]:
    """List personal space agents."""
```

- [ ] **Step 2: 实现方法逻辑**

```python
    params: dict[str, Any] = {"size": size}
    if keyword:
        params["name"] = keyword
    if pagination_marker:
        params["pagination_marker_str"] = pagination_marker
    if publish_status:
        params["publish_status"] = publish_status
    if publish_to_be:
        params["publish_to_be"] = publish_to_be
    
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"/api/agent-factory/v3/personal-space/agent-list?{query_string}"
    
    data = self._http.get(url)
    items = (data if isinstance(data, list) else data.get("entries") or [])
    return [_parse_agent(d) for d in items]
```

- [ ] **Step 3: Commit**

```bash
git add packages/python/src/kweaver/resources/agents.py
git commit -m "feat(python): add list_personal() method to AgentsResource"
```

---

### Task 3: 实现 list_templates() API 方法

**Files:**
- Modify: `packages/python/src/kweaver/resources/agents.py`

- [ ] **Step 1: 添加 list_templates() 方法**

```python
def list_templates(
    self,
    *,
    keyword: str | None = None,
    category_id: str | None = None,
    pagination_marker: str | None = None,
    size: int = 48,
) -> list[AgentTemplate]:
    """List published agent templates."""
```

- [ ] **Step 2: 实现方法逻辑**

```python
    params: dict[str, Any] = {"size": size}
    if keyword:
        params["name"] = keyword
    if category_id:
        params["category_id"] = category_id
    if pagination_marker:
        params["pagination_marker_str"] = pagination_marker
    
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"/api/agent-factory/v3/published/agent-tpl?{query_string}"
    
    data = self._http.get(url)
    items = (data if isinstance(data, list) else data.get("entries") or [])
    return [_parse_template(d) for d in items]


def _parse_template(d: Any) -> AgentTemplate:
    return AgentTemplate(
        id=str(d.get("tpl_id") or d.get("id", "")),
        name=d.get("name", ""),
        description=d.get("profile") or d.get("description", ""),
        config=d.get("config"),
    )
```

- [ ] **Step 3: Commit**

```bash
git add packages/python/src/kweaver/resources/agents.py
git commit -m "feat(python): add list_templates() and _parse_template() helper"
```

---

### Task 4: 实现 get_template() API 方法

**Files:**
- Modify: `packages/python/src/kweaver/resources/agents.py`

- [ ] **Step 1: 添加 get_template() 方法**

```python
def get_template(self, id: str) -> AgentTemplate:
    """Get published agent template by ID."""
```

- [ ] **Step 2: 实现方法逻辑**

```python
    data = self._http.get(f"/api/agent-factory/v3/published/agent-tpl/{id}")
    return _parse_template(data)
```

- [ ] **Step 3: Commit**

```bash
git add packages/python/src/kweaver/resources/agents.py
git commit -m "feat(python): add get_template() method"
```

---

### Task 5: 实现 list_categories() API 方法

**Files:**
- Modify: `packages/python/src/kweaver/resources/agents.py`

- [ ] **Step 1: 添加 list_categories() 方法**

```python
def list_categories(self) -> list[AgentCategory]:
    """List agent categories."""
```

- [ ] **Step 2: 实现方法逻辑**

```python
    data = self._http.get("/api/agent-factory/v3/category")
    items = (data if isinstance(data, list) else data.get("entries") or [])
    return [
        AgentCategory(
            id=str(c.get("id", "")),
            name=c.get("name", ""),
            description=c.get("description", ""),
        )
        for c in items
    ]
```

- [ ] **Step 3: Commit**

```bash
git add packages/python/src/kweaver/resources/agents.py
git commit -m "feat(python): add list_categories() method"
```

---

### Task 6: 修改 publish() 方法支持 category_id

**Files:**
- Modify: `packages/python/src/kweaver/resources/agents.py`

- [ ] **Step 1: 修改 publish() 方法签名**

将 `business_domain_id` 参数改为 `category_id`

- [ ] **Step 2: 更新方法实现**

```python
def publish(self, id: str, *, category_id: str | None = None) -> dict[str, Any]:
    """Publish an agent."""
    body: dict[str, Any] = {
        "business_domain_id": "bd_public",
        "category_ids": [category_id] if category_id else [],
        "description": "",
        "publish_to_where": ["square"],
        "pms_control": None,
    }
    data = self._http.post(f"/api/agent-factory/v3/agent/{id}/publish", json=body)
    return data or {}
```

- [ ] **Step 3: Commit**

```bash
git add packages/python/src/kweaver/resources/agents.py
git commit -m "feat(python): add category_id support to publish() method"
```

---

### Task 7: Python SDK API 层单元测试

**Files:**
- Modify: `packages/python/tests/unit/test_agents.py`

- [ ] **Step 1: 添加 test_list_personal_agents() 测试**

```python
def test_list_personal_agents(capture: RequestCapture):
    handler = lambda req: httpx.Response(200, json={"entries": [_agent_list_json()]})
    client = make_client(handler, capture)
    agents = client.agents.list_personal()
    assert len(agents) == 1
```

- [ ] **Step 2: 添加 test_list_templates() 测试**

```python
def test_list_templates(capture: RequestCapture):
    handler = lambda req: httpx.Response(200, json={"entries": [_template_list_json()]})
    client = make_client(handler, capture)
    templates = client.agents.list_templates()
    assert len(templates) == 1
```

- [ ] **Step 3: 添加 test_get_template() 测试**

```python
def test_get_template(capture: RequestCapture):
    handler = lambda req: httpx.Response(200, json=_template_detail_json())
    client = make_client(handler, capture)
    template = client.agents.get_template("tpl_01")
    assert template.id == "tpl_01"
```

- [ ] **Step 4: 添加 test_list_categories() 测试**

```python
def test_list_categories(capture: RequestCapture):
    handler = lambda req: httpx.Response(200, json={"entries": [_category_json()]})
    client = make_client(handler, capture)
    categories = client.agents.list_categories()
    assert len(categories) == 1
```

- [ ] **Step 5: 添加 test_publish_with_category_id() 测试**

```python
def test_publish_with_category_id(capture: RequestCapture):
    handler = lambda req: httpx.Response(200, json={})
    client = make_client(handler, capture)
    result = client.agents.publish("agent_01", category_id="cat_01")
    assert "agent_id" in capture.last_body()
    assert capture.last_body()["category_ids"] == ["cat_01"]
```

- [ ] **Step 6: 运行测试验证**

```bash
cd packages/python && pytest tests/unit/test_agents.py -v
```

- [ ] **Step 7: Commit**

```bash
git add packages/python/tests/unit/test_agents.py
git commit -m "test(python): add tests for new agent API methods"
```

---

## 阶段 2：Python CLI 命令扩展

### Task 8: 新增 CLI 工具函数

**Files:**
- Modify: `packages/python/src/kweaver/cli/_helpers.py`

- [ ] **Step 1: 添加 _generate_timestamped_path() 工具函数**

```python
from datetime import datetime
from pathlib import Path

def _generate_timestamped_path(path: str) -> str:
    """生成带时间戳的文件路径（与TS一致）."""
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    path_obj = Path(path)
    
    if path.as_posix().endswith("/"):
        return str(path_obj / f"agent-config-{timestamp}.json")
    
    return str(path_obj.parent / f"{path_obj.stem}-{timestamp}{path_obj.suffix}")
```

- [ ] **Step 2: Commit**

```bash
git add packages/python/src/kweaver/cli/_helpers.py
git commit -m "feat(python): add _generate_timestamped_path() helper"
```

---

### Task 9: 新增 agent personal-list 命令

**Files:**
- Modify: `packages/python/src/kweaver/cli/agent.py`

- [ ] **Step 1: 添加 personal-list 子命令**

```python
@agent_group.command("personal-list")
@click.option("--keyword", help="过滤名称")
@click.option("--pagination-marker", help="分页标记")
@click.option("--publish-status", help="发布状态")
@click.option("--publish-to-be", help="发布目标")
@click.option("--size", default=48, type=int, help="返回数量")
@click.option("--verbose", "-v", is_flag=True, help="显示完整JSON响应")
@handle_errors
def list_personal_agents(
    keyword: str | None,
    pagination_marker: str | None,
    publish_status: str | None,
    publish_to_be: str | None,
    size: int,
    verbose: bool,
) -> None:
    """列出私人空间的 Agent。"""
    client = make_client()
    agents = client.agents.list_personal(
        keyword=keyword,
        pagination_marker=pagination_marker,
        publish_status=publish_status,
        publish_to_be=publish_to_be,
        size=size,
    )
    if verbose:
        pp([a.model_dump() for a in agents])
    else:
        simplified = [{"name": a.name, "id": a.id, "description": a.description or ""} for a in agents]
        pp(simplified)
```

- [ ] **Step 2: Commit**

```bash
git add packages/python/src/kweaver/cli/agent.py
git commit -m "feat(python): add agent personal-list command"
```

---

### Task 10: 新增 agent category-list 命令

**Files:**
- Modify: `packages/python/src/kweaver/cli/agent.py`

- [ ] **Step 1: 添加 category-list 子命令**

```python
@agent_group.command("category-list")
@click.option("--verbose", "-v", is_flag=True, help="显示完整JSON响应")
@handle_errors
def list_categories(verbose: bool) -> None:
    """列出 Agent 分类。"""
    client = make_client()
    categories = client.agents.list_categories()
    if verbose:
        pp([c.model_dump() for c in categories])
    else:
        simplified = [{"name": c.name, "id": c.id} for c in categories]
        pp(simplified)
```

- [ ] **Step 2: Commit**

```bash
git add packages/python/src/kweaver/cli/agent.py
git commit -m "feat(python): add agent category-list command"
```

---

### Task 11: 新增 agent template-list 命令

**Files:**
- Modify: `packages/python/src/kweaver/cli/agent.py`

- [ ] **Step 1: 添加 template-list 子命令**

```python
@agent_group.command("template-list")
@click.option("--category-id", help="分类ID")
@click.option("--keyword", help="过滤名称")
@click.option("--pagination-marker", help="分页标记")
@click.option("--size", default=48, type=int, help="返回数量")
@click.option("--verbose", "-v", is_flag=True, help="显示完整JSON响应")
@handle_errors
def list_templates(
    category_id: str | None,
    keyword: str | None,
    pagination_marker: str | None,
    size: int,
    verbose: bool,
) -> None:
    """列出已发布的 Agent 模板。"""
    client = make_client()
    templates = client.agents.list_templates(
        keyword=keyword,
        category_id=category_id,
        pagination_marker=pagination_marker,
        size=size,
    )
    if verbose:
        pp([t.model_dump() for t in templates])
    else:
        simplified = [{"name": t.name, "id": t.id, "description": t.description or ""} for t in templates]
        pp(simplified)
```

- [ ] **Step 2: Commit**

```bash
git add packages/python/src/kweaver/cli/agent.py
git commit -m "feat(python): add agent template-list command"
```

---

### Task 12: 新增 agent template-get 命令

**Files:**
- Modify: `packages/python/src/kweaver/cli/agent.py`

- [ ] **Step 1: 添加 template-get 子命令**

```python
@agent_group.command("template-get")
@click.argument("template_id")
@click.option("--save-config", help="保存配置到文件（自动添加时间戳）")
@click.option("--verbose", "-v", is_flag=True, help="显示完整JSON响应")
@handle_errors
def get_template(template_id: str, save_config: str | None, verbose: bool) -> None:
    """获取已发布的 Agent 模板详情。"""
    from kweaver.cli._helpers import _generate_timestamped_path
    from pathlib import Path
    
    client = make_client()
    template = client.agents.get_template(template_id)
    
    if save_config and template.config:
        timestamped_path = _generate_timestamped_path(save_config)
        Path(timestamped_path).parent.mkdir(parents=True, exist_ok=True)
        Path(timestamped_path).write_text(json.dumps(template.config, indent=2), encoding="utf-8")
        click.echo(timestamped_path)
        return
    
    if verbose:
        pp(template.model_dump())
    else:
        simplified = {
            "id": template.id,
            "name": template.name,
            "description": template.description or "",
            "config": template.config,
        }
        pp(simplified)
```

- [ ] **Step 2: Commit**

```bash
git add packages/python/src/kweaver/cli/agent.py
git commit -m "feat(python): add agent template-get command with --save-config"
```

---

### Task 13: 新增 agent update 命令

**Files:**
- Modify: `packages/python/src/kweaver/cli/agent.py`

- [ ] **Step 1: 添加 update 子命令**

```python
@agent_group.command("update")
@click.argument("agent_id")
@click.option("--name", help="Agent名称")
@click.option("--profile", help="Agent描述")
@click.option("--system-prompt", help="系统提示词")
@click.option("--knowledge-network-id", help="业务知识网络ID")
@click.option("--config-path", help="配置文件路径")
@handle_errors
def update_agent(
    agent_id: str,
    name: str | None,
    profile: str | None,
    system_prompt: str | None,
    knowledge_network_id: str | None,
    config_path: str | None,
) -> None:
    """更新一个 Agent。"""
    from kweaver.cli._helpers import _generate_timestamped_path
    import json as json_module
    
    client = make_client()
    
    # 获取当前 Agent 配置
    current = client.agents.get(agent_id)
    current_dict = current.model_dump()
    
    # 如果指定了 config-path，从文件读取配置
    if config_path:
        with open(config_path) as f:
            config = json_module.load(f)
        current_dict["config"] = config
    
    # 更新字段
    if name:
        current_dict["name"] = name
    if profile:
        current_dict["profile"] = profile
    if system_prompt is not None:
        current_dict.setdefault("config", {})["system_prompt"] = system_prompt
    
    # 更新知识网络配置
    if knowledge_network_id:
        current_dict.setdefault("config", {}).setdefault("data_source", {})["knowledge_network"] = [
            {"knowledge_network_id": knowledge_network_id, "knowledge_network_name": ""}
        ]
    
    # 调用 update API
    client.agents.update(agent_id, current_dict)
    click.echo(f"Agent {agent_id} updated.")
```

- [ ] **Step 2: Commit**

```bash
git add packages/python/src/kweaver/cli/agent.py
git commit -m "feat(python): add agent update command with knowledge-network support"
```

---

### Task 14: 增强 agent get 命令

**Files:**
- Modify: `packages/python/src/kweaver/cli/agent.py`

- [ ] **Step 1: 修改 get 命令添加 --save-config 选项**

```python
@agent_group.command("get")
@click.argument("agent_id")
@click.option("--verbose", "-v", is_flag=True, help="显示完整JSON响应")
@click.option("--save-config", help="保存配置到文件（自动添加时间戳）")
@handle_errors
def get_agent(agent_id: str, verbose: bool, save_config: str | None) -> None:
    """获取 Agent 详情。"""
    from kweaver.cli._helpers import _generate_timestamped_path
    from pathlib import Path
    
    client = make_client()
    agent = client.agents.get(agent_id)
    
    if save_config and agent.config:
        timestamped_path = _generate_timestamped_path(save_config)
        Path(timestamped_path).parent.mkdir(parents=True, exist_ok=True)
        Path(timestamped_path).write_text(json.dumps(agent.config, indent=2), encoding="utf-8")
        click.echo(timestamped_path)
        return
    
    if verbose:
        pp(agent.model_dump())
    else:
        simplified = {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description or "",
            "status": agent.status,
            "kn_ids": agent.kn_ids,
        }
        pp(simplified)
```

- [ ] **Step 2: Commit**

```bash
git add packages/python/src/kweaver/cli/agent.py
git commit -m "feat(python): enhance agent get command with --save-config option"
```

---

### Task 15: Python CLI 单元测试

**Files:**
- Create: `packages/python/tests/unit/test_cli_agent.py`

- [ ] **Step 1: 创建测试文件并添加导入**

```python
"""Tests for agent CLI commands."""

import json
from pathlib import Path
import tempfile

import click
import httpx
from tests.conftest import make_client, RequestCapture
from kweaver.cli._helpers import _generate_timestamped_path
```

- [ ] **Step 2: 添加 test_generate_timestamped_path 测试**

```python
def test_generate_timestamped_path_with_directory():
    result = _generate_timestamped_path("/tmp/config/")
    assert "/tmp/config/agent-config-" in result
    assert result.endswith(".json")

def test_generate_timestamped_path_with_file():
    result = _generate_timestamped_path("/tmp/config.json")
    assert "/tmp/config-" in result
    assert result.endswith(".json")
```

- [ ] **Step 3: 添加 test_list_personal_agents_basic 测试**

```python
def test_list_personal_agents_basic(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"entries": [{"id": "a1", "name": "Test", "profile": "Desc"}]})

    from click.testing import CliRunner
    runner = CliRunner()
    with make_client(handler, capture):
        result = runner.invoke(["agent", "personal-list"])
    
    assert result.exit_code == 0
    assert "Test" in result.output
```

- [ ] **Step 4: 添加 test_list_categories_basic 测试**

```python
def test_list_categories_basic(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"entries": [{"id": "c1", "name": "分类1"}]})

    from click.testing import CliRunner
    runner = CliRunner()
    with make_client(handler, capture):
        result = runner.invoke(["agent", "category-list"])
    
    assert result.exit_code == 0
    assert "分类1" in result.output
```

- [ ] **Step 5: 添加 test_template_get_save_config 测试**

```python
def test_template_get_save_config(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "tpl_id": "t1",
            "name": "Template1",
            "profile": "Desc",
            "config": {"key": "value"}
        })

    from click.testing import CliRunner
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        
        with make_client(handler, capture):
            result = runner.invoke(["agent", "template-get", "t1", "--save-config", str(config_path)])
        
        assert result.exit_code == 0
        saved_path = result.output.strip()
        assert (Path(tmpdir) / saved_path).exists()
```

- [ ] **Step 6: 添加 test_update_with_knowledge_network_id 测试**

```python
def test_update_with_knowledge_network_id(capture: RequestCapture):
    call_count = [0]
    
    def handler(req: httpx.Request) -> httpx.Response:
        call_count[0] += 1
        if call_count[0] == 1:
            return httpx.Response(200, json={"id": "a1", "name": "Test", "config": {}})
        return httpx.Response(200, json={})

    from click.testing import CliRunner
    runner = CliRunner()
    with make_client(handler, capture):
        result = runner.invoke(["agent", "update", "a1", "--knowledge-network-id", "kn_01"])
    
    assert result.exit_code == 0
    body = capture.last_body()
    assert "knowledge_network" in body["config"]["data_source"]
```

- [ ] **Step 7: 运行测试验证**

```bash
cd packages/python && pytest tests/unit/test_cli_agent.py -v
```

- [ ] **Step 8: Commit**

```bash
git add packages/python/tests/unit/test_cli_agent.py
git commit -m "test(python): add tests for new agent CLI commands"
```

---

## 阶段 3：TypeScript SDK 测试补充

### Task 16: 创建 API 层测试文件

**Files:**
- Create: `packages/typescript/test/api/agent-list.test.ts`

- [ ] **Step 1: 创建测试文件并添加导入**

```typescript
import test from "node:test";
import assert from "node:assert/strict";
import { listPersonalAgents, listPublishedAgentTemplates, getPublishedAgentTemplate, listAgentCategories } from "../../src/api/agent-list.js";
```

- [ ] **Step 2: 添加测试辅助函数**

```typescript
const originalFetch = globalThis.fetch;

function mockFetchResponse(data: unknown, status = 200): ReturnType<typeof fetch> {
  return async () =>
    new Response(JSON.stringify(data), {
      status,
      headers: { "content-type": "application/json" },
    });
}
```

- [ ] **Step 3: 运行测试验证**

```bash
cd packages/typescript && npm test -- test/api/agent-list.test.ts
```

- [ ] **Step 4: Commit**

```bash
git add packages/typescript/test/api/agent-list.test.ts
git commit -m "test(ts): add agent-list API tests"
```

---

### Task 17: 为 listPersonalAgents 添加测试

**Files:**
- Modify: `packages/typescript/test/api/agent-list.test.ts`

- [ ] **Step 1: 添加 test_listPersonalAgents_returns_entries_on_200 测试**

```typescript
test("listPersonalAgents returns entries on 200", async () => {
  const payload = { entries: [{ id: "a1", name: "Test" }] };
  globalThis.fetch = mockFetchResponse(payload);

  const result = await listPersonalAgents({
    baseUrl: "https://test.com",
    accessToken: "token",
  });

  assert.equal(JSON.parse(result).entries[0].id, "a1");
  globalThis.fetch = originalFetch;
});
```

- [ ] **Step 2: 添加 test_listPersonalAgents_with_filters 测试**

```typescript
test("listPersonalAgents with filters sends correct params", async () => {
  globalThis.fetch = async (url: string) => {
    assert.match(url, /name=test/);
    assert.match(url, /size=10/);
    return mockFetchResponse({ entries: [] })();
  });

  await listPersonalAgents({
    baseUrl: "https://test.com",
    accessToken: "token",
    name: "test",
    size: 10,
  });

  globalThis.fetch = originalFetch;
});
```

- [ ] **Step 3: Commit**

```bash
git add packages/typescript/test/api/agent-list.test.ts
git commit -m "test(ts): add listPersonalAgents tests"
```

---

### Task 18: 为 listPublishedAgentTemplates 添加测试

**Files:**
- Modify: `packages/typescript/test/api/agent-list.test.ts`

- [ ] **Step 1: 添加 test_listPublishedAgentTemplates 测试**

```typescript
test("listPublishedAgentTemplates returns entries on 200", async () => {
  const payload = { entries: [{ tpl_id: "t1", name: "Template1" }] };
  globalThis.fetch = mockFetchResponse(payload);

  const result = await listPublishedAgentTemplates({
    baseUrl: "https://test.com",
    accessToken: "token",
  });

  assert.equal(JSON.parse(result).entries[0].tpl_id, "t1");
  globalThis.fetch = originalFetch;
});
```

- [ ] **Step 2: Commit**

```bash
git add packages/typescript/test/api/agent-list.test.ts
git commit -m "test(ts): add listPublishedAgentTemplates tests"
```

---

### Task 19: 为 getPublishedAgentTemplate 添加测试

**Files:**
- Modify: `packages/typescript/test/api/agent-list.test.ts`

- [ ] **Step 1: 添加 test_getPublishedAgentTemplate 测试**

```typescript
test("getPublishedAgentTemplate returns template on 200", async () => {
  const payload = { tpl_id: "t1", name: "Template1", config: {} };
  globalThis.fetch = mockFetchResponse(payload);

  const result = await getPublishedAgentTemplate({
    baseUrl: "https://test.com",
    accessToken: "token",
    templateId: "t1",
  });

  assert.equal(JSON.parse(result).tpl_id, "t1");
  globalThis.fetch = originalFetch;
});
```

- [ ] **Step 2: Commit**

```bash
git add packages/typescript/test/api/agent-list.test.ts
git commit -m "test(ts): add getPublishedAgentTemplate tests"
```

---

### Task 20: 为 listAgentCategories 添加测试

**Files:**
- Modify: `packages/typescript/test/api/agent-list.test.ts`

- [ ] **Step 1: 添加 test_listAgentCategories 测试**

```typescript
test("listAgentCategories returns categories on 200", async () => {
  const payload = { entries: [{ id: "c1", name: "Category1" }] };
  globalThis.fetch = mockFetchResponse(payload);

  const result = await listAgentCategories({
    baseUrl: "https://test.com",
    accessToken: "token",
  });

  assert.equal(JSON.parse(result).entries[0].id, "c1");
  globalThis.fetch = originalFetch;
});
```

- [ ] **Step 2: Commit**

```bash
git add packages/typescript/test/api/agent-list.test.ts
git commit -m "test(ts): add listAgentCategories tests"
```

---

### Task 21: 创建 CLI 命令测试文件

**Files:**
- Create: `packages/typescript/test/agent-new-commands.test.ts`

- [ ] **Step 1: 创建测试文件并添加导入**

```typescript
import test from "node:test";
import assert from "node:assert/strict";
import { generateTimestampedPath } from "../../src/commands/agent.js";
import { parseAgentTemplateListArgs, parseAgentTemplateGetArgs, parseAgentPersonalListArgs } from "../../src/commands/agent.js";
```

- [ ] **Step 2: 添加 generateTimestampedPath 测试**

```typescript
test("generateTimestampedPath with directory path", () => {
  const result = generateTimestampedPath("/tmp/config/");
  assert.match(result, /agent-config-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.json$/);
});

test("generateTimestampedPath with file path", () => {
  const result = generateTimestampedPath("/tmp/config.json");
  assert.match(result, /config-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.json$/);
});
```

- [ ] **Step 3: 运行测试验证**

```bash
cd packages/typescript && npm test -- test/agent-new-commands.test.ts
```

- [ ] **Step 4: Commit**

```bash
git add packages/typescript/test/agent-new-commands.test.ts
git commit -m "test(ts): add agent CLI tests for timestamped path generation"
```

---

### Task 22: 为 CLI 参数解析添加测试

**Files:**
- Modify: `packages/typescript/test/agent-new-commands.test.ts`

- [ ] **Step 1: 添加 parseAgentTemplateListArgs 测试**

```typescript
test("parseAgentTemplateListArgs parses all options", () => {
  const result = parseAgentTemplateListArgs([
    "--category-id", "cat1",
    "--name", "test",
    "--size", "10",
  ]);
  
  assert.equal(result.category_id, "cat1");
  assert.equal(result.name, "test");
  assert.equal(result.size, 10);
});
```

- [ ] **Step 2: 添加 parseAgentTemplateGetArgs 测试**

```typescript
test("parseAgentTemplateGetArgs parses save-config", () => {
  const result = parseAgentTemplateGetArgs(["t1", "--save-config", "/tmp/config.json"]);
  
  assert.equal(result.templateId, "t1");
  assert.equal(result.saveConfig, "/tmp/config.json");
});
```

- [ ] **Step 3: 运行测试验证**

```bash
cd packages/typescript && npm test -- test/agent-new-commands.test.ts
```

- [ ] **Step 4: Commit**

```bash
git add packages/typescript/test/agent-new-commands.test.ts
git commit -m "test(ts): add CLI argument parsing tests"
```

---

### Task 23: 最终验证与总结

**Files:**
- None

- [ ] **Step 1: 运行所有 Python 测试**

```bash
cd packages/python && pytest tests/unit/test_agents.py tests/unit/test_cli_agent.py -v
```

- [ ] **Step 2: 运行所有 TypeScript 测试**

```bash
cd packages/typescript && npm test
```

- [ ] **Step 3: 验证所有测试通过**

确保所有新增测试用例通过。

- [ ] **Step 4: 创建总结文档**

在 `docs/superpowers/plans/2025-04-02-python-sdk-agent-sync.md` 中添加实现总结。

- [ ] **Step 5: 提交总结文档**

```bash
git add docs/superpowers/plans/2025-04-02-python-sdk-agent-sync.md
git commit -m "docs: add implementation summary for python sdk agent sync"
```

---

## 验收标准

完成以上所有任务后：

- [ ] Python SDK 新增 4 个 API 方法：`list_personal()`, `list_templates()`, `get_template()`, `list_categories()`
- [ ] Python SDK 新增 5 个 CLI 子命令：`personal-list`, `category-list`, `template-list`, `template-get`, `update`
- [ ] Python SDK 1 个 CLI 命令增强：`get --save-config`
- [ ] Python 新增约 15+ 个单元测试用例
- [ ] TypeScript SDK 新增约 15+ 个单元测试用例
- [ ] 所有测试通过
- [ ] 代码风格与现有代码一致

---

## 附录：参考文档

- TypeScript 实现：`packages/typescript/src/commands/agent.ts`
- TypeScript API：`packages/typescript/src/api/agent-list.ts`
- Python Agent 资源：`packages/python/src/kweaver/resources/agents.py`
- Python CLI：`packages/python/src/kweaver/cli/agent.py`
- 测试参考：`packages/typescript/test/agent.test.ts`, `packages/python/tests/unit/test_agents.py`
