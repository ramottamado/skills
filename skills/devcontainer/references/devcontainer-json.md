# devcontainer.json templates

Replace `<name>` with the normalized project name and the version placeholders with the versions chosen from [base-images.md](base-images.md). The `name` value, the value after `--name`, and the `<name>-venv` volume all use the same string.

Every template carries the settings in "Shared settings" below. Python-enabled configs add "Python settings", and Java-enabled configs add "Java settings". The skill writes only `devcontainer.json`: there is no Containerfile.

The Python and mixed templates include the optional `postCreateCommand`. Drop it when "Python settings" says to.

## Python

```jsonc
{
	"name": "<name>",
	"image": "ghcr.io/astral-sh/uv:<uv-version>-python<python-version>-trixie-slim",
	"runArgs": [
		"--name",
		"<name>",
		"--tmpfs=/tmp:rw,exec,nosuid,nodev,mode=1777",
		"--secret=gh_token,type=env,target=GH_TOKEN"
	],
	"containerEnv": {
		"CLAUDE_CONFIG_DIR": "/home/vscode/.claude",
		"UV_LINK_MODE": "copy",
		"UV_COMPILE_BYTECODE": "1",
		"UV_PROJECT_ENVIRONMENT": "/home/vscode/.venv",
		"UV_PYTHON_INSTALL_DIR": "/home/vscode/.uv"
	},
	"containerUser": "vscode",
	"remoteUser": "vscode",
	"features": {
		"ghcr.io/devcontainers/features/common-utils:2": {
			"username": "vscode",
			"installZsh": true,
			"upgradePackages": true
		},
		"ghcr.io/devcontainers/features/git:1": {
			"version": "os-provided"
		},
		"ghcr.io/devcontainers/features/node:2": {
			"version": "lts"
		},
		"ghcr.io/anthropics/devcontainer-features/claude-code:1.0": {},
		"ghcr.io/devcontainers/features/github-cli:1": {},
		"ghcr.io/ramottamado/devcontainer-features/vscode-extensions-cache:latest": {}
	},
	"mounts": [
		"source=${localEnv:HOME}/.claude,target=/home/vscode/.claude,type=bind,consistency=cached",
		"source=${localEnv:HOME}/.config/gh,target=/home/vscode/.config/gh,type=bind,consistency=cached",
		"source=uv-vol,target=/home/vscode/.uv,type=volume,chown=true",
		"source=<name>-venv,target=/home/vscode/.venv,type=volume,chown=true"
	],
	"postCreateCommand": "uv sync --locked --all-groups",
	"customizations": {
		"vscode": {
			"extensions": [
				"ms-toolsai.jupyter",
				"ms-ossdata.vscode-pgsql",
				"ms-python.python",
				"ms-python.vscode-pylance",
				"ms-python.autopep8",
				"charliermarsh.ruff"
			],
			"settings": {
				"python.defaultInterpreterPath": "/home/vscode/.venv/bin/python",
				"python.terminal.activateEnvironment": false
			}
		}
	}
}
```

## Java

Leave out `installMaven` / `installGradle` when a wrapper (`mvnw`, `gradlew`) is committed. Use `installGradle` instead of `installMaven` for Gradle. `overrideFeatureInstallOrder` makes the java feature install last. If you add another feature, put it in the list before java.

