# Python SDK Auth Parity — Design

**Status:** Approved (brainstorming)
**Author:** cx (assisted)
**Date:** 2026-04-22

---

## Goal

让 Python SDK (`packages/python/`) 在**不依赖 TypeScript CLI、不依赖 Playwright**
的前提下，完整覆盖 TS `packages/typescript/src/auth/oauth.ts` 与
`auth/eacp-modify-password.ts` 的协议层能力，并清理已有死代码（`kweaver.cli`
模块、`PasswordAuth` 类、`playwright` 开发依赖）。

两条核心非功能要求（**不可妥协**）：

1. **TS ↔ Python 一致性**：
   `STUDIOWEB_LOGIN_PUBLIC_KEY_PEM`、`DEFAULT_SIGNIN_RSA_MODULUS_HEX`、
   `KWEAVER_SIGNIN_RSA_PUBLIC_KEY` 环境变量、`InitialPasswordChangeRequiredError`
   错误码 `401001017`、`/oauth2/signin` POST body 字段顺序与 base64 padding
   都必须 byte-for-byte 与 TS 实现一致。
2. **调用者轻松使用**：
   - 一行 `from kweaver.auth import http_signin` 即可登录；
   - 顶层 `kweaver.login(url, username=..., password=...)` 自动选最合适的策略；
   - 所有公共 API 走 keyword-only 参数 + 明确 default；
   - 错误抛 typed exception，永不 print；
   - 返回值都是结构化 dict / TypedDict / dataclass，方便 IDE 补全。

## Non-Goals

- 新增 Python `kweaver` 命令行 CLI（用户已确认放弃，转而专注 SDK）。
- 兼容旧 `PasswordAuth` API（属 0.x 破坏性变更）。
- 重写已有 `OAuth2BrowserAuth` / `ConfigAuth` / `OAuth2Auth` / `TokenAuth`
  / `NoAuth`，仅新增方法。
- TS 侧的修改（本 spec 只动 Python）。

## Architecture

新建 `packages/python/src/kweaver/auth/` 子包，按职责拆 6 个文件：

```
packages/python/src/kweaver/auth/
├── __init__.py        # public re-exports（唯一对外入口）
├── _crypto.py         # RSA PKCS#1 v1.5 加密 + modulus→PEM
├── _signin_html.py    # Next.js __NEXT_DATA__ 解析
├── _http_signin.py    # GET/POST /oauth2/signin + cookie jar + redirect chain
├── eacp.py            # eacp_modify_password / fetch_eacp_user_info / 401001017
└── store_helpers.py   # whoami / list_platforms / list_users / set_active_user
                       # / export_credentials
```

`packages/python/src/kweaver/_auth.py`（现有）：

- **新增** `HttpSigninAuth(AuthProvider)` — 用 `auth._http_signin` 的成果，
  对外像 `OAuth2BrowserAuth` 一样可以直接当 auth provider 用。
- **新增** `OAuth2BrowserAuth.login_with_refresh_token(client_id, client_secret,
  refresh_token, *, tls_insecure=False)` — headless 机器首次写入凭据。
- **删除** `PasswordAuth` 类。

`packages/python/src/kweaver/__init__.py`：

- 顶层 re-export `kweaver.auth` 的 6 个最常用名字
  (`http_signin`, `HttpSigninAuth`, `eacp_modify_password`, `whoami`,
   `list_platforms`, `InitialPasswordChangeRequiredError`)。
- 新增 `kweaver.login(...)`（见下）。

## Public API

### Top-level convenience（"轻松使用"的核心）

