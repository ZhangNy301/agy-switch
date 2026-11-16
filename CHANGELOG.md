# Changelog

## 1.0.6

- Fix tools run inside agy breaking behind a SOCKS proxy. The shim exported
  the `socks5h://` URL into all six proxy variables, which every process agy
  starts inherits — but `gh` (and any binary built with Go ≤ 1.22) parses
  `socks5h` as a hostname and fails with "error connecting to socks5h" (so
  `gh auth status` even reports the token as invalid), and npm / Node's fetch
  can't use SOCKS at all. For SOCKS proxies the shim now exports a local
  `http://` bridge instead: a small on-demand HTTP proxy on 127.0.0.1 that
  forwards CONNECT and plain-http requests through the SOCKS upstream with
  remote DNS. It requires a random per-install token (no free ride for other
  users of a shared host), keeps its port across restarts so running sessions
  survive, reloads proxy edits live and exits when idle with no agy running.
  SOCKS credentials no longer leak into child environments. If the bridge
  can't start, the shim warns and falls back to the raw SOCKS URL
- New `agy-switch bridge [status|stop]`; `proxy status` shows the bridge
- The shim's network-probe cache tag uses the configured upstream, so it
  stays shared with `agy-switch` itself when the bridge is in use
- A bridge URL in the environment (inside an agy session) is no longer
  "detected" as the user's own proxy by the add-proxy wizard

## 1.0.5

- Fix quota entries silently lost during TUI refresh: each profile refreshed
  on its own thread and every writer did an unsynchronized whole-file
  read-modify-write of meta.json, so the last saver dropped the other
  threads' fresh entries. All meta.json writes now go through a serialized
  update_meta() that re-loads inside the lock and merges into the newest copy
- Retry a transient retrieveUserQuotaSummary failure once (~1s later) instead
  of leaving the quota display blank for a whole TTL cycle; the tier call is
  not retried and partial results are still never cached

## 1.0.4

- macOS: support agy's Keychain credential storage. On GUI desktops agy keeps
  its OAuth token only in the login keychain (generic-password item, service
  "gemini" / account "antigravity", go-keyring base64 envelope) and never
  writes a token file — which made `login` report "no token was written" and
  `ls` show "no accounts yet". agy-switch now reads, watches, writes and
  deletes that item, so login, the picker, switch and logout all work on
  macOS. SSH sessions keep agy's file-based behavior; a keychain that refuses
  access degrades to the token file with a warning instead of a traceback
- Fix a race where the proxy shim re-asserted the previous account on every
  agy start — including the agy launched by `agy-switch login` after it had
  deliberately removed the live credential, resurrecting the old login before
  agy could show the browser flow

## 1.0.3

- Fix account misidentification when adopting a live login whose id_token is
  stale: agy rotates access/refresh tokens on refresh but never rewrites
  id_token, so the cached id_token can name a PREVIOUS account that once
  logged in on the same machine. Adoption now refreshes the token first and
  names the profile from the fresh identity in the refresh response
- The picker re-decodes the displayed email after a quota refresh, so a
  mis-cached identity corrects itself once the token is refreshed

## 1.0.2

- macOS support: agy falls back to the legacy gemini-cli credential
  (`~/.gemini/oauth_creds.json`, flat format) when its own token file is
  absent — agy-switch now reads/writes both paths, converting formats as
  needed. Fixes "login not completed" and the phantom already-logged-in
  account on such installs
- First run on a machine where agy is already logged in adopts that login as
  the first profile instead of showing "no accounts yet"
- Network self-check now honors the user's own env proxy (`HTTPS_PROXY` etc.)
  instead of probing direct and crying "unreachable"; path tagging
  distinguishes agy-switch proxy / env proxy / direct (shim included)

## 1.0.1

- Fix crash on macOS when pressing Ctrl-C inside the proxy add/edit prompts:
  the npm launcher exited on SIGINT before the Python process, the shell
  reclaimed the terminal, and the next tty read failed with EIO — leaving the
  screen stuck in the alt buffer. The launcher now forwards signals and
  outlives the child; tty reads/restores are EIO-safe
- Ctrl-C (`^C`) now quits the proxy manager and field editor
- `login` checks the network first and warns (with a proxy hint) when Google
  APIs are unreachable or the IP region is unsupported, instead of letting
  the browser callback hang silently

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
