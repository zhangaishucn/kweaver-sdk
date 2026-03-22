# 认证命令参考

平台认证管理。凭据存储在 `~/.kweaver/`。

## 前提

```bash
npm install playwright && npx playwright install chromium
```

## 命令

```bash
kweaver auth login <url> [--alias <name>]      # 输入账号密码登录
kweaver auth <url> [--alias <name>]             # 同上（简写）
kweaver auth logout [<platform>]                 # 登出（清除本地 token）
kweaver auth status                              # 查看 token 状态
kweaver auth list                                # 列出已保存的平台
kweaver auth use <platform>                      # 切换平台（URL 或 alias）
kweaver auth delete <platform> [-y]              # 删除平台凭证
```

## 说明

- `login` 支持两种方式：
  - **OAuth2 授权码登录**（默认，平台支持时）：获取 `access_token` + `refresh_token`，**支持自动刷新**，token 过期时 CLI 自动用 refresh_token 换取新 token
  - **Playwright cookie 登录**（回退方式）：通过 headless 浏览器提取 cookie token，**不支持自动刷新**，过期后需重新 `auth login`
- Token 有效期 1 小时
- 支持多平台，用 `--alias` 设置短名称方便切换

## 示例

```bash
kweaver auth login https://kweaver.example.com --alias prod
kweaver auth login https://kweaver-dev.example.com --alias dev
kweaver auth list
kweaver auth use prod
kweaver auth status
```
