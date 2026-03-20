# Network (network.bkn)

网络根文件，唯一入口。SDK/CLI 加载目录时自动发现 `network.bkn`。

## Frontmatter

```yaml
---
type: network
id: {network_id}
name: {显示名称}
tags: [tag1, tag2]               # 可选
business_domain: {domain}        # 可选
---
```

## Body 结构

- `# {显示名称}` + 网络描述
- `## Network Overview`：列出所有子目录中的定义 ID

## Template

```markdown
---
type: network
id: {network_id}
name: {网络名称}
tags: [{标签1}, {标签2}]
business_domain: {业务领域}
---

# {网络名称}

{网络描述}

## Network Overview

- **ObjectTypes** (object_types/): {object_id_1}, {object_id_2}
- **RelationTypes** (relation_types/): {relation_id_1}, {relation_id_2}
- **ActionTypes** (action_types/): {action_id_1}
- **ConceptGroups** (concept_groups/): {group_id_1}
```

## Example

See `examples/bkn/k8s-network/network.bkn`.
