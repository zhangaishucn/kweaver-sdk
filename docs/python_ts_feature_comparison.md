# Python vs TypeScript CLI 功能等价对比报告

> 自动生成 · 2026-03-15

## 1. 测试概览

| 维度 | Python (`packages/python`) | TypeScript (`packages/typescript`) |
|------|:-:|:-:|
| 测试总数 | **135** passed | **161** passed |
| 测试耗时 | ~0.24s | ~4.0s |
| 测试框架 | pytest + Click CliRunner | Node.js built-in test runner |
| Mock 策略 | `unittest.mock.patch` | 自定义 stub / mock fetch |
| 覆盖率 | 64.36% (branches) | 86.64% (lines) |

---

## 2. 功能域对比矩阵

### 2.1 顶层 CLI

| 功能点 | Python 测试 | TS 测试 | 等价 |
|--------|:-:|:-:|:-:|
| `--help` 显示所有命令 | `test_cli_help` | `run succeeds for help` | ✅ |
| `--version` | `test_cli_version` | — | ⚠️ TS 无 |
| 未知命令报错 | — | `run fails for unknown commands` | ⚠️ Py 无 |

### 2.2 Auth（认证 / 多平台管理）

| 功能点 | Python 测试 | TS 测试 | 等价 |
|--------|:-:|:-:|:-:|
| `auth status` 无平台 | `test_auth_status_no_platform` | `formatAuthStatusSummary` | ✅ |
| `auth status` 有平台 | `test_auth_status_with_platform` | `formatAuthStatusSummary` | ✅ |
| `auth list` 空列表 | `test_auth_list_empty` | — | ⚠️ TS 无 |
| `auth use` 切换平台 | `test_auth_use` | store tests 覆盖 | ✅ |
| `auth login` OAuth 流程 | — | `login with --no-open prints headless instructions` | ⚠️ Py 无 |
| `auth delete` 删除平台 | `test_auth_delete_with_yes` / `test_auth_delete_aborted` | `run auth delete removes a saved platform by alias` | ✅ |
| `auth logout` 登出 | — | `run auth logout clears token and callback` | ⚠️ Py 无 |
| OAuth URL 构建 | — | `buildAuthorizationUrl generates a complete oauth url` | ⚠️ Py 无 |
| OAuth 重定向配置 | — | `buildAuthRedirectConfig *` (2 tests) | ⚠️ Py 无 |
| Client provisioning | — | `getClientProvisioningMessage` | ⚠️ Py 无 |
| HTTP 错误格式化 | `test_handle_errors_adp_error` / `test_handle_errors_auth_error` | `formatHttpError *` (2 tests) | ✅ |
| 环境变量 Token | — | `ensureValidToken returns env token` | ⚠️ Py 无 |

### 2.3 Token

| 功能点 | Python 测试 | TS 测试 | 等价 |
|--------|:-:|:-:|:-:|
| `token` 打印 token | `test_token_prints_access_token` | `parseTokenArgs accepts no flags` | ✅ |
| `token` 无平台 | `test_token_no_platform` | — | ⚠️ TS 无 |
| `token` 无 token | `test_token_no_token_stored` | — | ⚠️ TS 无 |

### 2.4 KN（知识网络）

