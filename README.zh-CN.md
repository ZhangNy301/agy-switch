# agy-switch

**[Antigravity CLI](https://github.com/google/antigravity)（`agy`）的多账号管理器** —— 一键切换 Google 账号，一眼看清每个账号的 Gemini / Claude 额度，并在网络或区域受限时让 `agy` 走托管代理。

[English README](README.md)

[![npm](https://img.shields.io/npm/v/agy-switch)](https://www.npmjs.com/package/agy-switch)
[![license](https://img.shields.io/npm/l/agy-switch)](LICENSE)

[![demo](https://github.com/ZhangNy301/agy-switch/releases/download/demo-assets/agy-switch-demo.gif)](https://github.com/ZhangNy301/agy-switch/releases/download/demo-assets/agy-switch-demo.mp4)

## 为什么需要它

`agy` 在磁盘上只保存一个 OAuth token，想换账号就得退出重新登录。**agy-switch** 把每个账号的 token 存成快照：

- `asw` 打开交互式选择器：↑/↓ 选择，Enter 切换**并直接进入 `agy`**
- 每个账号显示邮箱、订阅等级（Free / Pro / Ultra）、Gemini 和 Claude 的 5 小时 + 每周额度、上次活跃时间——后台实时刷新
- 内置**代理管理器**：支持多个代理，协议自动探测（`https` / `socks5h` / `http` 竞速），探测出口区域和 IP 类型（机房 / 住宅 / 移动），支持有效期，一键开关。启用后每次运行 `agy` 自动走该代理
- 当 Google API 不可达、或当前 IP 区域不被 Google AI 支持时提前警告——不再对着 `region not supported` 一头雾水

## 环境要求

- Linux 或 macOS
- Python 3.7+（大多数系统自带）
- `curl`（用于代理探测和协议识别）
- [Antigravity CLI](https://github.com/google/antigravity) 本体

## 安装

**npm（推荐）：**

```bash
npm install -g agy-switch
```

**curl（不需要 Node.js）：**

```bash
curl -fsSL https://raw.githubusercontent.com/ZhangNy301/agy-switch/main/install.sh | bash
```

两种方式都会提供 `agy-switch` 和它的缩写别名 `asw`。请确保 `~/.local/bin` 在你的 `PATH` 里（如果不在，安装器会提示你）。

## 快速上手

```bash
agy-switch login     # 添加第一个账号（走 agy 的浏览器登录）
agy-switch login     # ……再加一个，已有账号不受影响
asw                  # 选账号 → Enter → 直接进入 agy
```

选择器按键：`↑`/`↓` 移动，`Enter` 切换并启动 agy，`r` 刷新额度，`q` 退出。

## 命令一览

| 命令 | 作用 |
| --- | --- |
| `agy-switch` / `asw` | 交互式账号选择器（切换并启动 agy） |
| `agy-switch ls` | 纯文本账号列表（显示缓存额度） |
| `agy-switch login` | 新增账号，不影响已有账号 |
| `agy-switch use <名字>` | 非交互切换 |
| `agy-switch rename <旧> <新>` | 重命名账号 |
| `agy-switch logout [名字] [--revoke]` | 从本机移除账号（`--revoke` 同时吊销 OAuth 授权） |
| `agy-switch proxy` | 交互式代理管理器 |
| `agy-switch proxy status` | 纯文本代理 + 网络状态 |
| `agy-switch proxy on [名字]` / `off` | 非交互启用 / 关闭代理 |
| `agy-switch --version` | 打印版本号 |

### 代理管理器按键

`↑`/`↓` 选择 · `Enter` 启用并退出 · `空格` 开/关 · `a` 添加 · `e` 编辑字段 · `R` 重命名 · `d` 删除 · `r` 重新探测 · `q` 退出

添加代理只需填 `服务器`、`端口`、`用户名?`、`密码?`——协议会自动探测（用 agy 的真实 API 端点竞速 `https` / `socks5h` / `http`），某个协议被网络悄悄拦截时会自动落到能用的那个。

## 工作原理

- **配置（profile）**就是 agy OAuth 凭证的快照，切换即把快照写回。token 从不出现在命令行或输出里。agy 用到的所有凭证位置都支持：macOS 图形桌面下的系统钥匙串（go-keyring 条目，service `gemini` / account `antigravity`）、`~/.gemini/antigravity-cli/antigravity-oauth-token`（Linux，以及 SSH 会话下的 macOS）、旧版 gemini-cli 风格的 `~/.gemini/oauth_creds.json`。在 agy 已登录的机器上首次运行会自动把当前登录收养为第一个账号。
- 数据存放在 `~/.local/share/agy-switch/`（账号快照、额度缓存、代理配置）。
- 启用代理后，agy-switch 会在 `~/.local/bin/agy` 安装一个小 shim：先注入代理环境变量，再 exec 真正的 `agy`。如果你自己在 shell 里 export 了 `http_proxy`/`https_proxy`，你的设置优先。
- 额度读取自 agy 的本地状态并后台刷新；刷新失败时显示缓存值。

## 卸载

```bash
agy-switch proxy off            # 停止注入代理
npm uninstall -g agy-switch     # 或：rm ~/.local/bin/agy-switch ~/.local/bin/asw
rm -rf ~/.local/share/agy-switch
# 如果 ~/.local/bin/agy 是 agy-switch 的 shim（文件头有注明），一并删除
```

## 参与贡献

欢迎 Issue 和 Pull Request。整个 CLI 就是一个零依赖的 Python 单文件（`bin/agy-switch`）——读懂它，改它，发 PR。

## 许可证

[MIT](LICENSE)
