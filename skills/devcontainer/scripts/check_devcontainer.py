# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Check a VS Code devcontainer.json against the devcontainer skill's rules.

1. "name" is set and is a valid Podman container name.
2. "runArgs" contains "--name <name>" (or "--name=<name>") exactly once, matching "name",
   plus the /tmp tmpfs and gh_token secret arguments.
3. "containerUser" and "remoteUser" are both declared as "vscode".
4. The image is the MCR Java trixie image (with the java feature) or the uv trixie-slim
   image; no "build" section.
5. The common-utils, git, node, claude-code, github-cli, and vscode-extensions-cache
   features are present with their required options.
6. CLAUDE_CONFIG_DIR and the ~/.claude and ~/.config/gh bind mounts are present. Named
   volumes use chown=true, and bind mounts don't.
7. Python (uv image): the uv containerEnv values, the uv-vol and <name>-venv volumes,
   and the Python VS Code extensions and settings. The uv sync postCreateCommand is
   optional and not checked.
8. Java (java feature): installs last, the ~/.m2 and ~/.gradle bind mounts, and the Java
   VS Code extensions.
9. No Docker-only features, docker.sock mounts, or Compose configuration.

Usage: uv run --script check_devcontainer.py [PROJECT_ROOT_OR_DEVCONTAINER_JSON]
Exits 1 if any rule is violated.
"""

import json
import re
import sys
from pathlib import Path

JAVA_IMAGE = re.compile(r"mcr\.microsoft\.com/devcontainers/java:[^:]+-trixie")
UV_IMAGE = re.compile(r"ghcr\.io/astral-sh/uv:[^:]+-python[^:]+-trixie-slim")
USER = "vscode"
JAVA_FEATURE = "ghcr.io/devcontainers/features/java"
# Feature ID prefix -> option values every config must set.
REQUIRED_FEATURES = {
    "ghcr.io/devcontainers/features/common-utils": {"username": USER, "installZsh": True, "upgradePackages": True},
    "ghcr.io/devcontainers/features/git": {"version": "os-provided"},
    "ghcr.io/devcontainers/features/node": {"version": "lts"},
    "ghcr.io/anthropics/devcontainer-features/claude-code": {},
    "ghcr.io/devcontainers/features/github-cli": {},
    "ghcr.io/ramottamado/devcontainer-features/vscode-extensions-cache": {},
}
REQUIRED_RUN_ARGS = (
    "--tmpfs=/tmp:rw,exec,nosuid,nodev,mode=1777",
    "--secret=gh_token,type=env,target=GH_TOKEN",
)
REQUIRED_ENV = {"CLAUDE_CONFIG_DIR": f"/home/{USER}/.claude"}
# Mount source -> target every config must have.
REQUIRED_MOUNTS = {
    "${localEnv:HOME}/.claude": f"/home/{USER}/.claude",
    "${localEnv:HOME}/.config/gh": f"/home/{USER}/.config/gh",
}
JAVA_MOUNTS = {
    "${localEnv:HOME}/.m2": f"/home/{USER}/.m2",
    "${localEnv:HOME}/.gradle": f"/home/{USER}/.gradle",
}
PYTHON_ENV = {
    "UV_LINK_MODE": "copy",
    "UV_COMPILE_BYTECODE": "1",
    "UV_PROJECT_ENVIRONMENT": f"/home/{USER}/.venv",
    "UV_PYTHON_INSTALL_DIR": f"/home/{USER}/.uv",
}
# Named volumes, mounted with chown=true. "{name}" is replaced with the config's name.
PYTHON_VOLUMES = {
    "uv-vol": f"/home/{USER}/.uv",
    "{name}-venv": f"/home/{USER}/.venv",
}
PYTHON_EXTENSIONS = (
    "ms-toolsai.jupyter",
    "ms-ossdata.vscode-pgsql",
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.autopep8",
    "charliermarsh.ruff",
)
PYTHON_SETTINGS = {
    "python.defaultInterpreterPath": f"/home/{USER}/.venv/bin/python",
    "python.terminal.activateEnvironment": False,
}
JAVA_EXTENSIONS = (
    "vscjava.vscode-java-pack",
    "vmware.vscode-boot-dev-pack",
    "ms-ossdata.vscode-pgsql",
    "redhat.vscode-xml",
    "redhat.vscode-yaml",
)
DISALLOWED_FEATURES = (
    "ghcr.io/devcontainers/features/docker-in-docker",
    "ghcr.io/devcontainers/features/docker-outside-of-docker",
)
CONTAINER_NAME = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.-]*")


def find_config(target):
    if target.is_file():
        return target
    for candidate in (target / ".devcontainer" / "devcontainer.json", target / ".devcontainer.json"):
        if candidate.is_file():
            return candidate
    sys.exit(f"No devcontainer.json found under {target}")


def strip_jsonc(text):
    """Remove // and /* */ comments and trailing commas, leaving strings intact."""
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == "\\" else 1
            out.append(text[i : j + 1])
            i = j + 1
        elif text.startswith("//", i):
            i = text.find("\n", i)
            i = n if i == -1 else i
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = n if end == -1 else end + 2
        else:
            out.append(c)
            i += 1
    return re.sub(r",(\s*[}\]])", r"\1", "".join(out))


