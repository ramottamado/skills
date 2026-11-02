# Dependency groups and extras

Upstream: [Development dependencies](https://docs.astral.sh/uv/concepts/projects/dependencies/#development-dependencies), [Dependency groups](https://docs.astral.sh/uv/concepts/projects/dependencies/#dependency-groups), [Optional dependencies](https://docs.astral.sh/uv/concepts/projects/dependencies/#optional-dependencies), [PEP 735](https://peps.python.org/pep-0735/).

## Groups

Dependency groups (PEP 735) are local-only sets of packages, such as tooling for tests, linting, or docs. They are never published in package metadata.

```toml
[dependency-groups]
dev = ["pytest>=8.3.4", {include-group = "lint"}]
lint = ["ruff>=0.8.4"]
docs = ["mkdocs-material>=9.5.49"]
```

- Add: `uv add --group docs mkdocs-material`. `--dev` is shorthand for `--group dev`.
- Remove: `uv remove --group docs mkdocs-material`.
- `{include-group = "..."}` nests one group inside another. The included packages must not conflict with the rest of that group.
- Group entries follow the version rule too: a single `>=<tested version>` floor. `uv add --group` writes that floor.
- Install: `uv sync --group docs`, `uv sync --all-groups`, `uv sync --only-group lint`, or `uv sync --no-dev`. See [commands.md](commands.md#sync-and-install).

### Default groups

`dev` is synced by default. Change that in `[tool.uv]`:

```toml
[tool.uv]
default-groups = ["dev", "lint"]   # or "all"
```

`--no-default-groups` skips them for one command.

### Legacy `tool.uv.dev-dependencies`

`[tool.uv] dev-dependencies` is the old form and is slated for removal. While it exists, uv combines it with `dependency-groups.dev`, and `uv add --dev` writes to it. To migrate, move its entries into `[dependency-groups] dev = [...]`, delete the old key, run `uv lock`, and check that the lockfile contents didn't change.

## Extras

Optional dependencies (`[project.optional-dependencies]`) are published with the package, and consumers install them as `pkg[extra]`.

- Add: `uv add --optional postgres psycopg`.
- Install locally: `uv sync --extra postgres` or `uv sync --all-extras`.

## Group or extra?

- Is it needed only to develop, test, or build docs for this repository? Use a **group**.
- Is it an optional runtime feature for users of the package? Use an **extra**.
- Is the project an application that is never published? Use groups, unless the deployment selects features with extras.

## Conflicts

uv resolves every group and extra together into one lockfile. If two of them can't coexist (for example two CUDA builds of torch), declare them as conflicting so that uv resolves them separately:

```toml
[tool.uv]
conflicts = [
  [{ group = "cpu" }, { group = "cu124" }],
]
# extras use: [{ extra = "cpu" }, { extra = "cu124" }]
```

After declaring a conflict, syncing both members together is an error. Install only one at a time.
