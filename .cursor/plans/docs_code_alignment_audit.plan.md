---
name: 设计文档与实现对齐审计
overview: |
  对比 docs/ 中 4 份设计文档与当前 monorepo 实际代码的差异，列出所有不匹配项，
  按"文档过时/代码缺失/结构错误"分类，生成可执行的修复计划。
todos:
  - id: fix-design-doc-structure
    content: "[文档] kweaver_sdk_design.md §5.2 目录树仍描述 skills/ + mcp/ 模块（已删除/未实现），且未反映 monorepo packages/ 结构"
    status: pending
  - id: fix-design-doc-naming
    content: "[文档] kweaver_sdk_design.md 中仍存在 'kweaverc' / 'kweaver-caller' 的引用，应统一为 kweaver（TS CLI）"
    status: pending
  - id: fix-integration-doc-status
    content: "[文档] integration_kweaver_caller.md 中 Context-Loader MCP 和对象类属性查询仍标为 P1 未完成，实际 Python 已实现 context_loader resource"
    status: pending
  - id: fix-integration-doc-structure
    content: "[文档] integration_kweaver_caller.md §5.2 目录树完全过时 — 列出了已删除的 skills/、integration/、mcp/ 目录，且未反映 monorepo"
    status: pending
  - id: fix-cli-refactor-spec-status
    content: "[文档] cli-first-refactor-design.md 状态 Completed 但内容未更新，仍引用旧路径 src/kweaver/skills/、tests/integration/"
    status: pending
  - id: fix-cli-refactor-plan-cleanup
    content: "[文档] cli-first-refactor.md（plan）任务步骤仍为 unchecked，应标记为已完成或删除"
    status: pending
  - id: fix-readme-py-only-cmds
    content: "[文档] README.md 中 'Python CLI 额外提供 ds/query/action' 与 SKILL.md 内容一致，但 TS CLI 的 kn 子命令结构不同（object-type/subgraph/action 在 kn 下），应明确差异"
    status: pending
  - id: fix-skill-md-py-ts-diff
    content: "[文档] SKILL.md 列出 Python 独有 ds/query/action 命令，但 TS 有等价功能在 kn 子命令下，需要更精确说明而非简单列为'独有'"
    status: pending
  - id: fix-comparison-doc-not-referenced
    content: "[文档] python_ts_feature_comparison.md 是自动生成的对比报告，未被 README 或其他文档引用"
    status: pending
  - id: code-py-context-loader-not-in-mcp
    content: "[代码 vs 设计] 设计文档要求 src/kweaver/mcp/ 模块（MCPClient 类），实际实现在 resources/context_loader.py，结构不匹配"
    status: pending
  - id: code-py-no-object-type-properties
    content: "[代码 vs 设计] integration_kweaver_caller.md §3.2.2 要求 QueryResource.object_type_properties()，Python SDK 未实现此方法"
    status: pending
  - id: code-ts-repo-url-wrong
    content: "[代码] packages/typescript/package.json repository.url 仍指向 kweaver-caller 旧仓库"
    status: pending
  - id: code-ts-npm-test-script-broken
    content: "[代码] packages/typescript/package.json scripts.test 使用引号包裹 glob（'test/**/*.test.ts'），在 npm run test 下可能失败"
    status: pending
  - id: code-root-package-json-outdated
    content: "[代码] 根 package.json version 0.5.0，与 Python 0.6.0 和 TS 0.1.4 均不匹配"
    status: pending
  - id: docs-e2e-tests-stale
    content: "[代码 vs 设计] cli-refactor-design 要求重写 test_full_flow_e2e.py 和 test_context_loader_e2e.py，实际 e2e/ 下文件可能仍引用已删除的 skills"
    status: pending
  - id: docs-design-monorepo-gap
    content: "[文档] kweaver_sdk_design.md 完全未提及 TypeScript CLI / monorepo / packages/ 结构，仍描述纯 Python 项目"
    status: pending
isProject: false
---

# 设计文档与实现对齐审计

## 审计范围

