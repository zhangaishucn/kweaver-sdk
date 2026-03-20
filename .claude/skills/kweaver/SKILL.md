---
name: kweaver
description: >-
  操作 KWeaver 知识网络与 Decision Agent — 构建知识网络、查询 Schema/实例、
  语义搜索、执行 Action、列举 Agent、与 Agent 对话。
  操作 Vega 数据平台 — 查询 Catalog/资源/模型、DSL/PromQL 查询、健康巡检。
  当用户提到"知识网络"、"知识图谱"、"查询对象类"、
  "执行 Action"、"有哪些 Agent"、"跟 Agent 对话"、
  "数据源"、"Catalog"、"Vega"、"指标模型"、"DSL 查询"、
  "健康检查"、"巡检"等意图时自动使用。
allowed-tools: Bash(kweaver *), Bash(npx kweaver *)
argument-hint: [自然语言指令]
requires:
  env: [KWEAVER_BASE_URL, KWEAVER_BUSINESS_DOMAIN]
---

# KWeaver CLI

KWeaver 平台的命令行工具，覆盖认证、知识网络管理与查询、Vega 数据平台、Agent 对话、可观测诊断。

## 安装

```bash
pip install kweaver-sdk[cli]     # Python（推荐）
npm install -g @kweaver-ai/kweaver-sdk  # Node.js
```

## 使用前提

**所有环境变量已预配置，直接执行命令即可。禁止提前检查环境变量是否存在，禁止询问用户提供密码或 Token。**

### 认证优先级

1. `KWEAVER_TOKEN` + `KWEAVER_BASE_URL` → 静态 Token
2. `~/.kweaver/` 凭据（`kweaver auth login` 写入）→ 自动刷新

## 全局选项

```bash
kweaver [--debug] [--dry-run] [--format md|json|yaml] <command> ...
```

| 选项 | 说明 |
|------|------|
| `--debug` | 打印完整请求/响应 + curl 命令到 stderr |
| `--dry-run` | 写操作只展示不执行 |
| `--format` | 输出格式（默认 `md`，可选 `json`/`yaml`） |

## 上下文管理

```bash
kweaver use kn-abc123   # 设置默认 KN，后续 BKN 命令自动继承
kweaver use             # 查看当前上下文
kweaver use --clear     # 清除
```

## 命令组总览

| 命令组 | 说明 | 详细参考 |
|--------|------|---------|
| `use` | KN 上下文管理 | 见上 |
| `bkn` | BKN 知识网络管理与查询 | `references/bkn.md` |
| `vega` | Vega 数据平台 | `references/vega.md` |
| `ds` | 数据源管理 | `references/ds.md` |
| `query` | 知识网络查询 | `references/query.md` |
| `action` | Action 执行 | `references/action.md` |
| `agent` | Agent 对话 | `references/agent.md` |
| `context-loader` | MCP 分层检索 | `references/context-loader.md` |
| `call` | 通用 API 调用 | `references/call.md` |
| `auth` | 认证管理 | `references/auth.md` |

**按需阅读**：需要具体命令参数或编排示例时，读取对应的 reference 文件。

## 注意事项

- **不要自行猜测 business_domain 值**，使用环境变量配置的值
- `action execute` 有副作用，执行前向用户确认
- 默认输出 Markdown，Agent 解析时用 `--format json`
- 命令组不带子命令 = 展示数据总览（`kweaver bkn` = KN 概览，`kweaver vega` = 平台概览）
- Vega 命令需要 `KWEAVER_VEGA_URL` 环境变量
