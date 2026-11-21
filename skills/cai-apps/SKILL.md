---
name: cai-apps
description: Deploy and operate Cloudera AI (CAI/CML/CDSW) Applications from a project: create apps from a manifest, set env vars and secrets, run as a service account, restart, verify, and troubleshoot. Use when asked to deploy, restart, configure, rotate a token, check, or debug a CAI Application, or to write an app launcher script, in a session that has CDSW_DOMAIN and CDSW_APIV2_KEY. Not for CAI jobs, models, or sessions, other platforms' app hosting, or Python dependency changes (use python-dependency-management); no sibling skill covers those yet.
---

# Deploying and operating Cloudera AI Applications

A CAI Application is a long-running process the platform runs from a script in the project, served at `https://<subdomain>.$CDSW_DOMAIN` behind CAI's authenticating proxy. This skill covers the lifecycle through the CAI API v2.

## Tooling

[scripts/cai_apps.py](scripts/cai_apps.py) is a standard-library wrapper over the API. Run it from a CAI session in the project (the session already has `CDSW_DOMAIN`, `CDSW_PROJECT_ID`, `CDSW_APIV2_KEY`). Copy it into the project (for example `scripts/cai_apps.py`) if it should be versioned with the code, or call it by its path here. `test_app.py` imports `cai_apps.py`, so copy the two scripts into the same folder together.

```bash
uv run --script cai_apps.py list                                  # status, run-as, health path
uv run --script cai_apps.py env <app> [--reveal]                  # secrets masked unless --reveal
uv run --script cai_apps.py set <app> KEY=value KEY2=@/path/file [--unset K] [--restart] [--dry-run]
uv run --script cai_apps.py restart <app>                         # also starts a stopped app; waits
uv run --script cai_apps.py stop <app>
uv run --script cai_apps.py run-as <app> <numeric-user-id>
uv run --script cai_apps.py public <app> on|off [--yes] [--restart] [--dry-run]   # unauthenticated access
uv run --script cai_apps.py create [--manifest deploy/apps.json] [--dry-run] [--start]
uv run --script cai_apps.py backup [app ...] [-o file.json]   # all apps by default
uv run --script cai_apps.py restore <file.json> [app ...] [--dry-run] [--start]
uv run --script cai_apps.py delete <app> [--backup file.json] [--yes] [--dry-run]
```

An app is addressed by subdomain or name. Variable names ending `_KEY`, `_TOKEN`, `_SECRET`, `_PASSWORD` are treated as secrets and masked.

The manifest (non-secret app definitions) format is in [references/apps.example.json](references/apps.example.json): `runtime_match` (substring of the runtime image id; the newest enabled match is used) and `apps[]` with `name`, `subdomain`, `script`, `cpu`, `memory`, `description`, `env`, and optionally `bypass_authentication`. `${VAR}` and `${VAR:-default}` in `env` values are filled from the local environment; `create` aborts and lists any unset variable without a default.

To try a launcher in the current session before creating the Application (three session ports, health probe, browser URL), use [scripts/test_app.py](scripts/test_app.py) and read [references/session-testing.md](references/session-testing.md).

For writing the app scripts themselves (port binding, Python, Node.js, Java and bash launchers, no `__file__` because runtimes are Jupyter-based, health checks, Kerberos refresh, app-to-app calls) read [references/launchers.md](references/launchers.md).

## Workflow

1. **Inspect:** `list` and `env <app>` show what is deployed, who it runs as, and its config. Read the project's launcher scripts and manifest before changing anything.
2. **Retrieve docs:** before any change that touches an API field or endpoint, fetch the workbench's own OpenAPI document, `https://$CDSW_DOMAIN/api/v2/swagger.json`, and check the field there; the deployed version is the authority, not memory or the web. If the fetch fails with a certificate error (a private CA), do not turn verification off on your own: use the platform's CA bundle (see "Trusting an internal CA" in [references/launchers.md](references/launchers.md)) or ask the user.
3. **Apply:** follow "First deployment" or "Common operations" below. Use `--dry-run` first. For a new app, run `test_app.py` first.
4. **Validate:** `list` for status, then the checks in "Verifying a deployment".
5. **Report:** which apps changed, which variables were set or removed (names only, never values), what was restarted, and any step you could not run.

