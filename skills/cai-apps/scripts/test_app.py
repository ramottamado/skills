#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Try an Application's launcher inside the current CAI session, before (or without) creating the Application.

Runs the manifest app's script in this session with the app's environment, binds it to one of the session's
three web-app ports, probes the health path, prints the browser URL, and stops it. Standard library only.
Needs CDSW_DOMAIN and CDSW_ENGINE_ID, which a CAI session already has. No CAI API call is made.

  test_app.py my-service                         # run the launcher on CDSW_APP_PORT, probe, stop
  test_app.py my-service --keep                  # leave it running; print the URL; Ctrl-C stops it
  test_app.py my-service --port-var READONLY     # use CDSW_READONLY_PORT instead (APP, READONLY, PUBLIC)
  test_app.py my-service --env TOKEN=@/path/to/file --env LOG_LEVEL=debug

The manifest is --manifest, else $CAI_APPS_MANIFEST, else ./deploy/apps.json. The app is addressed by
subdomain or name. Secrets are not in the manifest: pass them with --env KEY=@file.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from cai_apps import expand, find_app, manifest_path, parse_assignments  # sibling script in this folder

PORT_VARS = {"APP": "CDSW_APP_PORT", "READONLY": "CDSW_READONLY_PORT", "PUBLIC": "CDSW_PUBLIC_PORT"}
URL_PREFIX = {"APP": "", "READONLY": "read-only-", "PUBLIC": "public-"}


def probe(url: str) -> int | None:
    """HTTP status of `url`, or None if nothing answers. Any answer below 500 means the process is serving."""
    try:
        with urllib.request.urlopen(url, timeout=5) as res:
            return res.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except (urllib.error.URLError, OSError):
        return None


def port_in_use(port: str) -> bool:
    with socket.socket() as sock:
        sock.settimeout(1)
        return sock.connect_ex(("127.0.0.1", int(port))) == 0


def stop(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(10)
        except subprocess.TimeoutExpired:
            proc.kill()


def main() -> None:
    p = argparse.ArgumentParser(description="run an app's launcher in this session and probe it")
    p.add_argument("app", help="subdomain or name in the manifest")
    p.add_argument("--manifest")
    p.add_argument("--root", default=".", help="project root the manifest's script paths are relative to")
    p.add_argument("--env", action="append", default=[], metavar="KEY=VALUE|KEY=@file", help="extra or overriding env var")
    p.add_argument("--port-var", choices=sorted(PORT_VARS), default="APP", help="which session port to bind (default APP)")
    p.add_argument("--timeout", type=int, default=60, help="seconds to wait for the health path to answer")
    p.add_argument("--keep", action="store_true", help="keep running after a good probe until Ctrl-C")
    args = p.parse_args()

    manifest = json.loads(manifest_path(args.manifest).read_text())
    spec = find_app([{**a, "id": ""} for a in manifest["apps"]], args.app)
    missing: set[str] = set()
    app_env = {k: expand(v, dict(os.environ), missing) for k, v in spec.get("env", {}).items()}
    if missing:
        sys.exit(f"Set these in your environment first: {', '.join(sorted(missing))}")

    port_name = PORT_VARS[args.port_var]
    port = os.environ.get(port_name)
    if not port:
        sys.exit(f"{port_name} is not set. Run this inside a CAI session.")
    engine, domain = os.environ.get("CDSW_ENGINE_ID", ""), os.environ.get("CDSW_DOMAIN", "")

    env = {**os.environ, **app_env, **parse_assignments(args.env), "CDSW_APP_PORT": port}
    health = env.get("CDSW_APP_POLLING_ENDPOINT", "/")
    root = Path(args.root).resolve()
    script = root / spec["script"]
    if not script.is_file():
        sys.exit(f"Script not found: {script}")
    if "__file__" in script.read_text(errors="replace"):
        print("warning: the script mentions __file__. A deployed app runs through a Jupyter kernel where it is "
              "undefined, so this may work here and fail there (see references/launchers.md).")

    if port_in_use(port):
        sys.exit(f"FAIL: something is already listening on 127.0.0.1:{port} (a previous run or another app in this "
                 f"session). Stop it first, or pick another port with --port-var.")

    print(f"{spec['subdomain']}: running {spec['script']} on {port_name}={port}, health {health}")
    proc = subprocess.Popen([sys.executable, str(script)], cwd=root, env=env)
    signal.signal(signal.SIGTERM, lambda *_: (stop(proc), sys.exit(143)))
    url = f"http://127.0.0.1:{port}{health if health.startswith('/') else '/' + health}"
    deadline, status = time.time() + args.timeout, None
    try:
        while time.time() < deadline and proc.poll() is None and (status := probe(url)) is None:
            time.sleep(2)
        if proc.poll() is not None:
            sys.exit(f"FAIL: the launcher exited with code {proc.returncode} before answering on {url}")
        if proc.poll() is None and (status is None or status >= 500):
            stop(proc)
            sys.exit(f"FAIL: {url} gave {'no answer' if status is None else f'HTTP {status}'} within {args.timeout}s")
        if proc.poll() is not None:
            sys.exit(f"FAIL: the launcher exited with code {proc.returncode} while {url} was being probed")
        print(f"OK: {url} answered HTTP {status}")
        if engine and domain:
            print(f"Browser (log in to CAI first): https://{URL_PREFIX[args.port_var]}{engine}.{domain}")
        if args.keep:
            print("Running. Press Ctrl-C to stop.")
            proc.wait()
    except KeyboardInterrupt:
        pass
    finally:
        stop(proc)


if __name__ == "__main__":
    main()
