# ConceptGroup (concept_groups/*.bkn)

每个概念分组一个文件，放在 `concept_groups/` 目录下。用于将相关的对象类型组织在一起。

## Frontmatter

```yaml
---
type: concept_group
id: {group_id}
name: {显示名称}
tags: [tag1, tag2]               # 可选
---
```

## Body 结构

- `## ConceptGroup: {显示名称}` + 简短描述
- `### Object Types`（必须）：表格 ID | Name | Description

Object Types 表中的 ID 必须引用已有的 object_type ID。

## Template

```markdown
---
type: concept_group
id: {group_id}
name: {分组名称}
tags: [{标签1}]
---

## ConceptGroup: {分组名称}

{分组描述}

### Object Types

| ID | Name | Description |
|----|------|-------------|
| {object_id} | {对象名称} | {说明} |
```

## Example

See `examples/bkn/k8s-network/concept_groups/k8s.bkn`.