```python
def login(
    base_url: str,
    *,
    username: str | None = None,
    password: str | None = None,
    refresh_token: str | None = None,
    client_id: str | None = None,
    client_secret: str | None = None,
    new_password: str | None = None,
    no_auth: bool = False,
    tls_insecure: bool = False,
    open_browser: bool = True,
) -> TokenConfig:
    """One-call login. Strategy is picked from the arguments.

    | Provided                                       | Strategy                                |
    |------------------------------------------------|-----------------------------------------|
    | no_auth=True                                   | save_no_auth_platform (no network call) |
    | username + password                            | http_signin (no browser, no Playwright) |
    | refresh_token + client_id + client_secret      | refresh-token grant (no browser)        |
    | (none of the above) + open_browser=True        | OAuth2BrowserAuth.login()               |
    | (none of the above) + open_browser=False       | OAuth2BrowserAuth.login(no_browser=True)|

    For all strategies except no_auth=True: if the platform's `/oauth2/auth`
    or `/oauth2/signin` returns 404 (the platform has no OAuth installed),
    falls back to no-auth automatically and emits a one-line `RuntimeWarning`.

    Returns the saved TokenConfig and sets the platform as active.
    Raises ValueError if argument combination is ambiguous (e.g. no_auth=True
    combined with username/refresh_token).
    """
```

### `kweaver.auth` 公共面

```python
from kweaver.auth import (
    # auth providers (use as kweaver.KWeaver(auth=...))
    HttpSigninAuth,

    # one-shot functions
    http_signin,                # 最完整的 HTTP signin（细粒度参数）
    save_no_auth_platform,      # 显式把 base_url 标记成 no-auth 模式
    is_no_auth,                 # token == "__NO_AUTH__"
    NO_AUTH_TOKEN,              # 常量 "__NO_AUTH__"
    eacp_modify_password,
    fetch_eacp_user_info,

    # store helpers (operate on ~/.kweaver/)
    whoami,                     # 解 id_token + EACP userinfo
    list_platforms,
    list_users,
    get_active_user,
    set_active_user,
    export_credentials,         # 返回 dict, 不打印 copy command

    # constants & helpers (high-fidelity TS parity)
    STUDIOWEB_LOGIN_PUBLIC_KEY_PEM,
    DEFAULT_SIGNIN_RSA_MODULUS_HEX,
    rsa_modulus_hex_to_spki_pem,
    parse_signin_page_html_props,
    build_oauth2_signin_post_body,

    # exceptions
    InitialPasswordChangeRequiredError,
)
```

### `http_signin` 完整签名

```python
def http_signin(
    base_url: str,
    username: str,
    password: str,
    *,
    client_id: str | None = None,
    client_secret: str | None = None,
    new_password: str | None = None,
    signin_public_key_pem: str | None = None,   # 优先级见下
    signin_password_base64_plain: bool = False,  # debug 用，默认 RSA
    tls_insecure: bool = False,
    lang: str = "zh-cn",
    redirect_port: int = 9010,
) -> TokenConfig: ...
```

公钥优先级（与 TS 完全一致）：

1. 函数参数 `signin_public_key_pem`
2. 环境变量 `KWEAVER_SIGNIN_RSA_PUBLIC_KEY`（文件路径）
3. signin 页 `__NEXT_DATA__.publicKey` / `modulus`
4. `STUDIOWEB_LOGIN_PUBLIC_KEY_PEM` 常量

### No-auth handling（与 TS 完全一致）

```python
def save_no_auth_platform(
    base_url: str, *, tls_insecure: bool = False
) -> TokenConfig:
    """Mark a platform as no-auth (no OAuth, no token).

    Writes a TokenConfig with accessToken == NO_AUTH_TOKEN ("__NO_AUTH__") to
    ~/.kweaver/<platform>/token.json and sets the platform as active.
    No network call is made. Used by:
      - kweaver.login(..., no_auth=True) — explicit
      - http_signin / OAuth2BrowserAuth.login on /oauth2/auth 404 — auto-fallback
    """
```

`HttpSigninAuth.auth_headers()` 与 `OAuth2BrowserAuth.auth_headers()` 在检测到
`is_no_auth(token)` 时直接返回 `{}`（与 `ConfigAuth.auth_headers()` 现有行为一致）。

`OAuth2BrowserAuth.login(...)` 与 `http_signin(...)` 在以下情况触发自动 fallback
（与 TS `oauth2Login` / `oauth2PasswordSigninLogin` 完全一致）：

- `GET /oauth2/auth` 返回 **404**（平台未装 OAuth）
- `GET /api/dip-hub/v1/login` → redirect 链上任意一跳 **404**
- `_resolve_or_register_client` 的 `POST /oauth2/clients` 返回 **404**

