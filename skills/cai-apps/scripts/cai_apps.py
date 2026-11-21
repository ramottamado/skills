#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Manage Cloudera AI Applications in the current project through the CAI API v2 (standard library only).

Needs CDSW_DOMAIN, CDSW_PROJECT_ID and CDSW_APIV2_KEY, which a CAI session already has.
Run with `uv run --script cai_apps.py ...` (standard library only; plain `python3 cai_apps.py` also works).

  cai_apps.py list
  cai_apps.py env my-service                        # secrets masked; --reveal to show
  cai_apps.py set my-service LOG_LEVEL=debug --restart
  cai_apps.py set my-service SERVICE_TOKEN=@/path/to/file   # value read from a file
  cai_apps.py set my-service --unset OLD_VAR
  cai_apps.py restart my-service               # also starts a stopped app
  cai_apps.py stop my-service
  cai_apps.py run-as my-service 20                 # numeric id of a project machine user
  cai_apps.py public my-service on|off [--yes] [--restart] [--dry-run]   # unauthenticated access on an existing app
  cai_apps.py create [--dry-run] [--start]      # from the manifest
  cai_apps.py backup [app ...] [-o FILE]          # create payloads incl. env (secrets in clear), mode 600
  cai_apps.py restore FILE [app ...] [--dry-run] [--start]   # recreate apps missing from the project
  cai_apps.py delete my-service [--backup FILE] [--yes] [--dry-run]

The manifest is --manifest, else $CAI_APPS_MANIFEST, else ./deploy/apps.json.
An app is addressed by subdomain or name.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SECRET_SUFFIXES = ("_KEY", "_TOKEN", "_SECRET", "_PASSWORD")
# Fields of CreateApplicationRequest (swagger) that an Application also carries, minus `environment`/`project_id`.
PAYLOAD_FIELDS = (
    "name",
    "subdomain",
    "description",
    "script",
    "cpu",
    "memory",
    "nvidia_gpu",
    "kernel",
    "bypass_authentication",
    "runtime_identifier",
    "runtime_addon_identifiers",
    "run_as",
    "cdv_app",
    "accelerator_label_id",
    "resource_group_id",
    "resource_profile_id",
)
UNSET_IF_FALSY = {"run_as", "accelerator_label_id", "resource_group_id", "resource_profile_id"}
TRANSITIONAL = {"APPLICATION_UNKNOWN", "APPLICATION_STARTING", "APPLICATION_STOPPING"}


def is_secret(name: str) -> bool:
    return name.upper().endswith(SECRET_SUFFIXES)


def mask(env: dict[str, str]) -> dict[str, str]:
    return {k: ("<set>" if is_secret(k) else v) for k, v in env.items()}


def parse_assignments(items: list[str]) -> dict[str, str]:
    """`KEY=value`, or `KEY=@path` to read the value from a file (keeps secrets out of shell history)."""
    out: dict[str, str] = {}
    for item in items:
        key, sep, value = item.partition("=")
        if not sep or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            sys.exit(f"Expected KEY=VALUE or KEY=@file, got: {key!r}")
        if value.startswith("@"):
            value = Path(value[1:]).expanduser().read_text().strip()
        out[key] = value
    return out


_VAR = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")


def expand(value: str, environ: dict[str, str], missing: set[str]) -> str:
    def repl(m: re.Match) -> str:
        name, default = m.group(1), m.group(2)
        if environ.get(name):
            return environ[name]
        if default is not None:
            return default
        missing.add(name)
        return m.group(0)

    return _VAR.sub(repl, value)


def find_app(apps: list[dict], ident: str) -> dict:
    for a in apps:
        if ident.lower() in (a["subdomain"].lower(), a["name"].lower(), a["id"]):
            return a
    sys.exit(f"No application {ident!r}. Known: {', '.join(a['subdomain'] for a in apps) or 'none'}")


def env_of(app: dict) -> dict[str, str]:
    return json.loads(app.get("environment") or "{}")


