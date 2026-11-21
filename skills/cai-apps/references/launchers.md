# Writing launcher scripts for CAI Applications

A CAI Application runs one script. Each app is its own pod with the **project filesystem mounted at `/home/cdsw`**, so every app (and every session) shares the project's files and, with uv, one `.venv`.

## Rules every launcher must follow

- **Don't derive the project root from `__file__` (or `sys.argv[0]`, `inspect`, etc.).** CAI runtimes are Jupyter-based: the platform runs the script through a Jupyter kernel (IPython), not as `python script.py`. `__file__` is then undefined or not the script's real path, so `Path(__file__).resolve().parents[n]` fails or points at the wrong directory. Use the fixed mount `/home/cdsw` (the project root, see above) with an optional override such as `PROJECT_ROOT`, as in the launcher below. Don't rely on the working directory being the project root either. A child process started by the launcher has a real `__file__`.
- **Bind `127.0.0.1:$CDSW_APP_PORT`.** CAI sets the port and proxies to it. Never hard-code a port or bind `0.0.0.0`.
- **The launcher is plain Python on the runtime's system Python** (no project deps yet). It starts the real process in the foreground with `subprocess.run` and exits with its status, so when the program dies the app (and its kernel) dies with it. The program can be written in anything: Python, Node.js, Java.
- **Python programs always run through uv: `uv sync --frozen --no-dev --inexact`, never without `--inexact`.** All apps and sessions share one `.venv`; an exact `--no-dev` sync strips dev tools out from under everyone else. Then start with `uv run --frozen --no-sync <entry>`.
- **Don't capture the child's output** (`stdout=PIPE`): the log then appears only when the program exits. Let it inherit stdout/stderr so the app log is live.
- **Serve relative URLs only.** CAI serves each app under a path prefix, so a UI must call `api/ask`, not `/api/ask`.
- **Health endpoint = liveness only.** CAI restarts apps whose polling endpoint fails. Never make `/health` touch a database, warehouse, Kerberos or another app, or an upstream outage becomes a restart loop. Put dependency checks on a different path and set `CDSW_APP_POLLING_ENDPOINT` to the liveness one.
- **Find the interpreter before writing the launcher** (`uv`, `java`, `npx`/`node`, `bash`). If it is not on `PATH` or in the project, ask the user rather than assuming a location.
- **Set an env var in the launcher only if its value must be generated at start or taken from another variable the CAI runtime sets.** Examples: the program's own port variable, filled from `CDSW_APP_PORT`; a path built at start (such as a database file under the project root); a `PATH` prepend (it extends the existing value, where an app-environment `PATH` would replace it); a per-process value like a Kerberos cache path containing the user id. Every other value (host, CA paths, feature flags, the program's fixed settings, secrets) goes in the CAI Application's environment, through the manifest's `env` or `cai_apps.py set <app> KEY=value` (see SKILL.md), so a config change needs only `set --restart` and no launcher edit. The launcher inherits the app environment.
- **Fail fast on missing required env** with a message naming the variable; it lands in the app log.

## Launcher script

Keep the launcher thin: add only the env vars it must generate (see the rule above), then run the real program as a child process. The child is an ordinary process, so `__file__`, `sys.argv` and the working directory behave normally there. Only the marked block changes per app (see "Per language" below):

```python
import os, subprocess, sys
from pathlib import Path

port = os.environ.get("CDSW_APP_PORT") or sys.exit("CDSW_APP_PORT is not set: run this as a Cloudera AI Application.")
root = Path(os.environ.get("PROJECT_ROOT", "/home/cdsw"))  # fixed path, never __file__

# --- edit only this block: working directory, command, and env vars the launcher must generate ---
cwd = root
cmd = ["my-program"]
env = {**os.environ}                                      # add only generated or CAI-derived values here, e.g. "<PORT_VAR>": port
# ---------------------------------------------------------------------

sys.exit(subprocess.run(cmd, cwd=cwd, env=env).returncode)
```

`subprocess.run` blocks until the program exits and `sys.exit(<returncode>)` hands its status to CAI, so a failed start shows as one. Don't wrap it in `try`/`except` that prints and exits `1`, or use `check=True` (it raises a traceback instead): both hide the real exit code.

### Per language (the block to edit)