触发后行为：

1. 不抛异常，调用 `save_no_auth_platform(base_url, tls_insecure=...)`
2. 用 Python `warnings.warn(..., RuntimeWarning)` 发一条
   `"OAuth2 endpoint not found (404). Saving platform in no-auth mode."`
   （等价于 TS 的 `console.error` 一行）
3. 返回 no-auth TokenConfig

明确**不**触发 fallback 的情况：

- 401 / 403 / 5xx — 视为真实错误，原样抛
- TLS / DNS / 连接超时 — 原样抛 `httpx` 异常

## Data Flow — `http_signin`

```
http_signin(base_url, username, password, ...)
 │
 ├─ 1. resolve_or_register_client(base_url)
 │      └─ 复用 OAuth2BrowserAuth._resolve_or_register_client
 │
 ├─ 2. GET  base_url/api/dip-hub/v1/login        (follow redirects)
 │      └─ cookie jar 累积 csrf / __Host-ory_*   终点 /oauth2/signin?login_challenge=
 │
 ├─ 3. parse_signin_page_html_props(html)
 │      → {csrf, login_challenge, remember, publicKey?, modulus?}
 │
 ├─ 4. body = build_oauth2_signin_post_body(...)
 │      └─ password 用 RSA PKCS#1 v1.5 加密（cryptography 库）
 │
 ├─ 5. POST base_url/oauth2/signin               (with cookie jar)
 │      ├─ 401 + code=401001017
 │      │   ├─ if new_password is None  → raise InitialPasswordChangeRequiredError
 │      │   └─ else → eacp_modify_password(...) → 重试一次（_retry_count≤1）
 │      └─ 302 → follow redirect 到 /oauth2/auth?code=...
 │
 ├─ 6. exchange_code(code, client_id, client_secret, redirect_uri)
 │      └─ 复用 OAuth2BrowserAuth._exchange_code
 │
 └─ 7. PlatformStore.save_token + set_current_platform
        return TokenConfig
```

## Error Handling

| 场景 | 行为 |
|---|---|
| RSA 加密失败 / 公钥解析失败 | `RuntimeError("Failed to encrypt password with provided public key: ...")`, `__cause__` 保留 |
| `__NEXT_DATA__` 缺 csrf | `RuntimeError("Sign-in page did not expose CSRF token")` |
| GET signin 页 4xx/5xx | `RuntimeError(f"Failed to load OAuth2 sign-in page: {status} {body[:200]}")` |
| POST signin 401 + 401001017 + 无 `new_password` | `InitialPasswordChangeRequiredError(account, base_url, server_message)` |
| 401001017 + `new_password` 改密成功 | 自动重试 `http_signin` **一次**（防递归：内部 `_retry_count` 限 1） |
| 401001017 + 改密失败 | 抛改密的原始异常，`__cause__` 指向初始 401 |
| POST signin 其他 4xx/5xx | `RuntimeError(f"OAuth2 sign-in failed: {status} {body[:500]}")` |
| TLS 验证失败 + `tls_insecure=False` | 原始 `httpx.SSLError` 不吞 |
| 缺必需参数（如 `username` 空字符串） | `ValueError("username must be a non-empty string")` |
| `/oauth2/auth` 或 signin 链上 **404** | 不抛错，`save_no_auth_platform`+`warnings.warn(RuntimeWarning)`，返回 no-auth TokenConfig |
| `kweaver.login(no_auth=True, username="x")` | `ValueError("no_auth=True is mutually exclusive with username/password/refresh_token")` |
| `refresh_access_token(token)` 但 `is_no_auth(token)` | `RuntimeError(f"Cannot refresh no-auth session for {base_url}.")`（与 TS 一致） |
| `with_401_refresh_retry` / `with_token_retry` 见到 no-auth token | 跳过 refresh 直接执行原请求一次（与 TS 一致） |

`InitialPasswordChangeRequiredError` 字段：

```python
class InitialPasswordChangeRequiredError(RuntimeError):
    code: int = 401001017
    account: str
    base_url: str
    http_status: int = 401
    server_message: str
```

