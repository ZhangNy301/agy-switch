# agy-switch

**Multi-account manager for [Antigravity CLI](https://github.com/google/antigravity) (`agy`)** — switch Google accounts in one keystroke, see every account's Gemini / Claude quota at a glance, and route `agy` through managed proxies when your network or region gets in the way.

[中文文档](README.zh-CN.md)

[![npm](https://img.shields.io/npm/v/agy-switch)](https://www.npmjs.com/package/agy-switch)
[![license](https://img.shields.io/npm/l/agy-switch)](LICENSE)

[![demo](https://github.com/ZhangNy301/agy-switch/releases/download/demo-assets/agy-switch-demo.gif)](https://github.com/ZhangNy301/agy-switch/releases/download/demo-assets/agy-switch-demo.mp4)

## Why

`agy` keeps exactly one OAuth token on disk, so juggling multiple Google accounts means logging out and back in every time. **agy-switch** snapshots that token per account:

- `asw` opens an interactive picker: ↑/↓ to choose, Enter to switch **and jump straight into `agy`**
- Each account shows its email, subscription tier (Free / Pro / Ultra), Gemini and Claude 5-hour + weekly quota, and last-active time — refreshed live
- Built-in **proxy manager**: multiple proxies with auto protocol detection (`https` / `socks5h` / `http`), exit-region + IP-type probe (hosting / residential / mobile), expiry dates, one-key toggle. Every `agy` run then uses the active proxy automatically
- Warns you up front when Google APIs are unreachable or your IP region is unsupported by Google AI — no more mysterious `region not supported` errors

## Requirements

- Linux, macOS or Windows 10+
- Python 3.7+ (preinstalled on most Linux/macOS systems; on Windows: `winget install Python.Python.3.12`)
- `curl` (used for proxy probing and protocol detection; ships with Windows 10+)
- [Antigravity CLI](https://github.com/google/antigravity) itself

## Install

**npm (recommended):**

```bash
npm install -g agy-switch
```

**curl (no Node.js needed):**

```bash
curl -fsSL https://raw.githubusercontent.com/ZhangNy301/agy-switch/main/install.sh | bash
```

**Windows (PowerShell, no Node.js needed):**

```powershell
irm https://raw.githubusercontent.com/elhassu/agy-switch/main/install.ps1 | iex
```

All of these give you two commands: `agy-switch` and its short alias `asw`. On Linux/macOS make sure `~/.local/bin` is on your `PATH` (the installer tells you if it isn't); the Windows installer puts `%LOCALAPPDATA%\agy-switch\bin` on your user `PATH` itself.

## Quick start

```bash
agy-switch login     # add your first account (browser login via agy)
agy-switch login     # ...and another one
asw                  # pick an account → Enter → you're in agy
```

In the picker: `↑`/`↓` move, `Enter` switch & launch agy, `r` refresh quotas, `q` quit.

## Commands

| Command | What it does |
| --- | --- |
| `agy-switch` / `asw` | Interactive account picker (switch + launch agy) |
| `agy-switch ls` | Plain, non-interactive account list (cached quota) |
| `agy-switch login` | Add another account without losing existing ones |
| `agy-switch use <name>` | Switch non-interactively |
| `agy-switch rename <old> <new>` | Rename a profile |
| `agy-switch logout [name] [--revoke]` | Remove an account from this machine (`--revoke` also kills the OAuth grant) |
| `agy-switch proxy` | Interactive proxy manager |
| `agy-switch proxy status` | Plain proxy + network status |
| `agy-switch proxy on [name]` / `off` | Enable / disable a proxy non-interactively |
| `agy-switch bridge [status\|stop]` | Inspect / stop the local bridge used for SOCKS proxies (started automatically) |
| `agy-switch --version` | Print version |

### Proxy manager keys

`↑`/`↓` select · `Enter` enable & quit · `space` toggle on/off · `a` add · `e` edit fields · `R` rename · `d` delete · `r` re-probe · `q` quit

Add flow asks only for `server`, `port`, `username?`, `password?` — the protocol is auto-detected by racing `https` / `socks5h` / `http` against agy's real API endpoint, so a proxy that is silently blocked in one protocol still lands on a working one.

## How it works

- A **profile** is a snapshot of agy's OAuth credential. Switching writes the snapshot back. Tokens never appear on the command line or in output. Every credential location agy uses is supported: the macOS login keychain on GUI desktops (go-keyring item, service `gemini` / account `antigravity`), `~/.gemini/antigravity-cli/antigravity-oauth-token` (Linux, and macOS over SSH), and the legacy gemini-cli-style `~/.gemini/oauth_creds.json`. First run on a machine where agy is already logged in adopts that login as the first profile automatically.
- Data lives in `~/.local/share/agy-switch/` (profiles, quota cache, proxy configs).
- When a proxy is enabled, agy-switch installs a tiny shim at `~/.local/bin/agy` that exports the proxy environment and then execs the real `agy`. Your shell's own `http_proxy`/`https_proxy` still wins if you exported them.
- **SOCKS proxies go through a local bridge.** Everything agy runs (its shell commands, `gh`, `git`, `npm`, …) inherits the proxy variables, and many tools can't use a `socks5h://` URL from them — `gh` and other binaries built with Go ≤ 1.22 fail with `error connecting to socks5h`, npm and Node don't speak SOCKS at all. So for a SOCKS proxy the shim exports `http://agy-switch:<token>@127.0.0.1:<port>` instead: a small HTTP proxy, started on demand, that forwards every request through your SOCKS proxy with remote DNS (like `socks5h`). It listens on localhost only, requires a random per-install token (other users on a shared host can't use your proxy), keeps the same port across restarts, picks up proxy edits without restarting agy, and exits once idle with no agy running. Your SOCKS credentials never appear in child processes' environment. `agy-switch bridge status` / `stop` inspect it; its log is `~/.local/share/agy-switch/bridge.log`.
- Quotas are read from agy's local state and refreshed in the background; cached values are shown when refresh fails.

### Windows

- agy keeps its login in the **Windows Credential Manager** (generic credential `gemini:antigravity`); agy-switch reads and writes that item directly. Like agy itself, it stores `id_token_email` there instead of the full `id_token`, which keeps the item under Credential Manager's 2560-byte limit.
- Data lives in `%USERPROFILE%\.local\share\agy-switch\`.
- Proxy shim: `agy.exe` is renamed to `agy.real.exe`, and an `agy.cmd` beside it does what the bash shim does on Linux/macOS (proxy env, expiry, network check, account re-assert, SOCKS bridge). When an agy update puts a fresh `agy.exe` back, the next `agy-switch` run moves it behind the shim again.
- Use Windows Terminal, PowerShell or `cmd`. Git Bash's mintty isn't a real console, so the interactive picker won't start there — use `agy-switch ls` / `agy-switch use <name>` instead.

## Uninstall

```bash
agy-switch proxy off            # stop injecting the proxy
npm uninstall -g agy-switch     # or: rm ~/.local/bin/agy-switch ~/.local/bin/asw
rm -rf ~/.local/share/agy-switch
# if ~/.local/bin/agy is the agy-switch shim, remove it too (it says so in its header)
```

On Windows (PowerShell):

```powershell
agy-switch proxy off
$bin = "$env:LOCALAPPDATA\agy\bin"   # wherever agy.exe lives
if (Test-Path "$bin\agy.real.exe") { Remove-Item "$bin\agy.cmd"; Rename-Item "$bin\agy.real.exe" agy.exe }
npm uninstall -g agy-switch          # or: Remove-Item -Recurse "$env:LOCALAPPDATA\agy-switch"
Remove-Item -Recurse "$env:USERPROFILE\.local\share\agy-switch"
```

## Contributing

Issues and pull requests are welcome. The whole CLI is a single dependency-free Python file (`bin/agy-switch`) — read it, hack it, send a PR.

## License

[MIT](LICENSE)