**Python**: always run through `uv`, even for a single script (`[..., "python", "main.py"]`). Install deps first, then run through `uv` so the project `.venv` is used. Find `uv` with `shutil.which("uv") or str(Path.home() / ".local/bin/uv")` (exit with a hint, `pip install --user uv`, if missing).

```python
subprocess.run([uv, "sync", "--frozen", "--no-dev", "--inexact"], cwd=root, check=True)
cmd = [uv, "run", "--frozen", "--no-sync", "my-entry-point"]   # or [..., "python", "main.py"]
```

**Node.js (npx, npm scripts)**: the runtime may have no Node. Before writing the launcher, find `npx`/`node` (`shutil.which`, then look for a Node install in the project such as `node/bin`). **If neither is found, ask the user where Node is or how it should be installed; don't guess a path.** Put the install's `bin` first on `PATH`.

```python
env = {**os.environ, "PATH": f"{root}/node/bin:{os.environ.get('PATH', '')}"}
cmd = ["npx", "my-node-app"]                          # or ["node", "server.js"], ["npm", "start"]
```

**Java (jar)**: before writing the launcher, find `java` (`shutil.which`, then look for a JDK in the project such as `jdk/bin/java`) and check its version against what the program needs. **If none is found, ask the user where the JDK is or how it should be installed; don't guess a path.** Use the JDK path explicitly in `cmd` (the runtime's Java may be missing or the wrong version), and pass JVM options (`-D...`) as separate list items before `-jar`.

```python
cmd = [f"{root}/jdk/bin/java", "-jar", f"{root}/app.jar"]
```

**Bash script**: the launcher itself stays Python (the kernel runs Python), so call the script as the child. Invoke it through `bash` rather than relying on the executable bit, and set `PROJECT_ROOT` and the program's fixed settings in the app environment.

```python
cmd = ["bash", f"{root}/scripts/start.sh"]
```

Inside the script, start with `set -euo pipefail` so a failed setup step stops the app with a non-zero status, `cd "$PROJECT_ROOT"` (the script runs as an ordinary process, so `$0` is also reliable), finish with `exec <program> ...` so the program replaces the shell and its exit status becomes the script's. Without `exec`, the shell's last command status is returned and signals reach only the shell.

For a Kerberized app, see "Kerberos from a keytab" below.

### How the program takes host and port

The option names belong to the program, not to this skill, so never copy them from memory or from another program. Find them in this order: the program's own docs and `--help` (search the web for its configuration reference if the project doesn't include it), then the project's existing config, then ask the user. Then use whichever mechanism the program supports:

| It takes host/port from | Where it goes |
|---|---|
| Environment variables | Host (fixed `127.0.0.1`): the app environment, `<HOST_VAR>=127.0.0.1`. Port: the launcher, `env = {**os.environ, "<PORT_VAR>": port}`, because its value comes from `CDSW_APP_PORT`. For a bash script, use the variables in its `exec` line. |
| CLI flags | `cmd` (arguments cannot come from the app environment); append them: `[..., "<host-flag>", "127.0.0.1", "<port-flag>", port]`. For Java, JVM `-D` properties go before `-jar`. |
| Nothing (hard-coded port or `0.0.0.0`) | Look for an undocumented env var or config key first; otherwise start it from a small entry script that calls its API with `host="127.0.0.1", port=...`. Don't put a reverse proxy in front of it. |

Always take the port from `CDSW_APP_PORT`. It is often `8100`, but read it from the environment rather than hard-coding the number, since the platform decides it.

## Trusting an internal CA