```jsonc
{
	"name": "<name>",
	"image": "mcr.microsoft.com/devcontainers/java:<java-version>-trixie",
	"runArgs": [
		"--name",
		"<name>",
		"--tmpfs=/tmp:rw,exec,nosuid,nodev,mode=1777",
		"--secret=gh_token,type=env,target=GH_TOKEN"
	],
	"containerEnv": {
		"CLAUDE_CONFIG_DIR": "/home/vscode/.claude"
	},
	"containerUser": "vscode",
	"remoteUser": "vscode",
	"features": {
		"ghcr.io/devcontainers/features/common-utils:2": {
			"username": "vscode",
			"installZsh": true,
			"upgradePackages": true
		},
		"ghcr.io/devcontainers/features/git:1": {
			"version": "os-provided"
		},
		"ghcr.io/devcontainers/features/node:2": {
			"version": "lts"
		},
		"ghcr.io/anthropics/devcontainer-features/claude-code:1.0": {},
		"ghcr.io/devcontainers/features/github-cli:1": {},
		"ghcr.io/ramottamado/devcontainer-features/vscode-extensions-cache:latest": {},
		"ghcr.io/devcontainers/features/java:1": {
			"version": "<java-version>",
			"installMaven": true
		}
	},
	"overrideFeatureInstallOrder": [
		"ghcr.io/devcontainers/features/common-utils",
		"ghcr.io/devcontainers/features/git",
		"ghcr.io/devcontainers/features/node",
		"ghcr.io/anthropics/devcontainer-features/claude-code",
		"ghcr.io/devcontainers/features/github-cli",
		"ghcr.io/ramottamado/devcontainer-features/vscode-extensions-cache",
		"ghcr.io/devcontainers/features/java"
	],
	"mounts": [
		"source=${localEnv:HOME}/.claude,target=/home/vscode/.claude,type=bind,consistency=cached",
		"source=${localEnv:HOME}/.config/gh,target=/home/vscode/.config/gh,type=bind,consistency=cached",
		"source=${localEnv:HOME}/.m2,target=/home/vscode/.m2,type=bind,consistency=cached",
		"source=${localEnv:HOME}/.gradle,target=/home/vscode/.gradle,type=bind,consistency=cached"
	],
	"customizations": {
		"vscode": {
			"extensions": [
				"vscjava.vscode-java-pack",
				"vmware.vscode-boot-dev-pack",
				"ms-ossdata.vscode-pgsql",
				"redhat.vscode-xml",
				"redhat.vscode-yaml"
			]
		}
	}
}
```

## Python and Java

The Python template plus the java feature, which installs last through `overrideFeatureInstallOrder`. The extension list merges both stacks, with `ms-ossdata.vscode-pgsql` listed once.

```jsonc
{
	"name": "<name>",
	"image": "ghcr.io/astral-sh/uv:<uv-version>-python<python-version>-trixie-slim",
	"runArgs": [
		"--name",
		"<name>",
		"--tmpfs=/tmp:rw,exec,nosuid,nodev,mode=1777",
		"--secret=gh_token,type=env,target=GH_TOKEN"
	],
	"containerEnv": {
		"CLAUDE_CONFIG_DIR": "/home/vscode/.claude",
		"UV_LINK_MODE": "copy",
		"UV_COMPILE_BYTECODE": "1",
		"UV_PROJECT_ENVIRONMENT": "/home/vscode/.venv",
		"UV_PYTHON_INSTALL_DIR": "/home/vscode/.uv"
	},
	"containerUser": "vscode",
	"remoteUser": "vscode",
	"features": {
		"ghcr.io/devcontainers/features/common-utils:2": {
			"username": "vscode",
			"installZsh": true,
			"upgradePackages": true
		},
		"ghcr.io/devcontainers/features/git:1": {
			"version": "os-provided"
		},
		"ghcr.io/devcontainers/features/node:2": {
			"version": "lts"
		},
		"ghcr.io/anthropics/devcontainer-features/claude-code:1.0": {},
		"ghcr.io/devcontainers/features/github-cli:1": {},
		"ghcr.io/ramottamado/devcontainer-features/vscode-extensions-cache:latest": {},
		"ghcr.io/devcontainers/features/java:1": {
			"version": "<java-version>",
			"installMaven": true
		}
	},
	"overrideFeatureInstallOrder": [
		"ghcr.io/devcontainers/features/common-utils",
		"ghcr.io/devcontainers/features/git",
		"ghcr.io/devcontainers/features/node",
		"ghcr.io/anthropics/devcontainer-features/claude-code",
		"ghcr.io/devcontainers/features/github-cli",
		"ghcr.io/ramottamado/devcontainer-features/vscode-extensions-cache",
		"ghcr.io/devcontainers/features/java"
	],
	"mounts": [
		"source=${localEnv:HOME}/.claude,target=/home/vscode/.claude,type=bind,consistency=cached",
		"source=${localEnv:HOME}/.config/gh,target=/home/vscode/.config/gh,type=bind,consistency=cached",
		"source=uv-vol,target=/home/vscode/.uv,type=volume,chown=true",
		"source=<name>-venv,target=/home/vscode/.venv,type=volume,chown=true",
		"source=${localEnv:HOME}/.m2,target=/home/vscode/.m2,type=bind,consistency=cached",
		"source=${localEnv:HOME}/.gradle,target=/home/vscode/.gradle,type=bind,consistency=cached"
	],
	"postCreateCommand": "uv sync --locked --all-groups",
	"customizations": {
		"vscode": {
			"extensions": [
				"ms-toolsai.jupyter",
				"ms-ossdata.vscode-pgsql",
				"ms-python.python",
				"ms-python.vscode-pylance",
				"ms-python.autopep8",
				"charliermarsh.ruff",
				"vscjava.vscode-java-pack",
				"vmware.vscode-boot-dev-pack",
				"redhat.vscode-xml",
				"redhat.vscode-yaml"
			],
			"settings": {
				"python.defaultInterpreterPath": "/home/vscode/.venv/bin/python",
				"python.terminal.activateEnvironment": false
			}
		}
	}
}
```

