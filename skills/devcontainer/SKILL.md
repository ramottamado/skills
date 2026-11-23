---
name: devcontainer
description: Create or update a VS Code Dev Containers configuration (.devcontainer/devcontainer.json) that runs under Podman, for Python, Java, or mixed Python and Java projects (the uv image for Python, the MCR Java image for Java only) and for projects with neither, such as shell scripts or Containerfiles (the MCR base image). Use when the user asks for a dev container, a devcontainer.json, a .devcontainer folder, or VS Code Dev Containers setup ("Reopen in Container"); signals include pyproject.toml, requirements.txt, pom.xml, build.gradle, or settings.gradle. Not for GitHub Codespaces, JetBrains or other non-VS Code clients, Docker or Docker Compose based devcontainers, Containerfile or Dockerfile builds, or language toolchains other than Python and Java (no sibling skill yet), and not for adding Python packages inside the container (use python-dependency-management).
---

# Devcontainer

Use this skill to write or update the [VS Code Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers) configuration for a Python, Java, or mixed project, or for a project that is neither (the base image with only the always-on settings). The configuration is a single `.devcontainer/devcontainer.json`, with no Containerfile. VS Code opens it with **Dev Containers: Reopen in Container**. The container runs under Podman only. Don't add Docker-specific features, mounts, or settings.

Every generated file follows these rules:

- `name` is the project name with the suffix `-devcontainer` (for example `myapp-devcontainer`), and `runArgs` contains `"--name", "<name>"` with the identical string.
- `containerUser` and `remoteUser` are both `vscode`. The common-utils feature is always added with `"username": "vscode"`, `"userUid": "1000"`, `"userGid": "1000"`, `"installZsh": true`, and `"upgradePackages": true`. It creates the user with UID 1000 and a `/home/vscode` that `vscode` owns. An image that already has a UID 1000 user other than `vscode` breaks the bind mounts under rootless Podman (see "The vscode user" in [references/base-images.md](references/base-images.md)).
- Named volumes use the Podman mount option `chown=true`, so `vscode` owns them. Bind mounts of host directories never use it.
- Always add the git feature (`os-provided`), the node feature (`lts`), the claude-code feature (which depends on node), the github-cli feature (`"installDirectlyFromGitHubRelease": true`), and the vscode-extensions-cache feature.
- Always set `overrideFeatureInstallOrder` so common-utils, node, and claude-code install first, in that order, followed by git, github-cli, and vscode-extensions-cache (and java last, when enabled).
- Always add the run arguments `--tmpfs=/tmp:rw,exec,nosuid,nodev,mode=1777` and the `gh_token` Podman secret as `GH_TOKEN`. Set `CLAUDE_CONFIG_DIR` to `/home/vscode/.claude`, and bind-mount the host's `~/.claude` and `~/.config/gh` into `/home/vscode`.
- If Python is enabled (alone or with Java):
  - Use the `ghcr.io/astral-sh/uv` image, and set the uv variables in `containerEnv`.
  - Mount the volumes `uv-vol` at `/home/vscode/.uv` and `<name>-venv` at `/home/vscode/.venv`.
  - Optionally run `uv sync --locked --all-groups` as the `postCreateCommand`. Add it when the project has a `uv.lock`, unless the user doesn't want it. When there is no `uv.lock`, ask the user whether to add it anyway.
  - Optionally add the Python VS Code extensions and settings. Add them unless the user doesn't want them.
- If Java is enabled:
  - Add the `ghcr.io/devcontainers/features/java:1` feature, and make it install last with `overrideFeatureInstallOrder`.
  - Ask the user whether the project uses Maven, Gradle, both, or neither (infer it from the build files when they make it clear). Optionally bind-mount the matching host directory into `/home/vscode`: `~/.m2` for Maven, `~/.gradle` for Gradle. Add the mount for a Maven or Gradle project, and leave it out when the user doesn't use a build tool or doesn't want it. Podman refuses to start the container if a bind-mount source is missing, so warn the user to create it first.
  - Optionally add the Java VS Code extensions. Add them unless the user doesn't want them.
  - A Java-only project uses `mcr.microsoft.com/devcontainers/java:<java-version>-trixie`.
- If neither is enabled, use `mcr.microsoft.com/devcontainers/base:trixie` with only the always-on features, env, mounts, and run arguments.
- The exact images and features come from [references/base-images.md](references/base-images.md). The env, mounts, extensions, and settings come from [references/devcontainer-json.md](references/devcontainer-json.md).

