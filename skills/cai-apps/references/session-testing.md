# Testing an app inside a CAI session

[scripts/test_app.py](../scripts/test_app.py) runs a manifest app's launcher in the current session, probes its health path, and stops it, without creating or changing an Application. Use it to catch launcher mistakes (wrong command, missing env, bad bind) before `create`.

```bash
uv run --script scripts/test_app.py <app>                       # run on CDSW_APP_PORT, probe, stop
uv run --script scripts/test_app.py <app> --keep                # leave it up, print the browser URL, Ctrl-C stops
uv run --script scripts/test_app.py <app> --port-var READONLY   # APP (default), READONLY or PUBLIC
uv run --script scripts/test_app.py <app> --env TOKEN=@/path/to/chmod-600-file
```

The app comes from the manifest (`--manifest`, `$CAI_APPS_MANIFEST`, or `deploy/apps.json`). The script runs with the session's environment plus the manifest's `env` (`${VAR}` expanded the same way `create` does) plus any `--env`. Secrets are not in the manifest, so pass them with `--env KEY=@file`. It exits non-zero if the launcher dies, the health path does not answer within `--timeout`, or the port is already taken.

## The session's ports

A session exposes up to three web-app ports as environment variables. The script binds the launcher to the one you pick by setting `CDSW_APP_PORT` for the child, so a launcher that reads `CDSW_APP_PORT` (see [launchers.md](launchers.md)) needs no change.

| Variable | Browser URL | Who can open it |
|---|---|---|
| `CDSW_APP_PORT` | `https://<CDSW_ENGINE_ID>.<CDSW_DOMAIN>` | project contributors and admins |
| `CDSW_READONLY_PORT` | `https://read-only-<CDSW_ENGINE_ID>.<CDSW_DOMAIN>` | read-only project collaborators |
| `CDSW_PUBLIC_PORT` | `https://public-<CDSW_ENGINE_ID>.<CDSW_DOMAIN>` | all users; deprecated |

Per the [Cloudera AI documentation](https://docs.cloudera.com/machine-learning/1.5.5/projects/topics/ml-embedded-web-apps.html): only one port per access level exists, and the editors feature uses `CDSW_APP_PORT` by default, so if an editor is running use `--port-var READONLY`. The UI lives only while the session runs (it times out with the session). The docs' own examples bind `127.0.0.1`. Check that page for the current rules, since ports and URL patterns can change between versions.

## Differences from a deployed app

A passing test does not prove the deployment works. Check these separately:

- **Kernel:** a deployed app's launcher runs through a Jupyter kernel; the test runs it as `python script.py`. `__file__` works in the test and not when deployed, so the script warns when the launcher mentions it.
- **Identity:** the test runs as you, with your Kerberos ticket and injected API keys. A deployed app runs as its run-as account, or as whoever started it, so keytab permissions and tokens can differ.
- **Port and URL:** the session's port differs from the one an Application gets, and the browser URL is the session's, not `<subdomain>.$CDSW_DOMAIN`. Relative-URL and path-prefix problems can show up only when deployed.
- **Environment:** the test sees the manifest's env and your `--env`, not the deployed app's live environment or secrets.

Report any step you could not run, such as a service that is reachable only from the deployed app.
