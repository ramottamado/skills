# Writing launcher scripts for CAI Applications

A CAI Application runs one script. Each app is its own pod with the **project filesystem mounted at `/home/cdsw`**, so every app (and every session) shares the project's files and, with uv, one `.venv`.

## Rules every launcher must follow

- **Don't derive the project root from `__file__` (or `sys.argv[0]`, `inspect`, etc.).** CAI runtimes are Jupyter-based: the platform runs the script through a Jupyter kernel (IPython), not as `python script.py`. `__file__` is then undefined or not the script's real path, so `Path(__file__).resolve().parents[n]` fails or points at the wrong directory. Use the fixed mount `/home/cdsw` (the project root, see above) with an optional override such as `PROJECT_ROOT`, as in the launcher below. Don't rely on the working directory being the project root either. The same applies to code the launcher imports from a notebook-style context; a normally started child process (the console script) has a real `__file__`.
- **Bind `127.0.0.1:$CDSW_APP_PORT`.** CAI sets the port and proxies to it. Never hard-code a port or bind `0.0.0.0`.
- **Run with the runtime's system Python** (no project deps yet): the launcher installs deps, then starts the real process (a console script) in the foreground and exits with its status. Forward SIGTERM/SIGINT to the child.
- **`uv sync --frozen --no-dev --inexact`, never without `--inexact`.** All apps and sessions share one `.venv`; an exact `--no-dev` sync strips dev tools out from under everyone else. Then start with `uv run --frozen --no-sync <entry>`.
- **Serve relative URLs only.** CAI serves each app under a path prefix, so a UI must call `api/ask`, not `/api/ask`.
- **Health endpoint = liveness only.** CAI restarts apps whose polling endpoint fails. Never make `/health` touch a database, warehouse, Kerberos or another app, or an upstream outage becomes a restart loop. Put dependency checks on a different path and set `CDSW_APP_POLLING_ENDPOINT` to the liveness one.
- **Fail fast on missing required env** with a message naming the variable; it lands in the app log.

## Minimal launcher

```python
import os, shutil, signal, subprocess, sys
from pathlib import Path

root = Path(os.environ.get("PROJECT_ROOT", "/home/cdsw"))
uv = shutil.which("uv") or str(Path.home() / ".local/bin/uv")
if not Path(uv).exists():
    sys.exit("uv not found. In a session terminal run: pip install --user uv")
if not os.environ.get("CDSW_APP_PORT"):
    sys.exit("CDSW_APP_PORT is not set: run this as a Cloudera AI Application.")

subprocess.run([uv, "sync", "--frozen", "--no-dev", "--inexact"], cwd=root, check=True)
proc = subprocess.Popen([uv, "run", "--frozen", "--no-sync", "my-entry-point"], cwd=root,
                        env={**os.environ, "APP_HOST": "127.0.0.1"})
for sig in (signal.SIGTERM, signal.SIGINT):
    signal.signal(sig, lambda *_: proc.terminate())
sys.exit(proc.wait())
```

## Kerberos from a keytab

CAI starts an app with a ticket for the run-as user, but it lasts about 15 minutes and has a renewal limit. For a long-running app that talks to a Kerberized service (Impala, HDFS, Hive):

- Keep the keytab in a gitignored folder (e.g. `keytabs/`), readable by the run-as account.
- In the launcher, run `kinit -kt <keytab> <principal>` at start and then every ~hour from a daemon thread, into a **dedicated credential cache** (`KRB5CCNAME=FILE:/tmp/<app>_krb5cc_<uid>`), so it never clobbers the ticket CAI injected. Pass `KRB5CCNAME` to the child.
- Make the initial failure fatal only if the Kerberized service is actually required, and log refreshes ("refreshed Kerberos ticket") so you can verify them later.

## MCP servers behind the CAI proxy

The `mcp` SDK auto-enables a Host-header check for `127.0.0.1` binds, which rejects proxied requests with `421 Invalid Host header`. Disable it in the launcher unless an explicit allow-list is configured.

## App-to-app calls

Apps reach each other through the CAI proxy at `https://<subdomain>.$CDSW_DOMAIN` with `Authorization: Bearer <token>`. Derive the URL from a `*_SUBDOMAIN` env var so a subdomain change is one variable. Use a **dedicated long-lived API key** as the token (see SKILL.md), never the injected `CDSW_API_KEY`/`CDSW_APIV2_KEY`. Only the user-facing app needs a browser login; have it proxy `/api/*` server-side so the browser never needs CORS or the token.
