# RelationType (relation_types/*.bkn)

每个关系类型一个文件，放在 `relation_types/` 目录下。

## Frontmatter

```yaml
---
type: relation_type
id: {relation_id}
name: {显示名称}
tags: [tag1, tag2]               # 可选
---
```

## Body 结构

- `## RelationType: {显示名称}` + 简短描述
- `### Endpoint`（必须）：表格 Source | Target | Type
- 根据 Type 选择映射方式（见下）

### Endpoint 表格

| Source | Target | Type |
|--------|--------|------|
| {source_object_type_id} | {target_object_type_id} | direct 或 data_view |

Source 和 Target 必须引用已有的 object_type ID。

## 直接映射 (direct)

通过属性值匹配建立关联：

```markdown
### Mapping Rules

| Source Property | Target Property |
|-----------------|-----------------|
| {source_prop} | {target_prop} |
```

## 视图映射 (data_view)

通过中间视图建立关联，用以下三个 section 替代 Mapping Rules：

```markdown
### Mapping View

| Type | ID |
|------|-----|
| data_view | {view_id} |

### Source Mapping

| Source Property | View Property |
|-----------------|----------------|
| {source_prop} | {view_prop} |

### Target Mapping

| View Property | Target Property |
|---------------|-----------------|
| {view_prop} | {target_prop} |
```

## Template (direct)

```markdown
---
type: relation_type
id: {relation_id}
name: {关系名称}
tags: [{标签1}, {标签2}]
---

## RelationType: {关系名称}

{详细描述}

### Endpoint

| Source | Target | Type |
|--------|--------|------|
| {source_object_id} | {target_object_id} | direct |

### Mapping Rules

| Source Property | Target Property |
|-----------------|-----------------|
| {source_prop} | {target_prop} |
```

## Example

See `examples/bkn/k8s-network/relation_types/pod_belongs_node.bkn`.
