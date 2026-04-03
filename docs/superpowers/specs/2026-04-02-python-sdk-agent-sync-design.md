# Python SDK Agent 功能同步与测试补充设计文档

**日期**: 2025-04-02
**作者**: Claude
**状态**: 草案

## 1. 概述

本文档描述如何在 Python SDK 中实现与 TypeScript SDK 相同的新增 Agent 功能，并为两者添加单元测试。

### 1.1 背景

TypeScript SDK 最近新增了以下功能：
- 4 个新 API 函数（个人空间列表、模板列表、模板详情、分类列表）
- 4 个新 CLI 命令
- 2 个 CLI 命令增强（保存配置、知识网络配置）

Python SDK 需要同步实现这些功能，并补充相应的单元测试。

### 1.2 目标

1. 在 Python SDK 中实现与 TS SDK 完全一致的 API 和 CLI 功能
2. 为 Python 和 TypeScript SDK 的新增功能编写单元测试
3. 保持代码风格和测试风格与现有代码一致

---

## 2. 架构设计

### 2.1 分层结构

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI Layer                             │
│  (agent.py: personal-list, template-list, template-get, etc.)  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Resource Layer                           │
│  (agents.py: list_personal, list_templates, get_template, etc.) │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      HTTP Layer                              │
│                   (_http.py: fetch methods)                    │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 类型定义

新增类型定义在 `types.py` 中：

```python
class AgentTemplate(BaseModel):
    id: str
    name: str
    description: str
    config: dict[str, Any] | None = None

class AgentCategory(BaseModel):
    id: str
    name: str
    description: str = ""
```

---

## 3. 阶段 1：Python SDK API 层扩展

### 3.1 文件修改

**文件**: `packages/python/src/kweaver/resources/agents.py`

#### 新增方法

1. **list_personal()** - 列出私人空间 Agent
2. **list_templates()** - 列出已发布模板
3. **get_template()** - 获取模板详情
4. **list_categories()** - 列出分类

#### 修改方法

**publish()** 方法新增 `category_id` 参数

### 3.2 单元测试

**文件**: `packages/python/tests/unit/test_agents.py`

新增测试用例：
- `test_list_personal_agents()`
- `test_list_personal_agents_with_filters()`
- `test_list_templates()`
- `test_list_templates_with_filters()`
- `test_get_template()`
- `test_list_categories()`
- `test_publish_with_category_id()`

---

## 4. 阶段 2：Python CLI 命令扩展

### 4.1 文件修改

**文件**: `packages/python/src/kweaver/cli/agent.py`

#### 新增子命令

1. `agent personal-list` - 列出私人空间 Agent
2. `agent category-list` - 列出 Agent 分类
3. `agent template-list` - 列出已发布模板
4. `agent template-get` - 获取模板详情（支持 `--save-config`）

#### 新增命令

1. `agent update` - 更新 Agent（支持 `--knowledge-network-id` 和 `--config-path`）

#### 现有命令增强

1. `agent get` - 新增 `--save-config` 选项

### 4.2 工具函数

新增 `_generate_timestamped_path()` 函数用于生成带时间戳的文件路径。

### 4.3 单元测试

**文件**: `packages/python/tests/unit/test_cli_agent.py`（新建）

新增测试用例覆盖所有新增和增强的 CLI 命令。

---

## 5. 阶段 3：TypeScript SDK 测试补充

### 5.1 API 层测试

**文件**: `packages/typescript/test/api/agent-list.test.ts`（新建）

为以下 API 函数编写测试：
- `listPersonalAgents`
- `listPublishedAgentTemplates`
- `getPublishedAgentTemplate`
- `listAgentCategories`

### 5.2 CLI 命令测试

**文件**: `packages/typescript/test/agent-new-commands.test.ts`（新建）

测试内容：
- 参数解析函数
- 命令执行函数
- 时间戳路径生成工具

---

## 6. 实现细节

### 6.1 时间戳格式

两个 SDK 使用相同的时间戳格式：`YYYY-MM-DDTHH-MM-SS`

示例：`2026-04-02T14-21-26`

### 6.2 API 端点映射

| 功能 | API 端点 |
|------|---------|
| 个人空间列表 | `GET /personal-space/agent-list` |
| 模板列表 | `GET /published/agent-tpl` |
| 模板详情 | `GET /published/agent-tpl/{id}` |
| 分类列表 | `GET /category` |
| 发布（增强） | `POST /agent/{id}/publish` |

### 6.3 测试框架

- **Python**: 使用 `pytest` 和 `httpx.Request`
- **TypeScript**: 使用 `node:test` 和 mock `fetch`

---

## 7. 验收标准

- [ ] Python SDK 新增 4 个 API 方法
- [ ] Python SDK 新增 5 个 CLI 子命令（含 update）
- [ ] Python SDK 1 个 CLI 命令增强（get）
- [ ] Python 新增约 15+ 个单元测试用例
- [ ] TypeScript SDK 新增约 15+ 个单元测试用例
- [ ] 所有测试通过
- [ ] 代码风格与现有代码一致

---

## 8. 风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| API 端点行为不一致 | 先进行手动测试验证 |
| 测试 mock 不完整 | 参考现有测试的 mock 模式 |
| 时间戳处理差异 | 统一使用 datetime 格式化 |
| Python click 参数解析 | 参考 click 官档和现有命令 |

---

## 9. 附录

### 9.1 参考文件

- TypeScript 实现：`packages/typescript/src/commands/agent.ts`
- TypeScript API：`packages/typescript/src/api/agent-list.ts`
- Python Agent 资源：`packages/python/src/kweaver/resources/agents.py`
- Python CLI：`packages/python/src/kweaver/cli/agent.py`

### 9.2 相关文档

- [agent.md](skills/kweaver-core/references/agent.md) - Agent 命令参考
- [SKILL.md](skills/kweaver-core/SKILL.md) - Skill 文档
