"""Windows smoke test: Credential Manager store, switching, the agy.cmd shim,
the SOCKS bridge and console key mapping. Runs against a throwaway profile
dir and a separate credential target — never touches a real agy login."""
import base64, json, os, shutil, socket, subprocess, sys, tempfile, threading
import importlib.machinery, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "bin", "agy-switch")
SANDBOX = tempfile.mkdtemp()
AGYBIN = os.path.join(SANDBOX, "agybin")
os.makedirs(AGYBIN)
# a stand-in agy.exe: cmd.exe, so `agy /c set HTTP` shows the injected env
shutil.copy(os.path.join(os.environ["WINDIR"], "System32", "cmd.exe"),
            os.path.join(AGYBIN, "agy.exe"))
os.environ.update(USERPROFILE=os.path.join(SANDBOX, "home"),
                  LOCALAPPDATA=os.path.join(SANDBOX, "local"),
                  AGY_SWITCH_KEYRING_SERVICE="agyswitch-test",
                  AGY_SWITCH_GEO_URL="http://127.0.0.1:9/",
                  PATH=AGYBIN + os.pathsep + os.environ["PATH"])
for v in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY"):
    os.environ.pop(v, None)

loader = importlib.machinery.SourceFileLoader("asw", SCRIPT)
m = importlib.util.module_from_spec(importlib.util.spec_from_loader("asw", loader))
loader.exec_module(m)
assert m._wincred_target() == "agyswitch-test:antigravity"

failed = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        failed.append(name)


def jwt(email):
    b = lambda d: base64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip("=")
    return f"{b({'alg': 'none'})}.{b({'email': email})}.sig"


def tok(email, rt, with_id=True):
    t = {"token": {"access_token": "at-" + rt, "token_type": "Bearer", "refresh_token": rt,
                   "expiry": "2099-01-01T00:00:00Z"}, "auth_method": "oauth"}
    if with_id:
        t["id_token"] = jwt(email) + "x" * 1800  # realistic size: over wincred's 2560 cap
    else:
        t["id_token_email"] = email
    return t


def asw(*args):
    r = subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True,
                       timeout=120)
    return r.returncode, r.stdout + r.stderr


def agy(cmdline):
    r = subprocess.run([shutil.which("agy"), "/c", cmdline], capture_output=True, text=True,
                       timeout=120)
    return r.returncode, r.stdout


# --- Credential Manager store + switching ----------------------------------
m.kc_delete()
try:
    check("use_keychain on Windows", m.use_keychain())
    agy_style = tok("a@example.com", "rt-a", with_id=False)
    agy_style["extra_field"] = "keep-me"
    check("raw write (agy's own format)", m._wincred_write(json.dumps(agy_style))[0] == 0)
    loc, live, _style = m.live_cred()
    check("live_cred finds the credential", loc == m.KEYCHAIN_LOC
          and m.refresh_token_of(live) == "rt-a")
    check("email from id_token_email", m.decode_email(live) == "a@example.com")

    os.makedirs(m.PROFILES, exist_ok=True)
    m.write_json_atomic(m.profile_path("b"), tok("b@example.com", "rt-b"))
    m.write_json_atomic(m.profile_path("a"), live)
    m.switch_to("b")
    raw = m.kc_read_raw()
    d = json.loads(raw)
    check("switch wrote b", d["token"]["refresh_token"] == "rt-b")
    check("blob is raw JSON", raw.startswith("{"))
    check("id_token dropped, email set", "id_token" not in d
          and d["id_token_email"] == "b@example.com")
    check("blob within 2560 bytes", len(raw.encode()) <= 2560)
    check("extra field kept", d.get("extra_field") == "keep-me")
    check("_last backup is a", m.refresh_token_of(m.load_json(m.profile_path("_last"))) == "rt-a")

    m._wincred_write(json.dumps(tok("a@example.com", "rt-a", with_id=False)))
    check("clobber detected", m.live_was_clobbered())

    # a refused Credential Manager write stops the switch instead of silently
    # writing a token file that agy on Windows never reads
    before = m.refresh_token_of(m.kc_read_cred()[0])  # "a", from the clobber check above
    real_write = m._wincred_write
    m._wincred_write = lambda secret: (1, "simulated failure")
    try:
        m.switch_to("b")
        check("refused write raises", False)
    except m.CredentialStoreError:
        check("refused write raises", True)
    finally:
        m._wincred_write = real_write
    check("refused write changed nothing", before == "rt-a"
          and m.refresh_token_of(m.kc_read_cred()[0]) == "rt-a"
          and not os.path.isfile(m.LIVE))
    m.switch_to("b")

    # --- agy.exe shim (pip's launcher) -----------------------------------------
    shim_exe = os.path.join(AGYBIN, "agy.exe")
    real_exe = os.path.join(AGYBIN, "agy.real.exe")
    m.save_proxy_db({"version": 2, "active": None, "proxies": {
        "p1": {"protocol": "http", "host": "127.0.0.1", "port": 9}}})
    check("proxy on", asw("proxy", "on", "p1")[0] == 0)
    check("agy.exe moved to agy.real.exe", os.path.isfile(real_exe) and not m.is_shim(real_exe))
    check("agy.exe is now the shim", m.is_shim(shim_exe)
          and shutil.which("agy").lower().endswith("agy.exe"))
    rc, out = agy("set HTTPS_PROXY & set NO_PROXY & exit 7")
    check("shim injects the proxy", "HTTPS_PROXY=http://127.0.0.1:9" in out)
    check("shim sets NO_PROXY", "NO_PROXY=localhost" in out)
    check("shim passes the exit code", rc == 7)
    check("shim re-asserted account b",
          m.refresh_token_of(m.kc_read_cred()[0]) == "rt-b")
    # Node's spawn and Python's subprocess can't start a .cmd without a shell
    r = subprocess.run(["agy", "/c", "exit 3"], capture_output=True, timeout=120)
    check("shim starts without a shell", r.returncode == 3)
    r = subprocess.run(["agy", "/c", "echo", "two words", "&&", "exit", "0"],
                       capture_output=True, text=True, timeout=120)
    check("shim keeps arguments intact", "two words" in r.stdout)
    asw("proxy", "off")
    check("proxy off: no injection", "127.0.0.1:9" not in agy("set HTTPS_PROXY")[1])
    shutil.copy(os.path.join(os.environ["WINDIR"], "System32", "cmd.exe"), shim_exe)  # `agy update`
    asw("proxy", "status")
    check("repair moves an updated agy.exe behind the shim",
          m.is_shim(shim_exe) and not m.is_shim(real_exe) and os.path.isfile(real_exe))
    check("one agy-switch shim, no stray agy.cmd",
          not os.path.exists(os.path.join(AGYBIN, "agy.cmd")))

    # --- agy.cmd fallback when pip's launcher is missing ------------------------
    db = m.load_proxy_db()
    real_launcher = m._win_launcher
    m._win_launcher = lambda: None
    try:
        cfg = m.install_shim_win(db)
    finally:
        m._win_launcher = real_launcher
    cmd_shim = os.path.join(AGYBIN, "agy.cmd")
    check("fallback writes agy.cmd and removes the exe shim",
          cfg and cfg["shim_path"] == cmd_shim and m.is_shim(cmd_shim) and not os.path.exists(shim_exe))
    with open(cmd_shim, "rb") as f:
        check("agy.cmd is plain ASCII", all(b < 128 for b in f.read()))
    check("fallback shim runs", agy("exit 5")[0] == 5)
    m.install_shim_win(m.load_proxy_db())
    check("upgrading back to the exe shim removes agy.cmd",
          m.is_shim(shim_exe) and not os.path.exists(cmd_shim))
