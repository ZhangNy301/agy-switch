# agy-switch

**Multi-account manager for [Antigravity CLI](https://github.com/google/antigravity) (`agy`)** — switch Google accounts in one keystroke, see every account's Gemini / Claude quota at a glance, and route `agy` through managed proxies when your network or region gets in the way.

[中文文档](README.zh-CN.md)

[![npm](https://img.shields.io/npm/v/agy-switch)](https://www.npmjs.com/package/agy-switch)
[![license](https://img.shields.io/npm/l/agy-switch)](LICENSE)

<video src="https://github.com/ZhangNy301/agy-switch/releases/download/demo-assets/agy-switch-demo.mp4" controls muted playsinline width="100%"></video>

## Why

`agy` keeps exactly one OAuth token on disk, so juggling multiple Google accounts means logging out and back in every time. **agy-switch** snapshots that token per account:

- `asw` opens an interactive picker: ↑/↓ to choose, Enter to switch **and jump straight into `agy`**
- Each account shows its email, subscription tier (Free / Pro / Ultra), Gemini and Claude 5-hour + weekly quota, and last-active time — refreshed live
- Built-in **proxy manager**: multiple proxies with auto protocol detection (`https` / `socks5h` / `http`), exit-region + IP-type probe (hosting / residential / mobile), expiry dates, one-key toggle. Every `agy` run then uses the active proxy automatically
- Warns you up front when Google APIs are unreachable or your IP region is unsupported by Google AI — no more mysterious `region not supported` errors

## Requirements

- Linux or macOS
- Python 3.7+ (preinstalled on most systems)
- `curl` (used for proxy probing and protocol detection)
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

Both give you two commands: `agy-switch` and its short alias `asw`. Make sure `~/.local/bin` is on your `PATH` (the installer tells you if it isn't).

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
| `agy-switch --version` | Print version |

### Proxy manager keys

`↑`/`↓` select · `Enter` enable & quit · `space` toggle on/off · `a` add · `e` edit fields · `R` rename · `d` delete · `r` re-probe · `q` quit

Add flow asks only for `server`, `port`, `username?`, `password?` — the protocol is auto-detected by racing `https` / `socks5h` / `http` against agy's real API endpoint, so a proxy that is silently blocked in one protocol still lands on a working one.

## How it works

- A **profile** is a snapshot of agy's OAuth credential. Switching writes the snapshot back. Tokens never appear on the command line or in output. Every credential location agy uses is supported: the macOS login keychain on GUI desktops (go-keyring item, service `gemini` / account `antigravity`), `~/.gemini/antigravity-cli/antigravity-oauth-token` (Linux, and macOS over SSH), and the legacy gemini-cli-style `~/.gemini/oauth_creds.json`. First run on a machine where agy is already logged in adopts that login as the first profile automatically.
- Data lives in `~/.local/share/agy-switch/` (profiles, quota cache, proxy configs).
- When a proxy is enabled, agy-switch installs a tiny shim at `~/.local/bin/agy` that exports the proxy environment and then execs the real `agy`. Your shell's own `http_proxy`/`https_proxy` still wins if you exported them.
- Quotas are read from agy's local state and refreshed in the background; cached values are shown when refresh fails.

## Uninstall

```bash
agy-switch proxy off            # stop injecting the proxy
npm uninstall -g agy-switch     # or: rm ~/.local/bin/agy-switch ~/.local/bin/asw
rm -rf ~/.local/share/agy-switch
# if ~/.local/bin/agy is the agy-switch shim, remove it too (it says so in its header)
```

## Contributing

Issues and pull requests are welcome. The whole CLI is a single dependency-free Python file (`bin/agy-switch`) — read it, hack it, send a PR.

## License

[MIT](LICENSE)