## Inspect the project

- Detect the stack from the repository root:
  - Python: `pyproject.toml`, `uv.lock`, `requirements*.txt`, `setup.py`, `setup.cfg`, `.python-version`. The container always uses uv. Note whether the project already does (`uv.lock` or `[tool.uv]`), because `uv sync --locked` needs a `uv.lock`.
  - Java: `pom.xml`, `mvnw`, `build.gradle(.kts)`, `settings.gradle(.kts)`, `gradlew`, `.java-version`.
- If neither stack is detected, or the signals are ambiguous (for example a stray `requirements.txt` in a Java repo), ask the user whether the project is Python, Java, both, or neither. Neither is a valid answer: it gets the base image.
- Read the version hints: `requires-python` and `.python-version` for Python; `maven.compiler.release` (or `source`/`target`), `java.toolchain.languageVersion`, and `.java-version` for Java.
- For Java, note the build tool (Maven, Gradle, or both) and whether a wrapper (`mvnw`, `gradlew`) is committed.
- If `.devcontainer/devcontainer.json` already exists, read it and update it in place. Keep the user's other settings (extensions, mounts, env, commands). Ask before replacing the base image, removing a `build` section, or removing anything else.

## Derive the name

Take the first of these that exists:

1. `[project].name` in the root `pyproject.toml`
2. `<artifactId>` of the root `pom.xml` (not the parent's)
3. `rootProject.name` in `settings.gradle` or `settings.gradle.kts`
4. The repository directory name

If a mixed project has different Python and Java names, ask which one to use. Normalize the name into a valid Podman container name: lowercase it, replace every character outside `[a-z0-9_.-]` with `-`, and strip leading characters that are not `[a-z0-9]`. Then append `-devcontainer`, unless the name already ends with it. This is `<name>`: use the same string in `name`, after `--name`, and in the `<name>-venv` volume. For example, a project named `My_App` gives `my_app-devcontainer`, with the volume `my_app-devcontainer-venv`.

If an existing file uses a name without the suffix, rename it, and tell the user. Podman then creates a new container and, for Python, a new empty `<name>-venv` volume; the old container and volume stay until they are removed (`podman rm <old-name>`, `podman volume rm <old-name>-venv`).

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

- `uv run --script <skill-dir>/scripts/check_devcontainer.py <project-root>` checks the rules above. `<skill-dir>` is this skill's directory. Fix every `error:` line, and pass `note:` lines on to the user. An image outside the supported list, or a `build` section, that you kept from an existing file is reported as a `note:`; ask the user whether to switch it.
- If the [Dev Container CLI](https://github.com/devcontainers/cli) is installed, `devcontainer read-configuration --workspace-folder <project-root> --docker-path podman` shows how the CLI resolves the file, including variables such as `${localEnv:HOME}`. It doesn't prove the file is valid: its parser is lenient and exits 0 on malformed JSON, so rely on the checker for that. It needs a working Podman (it runs `podman ps`).
- If the user agrees to a build, `devcontainer up --workspace-folder <project-root> --docker-path podman` proves that the container starts, or the user can run **Dev Containers: Reopen in Container** in VS Code. Then:
  - `podman ps --filter name=<name>` shows the container under the expected name.
  - `podman exec <name> stat -c '%U %n' /home/vscode /home/vscode/.venv /home/vscode/.uv` should print `vscode` for every path.

## Report

- The detected stack, and whether you inferred it or the user confirmed it.
- The container name and the source it came from.
- The base image, user, and features, with the versions you chose and why.
- The host prerequisites (see "Host prerequisites" in [devcontainer-json.md](references/devcontainer-json.md)): the `gh_token` Podman secret and every bind-mounted host directory in the generated file (`~/.claude`, `~/.config/gh`, and `~/.m2` and/or `~/.gradle` for Java). Name each one and give a single `mkdir -p` command for all of them, because Podman fails with `statfs ...: no such file or directory` if any is missing. The checker prints this command as a `note:` line. For Python, also say whether a `uv.lock` exists and whether you added the uv sync `postCreateCommand`. If you added it without a `uv.lock`, give the manual fix (`uv init`, `uv lock`, or `uv sync`) from "Python settings" in [devcontainer-json.md](references/devcontainer-json.md).
- Any existing settings you changed or kept, and any validation you could not run.

## Skill feedback

If the user reports that this skill gave incorrect or outdated guidance, or is missing information, read [references/skill-feedback.md](references/skill-feedback.md).