finally:
    m.kc_delete()

# --- paths and scanning ---------------------------------------------------------
accented = os.path.join(SANDBOX, "José")
os.makedirs(accented)
short = m.win_short_path(accented)
if short == accented:
    print("SKIP short path for a non-ASCII folder (8.3 names are disabled on this volume)")
else:
    check("short path for a non-ASCII folder", short.isascii() and os.path.isdir(short))
blob = os.path.join(SANDBOX, "fake-agy.bin")
with open(blob, "wb") as f:
    f.write(b"\x00123456789012-abcdefghijklmnopqrstuvwxyz012345.apps.googleusercontent.com"
            b"GOCSPX-" + b"A" * 28 + b"trailingGoString\x00")
got = m._scan_oauth_strings(blob)
check("secret cut to its fixed length", got["secret"] == ["GOCSPX-" + "A" * 28])


# --- SOCKS bridge ------------------------------------------------------------
def socks_server():
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(16)

    def handle(c):
        c.recv(3)
        c.sendall(b"\x05\x00")
        hdr = c.recv(4)
        if hdr[3] == 3:
            host = c.recv(c.recv(1)[0]).decode()
        else:
            host = socket.inet_ntoa(c.recv(4))
        port = int.from_bytes(c.recv(2), "big")
        up = socket.create_connection((host, port), timeout=10)
        c.sendall(b"\x05\x00\x00\x01" + b"\x00" * 6)
        m._Bridge.pipe(c, up)
        c.close()
        up.close()

    def loop():
        while True:
            c, _ = srv.accept()
            threading.Thread(target=handle, args=(c,), daemon=True).start()
    threading.Thread(target=loop, daemon=True).start()
    return srv.getsockname()[1]


def curl(proxy, url):
    return subprocess.run(["curl", "-s", "-o", os.devnull, "-w", "%{http_code}", "--max-time",
                           "15", "-x", proxy, url], capture_output=True, text=True).stdout


m.save_proxy_db({"version": 2, "active": "s", "proxies": {
    "s": {"protocol": "socks5h", "host": "127.0.0.1", "port": socks_server()}}})
url = m.bridge_ensure()
check("bridge starts", bool(url))
if url:
    check("https via bridge -> socks", curl(url, "https://www.google.com/generate_204") == "204")
    check("http via bridge -> socks", curl(url, "http://www.google.com/generate_204") == "204")
    check("wrong token rejected",
          curl(url.replace("agy-switch:", "agy-switch:x"), "http://example.com/") == "407")
    try:
        m._listen(int(url.rsplit(":", 1)[1])).close()
        check("exclusive bind", False)
    except OSError:
        check("exclusive bind", True)
    check("second ensure reuses the bridge", m.bridge_ensure() == url)
    os.kill(m.bridge_state()["pid"], 15)

# --- console keys --------------------------------------------------------------
import msvcrt
seq = iter(["\xe0", "H", "\x00", "P", "\r", "\x1b", "q", "\x03", "\xe0", "K"])
msvcrt.getwch = lambda: next(seq)
msvcrt.kbhit = lambda: True
t = m.WinTerm()
check("WinTerm key mapping",
      [t.key() for _ in range(7)] == ["up", "down", "enter", "esc", "q", "\x03", ""])

print(f"\n{len(failed)} failed" if failed else "\nall checks passed")
sys.exit(1 if failed else 0)