## Testing Strategy

### 单元测试（offline，pytest-respx mock httpx）

`packages/python/tests/unit/auth/`:

| 文件 | 覆盖 |
|---|---|
| `test_signin_html.py` | 拷贝 TS `oauth-signin-html.test.ts` 的 HTML fixtures → 期望 props（csrf / login_challenge / publicKey）。**必须**用相同 fixture 验证 TS↔Python 等价。 |
| `test_signin_crypto.py` | 用一对已知 RSA key（fixture）→ `_crypto.encrypt_pkcs1_v15` → 私钥解密 == 原文。验证 `rsa_modulus_hex_to_spki_pem` 等价于 TS 实现（hex modulus 一致 → SPKI DER 一致）。 |
| `test_http_signin.py` | mock 完整 GET→POST→callback 序列：happy path / 401001017 抛错 / 401001017+new_password 自动重试一次成功 / 改密失败时异常链 / cookie 跨请求透传 / 公钥优先级 4 档 |
| `test_eacp_modify_password.py` | mock POST `/api/eacp/v1/user/modify-password` + RSA 解密 server-side 看到的 body |
| `test_eacp_user_info.py` | mock GET `/api/eacp/v1/user/get` 200/401/网络错误 |
| `test_store_helpers.py` | tmp_path PlatformStore：whoami / list_platforms / list_users / set_active_user / export_credentials |
| `test_login_top_level.py` | `kweaver.login(...)` 各参数组合 → 选对策略；冲突参数抛 `ValueError`；`no_auth=True` happy path；`no_auth=True` + `username` 抛错 |
| `test_http_signin_auth_provider.py` | `HttpSigninAuth.auth_headers()` lazy login、token 过期触发 refresh、no-auth token 返回 `{}` |
| `test_no_auth.py` | `save_no_auth_platform` 写盘 + 设 active；`http_signin` 遇 404 自动 fallback + 发 `RuntimeWarning`；`OAuth2BrowserAuth.login` 遇 404 自动 fallback；`ConfigAuth` / `HttpSigninAuth` / `OAuth2BrowserAuth` 在 no-auth token 下 `auth_headers() == {}`；no-auth token 调 refresh 抛 `RuntimeError` |

### TS↔Python 一致性测试

`tests/unit/auth/test_ts_parity.py`：

- `signin_post_body` 字段顺序、键名、base64 padding 必须 byte-for-byte 等于 TS
  `buildOauth2SigninPostBody` 的输出。落地方式：在 TS 测试里 dump 一份
  fixture JSON 到 `tests/fixtures/signin_post_body_*.json`，Python 测试 load
  并 assert 完全相等。
- `rsa_modulus_hex_to_spki_pem(DEFAULT_SIGNIN_RSA_MODULUS_HEX)` 输出 PEM 必须
  逐字节等于 TS 同名函数输出。

### 回归保护

`tests/unit/test_auth.py` 中：

- 删除 `PasswordAuth` 相关用例。
- `OAuth2BrowserAuth` / `ConfigAuth` / `OAuth2Auth` / `TokenAuth` / `NoAuth` 用例
  全部保留，外加给 `OAuth2BrowserAuth.login_with_refresh_token` 写 happy path
  + 已存在 client 时不重复注册 + 网络错误。

## Migration & Breaking Changes

| 变更 | 影响 |
|---|---|
| 删除 `kweaver._auth.PasswordAuth` | ⚠️ 0.x 破坏性变更，0.7.0 release notes 明确写 |
| 删除 `kweaver.cli` 包（`config.py`、`dataview.py`） | 零影响（从未在 `pyproject` `[project.scripts]` 注册，跑不起来） |
| 移除 `[dependency-groups].dev` 的 `playwright>=1.58.0` | 开发者 `pip install -e '.[dev]'` 无需再装 chromium |
| 版本 `0.6.8 → 0.7.0` | 因为有破坏性删除，bump minor |
| `from kweaver._auth import ConfigAuth` 仍工作 | ✅ 完全兼容 |
| 新增 `from kweaver.auth import ...` | ✅ 新公共 API，不影响旧代码 |