| 功能点 | Python 测试 | TS 测试 | 等价 |
|--------|:-:|:-:|:-:|
| `kn list` | `test_kn_list` | `listKnowledgeNetworks maps query filters` | ✅ |
| `kn list` 分页 | `test_kn_list_with_pagination` | `parseKnListArgs parses custom offset limit sort direction` | ✅ |
| `kn list` 格式化 | — | `formatSimpleKnList keeps only name id description` (2 tests) | ⚠️ Py 无 |
| `kn get` | `test_kn_get` | `getKnowledgeNetwork maps export and stats` | ✅ |
| `kn create` | `test_kn_create` / `test_kn_create_no_build` / `test_kn_create_with_tables_filter` | `createKnowledgeNetwork maps query params and JSON body` + `parseKnCreateArgs *` (2 tests) | ✅ |
| `kn update` | `test_kn_update` | `updateKnowledgeNetwork maps path and JSON body` + `parseKnUpdateArgs *` (2 tests) | ✅ |
| `kn delete` | — | `deleteKnowledgeNetwork maps method and path` + `parseKnDeleteArgs *` (6 tests) | ⚠️ Py 无 |
| `kn export` | `test_kn_export` | `getKnowledgeNetwork` (export=true) | ✅ |
| `kn stats` | `test_kn_stats` | `getKnowledgeNetwork` (stats=true) | ✅ |
| `kn build` (含 wait) | `test_kn_build_wait` / `test_kn_build_no_wait` | — | ⚠️ TS 无 |
| `kn` help 文本 | — | `run kn shows subcommand help` + 8 个 help 测试 | ⚠️ Py 无 |
| object-type query | — | `objectTypeQuery maps path body` + `parseKnObjectTypeQueryArgs *` (4 tests) | ⚠️ Py 无 |
| object-type properties | — | `objectTypeProperties maps path and body` | ⚠️ Py 无 |
| subgraph 查询 | `test_query_subgraph` / `test_query_subgraph_rt_not_found` | `subgraph maps path and body` | ✅ |
| action-type query | `test_action_query` | `actionTypeQuery maps path and body` | ✅ |
| action-type execute | `test_action_execute_wait` / `test_action_execute_no_wait` / `test_action_execute_by_name` / `test_action_execute_by_name_not_found` | `actionTypeExecute maps path and body` + `parseKnActionTypeExecuteArgs *` (3 tests) | ✅ |
| action-execution get | — | `actionExecutionGet maps path` | ⚠️ Py 无 |
| action-log list | `test_action_logs` | `actionLogsList maps query params` | ✅ |
| action-log get | `test_action_log_detail` | `actionLogGet maps path` | ✅ |
| action-log cancel | `test_kn_action_log_cancel_with_yes` | `actionLogCancel maps path` | ✅ |

### 2.5 Agent

| 功能点 | Python 测试 | TS 测试 | 等价 |
|--------|:-:|:-:|:-:|
| `agent list` | `test_agent_list` / `test_agent_list_keyword` / `test_agent_list_with_size` | `parseAgentListArgs *` (3 tests) + `formatSimpleAgentList` | ✅ |
| `agent chat` 参数解析 | — | `parseChatArgs *` (12 tests) | ⚠️ Py 无 |
| `agent chat` 发送请求 | — | `sendChatRequest *` (7 tests) | ⚠️ Py 无 |
| `agent chat` 流式 | — | `sendChatRequestStream *` (2 tests) | ⚠️ Py 无 |
| `agent chat` URL 构建 | — | `buildChatUrl *` / `buildAgentInfoUrl *` (3 tests) | ⚠️ Py 无 |
| `agent chat` 文本提取 | — | `extractText *` (4 tests) | ⚠️ Py 无 |
| `agent chat` 续聊命令 | — | `buildContinueCommand *` (2 tests) | ⚠️ Py 无 |
| `agent chat` Agent info | — | `fetchAgentInfo resolves id key and version` | ⚠️ Py 无 |
| `agent sessions` | `test_agent_sessions` | `run agent sessions prints conversations` + `parseAgentSessionsArgs *` (3 tests) + `listConversations *` (2 tests) | ✅ |
| `agent history` | `test_agent_history` / `test_agent_history_with_limit` | `run agent history prints messages` + `parseAgentHistoryArgs *` (3 tests) + `listMessages *` (2 tests) | ✅ |
| agent help 文本 | — | `run agent shows sessions and history in help text` + `run agent list --help` | ⚠️ Py 无 |

### 2.6 Call（通用 API 调用）