If the program calls HTTPS services signed by a private CA (the platform's own proxy, an internal API, an LLM gateway), it fails with certificate errors unless it trusts that CA. Ask the user where the CA certificate (PEM) is; don't guess. Keep it in the project, and set the runtime's own option. The env-var ones are fixed values, so they go in the app environment (`set <app> NODE_EXTRA_CA_CERTS=/home/cdsw/ca.pem`); the Java options go in `cmd`:

| Runtime | Setting | Notes |
|---|---|---|
| Node.js | `NODE_EXTRA_CA_CERTS=<ca.pem>` | Adds to the built-in roots. |
| Python (`requests`) | `REQUESTS_CA_BUNDLE=<bundle.pem>` | Replaces the default bundle. |
| Python (`ssl`, `httpx`, `urllib`, `uv`) | `SSL_CERT_FILE=<bundle.pem>` | Replaces the default roots. `uv` itself can also use `SSL_CERT_FILE` or `--native-tls`; check its docs. |
| Java | `-Djavax.net.ssl.trustStore=<truststore.jks>` and `-Djavax.net.ssl.trustStorePassword=<password>` in `cmd`, before `-jar` | Java has no "extra CA" option: build a truststore that contains the CA (below). |

For the Python settings, a bundle that replaces the defaults must also contain the public roots if the program calls public services: concatenate the system bundle and the internal CA into one file. Check the library's docs for the exact variable, since libraries differ.

For Java, create the truststore once (a session terminal or a pre-step), starting from a copy of the JDK's `lib/security/cacerts` so public roots stay trusted, then import the CA:

```bash
cp "$JAVA_HOME/lib/security/cacerts" truststore.jks
keytool -importcert -noprompt -alias internal-ca -file ca.pem -keystore truststore.jks
```

`keytool` asks for the truststore password. Treat it as a secret, like any other: put it in the app's environment with `cai_apps.py set <app> TRUSTSTORE_PASSWORD=@/path/to/chmod-600-file` (see SKILL.md; names ending `_PASSWORD` are masked), and have the launcher read it, failing fast if it is unset:

```python
pw = os.environ.get("TRUSTSTORE_PASSWORD") or sys.exit("TRUSTSTORE_PASSWORD is not set")
cmd = [f"{root}/jdk/bin/java", f"-Djavax.net.ssl.trustStore={root}/truststore.jks",
       f"-Djavax.net.ssl.trustStorePassword={pw}", "-jar", f"{root}/app.jar"]
```

Never hard-code it in the launcher or commit it. Keep the CA and truststore in the project.

## Kerberos from a keytab

CAI starts an app with a ticket for the run-as user, but it lasts about 15 minutes and has a renewal limit. For a long-running app that talks to a Kerberized service (Impala, HDFS, Hive):

- Keep the keytab in a gitignored folder (e.g. `keytabs/`). The run-as account can read it: CAI only allows run-as for a machine user with Operator access to the project.
- In the launcher, run `kinit -kt <keytab> <principal>` at start and then every ~hour from a daemon thread, into a **dedicated credential cache** (`KRB5CCNAME=FILE:/tmp/<app>_krb5cc_<uid>`), so it never clobbers the ticket CAI injected. Pass `KRB5CCNAME` to the child.
- **Java programs** are configured through JVM options rather than just the ticket cache. Keep `krb5.conf` and a JAAS file in the project and pass them as JVM options in `cmd`, before `-jar`:

  ```python
  cmd = [f"{root}/jdk/bin/java",
         f"-Djava.security.krb5.conf={root}/krb5.conf",
         f"-Djava.security.auth.login.config={root}/jaas.conf",
         "-Djavax.security.auth.useSubjectCredsOnly=false",
         "-jar", f"{root}/app.jar"]
  ```

  For troubleshooting add `-Dsun.security.krb5.debug=true`, `-Dsun.security.jgss.debug=true` and `-Dsun.security.spnego.debug=true` temporarily; they are verbose, so remove them afterwards. The JAAS file's login module and its options depend on the program, so take them from its docs.
- Make the initial failure fatal only if the Kerberized service is actually required, and log refreshes ("refreshed Kerberos ticket") so you can verify them later.

## MCP servers behind the CAI proxy

The `mcp` SDK auto-enables a Host-header check for `127.0.0.1` binds, which rejects proxied requests with `421 Invalid Host header`. Disable it in the launcher unless an explicit allow-list is configured.

## App-to-app calls

Apps reach each other through the CAI proxy at `https://<subdomain>.$CDSW_DOMAIN` with `Authorization: Bearer <token>`. Derive the URL from a `*_SUBDOMAIN` env var so a subdomain change is one variable. Use a **dedicated long-lived API key** as the token (see SKILL.md), never the injected `CDSW_API_KEY`/`CDSW_APIV2_KEY`. Only the user-facing app needs a browser login; have it proxy `/api/*` server-side so the browser never needs CORS or the token.
