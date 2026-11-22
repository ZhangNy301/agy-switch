"""Linux / macOS smoke test: CLI basics + drive the TUI through a real pty.
Runs against a throwaway HOME — never touches a real agy login."""
import base64, json, os, pty, select, subprocess, sys, tempfile, time

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bin", "agy-switch")
home = tempfile.mkdtemp()
os.makedirs(f"{home}/.local/share/agy-switch/profiles", exist_ok=True)
os.makedirs(f"{home}/.gemini/antigravity-cli", exist_ok=True)
# SSH_CONNECTION: keep macOS runners on the token file, away from the login keychain
env = dict(os.environ, HOME=home, SSH_CONNECTION="1", AGY_SWITCH_GEO_URL="http://127.0.0.1:9/")


def jwt(email):
    b = lambda d: base64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip("=")
    return f"{b({'alg': 'none'})}.{b({'email': email})}.sig"


for name in ("alice", "bob"):
    t = {"token": {"access_token": "x", "refresh_token": "rt-" + name,
                   "expiry": "2099-01-01T00:00:00Z"}, "id_token": jwt(name + "@ex.com")}
    json.dump(t, open(f"{home}/.local/share/agy-switch/profiles/{name}.json", "w"))
json.dump(json.load(open(f"{home}/.local/share/agy-switch/profiles/alice.json")),
          open(f"{home}/.gemini/antigravity-cli/antigravity-oauth-token", "w"))


def run(*a):
    r = subprocess.run([sys.executable, SCRIPT, *a], env=env, capture_output=True, text=True, timeout=60)
    return r.returncode, r.stdout + r.stderr


ok = True
def check(name, cond):
    global ok
    print(("PASS " if cond else "FAIL ") + name)
    ok &= bool(cond)


check("--version", run("--version")[1].startswith("agy-switch"))
check("ls lists both", all(n in run("ls")[1] for n in ("alice", "bob")))
check("use bob", run("use", "bob")[0] == 0)
live = json.load(open(f"{home}/.gemini/antigravity-cli/antigravity-oauth-token"))
check("live token is bob", live["token"]["refresh_token"] == "rt-bob")

# TUI through a pty: down-arrow (wraps to alice), then Enter -> switches to alice
env2 = dict(env, PATH="/usr/bin:/bin")  # no agy on PATH -> prints message instead of exec
pid, fd = pty.fork()
if pid == 0:
    os.execve(sys.executable, [sys.executable, SCRIPT], env2)
out = b""
def drain(t):
    global out
    end = time.time() + t
    while time.time() < end:
        r, _, _ = select.select([fd], [], [], 0.1)
        if r:
            try:
                out += os.read(fd, 65536)
            except OSError:
                return
drain(3)
os.write(fd, b"\x1b[B")
drain(0.5)
os.write(fd, b"\r")
drain(3)
os.waitpid(pid, 0)
text = out.decode(errors="replace")
check("TUI rendered", "agy-switch" in text and "bob" in text)
check("TUI switched to alice", "switched to 'alice'" in text)
live = json.load(open(f"{home}/.gemini/antigravity-cli/antigravity-oauth-token"))
check("live token is alice", live["token"]["refresh_token"] == "rt-alice")
sys.exit(0 if ok else 1)