def run_arg_names(run_args):
    names = []
    for i, arg in enumerate(run_args):
        if arg == "--name":
            names.append(run_args[i + 1] if i + 1 < len(run_args) else None)
        elif isinstance(arg, str) and arg.startswith("--name="):
            names.append(arg.removeprefix("--name="))
    return names


def parse_mount(mount):
    """Mounts are either "key=value,..." strings or objects."""
    if isinstance(mount, dict):
        return mount
    return dict(part.split("=", 1) for part in mount.split(",") if "=" in part)


def find_feature(config, prefix):
    return next((v for k, v in config.get("features", {}).items() if k.startswith(prefix)), None)


def check_mounts(config, required, errors):
    mounts = {(m.get("source"), m.get("target")) for m in map(parse_mount, config.get("mounts", []))}
    for source, target in required.items():
        if (source, target) not in mounts:
            errors.append(f'"mounts" is missing {source} mounted at {target}')


def check_volume_owners(config, errors):
    """Named volumes need chown=true so the container user owns them; host binds must not have it."""
    for mount in map(parse_mount, config.get("mounts", [])):
        chown = str(mount.get("chown", "false")).lower() == "true"
        if mount.get("type") == "volume" and not chown:
            errors.append(f'volume {mount.get("source")} at {mount.get("target")} needs chown=true')
        elif mount.get("type") == "bind" and chown:
            errors.append(
                f'bind mount {mount.get("source")} has chown=true, which re-owns the host files; remove it'
            )


def check_env(config, required, errors):
    for key, expected in required.items():
        actual = config.get("containerEnv", {}).get(key)
        if actual != expected:
            errors.append(f'"containerEnv" {key} is {actual!r}; set it to {expected!r}')


def check_vscode(config, extensions, settings, errors):
    vscode = config.get("customizations", {}).get("vscode", {})
    present = {e.lower() for e in vscode.get("extensions", [])}
    for extension in extensions:
        if extension.lower() not in present:
            errors.append(f'"customizations.vscode.extensions" is missing {extension!r}')
    for key, expected in settings.items():
        actual = vscode.get("settings", {}).get(key)
        if actual != expected:
            errors.append(f'"customizations.vscode.settings" {key} is {actual!r}; set it to {expected!r}')


def check_java_last(config, errors):
    """overrideFeatureInstallOrder must list every other feature, then the java feature last."""
    order = [re.sub(r"[:@][^/]*$", "", f) for f in config.get("overrideFeatureInstallOrder", [])]
    if not order or order[-1] != JAVA_FEATURE:
        errors.append(f'"overrideFeatureInstallOrder" must end with {JAVA_FEATURE!r} so it installs last')
    for feature in config.get("features", {}):
        base = re.sub(r"[:@][^/]*$", "", feature)
        if base != JAVA_FEATURE and base not in order:
            errors.append(f'{base} is not in "overrideFeatureInstallOrder", so it would install after java')


