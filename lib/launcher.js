#!/usr/bin/env node
// npm launcher for agy-switch: the CLI itself is a single-file Python program
// (bin/agy-switch); this wrapper finds a Python 3 interpreter and forwards
// all arguments to it, preserving stdio and the exit code.
"use strict";

const { spawn, spawnSync } = require("child_process");
const path = require("path");
const fs = require("fs");

const SCRIPT = path.join(__dirname, "..", "bin", "agy-switch");

function findPython() {
  for (const cmd of ["python3", "python"]) {
    const r = spawnSync(cmd, ["-c", "import sys; print(sys.version_info[:2] >= (3, 7))"], {
      stdio: ["ignore", "pipe", "ignore"],
    });
    if (r.status === 0 && String(r.stdout).trim() === "True") return cmd;
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
      "  macOS (brew):  brew install python3"
  );
  process.exit(1);
}

const child = spawn(python, [SCRIPT, ...process.argv.slice(2)], { stdio: "inherit" });
child.on("error", (err) => {
  console.error("agy-switch: failed to start Python: " + err.message);
  process.exit(1);
});
child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code === null ? 1 : code);
});