## File Touch List

**Create (19):**

- `packages/python/src/kweaver/auth/__init__.py`
- `packages/python/src/kweaver/auth/_crypto.py`
- `packages/python/src/kweaver/auth/_signin_html.py`
- `packages/python/src/kweaver/auth/_http_signin.py`
- `packages/python/src/kweaver/auth/eacp.py`
- `packages/python/src/kweaver/auth/store_helpers.py`
- `packages/python/tests/unit/auth/__init__.py`
- `packages/python/tests/unit/auth/test_signin_html.py`
- `packages/python/tests/unit/auth/test_signin_crypto.py`
- `packages/python/tests/unit/auth/test_http_signin.py`
- `packages/python/tests/unit/auth/test_eacp_modify_password.py`
- `packages/python/tests/unit/auth/test_eacp_user_info.py`
- `packages/python/tests/unit/auth/test_store_helpers.py`
- `packages/python/tests/unit/auth/test_login_top_level.py`
- `packages/python/tests/unit/auth/test_http_signin_auth_provider.py`
- `packages/python/tests/unit/auth/test_no_auth.py`
- `packages/python/tests/unit/auth/test_ts_parity.py`
- `packages/python/tests/fixtures/signin_post_body_basic.json`（由 TS 测试生成）
- `packages/python/tests/fixtures/signin_page_basic.html`（拷贝自 TS 测试）

**Modify:**

- `packages/python/src/kweaver/_auth.py`
  — 删 `PasswordAuth`；加 `HttpSigninAuth` 薄封装；加
  `OAuth2BrowserAuth.login_with_refresh_token`
- `packages/python/src/kweaver/__init__.py`
  — re-export `kweaver.auth` 的核心名字；新增 `login(...)`
- `packages/python/pyproject.toml`
  — 删 `[dependency-groups].dev` 的 `playwright>=1.58.0`；version `0.6.8 → 0.7.0`
- `packages/python/tests/unit/test_auth.py`
  — 删 `PasswordAuth` 用例；加 `OAuth2BrowserAuth.login_with_refresh_token` 用例
- `README.md` / `README.zh.md`
  — 新增 "Pure Python auth (no Node, no browser)" 段落
- `packages/python/README.md`（如存在）
  — 同上

**Delete:**

- `packages/python/src/kweaver/cli/` 整个目录

## Open Questions（已解决，留档）

- ✅ Q1 范围：选 C（全面对齐）
- ✅ Q2 CLI：取消 Python CLI
- ✅ Q3 PasswordAuth：删除（A）
- ✅ Q4 HTTP signin 深度：1:1 等价（A）
- ✅ Q5 SDK ↔ CLI 行为差：SDK 不交互、不打印、纯函数返回/抛错
- ✅ Q6 No-auth：保留显式 `no_auth=True` 入口 + 404 自动 fallback（与 TS 一致）

## Acceptance Criteria

1. 在没有 Node、没有 Chromium 的容器里，下面这段代码可以走通：
   ```python
   import kweaver
   kweaver.login("https://dip-poc.aishu.cn", username="alice", password="x")
   client = kweaver.KWeaver()
   client.knowledge_networks.list()
   ```
2. `pip install kweaver-sdk[dev]` 不再触发 chromium 下载。
3. `pytest packages/python` 全绿，覆盖率 ≥ 65%（pyproject `fail_under`）。
4. `tests/unit/auth/test_ts_parity.py` 所有 fixture 与 TS 输出 byte-equal。
5. 在已存在的 401001017 部署上，`http_signin(..., new_password="newpwd")` 自动改密
   并重试成功。
6. 在没有 OAuth 的部署上：
   - `kweaver.login(url, no_auth=True)` 一行写入 no-auth platform，无网络请求；
   - `kweaver.login(url, username="x", password="y")` 在 `/oauth2/auth` 返回 404
     时自动 fallback 到 no-auth，发一条 `RuntimeWarning`，不抛错；
   - 后续 `KWeaver(auth=ConfigAuth())` 调 API 时 `Authorization` header 不出现。