## Shared settings

Every config gets these, whatever the stack:

| Setting | Value | Purpose |
| --- | --- | --- |
| `runArgs` | `"--tmpfs=/tmp:rw,exec,nosuid,nodev,mode=1777"` | Mounts `/tmp` as an in-memory tmpfs, world-writable with the sticky bit, and allows executables in it |
| `runArgs` | `"--secret=gh_token,type=env,target=GH_TOKEN"` | Exposes the Podman secret `gh_token` as `GH_TOKEN` for `gh` and git |
| `containerEnv` | `"CLAUDE_CONFIG_DIR": "/home/vscode/.claude"` | Points Claude Code at the mounted config |
| `mounts` | `${localEnv:HOME}/.claude` → `/home/vscode/.claude` (bind) | Shares the host's Claude Code config and sign-in |
| `mounts` | `${localEnv:HOME}/.config/gh` → `/home/vscode/.config/gh` (bind) | Shares the host's GitHub CLI config |
| common-utils feature | `"username": "vscode"`, `"installZsh": true`, `"upgradePackages": true` | Creates `vscode` and its home `/home/vscode`, installs zsh, and upgrades OS packages |

## Python settings

| Setting | Value | Purpose |
| --- | --- | --- |
| `containerEnv` | `"UV_LINK_MODE": "copy"` | Copies packages into the venv, because the uv cache and the venv volume are on different filesystems, so hardlinks can't work |
| `containerEnv` | `"UV_COMPILE_BYTECODE": "1"` | Compiles `.pyc` files at install time |
| `containerEnv` | `"UV_PROJECT_ENVIRONMENT": "/home/vscode/.venv"` | Puts the project venv on the `<name>-venv` volume |
| `containerEnv` | `"UV_PYTHON_INSTALL_DIR": "/home/vscode/.uv"` | Puts uv-managed Pythons on the `uv-vol` volume |
| `mounts` | volume `uv-vol` → `/home/vscode/.uv`, `chown=true` | Python installs, shared by every project |
| `mounts` | volume `<name>-venv` → `/home/vscode/.venv`, `chown=true` | This project's virtual environment, kept across container rebuilds |
| `postCreateCommand` (optional) | `uv sync --locked --all-groups` | Installs the locked dependencies, including every dependency group |
| VS Code extensions | `ms-toolsai.jupyter`, `ms-ossdata.vscode-pgsql`, `ms-python.python`, `ms-python.vscode-pylance`, `ms-python.autopep8`, `charliermarsh.ruff` | |
| VS Code settings | `"python.defaultInterpreterPath": "/home/vscode/.venv/bin/python"`, `"python.terminal.activateEnvironment": false` | Uses the uv environment without auto-activating it in terminals |

The volume targets must match `UV_PYTHON_INSTALL_DIR` and `UV_PROJECT_ENVIRONMENT`.