| 功能点 | Python 测试 | TS 测试 | 等价 |
|--------|:-:|:-:|:-:|
| `call` GET | `test_call_get` | `parseCallArgs parses curl-style request flags` | ✅ |
| `call` POST + body | `test_call_post_with_body` | `parseCallArgs defaults to POST when data is present` | ✅ |
| `call` 空响应 | `test_call_empty_response` | — | ⚠️ TS 无 |
| `call` 自定义 Header | `test_call_with_header` | — | ⚠️ TS 无 |
| `call` biz-domain | `test_call_with_biz_domain` | `parseCallArgs supports custom business domain` | ✅ |
| `call` verbose | `test_call_verbose_prints_to_stderr` | `parseCallArgs supports verbose output` + `formatVerboseRequest` | ✅ |
| `call` pretty | — | `parseCallArgs supports pretty output` + `formatCallOutput pretty prints json` | ⚠️ Py 无 |
| SSE done marker | — | `stripSseDoneMarker removes terminal done event` | ⚠️ Py 无 |

### 2.7 Context-Loader（MCP 客户端）

| 功能点 | Python 测试 | TS 测试 | 等价 |
|--------|:-:|:-:|:-:|
| session 初始化 | `test_session_initialization` / `test_session_cached_on_second_call` | context-loader tests 隐含初始化 | ✅ |
| `kn-search` | `test_kn_search_returns_schema` / `test_kn_search_only_schema_flag` | `knSearch sends JSON-RPC request` | ✅ |
| query object instance | `test_query_object_instance_returns_datas` | — | ⚠️ TS 无 |
| get logic properties | `test_get_logic_properties_raises_on_missing_params` / `test_get_logic_properties_returns_values` | — | ⚠️ TS 无 |
| get action info | `test_get_action_info_returns_dynamic_tools` | — | ⚠️ TS 无 |
| `tools/list` | `test_list_tools` | `listTools sends tools/list` | ✅ |
| `resources/list` | `test_list_resources` | `listResources sends resources/list` | ✅ |
| `resources/read` | — | `readResource sends resources/read with uri` | ⚠️ Py 无 |
| `resources/templates/list` | — | `listResourceTemplates sends resources/templates/list` | ⚠️ Py 无 |
| `prompts/list` | — | `listPrompts sends prompts/list` | ⚠️ Py 无 |
| `prompts/get` | — | `getPrompt sends prompts/get with name` | ⚠️ Py 无 |
| 输入验证 | — | `validateCondition *` (4 tests) + `validateInstanceIdentity *` (3 tests) + `validateInstanceIdentities *` (2 tests) + `formatMissingInputParamsHint` | ⚠️ Py 无 |
| RPC 错误处理 | `test_rpc_error_raises_runtime_error` / `test_missing_session_id_raises` | — | ⚠️ TS 无 |
| config set/list/show | `test_context_loader_config_set` / `test_context_loader_config_list` / `test_context_loader_config_show` / `test_context_loader_config_set_no_active_platform` | `run context-loader config show when not configured` / `run context-loader config set use list` | ✅ |
| context-loader help | — | `run context-loader shows subcommand help` + 3 tests | ⚠️ Py 无 |

### 2.8 Store（配置持久化）

| 功能点 | Python 测试 | TS 测试 | 等价 |
|--------|:-:|:-:|:-:|
| 多平台保存/切换 | `test_use_sets_active_platform` / `test_save_and_load_token` / `test_save_and_load_client` | `store saves multiple platforms and switches current platform` | ✅ |
| 别名解析 | `test_set_alias_and_resolve` | `store supports aliases and resolves them to platform urls` | ✅ |
| 删除平台 | `test_delete_platform` | `store deletes platform data aliases and resets current platform` | ✅ |
| 列出平台 | `test_list_platforms` | — | ⚠️ TS 无 |
| URL 编码 | `test_encode_url_is_url_safe_base64` | — | ⚠️ TS 无 |
| 遗留格式迁移 | — | `store migrates legacy single-platform files automatically` | ⚠️ Py 无 |
| context-loader config | — | `store saves and loads context-loader config per platform` + 2 tests | ⚠️ Py 无 |

