---
name: kweaver
description: >-
  操作 KWeaver 知识网络与 Decision Agent — 构建知识网络、查询 Schema/实例、
  语义搜索、执行 Action、列举 Agent、与 Agent 对话。
  当用户提到"知识网络"、"知识图谱"、"查询对象类"、
  "执行 Action"、"有哪些 Agent"、"跟 Agent 对话"等意图时自动使用。
allowed-tools: Bash(kweaver *), Bash(npx kweaver *)
argument-hint: [自然语言指令]
requires:
  env: [KWEAVER_BASE_URL, KWEAVER_BUSINESS_DOMAIN, KWEAVER_TOKEN]
  bins: [node]
---

# KWeaver CLI

KWeaver 平台的命令行工具，覆盖认证、知识网络管理与查询、Agent 对话、Context Loader 检索、通用 API 调用五大能力。

## 安装

```bash
npm install -g kweaver-sdk
```

需 Node.js 22+。也可用 `npx kweaver` 临时运行。

## 使用前提

**使用任何命令前，必须先认证。** 若用户未认证，提示先执行 `kweaver auth login <platform-url>`。

**重要规则**:
1. **所有环境变量已预配置，直接执行命令即可。禁止提前检查环境变量是否存在，禁止询问用户提供密码或 Token。**

### 认证优先级

CLI 按以下顺序尝试认证（无需用户干预）：

1. **环境变量 Token** — `KWEAVER_TOKEN` + `KWEAVER_BASE_URL` 同时存在时优先使用
2. **ConfigAuth** — 读取 `~/.kweaver/` 凭据（由 `kweaver auth login` 写入），自动刷新 Token

环境变量 `KWEAVER_BASE_URL` 和 `KWEAVER_BUSINESS_DOMAIN` 用于指定平台地址和业务域。

---

## 命令速查

### 认证 (auth)

```bash
kweaver auth login <platform-url>                # 浏览器 OAuth2 登录
kweaver auth login <platform-url> --alias prod   # 登录并设别名
kweaver auth status                              # 当前认证状态
kweaver auth list                                # 已保存的平台
kweaver auth use <platform|alias>                # 切换平台
kweaver auth delete <platform|alias>             # 删除平台配置
kweaver auth logout                              # 登出
kweaver token                                    # 打印当前 access token
```

### 知识网络 (kn)

```bash
kweaver kn list [options]                        # 列出知识网络
kweaver kn get <kn-id> [options]                 # 查看详情
kweaver kn stats <kn-id>                          # 查看统计
kweaver kn export <kn-id>                         # 导出定义
kweaver kn create [options]                      # 创建网络
kweaver kn update <kn-id> [options]              # 更新网络
kweaver kn delete <kn-id> [--yes]                 # 删除（默认需确认）
kweaver kn object-type query <kn-id> <ot-id> ['<json>']   # 对象实例查询
kweaver kn object-type properties <kn-id> <ot-id> '<json>' # 对象属性查询
kweaver kn subgraph <kn-id> '<json>'              # 子图查询
kweaver kn action-type query <kn-id> <at-id> '<json>'     # 行动信息查询
kweaver kn action-type execute <kn-id> <at-id> '<json>' [--wait] # 执行行动
kweaver kn action-execution get <kn-id> <execution-id>    # 获取执行状态
kweaver kn action-log list <kn-id> [options]     # 列出执行日志
kweaver kn action-log get <kn-id> <log-id>       # 查看执行日志
kweaver kn action-log cancel <kn-id> <log-id>    # 取消执行
```

### Agent (agent)

```bash
kweaver agent list [options]                      # 列出已发布 Agent
kweaver agent chat <agent-id> [-m "message"]      # 与 Agent 对话（支持交互式 TUI）
kweaver agent sessions <agent-id>                 # 列出会话
kweaver agent history <conversation-id>           # 查看消息历史
```

### Context Loader

```bash
kweaver context-loader config set --kn-id <id>    # 配置当前知识网络
kweaver context-loader config use <name>          # 切换配置
kweaver context-loader config list                # 列出所有配置
kweaver context-loader config show                # 查看当前配置
kweaver context-loader kn-search "<query>"        # 检索 schema
kweaver context-loader query-object-instance '<json>'  # 查询实例
kweaver context-loader query-instance-subgraph '<json>' # 子图
kweaver context-loader get-logic-properties '<json>'    # 逻辑属性
kweaver context-loader get-action-info '<json>'         # 行动信息
```

### 通用 API 调用 (call)

```bash
kweaver call <path>                               # GET（自动注入认证）
kweaver call <path> -X POST -d '<json>'           # POST
kweaver call <path> -H "Name: Value" -bd <domain> # 自定义 header、业务域
```

---

## 操作手册

### 1. 探索已有知识网络

```bash
kweaver kn list
kweaver kn get <kn-id> --stats
kweaver kn export <kn-id>
```

### 2. 查询知识网络数据

```bash
# 通过 Context Loader 分层检索
kweaver context-loader config set --kn-id <kn-id>
kweaver context-loader kn-search "高血压 治疗 药品" --only-schema --pretty

# 直接查询对象实例
kweaver kn object-type query <kn-id> <ot-id> --limit 10 --pretty
```

### 3. Agent 对话

```bash
kweaver agent list
kweaver agent chat <agent-id> -m "华东仓库库存情况"
kweaver agent sessions <agent-id>
kweaver agent history <conversation-id>
```

### 4. 执行 Action

```bash
kweaver kn action-type execute <kn-id> <at-id> '{"params":{}}' --wait
kweaver kn action-log list <kn-id>
kweaver kn action-log get <kn-id> <log-id>
```

---

## KN 与 Context Loader 的边界

- **kn**：直接调用 ontology-query 原生接口，适合已知 `kn_id`、`ot_id`、`at_id` 且需透传 JSON 的场景
- **context-loader**：schema → 实例 → 逻辑属性/行动信息 的分层检索工作流，适合 Agent 化检索（需先 `kn-search` 发现 schema，再逐层调用）

---

## 注意事项

- **不要自行猜测或枚举 business_domain 值**，只使用环境变量中配置的值
- `action-type execute` 有副作用，仅在用户明确请求时执行，执行前向用户确认
- 所有命令输出 JSON 格式，默认 pretty-print（indent=2）