def main():
    path = find_config(Path(sys.argv[1] if len(sys.argv) > 1 else "."))
    try:
        config = json.loads(strip_jsonc(path.read_text()))
    except json.JSONDecodeError as exc:
        sys.exit(f"{path}: cannot parse: {exc}")

    errors = []

    name = config.get("name")
    if not name:
        errors.append('"name" is missing; set it to the project name')
    elif not CONTAINER_NAME.fullmatch(name):
        errors.append(f'"name" {name!r} is not a valid container name ([a-zA-Z0-9][a-zA-Z0-9_.-]*)')

    names = run_arg_names(config.get("runArgs", []))
    if not names:
        errors.append('"runArgs" has no --name; add "--name", "<name>"')
    elif len(names) > 1:
        errors.append(f'"runArgs" has {len(names)} --name entries; keep exactly one')
    elif names[0] != name:
        errors.append(f'"runArgs" --name {names[0]!r} does not match "name" {name!r}')

    for arg in REQUIRED_RUN_ARGS:
        if arg not in config.get("runArgs", []):
            errors.append(f'"runArgs" is missing {arg!r}')

    check_env(config, REQUIRED_ENV, errors)

    for key in ("containerUser", "remoteUser"):
        if not config.get(key):
            errors.append(f'"{key}" is missing; declare it as {USER!r} even if the image sets a user')
        elif config[key] != USER:
            errors.append(f'"{key}" is {config[key]!r}; set it to {USER!r}')

    java = find_feature(config, JAVA_FEATURE) is not None
    image = config.get("image") or ""
    python = bool(UV_IMAGE.fullmatch(image))
    if "dockerComposeFile" in config:
        errors.append('"dockerComposeFile" is not supported; this skill covers image-based Podman configs')
    if "build" in config:
        errors.append('"build" is not supported; use "image" and put Containerfile ENV values in "containerEnv"')
    if not image:
        errors.append('no "image" set')
    elif JAVA_IMAGE.fullmatch(image):
        if not java:
            errors.append(f"{JAVA_FEATURE} is missing; add it whenever Java is enabled")
    elif not python:
        errors.append(f'"image" {image!r} is not a supported base image (see references/base-images.md)')

    for prefix, options in REQUIRED_FEATURES.items():
        value = find_feature(config, prefix)
        if value is None:
            errors.append(f"{prefix} is missing; every config needs it")
            continue
        for key, expected in options.items():
            if value.get(key) != expected:
                errors.append(f"{prefix} {key} is {value.get(key)!r}; set it to {expected!r}")

    check_mounts(config, REQUIRED_MOUNTS, errors)
    check_volume_owners(config, errors)

    if python:
        check_env(config, PYTHON_ENV, errors)
        check_mounts(config, {s.format(name=name): t for s, t in PYTHON_VOLUMES.items()}, errors)
        check_vscode(config, PYTHON_EXTENSIONS, PYTHON_SETTINGS, errors)

    if java:
        check_java_last(config, errors)
        check_mounts(config, JAVA_MOUNTS, errors)
        check_vscode(config, JAVA_EXTENSIONS, {}, errors)

    for feature in config.get("features", {}):
        if feature.startswith(DISALLOWED_FEATURES):
            errors.append(f"feature {feature!r} requires Docker; remove it")

    for mount in config.get("mounts", []):
        text = mount if isinstance(mount, str) else json.dumps(mount)
        if "docker.sock" in text:
            errors.append(f"mount {text!r} binds the Docker socket; remove it")

    for error in errors:
        print(f"error: {error}")
    if errors:
        sys.exit(1)
    print(f"ok: {path} passes the devcontainer rules")


if __name__ == "__main__":
    main()