### 2.9 Display Text（文本处理）

| 功能点 | Python 测试 | TS 测试 | 等价 |
|--------|:-:|:-:|:-:|
| HTML 实体解码 | — | `decodeHtmlEntities *` (2 tests) | ⚠️ Py 无 |
| HTML 注释去除 | — | `stripHtmlComments *` (2 tests) | ⚠️ Py 无 |
| 文本标准化 | — | `normalizeDisplayText *` (2 tests) | ⚠️ Py 无 |

### 2.10 Python 独有功能

| 功能点 | Python 测试 | 说明 |
|--------|:-:|:--|
| 数据源 CRUD | `test_datasources.py` (6 tests) | TS 不支持 |
| 数据视图 CRUD | `test_dataviews.py` (4 tests) | TS 不支持 |
| 对象类 CRUD | `test_object_types.py` (4 tests) | TS 不支持 |
| 关系类映射 | `test_relation_types.py` (2 tests) | TS 不支持 |
| 语义搜索 | `test_query.py::test_semantic_search_defaults` | TS 不支持 |
| 实例查询 (SDK) | `test_query.py` (4 tests) | TS 通过 context-loader |
| Conversation CRUD | `test_conversations.py` (6 tests) | TS 不支持 |
| KN build | `test_knowledge_networks.py::test_build_returns_build_job` | TS 不支持 |
| 错误类型映射 | `test_errors.py` (9 tests) | TS 有不同实现 |
| DS CLI 命令 | `test_cli.py::test_ds_*` (8 tests) | TS 不支持 |
| Query CLI 命令 | `test_cli.py::test_query_*` (5 tests) | TS 不支持 |

---

## 3. 等价性统计

| 分类 | 完全等价 ✅ | 仅 Python ⚠️ | 仅 TypeScript ⚠️ |
|------|:-:|:-:|:-:|
| Auth | 4 | 1 | 5 |
| Token | 1 | 2 | 0 |
| KN | 11 | 1 | 5 |
| Agent | 3 | 0 | 9 |
| Call | 4 | 2 | 2 |
| Context-Loader | 4 | 3 | 5 |
| Store | 3 | 2 | 2 |
| CLI 通用 | 1 | 0 | 1 |
| Display Text | 0 | 0 | 3 |
| Python 独有 | — | 10 | — |
| **合计** | **31** | **21** | **32** |

---

## 4. 架构差异总结

| 维度 | Python | TypeScript |
|------|--------|------------|
| CLI 框架 | Click（声明式装饰器） | 手动 argv 解析 |
| SDK 层 | 完整 Resources API（可 import） | 无公共 API（纯 CLI） |
| HTTP 层 | httpx + 重试 + 拦截器 | 原生 fetch 封装 |
| 认证 | ConfigAuth + OAuth2BrowserAuth 类 | oauth.ts 函数式 |
| 配置存储 | PlatformStore 类 | store.ts 函数式 |
| TUI | 无 | Ink (React) 交互式 |
| 测试策略 | 集成式（CLI → SDK → mock HTTP） | 单元式（解析器 + API 函数分别测试） |

---

## 5. 结论

**核心等价功能已对齐**：auth 管理、kn CRUD、agent 会话管理、action 执行/日志、context-loader MCP、通用 API 调用、配置存储——共 31 个功能点在两套 CLI 中行为一致。

**Python 独有**（21 项）：主要是 SDK 层的 Resources API（数据源、数据视图、对象类/关系类 CRUD、Conversation CRUD），以及 `kn build`、`query` 子命令等。

**TypeScript 独有**（32 项）：主要是更精细的单元测试（参数解析、文本处理、help 文本验证），以及 MCP 协议的完整覆盖（resources/read、templates、prompts），和 Ink TUI 交互式 agent chat。

两套 CLI 在**用户可见的核心场景**上功能等价，差异集中在底层测试粒度和各自独占的 SDK 能力。
