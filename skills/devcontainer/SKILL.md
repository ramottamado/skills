---
name: devcontainer
description: Create or update a VS Code Dev Containers configuration (.devcontainer/devcontainer.json) for Python, Java, or mixed Python and Java projects that run under Podman. Names the container after the project, puts a matching --name in runArgs, always declares containerUser and remoteUser as vscode (created by the common-utils feature), uses the uv image for Python and the MCR Java image for Java-only projects, and adds the required features, env, mounts, secrets, VS Code extensions, and settings. Python projects can also run uv sync on create. Use when the user asks for a dev container, a devcontainer.json, a .devcontainer folder, or VS Code Dev Containers setup ("Reopen in Container"), and the project has signals such as pyproject.toml, requirements.txt, pom.xml, build.gradle, or settings.gradle. Not for GitHub Codespaces, the JetBrains or other non-VS Code clients, Docker or Docker Compose based devcontainers, Containerfile or Dockerfile builds, or other languages (no sibling skill yet), and not for adding Python packages inside the container (use python-dependency-management).
---

# Devcontainer

Use this skill to write or update the [VS Code Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers) configuration for a Python, Java, or mixed project. The configuration is a single `.devcontainer/devcontainer.json`, with no Containerfile. VS Code opens it with **Dev Containers: Reopen in Container**. The container runs under Podman only. Don't add Docker-specific features, mounts, or settings.

Every generated file follows these rules:

- `name` is the project name, and `runArgs` contains `"--name", "<name>"` with the identical string.
- `containerUser` and `remoteUser` are both `vscode`. The common-utils feature is always added with `"username": "vscode"`, `"installZsh": true`, and `"upgradePackages": true`. It creates the user and a `/home/vscode` that `vscode` owns.
- Named volumes use the Podman mount option `chown=true`, so `vscode` owns them. Bind mounts of host directories never use it.
- Always add the git feature (`os-provided`), the node feature (`lts`), the claude-code feature (which depends on node), the github-cli feature, and the vscode-extensions-cache feature.
- Always add the run arguments `--tmpfs=/tmp:rw,exec,nosuid,nodev,mode=1777` and the `gh_token` Podman secret as `GH_TOKEN`. Set `CLAUDE_CONFIG_DIR` to `/home/vscode/.claude`, and bind-mount the host's `~/.claude` and `~/.config/gh` into `/home/vscode`.
- If Python is enabled (alone or with Java):
  - Use the `ghcr.io/astral-sh/uv` image, and set the uv variables in `containerEnv`.
  - Mount the volumes `uv-vol` at `/home/vscode/.uv` and `<name>-venv` at `/home/vscode/.venv`.
  - Optionally run `uv sync --locked --all-groups` as the `postCreateCommand`. Add it when the project has a `uv.lock`, unless the user doesn't want it. When there is no `uv.lock`, ask the user whether to add it anyway.
  - Add the Python VS Code extensions and settings.
- If Java is enabled:
  - Add the `ghcr.io/devcontainers/features/java:1` feature, and make it install last with `overrideFeatureInstallOrder`.
  - Bind-mount the host's `~/.m2` and `~/.gradle` into `/home/vscode`.
  - Add the Java VS Code extensions.
  - A Java-only project uses `mcr.microsoft.com/devcontainers/java:<java-version>-trixie`.
- The exact images and features come from [references/base-images.md](references/base-images.md). The env, mounts, extensions, and settings come from [references/devcontainer-json.md](references/devcontainer-json.md).

## Inspect the project

- Detect the stack from the repository root:
  - Python: `pyproject.toml`, `uv.lock`, `requirements*.txt`, `setup.py`, `setup.cfg`, `.python-version`. The container always uses uv. Note whether the project already does (`uv.lock` or `[tool.uv]`), because `uv sync --locked` needs a `uv.lock`.
  - Java: `pom.xml`, `mvnw`, `build.gradle(.kts)`, `settings.gradle(.kts)`, `gradlew`, `.java-version`.