`chown=true` is a Podman mount option. It makes Podman give each named volume to the container user (`vscode`), so `uv sync` can write to it. Use it only on `type=volume` mounts, never on bind mounts of host directories (see "The vscode user" in [base-images.md](base-images.md)).

The `postCreateCommand` is optional:

- Add it when the project has a `uv.lock`, unless the user says they'll sync by hand.
- When there is no `uv.lock`, ask the user whether to add it anyway. Explain that `--locked` makes the command fail, and VS Code shows the error after creating the container, until a `uv.lock` is committed. They can create one with `uv lock` (see the `python-dependency-management` skill). Add the command only if they say yes. Otherwise leave it out.
- Without it, the venv volume stays empty until someone runs `uv sync`.

If the command fails because `uv.lock` is missing, the container keeps running. VS Code shows the error, and the `<name>-venv` volume stays empty. Fix it from a terminal inside the container, in the workspace folder, then reload the window so the Python extension picks up `/home/vscode/.venv/bin/python`:

| Situation | Run |
| --- | --- |
| No `pyproject.toml` (not a uv project yet) | `uv init`, then `uv sync --all-groups` |
| `pyproject.toml` but no `uv.lock` | `uv lock`, then `uv sync --locked --all-groups` |
| `uv.lock` exists but is out of date | `uv lock`, then `uv sync --locked --all-groups` |

`uv sync` without `--locked` also creates or updates `uv.lock`, so `uv sync --all-groups` alone works in every case above except a missing `pyproject.toml`. Commit the new `uv.lock` so the next container build syncs cleanly. Dependency changes after that belong to the `python-dependency-management` skill.

## Java settings

| Setting | Value | Purpose |
| --- | --- | --- |
| `mounts` | `${localEnv:HOME}/.m2` → `/home/vscode/.m2` (bind) | Shares the host's Maven repository and settings |
| `mounts` | `${localEnv:HOME}/.gradle` → `/home/vscode/.gradle` (bind) | Shares the host's Gradle caches, wrapper distributions, and settings |
| VS Code extensions | `vscjava.vscode-java-pack`, `vmware.vscode-boot-dev-pack`, `ms-ossdata.vscode-pgsql`, `redhat.vscode-xml`, `redhat.vscode-yaml` | |

## Host prerequisites

Tell the user about these in the report, because the container fails to start without them:

- The Podman secret must exist: `printf '%s' "$(gh auth token)" | podman secret create gh_token -`. Check it with `podman secret ls`.
- The bind-mounted host directories must exist: `mkdir -p ~/.claude ~/.config/gh`, plus `~/.m2` and `~/.gradle` when Java is enabled. Podman creates named volumes on first use.

## Updating an existing file

- If the file uses `build` with a Containerfile or Dockerfile, ask before replacing it with `image`. Move any `ENV` values that the user wants to keep into `containerEnv`.
- Keep other `runArgs` entries, and make sure exactly one `--name` pair, one `/tmp` tmpfs, and one `gh_token` secret are present.
- Add the required extensions and settings to any existing `customizations.vscode` without removing the user's own.
- If a `postCreateCommand` already exists and you are adding the uv sync, chain it (`<existing> && uv sync --locked --all-groups`) rather than replacing the command.
- Keep other `containerEnv` values, mounts, features, and user settings unless they appear on the disallowed list in [base-images.md](base-images.md). Replace a mount that targets the same path with the required one.
- Match the file's existing indentation and comment style.

## Podman notes

- Podman is selected in VS Code, not in devcontainer.json: the user setting `dev.containers.dockerPath` is set to `podman`. With the Dev Container CLI, pass `--docker-path podman`. Don't put either one in the project file.
- The run arguments above are the only required ones. Add the following only when the user asks for them or reports the matching symptom:
  - `--userns=keep-id`: files in bind-mounted folders show the wrong owner under rootless Podman.
  - `--security-opt=label=disable`, or `:z` on bind mounts: SELinux denies access to mounted folders (for example on Fedora or RHEL hosts).
- A fixed `--name` means that only one container with that name can exist. If `podman` reports that the name is already in use, remove the old container (`podman rm <name>`) rather than changing the name.
