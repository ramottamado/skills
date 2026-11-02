# Troubleshooting dependency problems

Read the full error first, because uv's messages usually name the cause. Fix the declaration, not the environment: a manual change to `.venv` is undone by the next sync. Upstream: [Resolution](https://docs.astral.sh/uv/concepts/resolution/), [Settings](https://docs.astral.sh/uv/reference/settings/).

## No solution found while resolving

uv prints a derivation chain ("Because A depends on B<2 and C depends on B>=2…").

1. Find who requires what: `uv tree --invert --package <pkg>`. Use `uv tree` for the whole graph.
2. Common fixes, in order of preference:
   - Lower the `>=` floor on the package at the root of the chain, but only to a version you then test. The version rule still applies, so don't add an upper bound. Use `constraint-dependencies` instead.
   - Upgrade the dependent that holds the old pin: `uv lock --upgrade-package <dependent>`.
   - Narrow `requires-python` if the conflict involves Python versions uv must also support. uv resolves for the whole `requires-python` range, not just the local interpreter.
   - Limit target platforms with `[tool.uv] environments` if the failure is on a platform you don't ship.
   - Constrain a transitive dependency without depending on it directly: `[tool.uv] constraint-dependencies = ["grpcio<1.65"]`. This is the only place an upper bound belongs. Tell the user, and say what would let it be removed.
   - In a workspace, two members can't need incompatible versions, because they share one lockfile. The subset rule already gives them the same specifier, so fix the conflict at the root.
   - As a last resort, `[tool.uv] override-dependencies = ["werkzeug==2.3.0"]` replaces what dependents declare. Tell the user, with the reason.
3. Prerelease-only packages need `--prerelease allow` or an explicit prerelease specifier.

## Lockfile is out of date

`uv sync --locked` or `uv lock --check` fails because someone edited `pyproject.toml` without relocking. Run `uv lock`, review the diff, and commit both files. If a merge conflict hits `uv.lock`, take either side's version, then run `uv lock` to regenerate it. Don't merge it by hand.

## ModuleNotFoundError or an import of the wrong version

- The code wasn't run through `uv run`, so it used another interpreter. Use `uv run python ...` or `uv run <tool>`.
- `VIRTUAL_ENV` points at a different environment. uv warns about this, so deactivate it or unset the variable.
- The package is in a group or extra that wasn't synced, for example after `--no-dev`. Sync with `--group` or `--extra`.
- The package was installed with `pip` and removed by `uv sync`. Add it with `uv add`.
- The package is missing from `pyproject.toml` and was only present transitively. Add it as a direct dependency if the code imports it.

## Build failures (sdist only, no wheel)

- Check whether a different version ships wheels for the platform, then constrain to it.
- Missing system libraries (compilers, `libpq-dev`, and so on): install them at the OS level and say so in the report.
- The package's build forgets a build dependency: `[tool.uv] extra-build-dependencies = { <pkg> = ["setuptools"] }`.
- The package must build against the installed environment (for example against torch): `[tool.uv] no-build-isolation-package = ["<pkg>"]`, after its build dependencies are installed.
- To pin build tooling, use `build-constraint-dependencies`.

## Platform or marker problems

- The lock fails on a platform you don't support: set `[tool.uv] environments = ["sys_platform == 'linux'"]`.
- A platform needs to be guaranteed wheels: set `required-environments`.
- Add packages that only one platform needs with a marker (see [commands.md](commands.md#add)).

## Private index authentication

- Declare the index in `[[tool.uv.index]]` with a `name`, and pass credentials through `UV_INDEX_<NAME>_USERNAME`, `UV_INDEX_<NAME>_PASSWORD`, `.netrc`, or a keyring.
- Never write tokens into `pyproject.toml`, `uv.lock`, or committed files.
- Upstream: [Index authentication](https://docs.astral.sh/uv/concepts/indexes/#authentication).

## Python version mismatch

- `requires-python` excludes the interpreter, or `.python-version` disagrees with it. Align them with `uv python pin <version>`. Installing interpreters is outside this skill.

## Stale cache or broken environment

- `uv cache clean <pkg>` clears one package's cache. Avoid wiping the whole cache unless necessary.
- If `.venv` is corrupt, delete it and run `uv sync`.
