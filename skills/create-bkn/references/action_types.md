# ActionType (action_types/*.bkn)

每个行动类型一个文件，放在 `action_types/` 目录下。

## Frontmatter

```yaml
---
type: action_type
id: {action_id}
name: {显示名称}
tags: [tag1, tag2]               # 可选
enabled: boolean                 # 可选，建议默认 false
risk_level: low | medium | high  # 可选
requires_approval: boolean       # 可选
---
```

## Body 结构

必须 section：
- `## ActionType: {显示名称}` + 简短描述
- `### Bound Object`
- `### Tool Configuration`
- `### Parameter Binding`

可选 section：
- `### Affect Object`
- `### Trigger Condition`
- `### Pre-conditions`
- `### Scope of Impact`
- `### Schedule`
- `### Execution Description`

### Bound Object

| Bound Object | Action Type |
|--------------|-------------|
| {object_type_id} | add / modify / delete |

### Affect Object（可选）

| Affect Object |
|---------------|
| {object_type_id} |

### Trigger Condition（可选）

YAML 代码块：

```yaml
condition:
  object_type_id: {object_type_id}
  field: {property_name}
  operation: {operator}
  value: {value}
```

### Pre-conditions（可选）

| Object | Check | Condition | Message |
|--------|-------|-----------|---------|
| {object_type_id} | relation:{relation_id} | exist | {违反说明} |
| {object_type_id} | property:{property_name} | {op} {value} | {违反说明} |

### Scope of Impact（可选）

| Object | Impact Description |
|--------|--------------------|
| {object_type_id} | {影响说明} |

### Tool Configuration

tool 类型：

| Type | Toolbox ID | Tool ID |
|------|------------|---------|
| tool | {toolbox_id} | {tool_id} |

mcp 类型：

| Type | MCP ID | Tool Name |
|------|--------|-----------|
| mcp | {mcp_id} | {tool_name} |

### Parameter Binding

| Parameter | Type | Source | Binding | Description |
|-----------|------|--------|---------|-------------|
| {param} | string | property | {property_name} | {说明} |
| {param} | string | input | - | {说明} |
| {param} | string | const | {value} | {说明} |

Source 值：`property`（对象属性）/ `input`（用户输入）/ `const`（常量）

### Schedule（可选）

| Type | Expression |
|------|------------|
| FIX_RATE | {interval} |
| CRON | {cron_expr} |

### Execution Description（可选）

编号列表描述执行流程。

## 触发条件操作符

| 操作符 | 说明 |
|--------|------|
| == | 等于 |
| != | 不等于 |
| > / < / >= / <= | 比较 |
| in / not_in | 包含于/不包含于 |
| exist / not_exist | 存在/不存在 |
| range | 范围内 |

## Template

````markdown
---
type: action_type
id: {action_id}
name: {行动名称}
tags: [{标签1}, {标签2}]
enabled: false
risk_level: medium
requires_approval: true
---

## ActionType: {行动名称}

{详细描述}

### Bound Object

| Bound Object | Action Type |
|--------------|-------------|
| {object_id} | modify |

### Affect Object

| Affect Object |
|---------------|
| {object_id} |

### Trigger Condition

```yaml
condition:
  object_type_id: {object_id}
  field: {property_name}
  operation: {operator}
  value: {value}
```

> {触发条件说明}

### Pre-conditions

| Object | Check | Condition | Message |
|--------|-------|-----------|---------|
| {object_id} | relation:{relation_id} | exist | {违反说明} |

### Scope of Impact

| Object | Impact Description |
|--------|---------------------|
| {object_id} | {影响描述} |

### Tool Configuration

| Type | Toolbox ID | Tool ID |
|------|------------|---------|
| tool | {box_id} | {tool_id} |

### Parameter Binding

| Parameter | Type | Source | Binding | Description |
|-----------|------|--------|---------|-------------|
| {param} | string | property | {property_name} | {说明} |
| {param} | string | const | {value} | {说明} |

### Schedule

| Type | Expression |
|------|------------|
| FIX_RATE | {interval} |

### Execution Description

1. {步骤1}
2. {步骤2}
3. {步骤3}
````

## Example

See `examples/bkn/k8s-network/action_types/restart_pod.bkn`.