class Api:
    def __init__(self) -> None:
        try:
            self.domain, self.project = os.environ["CDSW_DOMAIN"], os.environ["CDSW_PROJECT_ID"]
            self.key = os.environ["CDSW_APIV2_KEY"]
        except KeyError as exc:
            sys.exit(f"{exc.args[0]} is not set. Run this from a CAI session in the project.")
        self.base = f"https://{self.domain}/api/v2"

    def call(self, method: str, path: str, body: dict | None = None) -> dict:
        req = urllib.request.Request(
            f"{self.base}{path}",
            json.dumps(body).encode() if body is not None else None,
            {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
            method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as res:
                return json.loads(res.read() or b"{}")
        except urllib.error.HTTPError as exc:
            sys.exit(f"{method} {path} failed: HTTP {exc.code} {exc.read().decode()[:300]}")

    @property
    def apps_path(self) -> str:
        return f"/projects/{self.project}/applications"

    def apps(self) -> list[dict]:
        apps: list[dict] = []
        token = ""
        while True:
            query = "?page_size=100" + (f"&page_token={urllib.parse.quote(token)}" if token else "")
            page = self.call("GET", self.apps_path + query)
            apps += page.get("applications", [])
            token = page.get("next_page_token", "")
            if not token:
                return apps

    def wait(self, app_id: str, timeout: int = 300, grace: int = 10) -> str:
        """Poll until the app leaves STARTING/STOPPING. The status can still show the old state right after a
        restart or stop request, so a settled status counts only once `grace` seconds have passed or it changed."""
        start = time.time()
        deadline, status, first = start + timeout, "", None
        while time.time() < deadline:
            status = self.call("GET", f"{self.apps_path}/{app_id}")["status"]
            first = first or status
            settled = status not in TRANSITIONAL
            if settled and (status != first or time.time() - start >= grace):
                return status
            time.sleep(3)
        return status


def cmd_list(api: Api, _: argparse.Namespace) -> None:
    for a in api.apps():
        e = env_of(a)
        print(
            f"{a['subdomain']:<12} {a['status']:<22} run_as={a.get('run_as', 0):<4} "
            f"health={e.get('CDSW_APP_POLLING_ENDPOINT', '-'):<12} "
            f"{'PUBLIC ' if a.get('bypass_authentication') else ''}{a['name']}"
        )


def cmd_env(api: Api, args: argparse.Namespace) -> None:
    env = env_of(find_app(api.apps(), args.app))
    for k, v in sorted((env if args.reveal else mask(env)).items()):
        print(f"{k}={v}")


def cmd_set(api: Api, args: argparse.Namespace) -> None:
    app = find_app(api.apps(), args.app)
    env = env_of(app)
    changes, removals = parse_assignments(args.assignments), args.unset or []
    env.update(changes)
    for k in removals:
        env.pop(k, None)
    shown = {**mask(changes), **{k: "<removed>" for k in removals}}
    print(f"{app['subdomain']}: {json.dumps(shown)}")
    if args.dry_run:
        return
    # `environment` is a JSON-encoded *string*, and it replaces the whole value: always send the full dict.
    api.call("PATCH", f"{api.apps_path}/{app['id']}", {"environment": json.dumps(env)})
    print("updated; restart the app for it to take effect" if not args.restart else "updated")
    if args.restart:
        restart(api, app)


def restart(api: Api, app: dict) -> None:
    api.call("POST", f"{api.apps_path}/{app['id']}:restart", {})
    print(f"{app['subdomain']}: restarting ... {api.wait(app['id'])}")


def cmd_restart(api: Api, args: argparse.Namespace) -> None:
    restart(api, find_app(api.apps(), args.app))


def cmd_stop(api: Api, args: argparse.Namespace) -> None:
    app = find_app(api.apps(), args.app)
    api.call("POST", f"{api.apps_path}/{app['id']}:stop", {})
    print(f"{app['subdomain']}: stopping ... {api.wait(app['id'])}")


def cmd_run_as(api: Api, args: argparse.Namespace) -> None:
    app = find_app(api.apps(), args.app)
    api.call("PATCH", f"{api.apps_path}/{app['id']}", {"run_as": args.user_id})
    print(f"{app['subdomain']}: run_as={args.user_id}")


def cmd_public(api: Api, args: argparse.Namespace) -> None:
    """Toggle `bypass_authentication` (unauthenticated access) on an existing app."""
    app = find_app(api.apps(), args.app)
    want = args.state == "on"
    now = bool(app.get("bypass_authentication"))
    print(f"{app['subdomain']}: unauthenticated access is {'on' if now else 'off'}, requested {args.state}")
    if now == want or args.dry_run:
        return
    if want and not args.yes:
        if not sys.stdin.isatty():
            sys.exit(
                "Refusing to open an app to unauthenticated access without confirmation: pass --yes, or run from a terminal."
            )
        if (
            input(
                f"Anyone with the URL will reach it without login. Type the subdomain {app['subdomain']!r} to confirm: "
            ).strip()
            != app["subdomain"]
        ):
            sys.exit("Subdomain did not match; nothing changed.")
    api.call("PATCH", f"{api.apps_path}/{app['id']}", {"bypass_authentication": want})
    # A PATCH can silently ignore a false/zero value, so read it back instead of trusting the 200.
    got = bool(api.call("GET", f"{api.apps_path}/{app['id']}").get("bypass_authentication"))
    if got != want:
        sys.exit(
            f"{app['subdomain']}: PATCH returned OK but bypass_authentication is still {got}. Change it in the CAI UI."
        )
    print(
        f"{app['subdomain']}: unauthenticated access {'on' if got else 'off'}"
        + ("" if args.restart else "; restart the app if it does not take effect")
    )
    if args.restart:
        restart(api, app)


def resolve_runtime(api: Api, match: str) -> str:
    runtimes = api.call("GET", "/runtimes?page_size=200").get("runtimes", [])
    ids = sorted(
        r["image_identifier"] for r in runtimes if match in r["image_identifier"] and r.get("status") == "ENABLED"
    )
    if not ids:
        sys.exit(f"No enabled runtime matches {match!r}")
    return ids[-1]


def manifest_path(arg: str | None) -> Path:
    path = Path(arg or os.environ.get("CAI_APPS_MANIFEST") or "deploy/apps.json").expanduser()
    if not path.is_file():
        sys.exit(f"Manifest not found: {path} (use --manifest or CAI_APPS_MANIFEST)")
    return path


def cmd_create(api: Api, args: argparse.Namespace) -> None:
    manifest = json.loads(manifest_path(args.manifest).read_text())
    existing = {a["subdomain"] for a in api.apps()}
    missing: set[str] = set()
    specs = []
    for spec in manifest["apps"]:
        env = {k: expand(v, dict(os.environ), missing) for k, v in spec.get("env", {}).items()}
        specs.append({**{k: v for k, v in spec.items() if k != "env"}, "environment": env})
    if missing:
        sys.exit(f"Set these in your environment first: {', '.join(sorted(missing))}")
    runtime = resolve_runtime(api, manifest["runtime_match"])
    for spec in specs:
        if spec["subdomain"] in existing:
            print(f"{spec['subdomain']}: exists, skipping (use `set` to change it)")
            continue
        body = {
            **spec,
            "project_id": api.project,
            "kernel": "",
            "runtime_identifier": runtime,
            "bypass_authentication": bool(spec.get("bypass_authentication", False)),
        }
        if args.dry_run:
            print(f"{spec['subdomain']}: would create {json.dumps({**body, 'environment': mask(spec['environment'])})}")
            continue
        app = api.call("POST", api.apps_path, body)
        # CAI starts an application the moment it is created. Stop it unless asked otherwise.
        if args.start:
            print(f"{spec['subdomain']}: created ... {api.wait(app['id'])}")
        else:
            api.call("POST", f"{api.apps_path}/{app['id']}:stop", {})
            print(f"{spec['subdomain']}: created, stopped ... {api.wait(app['id'])}")


def create_payload(app: dict, project: str) -> dict:
    """Rebuild the POST body that would recreate `app`. `environment` is an object here, a JSON string in GET."""
    body = {"project_id": project}
    for k in PAYLOAD_FIELDS:
        v = app.get(k)
        if v is None or (k in UNSET_IF_FALSY and not v):
            continue
        body[k] = v
    body["environment"] = env_of(app)
    return body


def write_backup(api: Api, apps: list[dict], out: Path) -> None:
    if out.exists():
        sys.exit(f"{out} already exists; choose another --output (backups are never overwritten).")
    doc = {
        "_comment": "Backup of CAI Applications as create payloads. Contains environment values, secrets included "
        "in clear text: keep it private and out of git.",
        "domain": api.domain,
        "project_id": api.project,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "applications": [create_payload(a, api.project) for a in apps],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(doc, f, indent=2)
        f.write("\n")
    print(f"backed up {len(apps)} application(s) to {out} (mode 600, contains secrets)")


def cmd_backup(api: Api, args: argparse.Namespace) -> None:
    apps = api.apps()
    chosen = [find_app(apps, i) for i in args.apps] if args.apps else apps
    if not chosen:
        sys.exit("No applications to back up.")
    out = Path(args.output or f"cai-apps-backup-{time.strftime('%Y%m%d-%H%M%S')}.json").expanduser()
    write_backup(api, chosen, out)


def cmd_restore(api: Api, args: argparse.Namespace) -> None:
    path = Path(args.file).expanduser()
    if not path.is_file():
        sys.exit(f"Backup not found: {path}")
    doc = json.loads(path.read_text())
    if doc.get("domain") not in (None, api.domain):
        print(f"note: backup is from {doc['domain']}, this is {api.domain}; run_as and runtime ids may not exist here")
    specs = doc["applications"]
    if args.apps:
        wanted = {a.lower() for a in args.apps}
        specs = [s for s in specs if wanted & {s["subdomain"].lower(), s["name"].lower()}]
        unknown = wanted - {x.lower() for s in specs for x in (s["subdomain"], s["name"])}
        if unknown:
            sys.exit(f"Not in the backup: {', '.join(sorted(unknown))}")
    existing = {a["subdomain"] for a in api.apps()}
    for spec in specs:
        sub = spec["subdomain"]
        if sub in existing:
            print(f"{sub}: exists, skipping (delete it first to restore over it)")
            continue
        body = {**spec, "project_id": api.project}
        if args.dry_run:
            print(f"{sub}: would create {json.dumps({**body, 'environment': mask(body.get('environment', {}))})}")
            continue
        app = api.call("POST", api.apps_path, body)
        # CAI starts an application the moment it is created. Stop it unless asked otherwise.
        if args.start:
            print(f"{sub}: restored ... {api.wait(app['id'])}")
        else:
            api.call("POST", f"{api.apps_path}/{app['id']}:stop", {})
            print(f"{sub}: restored, stopped ... {api.wait(app['id'])}")


def cmd_delete(api: Api, args: argparse.Namespace) -> None:
    app = find_app(api.apps(), args.app)
    print(f"{app['subdomain']}: {app['status']}, run_as={app.get('run_as', 0)}")
    if args.dry_run:
        print("dry run: would delete" + (f" after backing up to {args.backup}" if args.backup else ""))
        return
    if args.backup:
        write_backup(api, [app], Path(args.backup).expanduser())
    if not args.yes:
        if not sys.stdin.isatty():
            sys.exit("Refusing to delete without confirmation: pass --yes, or run from a terminal.")
        if input(f"Type the subdomain {app['subdomain']!r} to delete it permanently: ").strip() != app["subdomain"]:
            sys.exit("Subdomain did not match; nothing deleted.")
    api.call("DELETE", f"{api.apps_path}/{app['id']}")
    gone = all(a["id"] != app["id"] for a in api.apps())
    print(f"{app['subdomain']}: deleted" if gone else f"{app['subdomain']}: delete requested, still listed")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="applications, status, run-as and health path").set_defaults(fn=cmd_list)
    s = sub.add_parser("env", help="show an application's environment (secrets masked)")
    s.add_argument("app")
    s.add_argument("--reveal", action="store_true", help="print secret values too")
    s.set_defaults(fn=cmd_env)
    s = sub.add_parser("set", help="add/change/remove environment variables")
    s.add_argument("app")
    s.add_argument("assignments", nargs="*", metavar="KEY=VALUE|KEY=@file")
    s.add_argument("--unset", action="append", metavar="KEY", help="remove a variable (repeatable)")
    s.add_argument("--restart", action="store_true")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(fn=cmd_set)
    for name, fn in (("restart", cmd_restart), ("stop", cmd_stop)):
        s = sub.add_parser(name)
        s.add_argument("app")
        s.set_defaults(fn=fn)
    s = sub.add_parser("run-as", help="run an app as a project machine user")
    s.add_argument("app")
    s.add_argument("user_id", type=int)
    s.set_defaults(fn=cmd_run_as)
    s = sub.add_parser("public", help="turn unauthenticated access (bypass_authentication) on or off for an app")
    s.add_argument("app")
    s.add_argument("state", choices=["on", "off"])
    s.add_argument("--yes", action="store_true", help="skip the typed confirmation when turning it on")
    s.add_argument("--restart", action="store_true")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(fn=cmd_public)
    s = sub.add_parser("create", help="create the manifest's apps that don't exist yet")
    s.add_argument("--manifest", help="path to the manifest (default: deploy/apps.json)")
    s.add_argument("--dry-run", action="store_true")
    s.add_argument("--start", action="store_true", help="leave them running (default: stop right after creation)")
    s.set_defaults(fn=cmd_create)
    s = sub.add_parser(
        "backup", help="write apps and env as create payloads to a JSON file (mode 600, secrets in clear)"
    )
    s.add_argument("apps", nargs="*", help="subdomains or names (default: all)")
    s.add_argument(
        "-o", "--output", help="file to write (default: cai-apps-backup-<timestamp>.json; never overwritten)"
    )
    s.set_defaults(fn=cmd_backup)
    s = sub.add_parser("restore", help="recreate apps from a backup file (existing subdomains are skipped)")
    s.add_argument("file")
    s.add_argument("apps", nargs="*", help="subdomains or names to restore (default: all in the file)")
    s.add_argument("--dry-run", action="store_true")
    s.add_argument("--start", action="store_true", help="leave them running (default: stop right after creation)")
    s.set_defaults(fn=cmd_restore)
    s = sub.add_parser("delete", help="permanently delete an application")
    s.add_argument("app")
    s.add_argument("--backup", metavar="FILE", help="back the app up to FILE before deleting")
    s.add_argument("--yes", action="store_true", help="skip the typed confirmation")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(fn=cmd_delete)
    args = p.parse_args()
    args.fn(Api(), args)


if __name__ == "__main__":
    main()