- If neither stack is detected, or the signals are ambiguous (for example a stray `requirements.txt` in a Java repo), ask the user whether the project is Python, Java, or both.
- Read the version hints: `requires-python` and `.python-version` for Python; `maven.compiler.release` (or `source`/`target`), `java.toolchain.languageVersion`, and `.java-version` for Java.
- For Java, note the build tool (Maven or Gradle) and whether a wrapper (`mvnw`, `gradlew`) is committed.
- If `.devcontainer/devcontainer.json` already exists, read it and update it in place. Keep the user's other settings (extensions, mounts, env, commands). Ask before replacing the base image, removing a `build` section, or removing anything else.

## Derive the name

Take the first of these that exists:

1. `[project].name` in the root `pyproject.toml`
2. `<artifactId>` of the root `pom.xml` (not the parent's)
3. `rootProject.name` in `settings.gradle` or `settings.gradle.kts`
4. The repository directory name

If a mixed project has different Python and Java names, ask which one to use. Normalize the name into a valid Podman container name: lowercase it, replace every character outside `[a-z0-9_.-]` with `-`, and strip leading characters that are not `[a-z0-9]`. Use the same normalized string in `name`, after `--name`, and in the `<name>-venv` volume.

## Retrieve the docs

Check current tags and options upstream instead of trusting memorized values:

- [devcontainer.json reference](https://containers.dev/implementors/json_reference/) and [VS Code Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers)
- [uv Docker images](https://docs.astral.sh/uv/guides/integration/docker/) and the [MCR Java image](https://github.com/devcontainers/images/tree/main/src/java), including their tag lists
- Feature options: [java](https://github.com/devcontainers/features/tree/main/src/java), [common-utils](https://github.com/devcontainers/features/tree/main/src/common-utils), [git](https://github.com/devcontainers/features/tree/main/src/git), [node](https://github.com/devcontainers/features/tree/main/src/node), and [claude-code](https://github.com/anthropics/devcontainer-features)
- [VS Code: use Podman with Dev Containers](https://code.visualstudio.com/remote/advancedcontainers/docker-options#_podman), and the `--mount` options (including `chown`) in `man podman-run`

## Apply the change

1. Pick the image and features for the detected stack from [references/base-images.md](references/base-images.md).
2. Write `.devcontainer/devcontainer.json` using the matching template in [references/devcontainer-json.md](references/devcontainer-json.md).
3. Add only what the project needs. Don't add `--userns`, SELinux, or other Podman flags unless the user asks for them. [references/devcontainer-json.md](references/devcontainer-json.md) covers those options.

## Validate

- `uv run --script <skill-dir>/scripts/check_devcontainer.py <project-root>` checks the rules above. `<skill-dir>` is this skill's directory. Fix every `error:` line, and pass `note:` lines on to the user.
- If the [Dev Container CLI](https://github.com/devcontainers/cli) is installed, `devcontainer read-configuration --workspace-folder <project-root> --docker-path podman` confirms that the file parses.
- If the user agrees to a build, `devcontainer up --workspace-folder <project-root> --docker-path podman` proves that the container starts, or the user can run **Dev Containers: Reopen in Container** in VS Code. Then:
  - `podman ps --filter name=<name>` shows the container under the expected name.
  - `podman exec <name> stat -c '%U %n' /home/vscode /home/vscode/.venv /home/vscode/.uv` should print `vscode` for every path.

## Report

- The detected stack, and whether you inferred it or the user confirmed it.
- The container name and the source it came from.
- The base image, user, and features, with the versions you chose and why.
- The host prerequisites (see "Host prerequisites" in [devcontainer-json.md](references/devcontainer-json.md)): the `gh_token` Podman secret and the bind-mounted directories. For Python, also say whether a `uv.lock` exists and whether you added the uv sync `postCreateCommand`. If you added it without a `uv.lock`, give the manual fix (`uv init`, `uv lock`, or `uv sync`) from "Python settings" in [devcontainer-json.md](references/devcontainer-json.md).
- Any existing settings you changed or kept, and any validation you could not run.

## Skill feedback

If the user reports that this skill gave incorrect or outdated guidance, or is missing information, read [references/skill-feedback.md](references/skill-feedback.md).
