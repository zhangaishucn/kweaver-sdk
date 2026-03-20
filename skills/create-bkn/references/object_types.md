# ObjectType (object_types/*.bkn)

每个对象类型一个文件，放在 `object_types/` 目录下。

## Frontmatter

```yaml
---
type: object_type
id: {object_id}                  # 小写+下划线
name: {显示名称}
tags: [tag1, tag2]               # 可选
---
```

## Body 结构

- `## ObjectType: {显示名称}` + 简短描述
- `### Data Properties`（必须）：表格
- `### Keys`（必须）
- `### Logic Properties`（可选）
- `### Data Source`（可选）

### Data Properties 表格

| Name | Display Name | Type | Description | Mapped Field |
|------|--------------|------|-------------|--------------|

### Keys 格式

```
Primary Keys: {key_name}
Display Key: {key_name}
Incremental Key:
```

- Primary Keys：至少一个
- Display Key：一个
- Incremental Key：可选，可为空

### Logic Properties（可选）

每个逻辑属性用 `####` 子标题：

```markdown
#### {property_name}

- **Display**: {显示名}
- **Type**: metric | operator
- **Source**: {source_id} ({source_type})
- **Description**: {description}

| Parameter | Type | Source | Binding | Description |
|-----------|------|--------|---------|-------------|
| {param} | string | property | {property_name} | 从对象属性绑定 |
| {param} | array | input | - | 运行时用户输入 |
| {param} | string | const | {value} | 常量值 |
```

Source 值：`property`（对象属性）/ `input`（用户输入）/ `const`（常量）
Binding：property 时填属性名，const 时填常量值，input 时填 `-`

### Data Source（可选）

| Type | ID | Name |
|------|-----|------|
| data_view | {view_id} | {view_name} |

## 数据类型

Type 列标准类型（大小写不敏感）：

| 类型 | 说明 |
|------|------|
| string | 字符串 |
| integer | 整数 |
| float | 浮点数 |
| decimal | 精确十进制数 |
| boolean | 布尔值 |
| date | 日期（无时间） |
| time | 时间（无日期） |
| datetime | 日期时间 |
| text | 长文本 |
| json | JSON 结构数据 |
| binary | 二进制数据 |

不在列表中的类型透传。

## Template

```markdown
---
type: object_type
id: {object_id}
name: {对象名称}
tags: [{标签1}, {标签2}]
---

## ObjectType: {对象名称}

{详细描述}

### Data Properties

| Name | Display Name | Type | Description | Mapped Field |
|------|--------------|------|-------------|--------------|
| {name} | {显示名} | string | {说明} | {mapped_field} |
| {name} | {显示名} | integer | {说明} | {mapped_field} |

### Logic Properties

### Keys

Primary Keys: {primary_key}
Display Key: {display_key}
Incremental Key:

### Data Source

| Type | ID | Name |
|------|-----|------|
| data_view | {view_id} | {view_name} |
```

## Example

See `examples/bkn/k8s-network/object_types/pod.bkn`.
