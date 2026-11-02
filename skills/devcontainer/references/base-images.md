# Supported base images and features

These are the only base images and features the skill generates. Extend this file, not `SKILL.md`, when you support another stack. Keep [scripts/check_devcontainer.py](../scripts/check_devcontainer.py) (`JAVA_IMAGE`, `UV_IMAGE`, `REQUIRED_FEATURES`, `DISALLOWED_FEATURES`) in sync with it, and keep the script's env, mount, extension, and setting constants in sync with [devcontainer-json.md](devcontainer-json.md).

## Image by stack

| Stack | `image` | Features beyond the always-on set |
| --- | --- | --- |
| Python | `ghcr.io/astral-sh/uv:<uv-version>-python<python-version>-trixie-slim` | None |
| Python and Java | `ghcr.io/astral-sh/uv:<uv-version>-python<python-version>-trixie-slim` | java |
| Java | `mcr.microsoft.com/devcontainers/java:<java-version>-trixie` | java |

Whenever Python is enabled, use the uv image, even if the project doesn't use uv yet. Don't use an MCR Python image, and don't write a Containerfile: the image is used as-is, and the uv settings go in `containerEnv` (see "Python settings" in [devcontainer-json.md](devcontainer-json.md)).

## The vscode user

`containerUser` and `remoteUser` are always `vscode`. Declare both even when the image already defines the user.

The common-utils feature with `"username": "vscode"` is always added. It creates the `vscode` user and its home directory `/home/vscode`, owned by `vscode`. The uv image has no `vscode` user, so common-utils is what creates it there. On the MCR Java image, the user already exists and common-utils keeps it.

Ownership under `/home/vscode`:

- Named volumes mounted under `/home/vscode` use the Podman mount option `chown=true`. Podman then gives the volume to the container user, so `vscode` can write to it. See "Python settings" in [devcontainer-json.md](devcontainer-json.md).
- Never put `chown=true` on a bind mount of a host directory. Under rootless Podman it recursively changes the owner of the host's files to a container UID, which can lock the user out of their own `~/.claude` or `~/.config/gh`.

## Features

| Feature | When | Options |
| --- | --- | --- |
| `ghcr.io/devcontainers/features/common-utils:2` | Always (creates the `vscode` user) | `"username": "vscode"`, `"installZsh": true`, `"upgradePackages": true` |
| `ghcr.io/devcontainers/features/git:1` | Always | `"version": "os-provided"` |
| `ghcr.io/devcontainers/features/node:2` | Always (claude-code depends on it) | `"version": "lts"` |
| `ghcr.io/anthropics/devcontainer-features/claude-code:1.0` | Always | None |
| `ghcr.io/devcontainers/features/github-cli:1` | Always | None |
| `ghcr.io/ramottamado/devcontainer-features/vscode-extensions-cache:latest` | Always | None |
| `ghcr.io/devcontainers/features/java:1` | Java enabled, including Java only | `"version": "<java-version>"`, plus the build-tool options below |

claude-code needs Node, so the node feature must install first. The claude-code feature declares that ordering itself. If a build fails because `npm` is missing, add `"overrideFeatureInstallOrder"` with the node feature before claude-code.

The java feature always installs last. Whenever Java is enabled, set `"overrideFeatureInstallOrder"` to every feature ID in the config, without its version tag, in this order: common-utils, git, node, claude-code, github-cli, vscode-extensions-cache, any other features, and java last. Features listed there install first and in the given order, so a feature left out of the list would install after java.

## Choosing versions

- Python: use the project's `.python-version`, or the lowest version that `requires-python` allows. Fall back to the newest stable Python that the uv image publishes.
- uv: the reference tag is `0.13.3-python3.14-trixie-slim`. Use the newest uv release that has a `-python<python-version>-trixie-slim` tag.
- Java: use `.java-version`, `maven.compiler.release`, or the Gradle toolchain version. Fall back to the newest LTS. For a Java-only project, confirm that the `<java-version>-trixie` tag exists for the MCR Java image.
- Confirm image tags against the published tag lists before writing them: [uv images](https://docs.astral.sh/uv/guides/integration/docker/#available-images) and the [MCR Java image](https://github.com/devcontainers/images/tree/main/src/java).

## Java build tools

- If `mvnw` or `gradlew` is committed, the wrapper provides the build tool. Don't install Maven or Gradle.
- Otherwise, set `"installMaven": true` for a Maven project or `"installGradle": true` for a Gradle project on the java feature. Check the feature's current option names in its [README](https://github.com/devcontainers/features/tree/main/src/java).

## Disallowed

These assume a Docker daemon, or a build step this skill doesn't use, and break or make no sense under Podman. Never add them, and flag them when you update an existing file:

- `ghcr.io/devcontainers/features/docker-in-docker`
- `ghcr.io/devcontainers/features/docker-outside-of-docker`
- Mounts of `/var/run/docker.sock`
- `dockerComposeFile` based configurations
- `build` / Containerfile or Dockerfile based configurations

Any other image is outside the supported list. If an existing file already uses one, or uses `build`, keep it, apply the naming, user, and feature rules, and ask the user before switching it to a supported image.
