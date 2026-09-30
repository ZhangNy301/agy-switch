# Changelog

## 1.0.0

Initial public release.

- Interactive account picker (`agy-switch` / `asw`) with live quota display:
  Gemini and Claude 5-hour / weekly limits, subscription tier, last-active time
- `login` / `use` / `rename` / `logout` account management (profiles are
  snapshots of agy's OAuth token; switching restores a snapshot)
- Auto-correction when a still-running agy overwrites the live token of
  another account
- `proxy` manager: multiple proxies, interactive TUI (add / edit / rename /
  delete / toggle / re-probe), auto protocol detection (https / socks5h /
  http, raced against agy's real endpoint), exit-region and IP-type probe
  (hosting / residential / mobile), expiry with optional direct fallback
- Network self-check: warns when Google APIs are unreachable or the current
  IP region is unsupported by Google AI
- `agy` shim that injects the active proxy into every agy run