| 文档 | 路径 | 角色 |
|------|------|------|
| SDK 设计文档 | `docs/kweaver_sdk_design.md` | 主设计文档（v0.6.0） |
| 整合方案 | `docs/integration_kweaver_caller.md` | TS → Python 能力整合计划 |
| CLI 重构规格 | `docs/superpowers/specs/2026-03-13-cli-first-refactor-design.md` | CLI-first 架构决策 |
| CLI 重构计划 | `docs/superpowers/plans/2026-03-13-cli-first-refactor.md` | CLI-first 实施计划 |
| 功能对比 | `docs/python_ts_feature_comparison.md` | Python vs TS 测试对比报告 |
| README | `README.md` | 项目入口文档 |
| SKILL.MD | `skills/kweaver-core/SKILL.md` | AI Agent 操作手册 |

## 发现的问题（17 项）

### A. 文档结构过时（7 项）

#### A1. kweaver_sdk_design.md — 未反映 monorepo 结构
**严重程度**: 高
**位置**: §4.1 逻辑分层、§5.2 目录树
**问题**: 整个文档描述的是纯 Python 单仓结构 `src/kweaver/`。实际项目已重组为：
```
kweaver-sdk/
├── packages/python/src/kweaver/   ← 实际位置
├── packages/typescript/src/       ← 文档完全未提及
```
**文档中的错误路径**: `src/kweaver/skills/`（已删除）、`src/kweaver/mcp/`（未创建，用了 `resources/context_loader.py` 替代）
**修复**: 更新 §5.2 目录树反映 monorepo，增加 "TypeScript CLI" 章节

#### A2. integration_kweaver_caller.md — 目录树完全过时
**严重程度**: 高
**位置**: §5.2 目录变更
**问题**: 列出了 `src/kweaver/skills/`（已删除）、`tests/integration/`（已删除）、`src/kweaver/mcp/`（未按此结构实现）、`tests/cli/`（测试在 tests/unit/test_cli.py）。实际已经是 monorepo 结构。
**修复**: 重写 §5.2 或标记为"历史文档，已完成"

#### A3. integration_kweaver_caller.md — P1 状态未更新
**严重程度**: 中
**位置**: §2 能力对比表
**问题**: "Context-Loader MCP" 仍标为 **P1**（待完成），实际 Python 已有 `resources/context_loader.py` + `cli/context_loader.py`。"对象类属性查询"仍标为 **P1**，TS 已实现但 Python 未实现。
**修复**: 更新状态标记

#### A4. cli-first-refactor-design.md — 已完成但内容未清理
**严重程度**: 低
**位置**: 全文
**问题**: Status 标记为 "Completed (v0.6.0)"，但内容仍引用旧路径 `src/kweaver/skills/`、`tests/integration/`。作为历史记录可以保留，但容易误导。
**修复**: 在文件头部加 "本文为历史记录" 声明

#### A5. cli-first-refactor.md（plan）— 任务全部 unchecked
**严重程度**: 低
**位置**: 全文 15 个任务
**问题**: 所有 `- [ ]` 步骤均未标记完成，但实际全部已实现。
**修复**: 批量改为 `- [x]` 或在文件头标记 "已全部完成"

#### A6. kweaver_sdk_design.md — 仍引用 kweaverc
**严重程度**: 中
**位置**: §8（认证设计）中多处引用
**问题**: 文档中仍有 `kweaverc auth <url>` 等旧命令名。实际 CLI 已统一为 `kweaver`。
**修复**: 全局替换 `kweaverc` → `kweaver`（仅在命令引用中）

#### A7. python_ts_feature_comparison.md — 未被任何文档引用
**严重程度**: 低
**问题**: 这份自动生成的对比报告没有从 README 或其他文档链接到，可能被忽略。
**修复**: 在 README 或 integration 文档中添加链接

### B. 代码与设计不匹配（4 项）

#### B1. Context-Loader 实现结构不匹配设计
**严重程度**: 中
**设计要求** (integration_kweaver_caller.md §3.2.3):
```
src/kweaver/mcp/
├── __init__.py
├── client.py    ← MCPClient (JSON-RPC 2.0)
└── server.py    ← 可选 MCP Server
```
**实际实现**:
```
src/kweaver/resources/context_loader.py    ← ContextLoaderResource
src/kweaver/cli/context_loader.py          ← CLI 命令
```
**问题**: 实现为 Resource 而非独立 mcp/ 模块。功能已覆盖（kn_search、query_object_instance 等），但架构不同。
**修复**: 更新设计文档匹配实际实现（Resource 模式更简洁，无需改代码）

