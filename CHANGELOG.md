# Changelog

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
