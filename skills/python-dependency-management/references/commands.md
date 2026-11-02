# uv dependency commands

Detail for adding, removing, updating, syncing, and installing. Confirm flags against `uv <command> --help` for the installed version. Upstream: [Managing dependencies](https://docs.astral.sh/uv/concepts/projects/dependencies/), [Locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/).

## Add

- `uv add httpx` writes `httpx>=<resolved version>`, then locks and syncs. That lower bound is the form the version rule requires. Don't pass `--bounds`, which writes upper bounds or exact pins.
- To require a newer floor, pass it explicitly: `uv add 'httpx>=0.28.1'`. Never add `<`, `==`, `~=`, or `!=`.
- Add platform-specific packages with markers: `uv add 'pywin32>=308; sys_platform == "win32"'`.
- `uv add -r requirements.txt` imports an existing requirements file. Afterwards, rewrite any `==` or range pins it brings in to `>=<locked version>`.
- In a workspace, `uv add --package <member> <pkg>` targets a member. Add the package to the root first, as described in [workspaces.md](workspaces.md).
- Targets: `--dev`, `--group <name>`, `--optional <extra>`. See [dependency-groups.md](dependency-groups.md).

### Sources

Non-registry sources are recorded in `[tool.uv.sources]`, and the requirement in `[project]` stays a plain name:

- Git: `uv add git+https://github.com/org/repo --tag v1.2.0` (or `--branch`, `--rev`)
- Local path: `uv add ../libs/mylib`. Add `--editable` for an editable install.
- Workspace member: `uv add <member>` from the workspace root writes `{ workspace = true }`.
- A custom index goes in `[[tool.uv.index]]`, and `uv add <pkg> --index <name>=<url>` pins the package to it. Keep credentials out of the file. See [troubleshooting.md](troubleshooting.md#private-index-authentication).

Upstream: [Dependency sources](https://docs.astral.sh/uv/concepts/projects/dependencies/#dependency-sources), [Package indexes](https://docs.astral.sh/uv/concepts/indexes/).

## Remove

- `uv remove httpx`. Pass the same `--dev`, `--group`, or `--optional` flag the package was declared under.
- If the package is still needed transitively, it stays in `uv.lock`. Check with `uv tree --invert --package httpx`.

## Update

- One package: `uv lock --upgrade-package httpx`. Repeat the flag for several packages, or use `--upgrade-package 'httpx==0.28.1'` to target a version (this is a lock argument, not a specifier written to `pyproject.toml`). This changes only the lockfile, so run `uv sync` afterwards.
- Everything: `uv lock --upgrade`. Review the diff, because it can be large.
- Run the tests, then raise each upgraded direct dependency's floor to its new locked version: `uv add 'httpx>=0.28.1'`. In a workspace, do this in the root and in every member that declares the package. The floors in `pyproject.toml` then record what was tested.
- `uv tree --outdated` shows which packages have newer releases.

## Sync and install

`uv sync` makes `.venv` match the lockfile exactly and removes packages that aren't in it. `uv run` syncs automatically before running.

| Flag | Effect |
| --- | --- |
| `--locked` | Fail if `uv.lock` is out of date instead of updating it (use this in CI) |
| `--frozen` | Use `uv.lock` as-is without checking it against `pyproject.toml` |
| `--no-dev` | Skip the `dev` group |
| `--group <name>` / `--all-groups` | Also install a named group, or every group |
| `--only-group <name>` | Install only that group, without the project or default groups |
| `--no-default-groups` | Skip `default-groups` |
| `--extra <name>` / `--all-extras` | Include optional extras |
| `--inexact` | Keep packages that aren't in the lockfile |
| `--no-install-project` | Install dependencies but not the project itself (useful for Docker layer caching) |
| `--package <member>` | Sync one workspace member |
| `--all-packages` | Sync every workspace member (confirm with `uv sync --help`) |

`--no-sync` on `uv add`, `uv remove`, and `uv run` updates the lockfile without touching `.venv`.

## Export

- `uv export --format requirements.txt -o requirements.txt` produces a pinned file for tools that need one. Add `--no-dev`, `--group`, or `--extra` as needed, and `--no-hashes` if the consumer can't handle hashes.
- The exported file is derived output. Regenerate it after every lock change and never edit it by hand.

## CI and Docker

- CI: `uv sync --locked`, then `uv run pytest`. Cache uv's cache directory, not `.venv`.
- Docker: copy `pyproject.toml` and `uv.lock`, run `uv sync --locked --no-install-project`, then copy the source and run `uv sync --locked`. See the [Docker guide](https://docs.astral.sh/uv/guides/integration/docker/).