`backup` writes each app as the body `POST` create takes (`project_id`, `name`, `subdomain`, `script`, `cpu`, `memory`, `runtime_identifier`, `run_as`, `environment` as an object, and so on) plus the domain, project and timestamp. **The file contains every environment value, secrets included, in clear text.** It is created with mode 600, never overwrites an existing file, and must stay out of git (add it to `.gitignore`). Do not print or paste its contents. `restore` recreates the apps in a backup that are missing from the project (existing subdomains are skipped, so `delete` one first to restore over it). Like `create`, it stops each app right after creation unless `--start`; run `--dry-run` first (secrets masked). The payload carries `run_as` and `runtime_identifier`, so restoring into another project or deployment can fail if they don't exist there.

`delete` is permanent. It asks you to type the app's subdomain unless `--yes` is passed, and refuses without a terminal. Use `--backup <file>` to save the app first. Confirm with the user before deleting, always back up first, and never pass `--yes` on your own initiative.

## Facts that cost time to learn

- **`"bypass_authentication": true` in the manifest makes an app reachable without logging in to CAI** (the `bypass_authentication` field of the create request). Anyone who has the URL can call it, so only use it for apps that are meant to be public or that authenticate callers themselves, and confirm with the user first. `create --dry-run` shows the value. Default is `false`. To change an existing app use `public <app> on|off`; turning it on asks you to type the subdomain unless `--yes` (never pass `--yes` on your own initiative), and the command reads the value back because a PATCH may ignore `false`.
- **Creating an app starts it immediately**, half-configured. `create` stops each new app straight away unless `--start`.
- **`environment` is a JSON-encoded string and `PATCH` replaces it whole.** A naive PATCH with one key wipes the rest; the script always sends the full merged dict. Do the same if you call the API directly.
- **Env var changes need a restart.** Variables are read at process start. A `set` that "worked" but changed nothing means you did not restart.
- **App-level env vars are visible to anyone who can see the app's settings.** Decide what goes there accordingly.
- **Deploying code = save/commit the files and `restart`.** Apps run the project's files in place from the shared filesystem.
- **Changing a subdomain** (`PATCH` `subdomain`, then restart) kills the old URL (certificate mismatch). Update every `*_SUBDOMAIN` variable on apps that call it, and tell people with bookmarks.

## Prerequisites (check before the first deployment)

1. **A service account to run the apps (optional).** Check whether the project has a *machine user* (CAI UI, project settings; ask the user if unsure). If it does, note its numeric user ID and use it as the run-as account. **If the project has none, do not set `run_as`**: leave it out of the manifest, skip `run-as`, and tell the user the apps will run as whoever started them, so their Kerberos identity and injected API keys change with that person. Never invent a user ID or substitute a normal collaborator.
2. **Read access for that account** (skip if there is no service account) to the project directory, including `.venv` and any `keytabs/` folder.
3. **A Kerberos keytab** if the app talks to a Kerberized service. Keep it in a gitignored folder. Find the principal with `klist -kt <keytab>`.
4. **A long-lived service token** for app-to-app calls: a CAI API key created on purpose and accepted by the proxy as a Bearer token. **Never reuse the injected `CDSW_API_KEY` / `CDSW_APIV2_KEY`**: they belong to whoever runs the app and may be rotated underneath you.
5. Any third-party API keys the apps need.

**Secrets**: put each in a `chmod 600` file and pass `KEY=@/path/to/file`. That keeps values out of shell history and the conversation. Never print them; `env` masks by default, and avoid `--reveal` unless the user asks.

## First deployment

