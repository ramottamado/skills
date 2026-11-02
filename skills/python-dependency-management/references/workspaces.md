# Workspaces

A uv workspace is several projects (members) that share one `uv.lock` and one `.venv` at the workspace root. Upstream: [Workspaces](https://docs.astral.sh/uv/concepts/projects/workspaces/).

```toml
# root pyproject.toml
[project]
name = "acme"
dependencies = ["httpx>=0.28.1", "pydantic>=2.10.3", "acme-core"]

[tool.uv.workspace]
members = ["packages/*"]
exclude = ["packages/experimental"]

[tool.uv.sources]
acme-core = { workspace = true }
```

## Inspect

- Read `[tool.uv.workspace]` in the root `pyproject.toml` to find the members, then read each member's `pyproject.toml`.
- Run uv commands from the workspace root. Target a member with `--package <name>` (`uv add`, `uv remove`, `uv sync`, `uv run`, `uv tree`).
- Members depend on each other by name, with `{ workspace = true }` in `[tool.uv.sources]`. These are exempt from both rules below.
- If the root has no `[project]` table (a virtual workspace), the subset rule has nothing to check against. Stop and ask the user where workspace dependencies should be declared.

## Subset rule

**Every member's `[project] dependencies` must also appear in the root `[project] dependencies`, with the same specifier.** The root is the single list of every third-party runtime dependency in the workspace, and its floors are the tested versions.

- The rule covers `[project] dependencies` only. Dependency groups and extras still follow the version rule, but they don't have to appear in the root.
- Markers may differ (a member can need a package only on one platform), but the version specifier must match.

### Add a dependency to a member

1. If the root doesn't declare it yet, add it there first: `uv add <pkg>`. This writes `<pkg>>=<resolved version>`.
2. Add it to the member with the root's exact specifier: `uv add --package <member> '<pkg>>=<root floor>'`.
3. Run the tests (see [Validate](#validate)). The floor is now the tested version.

### Remove a dependency from a member

1. `uv remove --package <member> <pkg>`.
2. Leave the root entry in place if another member, or the root's own code, still uses the package. Search the members' `pyproject.toml` files and the root's imports. Remove it from the root (`uv remove <pkg>`) only when nothing uses it.

### Upgrade a dependency

1. `uv lock --upgrade-package <pkg>`, then run the tests.
2. Raise the floor to the newly tested version in the root and in **every** member that declares it, with `uv add '<pkg>>=<new>'` and `uv add --package <member> '<pkg>>=<new>'`. Read the new version from `uv.lock`.

## Validate

- Run the bundled checker from the workspace root. It enforces the subset rule and the version rule, and notes root floors that are below the locked version:

  ```
  uv run --script <skill-dir>/scripts/check_deps.py .
  ```

  `<skill-dir>` is this skill's directory, the folder that contains `SKILL.md`.
- `uv lock --check` and `uv sync --locked --all-packages`.
- Test each affected member: `uv run --package <member> pytest`.