#### B2. Python SDK 缺少 object_type_properties 方法
**严重程度**: 中
**设计要求** (integration_kweaver_caller.md §3.2.2):
```python
QueryResource.object_type_properties(kn_id, ot_id, body) -> dict
```
**实际**: Python `resources/query.py` 没有此方法。TS 侧 `ontology-query.ts` 已实现 `objectTypeProperties()`。
**修复**: Python SDK 补充实现，或在文档中标记为"仅 TS 支持"

#### B3. E2E 测试可能仍引用已删除的 skills
**严重程度**: 中
**位置**: `packages/python/tests/e2e/test_full_flow_e2e.py`, `test_context_loader_e2e.py`
**设计要求** (cli-refactor-design): 这两个文件应被重写为 CLI 测试
**修复**: 检查并更新 E2E 测试代码（如仍导入 kweaver.skills 则会运行时报错）

#### B4. packages/typescript/package.json repository URL 指向旧仓库
**严重程度**: 低
**当前值**: `git+https://github.com/sh00tg0a1/kweaver-caller.git`
**应为**: `git+https://github.com/kweaver-ai/kweaver-sdk.git`
**修复**: 更新 package.json

### C. 版本与元数据不一致（2 项）

#### C1. 根 package.json version 与子包不匹配
**严重程度**: 低
**当前**: 根 `package.json` version = `0.5.0`，Python = `0.6.0`，TS = `0.1.4`
**修复**: 统一根 version 为 `0.6.0`，或改为 monorepo 语义版本

#### C2. TS package.json scripts.test glob 问题
**严重程度**: 低
**当前**: `"test": "node --import tsx --test test/**/*.test.ts"`
**问题**: shell 展开在 `npm run test` 下可能不工作（取决于 shell），Makefile 中已修复但 package.json 未同步
**修复**: 同步 package.json 中的 test script

### D. SKILL.md / README 精确度问题（2 项）

#### D1. "Python 独有命令" 表述不准确
**严重程度**: 低
**位置**: README.md, SKILL.md §Python 独有命令
**问题**: `ds` 确实仅 Python 有，但 `query instances/subgraph` 和 `action execute/logs` 在 TS 中有等价功能（在 `kn object-type query`、`kn subgraph`、`kn action-type execute` 下），不应简单标为 "独有"。
**修复**: 改为 "Python CLI 额外的命令组（TS 等价功能在 kn 子命令下）"

#### D2. .claude/skills/kweaver/SKILL.md 与 skills/kweaver-core/SKILL.md 内容不同
**严重程度**: 中
**问题**: cli-refactor-design 要求两者内容一致（仅 frontmatter 可不同）。需验证是否同步。
**修复**: 检查并同步两个 SKILL.md

---

## 建议执行顺序

### Phase 1: 代码修复（不改文档，先修代码问题）
1. B4 — 修 TS package.json repository URL
2. C2 — 修 TS package.json test script
3. C1 — 统一根 package.json version

### Phase 2: 文档更新（最小必要更新）
4. A3 — integration_kweaver_caller.md 更新 P1 状态
5. A6 — kweaver_sdk_design.md 替换 kweaverc 引用
6. A4 + A5 — 给历史文档加 "已完成" 标记
7. A7 — README 增加对比报告链接

### Phase 3: 文档重构（结构性更新）
8. A1 — kweaver_sdk_design.md 增加 monorepo 章节
9. A2 — integration_kweaver_caller.md 更新目录树
10. B1 — 更新 MCP 设计文档匹配 Resource 实现
11. D1 + D2 — 修正 SKILL.md / README 中的独有命令描述

### Phase 4: 代码补充（可选）
12. B2 — Python SDK 补充 object_type_properties 方法
13. B3 — 检查并修复 E2E 测试

---

## 决策点（需要确认）

1. **kweaver_sdk_design.md 是否继续维护？** — 如果是，需要 Phase 3 的大量更新；如果冻结为历史文档，只需加声明。
2. **integration_kweaver_caller.md 是否保留？** — 整合已完成，可标记为归档。
3. **Python SDK 是否补充 object_type_properties？** — 这是 TS 已有但 Python 缺失的功能。
4. **E2E 测试是否需要修复？** — 如果 CI 不运行 E2E（当前 make ci 只跑 unit），可延后处理。