1. Write the manifest and export the non-secret values it references.
2. **Preview, then create:** `create --dry-run`, then `create`. Existing apps are skipped.
3. **Set secrets** on each app that needs them (`set <app> TOKEN=@file`). A shared token goes on every app in the chain.
4. **Run as the service account, only if the project has one:** `run-as <app> <user-id>` for each app. With no machine user, skip this step and leave `run_as` unset; nothing then needs a restart on account of run-as. If CAI answers `500: Run as user does not have the right permissions for project`, the account is not yet a project *machine user*: add it in the CAI UI first (a normal collaborator with write access is not the same thing).
5. **Start in dependency order** (upstream services first, UI last) with `restart <app>` (`create` leaves the apps stopped, so this is their first start; it is not an extra restart). If you created with `--start` and no step after it changed an app (no `run-as`, and secrets were set before the first start or not needed), skip it and just `list`.
6. **Verify** (below).

Starting, stopping, restarting, changing run-as, and rotating tokens affect running services: confirm with the user before doing them on apps that already serve people.

## Common operations

| Task | How |
|---|---|
| Change a setting | `set <app> KEY=value --restart` |
| Rotate the service token | Create the new key, `set` it on **all** apps, restart all, then revoke the old one. The old token stops working on revoke, so swap quickly. |
| Remove a setting | `set <app> --unset KEY --restart` |
| Stop everything | `stop` each app, UI first |
| Save before a risky change | `backup -o <file>` (secrets in clear, mode 600) |
| Recreate from a backup | `restore <file> --dry-run`, then `restore <file>` |
| Remove an app | `delete <app> --backup <file>` after the user agrees |
| Preview any change | `set ... --dry-run`, `create --dry-run` |

## Verifying a deployment

The proxy requires authentication. Browsers log in; scripts send the token:

```bash
TOKEN=$(cat ~/secrets/service-token)
curl -s -H "Authorization: Bearer $TOKEN" https://<subdomain>.$CDSW_DOMAIN/<health-path>
```

A request without the token gets a `302` to the CAI login page: the app is up and protected, not broken. An app created with `"bypass_authentication": true` is the exception: it answers anyone who has the URL, with no login (`list` marks it `PUBLIC`). Application logs are in the CAI UI (the application's page) only: API v2 has no endpoint for them (checked against swagger.json; recheck if the platform is upgraded), so the script has no `logs` command. Ask the user to paste the relevant log lines. Make each app's health endpoint report enough to see its config (for example which LLM or backend it is on) without exposing secrets.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| App restart-loops | The polling endpoint (`CDSW_APP_POLLING_ENDPOINT`) fails. Make it liveness-only: no database, Kerberos or downstream calls. |
| `421 Invalid Host header` (MCP server) | The MCP SDK's host check rejects proxied requests. Disable it in the launcher, or set an allow-list. |
| Exits at start with a Kerberos error | Run-as account cannot read the keytab (check `/home/cdsw` and `keytabs/` permissions), principal does not match the keytab, or the KDC/realm is unreachable. |
| Auth errors after ~15 min to hours | CAI-issued tickets last about 15 minutes. Refresh from a keytab into a dedicated ccache (see launchers.md) and check the log shows refreshes. |
| `set` succeeded, nothing changed | No restart. |
| `500 ... right permissions` setting run-as | Account is not a project machine user yet. |
| Certificate error on an old URL | Subdomain was changed; use the new one. |
| `302` to login from a script | Missing or wrong Bearer token (or a token that was revoked/rotated), or the app was not created with `bypass_authentication`. |
| App-to-app call fails with 401/302 | Caller's token env var is unset or differs from the one the callee's proxy accepts; check with `env <app>` (masked values show only `<set>`; compare with `--reveal` only if the user agrees). |

## Without the script

Base `https://$CDSW_DOMAIN/api/v2/projects/$CDSW_PROJECT_ID/applications` with `Authorization: Bearer $CDSW_APIV2_KEY`. `GET` lists (paginated with `page_size` and `page_token`; follow `next_page_token`), `POST` creates, `PATCH .../{id}` updates, and `POST .../{id}:restart` and `:stop` control state. Statuses include `APPLICATION_STARTING` and `APPLICATION_STOPPING`, so wait for them to settle. Everything else is in the swagger document above.

## Skill feedback

If the user reports that this skill gave incorrect or outdated guidance, or is missing information, read [references/skill-feedback.md](references/skill-feedback.md).
