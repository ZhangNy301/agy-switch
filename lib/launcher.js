#!/usr/bin/env node
// npm launcher for agy-switch: the CLI itself is a single-file Python program
// (bin/agy-switch); this wrapper finds a Python 3 interpreter and forwards
// all arguments to it, preserving stdio and the exit code.
"use strict";

const { spawn, spawnSync } = require("child_process");
const path = require("path");
const fs = require("fs");

const SCRIPT = path.join(__dirname, "..", "bin", "agy-switch");
const IS_WIN = process.platform === "win32";

// Windows: the `py` launcher is the most reliable entry point; `python3` is
// often the Microsoft Store stub, which fails the version check below.
const CANDIDATES = IS_WIN
  ? [["py", ["-3"]], ["python", []], ["python3", []]]
  : [["python3", []], ["python", []]];

function findPython() {
  for (const [cmd, pre] of CANDIDATES) {
    const r = spawnSync(cmd, [...pre, "-c", "import sys; print(sys.version_info[:2] >= (3, 7))"], {
      stdio: ["ignore", "pipe", "ignore"],
    });
    if (r.status === 0 && String(r.stdout).trim() === "True") return [cmd, pre];
  }
  return null;
}

if (!fs.existsSync(SCRIPT)) {
  console.error("agy-switch: bundled script missing (" + SCRIPT + ") — reinstall the package");
  process.exit(1);
}

const python = findPython();
if (!python) {
  console.error(
    "agy-switch: Python 3.7+ is required but was not found on PATH.\n" +
      "  Debian/Ubuntu: sudo apt install python3\n" +
      "  macOS (brew):  brew install python3\n" +
      "  Windows:       winget install Python.Python.3.12"
  );
  process.exit(1);
}

const [cmd, pre] = python;
const child = spawn(cmd, [...pre, SCRIPT, ...process.argv.slice(2)], { stdio: "inherit" });
child.on("error", (err) => {
  console.error("agy-switch: failed to start Python: " + err.message);
  process.exit(1);
});
// Stay alive on signals until the child exits: if we died first, the shell
// would reclaim the foreground terminal and the child's next tty read would
// fail with EIO (this is what stranded the proxy manager in raw mode).
// On Windows the console already delivers Ctrl-C to the child, and
// child.kill() there is a hard TerminateProcess that would skip its cleanup —
// so only swallow the signal.
for (const sig of ["SIGINT", "SIGTERM", "SIGHUP"]) {
  process.on(sig, () => {
    if (IS_WIN) return;
    try {
      child.kill(sig);
    } catch {}
  });
}
child.on("exit", (code, signal) => {
  if (signal && !IS_WIN) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code === null ? 1 : code);
});
