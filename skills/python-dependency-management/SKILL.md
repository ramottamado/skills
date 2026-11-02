---
name: python-dependency-management
description: Add, remove, upgrade, sync, or install Python dependencies, and fix dependency problems, in Python >=3.13 projects and multi-project workspaces managed by uv, including dependency groups ([dependency-groups], dev dependencies) and optional extras. Enforces ">=<tested version>" specifiers and keeps workspace members' dependencies a subset of the root's. Use when a pyproject.toml or uv.lock is present and the user asks to add, install, remove, upgrade, or pin a package, mentions pip install, requirements.txt, a dev dependency, a dependency group, a workspace member ([tool.uv.workspace]), or an out-of-date lockfile, or hits a ModuleNotFoundError or resolver conflict. Not for installing Python versions or CLI tools (uv python, uv tool), building or publishing packages, or non-Python dependencies; this repo has no sibling skill for those yet.
---

# Python dependency management

Use this skill to change or repair a Python project's dependencies with uv. uv manages all Python dependencies: `pyproject.toml` declares them, `uv.lock` pins them, and `.venv` is synced from the lockfile.

This skill supports Python >=3.13. Its bundled script requires Python 3.13 or later, and its guidance assumes projects that declare `requires-python = ">=3.13"` or a narrower range.

## Inspect the project

- Read `pyproject.toml`: `[project] dependencies`, `requires-python`, `[project.optional-dependencies]`, `[dependency-groups]`, and `[tool.uv]` (workspace members, `sources`, `index`, `default-groups`, `conflicts`).
- Check that `requires-python` stays within `>=3.13`. If the project allows older Pythons, tell the user it is outside this skill's supported range, and don't raise `requires-python` without their agreement.
- Check for `uv.lock` and `.python-version`, and whether the project is a workspace (`[tool.uv.workspace]` in the root) or a member of one. For workspaces, read [references/workspaces.md](references/workspaces.md) before changing anything.
- Run `uv --version`. Flags change between releases, so confirm any flag you are unsure of with `uv <command> --help`.
- A standalone script with an inline `# /// script` block (PEP 723) takes `uv add --script <file>`, not project commands.
- If the project uses pip, Poetry, or a bare `requirements.txt` without uv, tell the user. Migrate only if they ask, following the [migration guide](https://docs.astral.sh/uv/guides/migration/pip-to-project/).

## Retrieve the docs

Prefer the upstream docs to memorized syntax:

- [Managing dependencies](https://docs.astral.sh/uv/concepts/projects/dependencies/)
- [Locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/)
- [Resolution](https://docs.astral.sh/uv/concepts/resolution/)
- [CLI reference](https://docs.astral.sh/uv/reference/cli/) and [settings reference](https://docs.astral.sh/uv/reference/settings/)

## Apply the change

| Request | Command |
| --- | --- |
| Add a package | `uv add <pkg>` (`--dev`, `--group <name>`, or `--optional <extra>` to target a group or extra; `--package <member>` in a workspace) |
| Remove a package | `uv remove <pkg>` (with the same `--dev`, `--group`, `--optional`, or `--package` flag it was added with) |
| Update one package | `uv lock --upgrade-package <pkg>`, test, then raise the floor with `uv add '<pkg>>=<new>'` |
| Update everything | `uv lock --upgrade`, test, then raise the floor of every direct dependency whose locked version changed |
| Install or sync the environment | `uv sync` |
| Run code in the environment | `uv run <command>` |

Dependency rules:

- **Version rule.** Every versioned requirement, in project dependencies, extras, and dependency groups, is a single lower bound at the tested version: `httpx>=0.28.1`. Don't use `==`, `~=`, `<`, `!=`, or combined ranges. The tested version is the version in `uv.lock` that the tests passed against. `uv add <pkg>` already writes `>=<resolved version>`, so don't pass `--bounds`. After an upgrade, raise the floor to the new tested version. Git, path, URL, and workspace sources carry no version and are exempt. If an existing requirement breaks the rule, report it, and rewrite it only as part of the requested change or with the user's agreement.
- **Subset rule (workspaces).** Every member's `[project] dependencies` must also appear in the root `[project] dependencies`, with the same specifier. Add to the root first, then the member. See [references/workspaces.md](references/workspaces.md).

Command rules:

- Never run `pip install` or `uv pip install` inside a project. They change `.venv` without updating `pyproject.toml` or `uv.lock`, and the next `uv sync` removes the package.
- Never hand-edit `uv.lock`.
- Prefer `uv add` and `uv remove` over editing `pyproject.toml`. If you do edit it by hand, run `uv lock` afterwards.
- Keep `pyproject.toml` and `uv.lock` changes together in the same commit.
- Don't add `[tool.uv]` constraints or overrides without telling the user why.

Read these references when you need them:

- [references/workspaces.md](references/workspaces.md) covers multi-project workspaces: members, `--package`, and adding, removing, or upgrading under the subset rule.
- [references/commands.md](references/commands.md) covers sources (git, path, editable, index), sync flags, `--frozen` and `--locked`, workspaces, `requirements.txt` import and export, and CI or Docker installs.
- [references/dependency-groups.md](references/dependency-groups.md) covers dependency groups, the `dev` group, default groups, extras, and conflicts.
- [references/troubleshooting.md](references/troubleshooting.md) covers resolver failures, stale lockfiles, `ModuleNotFoundError`, build failures, private indexes, and other dependency problems.

## Validate

- `uv run --script <skill-dir>/scripts/check_deps.py <project-root>` enforces the version rule and, in workspaces, the subset rule. `<skill-dir>` is this skill's directory. Fix every `error:` line. A `note:` line marks a root floor below its locked version: after an upgrade, raise that floor.
- `uv lock --check` confirms that the lockfile matches `pyproject.toml`.
- `uv sync --locked` confirms that the environment installs from the lockfile.
- `uv run python -c "import <module>"` smoke-tests a package you added.
- Run the project's tests through `uv run` (for example `uv run pytest`, or `uv run --package <member> pytest` for each affected workspace member). A floor counts as tested only after these pass.

## Report

- List the packages added, removed, or changed, with old and new versions from the `uv.lock` diff, and which groups or extras each one went into.
- Name any constraints, overrides, or sources you added, and why.
- Name any validation you could not run.

## Skill feedback

If the user reports that this skill gave incorrect or outdated guidance, or is missing information, read [references/skill-feedback.md](references/skill-feedback.md).
