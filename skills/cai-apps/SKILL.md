---
name: cai-apps
description: Deploy and operate Cloudera AI (CAI/CML/CDSW) Applications from a project: create apps from a manifest, set env vars and secrets, run as a service account, restart, verify, and troubleshoot. Use when asked to deploy, restart, configure, rotate a token, check, or debug a CAI Application, or to write an app launcher script, in a session that has CDSW_DOMAIN and CDSW_APIV2_KEY. Not for CAI jobs, models, or sessions, other platforms' app hosting, or Python dependency changes (use python-dependency-management); no sibling skill covers those yet.
---

# Deploying and operating Cloudera AI Applications

A CAI Application is a long-running process the platform runs from a script in the project, served at `https://<subdomain>.$CDSW_DOMAIN` behind CAI's authenticating proxy. This skill covers the lifecycle through the CAI API v2.

## Tooling

[scripts/cai_apps.py](scripts/cai_apps.py) is a standard-library wrapper over the API. Run it from a CAI session in the project (the session already has `CDSW_DOMAIN`, `CDSW_PROJECT_ID`, `CDSW_APIV2_KEY`). Copy it into the project (for example `scripts/cai_apps.py`) if it should be versioned with the code, or call it by its path here.

```bash
uv run --script cai_apps.py list                                  # status, run-as, health path
uv run --script cai_apps.py env <app> [--reveal]                  # secrets masked unless --reveal
uv run --script cai_apps.py set <app> KEY=value KEY2=@/path/file [--unset K] [--restart] [--dry-run]
uv run --script cai_apps.py restart <app>                         # also starts a stopped app; waits
uv run --script cai_apps.py stop <app>
uv run --script cai_apps.py run-as <app> <numeric-user-id>
uv run --script cai_apps.py create [--manifest deploy/apps.json] [--dry-run] [--start]
```

An app is addressed by subdomain or name. Variable names ending `_KEY`, `_TOKEN`, `_SECRET`, `_PASSWORD` are treated as secrets and masked.

The manifest (non-secret app definitions) format is in [references/apps.example.json](references/apps.example.json): `runtime_match` (substring of the runtime image id; the newest enabled match is used) and `apps[]` with `name`, `subdomain`, `script`, `cpu`, `memory`, `description`, `env`. `${VAR}` and `${VAR:-default}` in `env` values are filled from the local environment; `create` aborts and lists any unset variable without a default.

For writing the app scripts themselves (port binding, uv, health checks, Kerberos refresh, app-to-app calls) read [references/launchers.md](references/launchers.md).

## Workflow

1. **Inspect:** `list` and `env <app>` show what is deployed, who it runs as, and its config. Read the project's launcher scripts and manifest before changing anything.
2. **Retrieve docs:** the API reference is the OpenAPI document at `https://$CDSW_DOMAIN/api/v2/swagger.json`. Check it rather than trusting memory.
3. **Apply:** follow "First deployment" or "Common operations" below. Use `--dry-run` first.
4. **Validate:** `list` for status, then the checks in "Verifying a deployment".
5. **Report:** which apps changed, which variables were set or removed (names only, never values), what was restarted, and any step you could not run.

## Facts that cost time to learn

- **Creating an app starts it immediately**, half-configured. `create` stops each new app straight away unless `--start`.
- **`environment` is a JSON-encoded string and `PATCH` replaces it whole.** A naive PATCH with one key wipes the rest; the script always sends the full merged dict. Do the same if you call the API directly.
- **Env var changes need a restart.** Variables are read at process start. A `set` that "worked" but changed nothing means you did not restart.
- **App-level env vars are visible to anyone who can see the app's settings.** Decide what goes there accordingly.
- **Deploying code = save/commit the files and `restart`.** Apps run the project's files in place from the shared filesystem.
- **Changing a subdomain** (`PATCH` `subdomain`, then restart) kills the old URL (certificate mismatch). Update every `*_SUBDOMAIN` variable on apps that call it, and tell people with bookmarks.

## Prerequisites (check before the first deployment)

1. **A service account to run the apps.** Add a CAI machine user to the project as a *run-as account* and note its numeric user ID. Otherwise apps run as whoever started them, and their Kerberos identity and injected API keys change with that person.
2. **Read access for that account** to the project directory, including `.venv` and any `keytabs/` folder.
3. **A Kerberos keytab** if the app talks to a Kerberized service. Keep it in a gitignored folder. Find the principal with `klist -kt <keytab>`.
4. **A long-lived service token** for app-to-app calls: a CAI API key created on purpose and accepted by the proxy as a Bearer token. **Never reuse the injected `CDSW_API_KEY` / `CDSW_APIV2_KEY`**: they belong to whoever runs the app and may be rotated underneath you.
5. Any third-party API keys the apps need.

**Secrets**: put each in a `chmod 600` file and pass `KEY=@/path/to/file`. That keeps values out of shell history and the conversation. Never print them; `env` masks by default, and avoid `--reveal` unless the user asks.

## First deployment

1. Write the manifest and export the non-secret values it references.
2. **Preview, then create:** `create --dry-run`, then `create`. Existing apps are skipped.
3. **Set secrets** on each app that needs them (`set <app> TOKEN=@file`). A shared token goes on every app in the chain.
4. **Run as the service account:** `run-as <app> <user-id>` for each app. If CAI answers `500: Run as user does not have the right permissions for project`, the account is not yet a project *machine user*: add it in the CAI UI first (a normal collaborator with write access is not the same thing).
5. **Start in dependency order** (upstream services first, UI last) with `restart <app>`, then `list`.
6. **Verify** (below).

Starting, stopping, restarting, changing run-as, and rotating tokens affect running services: confirm with the user before doing them on apps that already serve people.

## Common operations

| Task | How |
|---|---|
| Change a setting | `set <app> KEY=value --restart` |
| Rotate the service token | Create the new key, `set` it on **all** apps, restart all, then revoke the old one. The old token stops working on revoke, so swap quickly. |
| Remove a setting | `set <app> --unset KEY --restart` |
| Stop everything | `stop` each app, UI first |
| Preview any change | `set ... --dry-run`, `create --dry-run` |

## Verifying a deployment

The proxy requires authentication. Browsers log in; scripts send the token:

```bash
TOKEN=$(cat ~/secrets/service-token)
curl -s -H "Authorization: Bearer $TOKEN" https://<subdomain>.$CDSW_DOMAIN/<health-path>
```

A request without the token gets a `302` to the CAI login page: the app is up and protected, not broken. Application logs are in the CAI UI (the application's page). Make each app's health endpoint report enough to see its config (for example which LLM or backend it is on) without exposing secrets.

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
| `302` to login from a script | Missing or wrong Bearer token (or a token that was revoked/rotated). |
| App-to-app call fails with 401/302 | Caller's token env var is unset or differs from the one the callee's proxy accepts; check with `env <app>` (masked values show only `<set>`; compare with `--reveal` only if the user agrees). |

## Without the script

Base `https://$CDSW_DOMAIN/api/v2/projects/$CDSW_PROJECT_ID/applications` with `Authorization: Bearer $CDSW_APIV2_KEY`. `GET` lists (paginated with `page_size` and `page_token`; follow `next_page_token`), `POST` creates, `PATCH .../{id}` updates, and `POST .../{id}:restart` and `:stop` control state. Statuses include `APPLICATION_STARTING` and `APPLICATION_STOPPING`, so wait for them to settle. Everything else is in the swagger document above.

## Skill feedback

If the user reports that this skill gave incorrect or outdated guidance, or is missing information, read [references/skill-feedback.md](references/skill-feedback.md).
