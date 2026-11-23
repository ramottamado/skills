# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

A compendium of agent skills written in-house for future development work. The repo is distributed three ways, and every change must keep all of them working:

1. **Claude Code plugin marketplace**: `/plugin marketplace add ramottamado/skills`, then `/plugin install skills@ramottamado`. The marketplace is `ramottamado` and the plugin is `skills`. The license is MIT.
2. **Antigravity plugin**: `agy plugin install https://github.com/ramottamado/skills` (the [Antigravity CLI](https://antigravity.google/docs/plugins/)). Its manifest is `.antigravity-plugin/plugin.json`, and it reads the same `skills/` directory as the other two.
3. **`npx skills`**: `npx skills add https://github.com/ramottamado/skills`

The layout follows [cloudflare/skills](https://github.com/cloudflare/skills). Use that repo as the reference when deciding where something goes.

There is no build step or test suite. The checks are the two manifest validators and the Python linters under "Validating changes". The development environment is `.devcontainer/`, a Python 3.13 uv image (user `vscode`) with Node LTS, Claude Code, and the Dev Container CLI (`devcontainer`) installed. It also mounts the host's `~/.gemini` and installs the Antigravity VS Code extension. The `agy` CLI is at `~/.gemini/bin/agy` (under that mount) and is not on PATH. When you add tooling, document its commands here.

Helper scripts in `skills/*/scripts/` carry PEP 723 metadata. Run them with `uv run --script <path>`. For example, `uv run --script skills/devcontainer/scripts/check_devcontainer.py .` checks this repo's own `.devcontainer/devcontainer.json`. Inside the container, `devcontainer read-configuration` needs a stub engine (see "Validating changes"), and `devcontainer up` needs Podman on the host.

## Scope and testing rules

- This repo is solely for agent skills. It has no application code of its own, so don't add a Python or Java project (`pyproject.toml`, `pom.xml`, `build.gradle`, sources) to the repo root.
- Python and Java in the devcontainer exist only to test the skills. Don't treat them as the repo's own stack. Keep `.devcontainer/` minimal, and don't add build-tool mounts or tooling that only a real project would need.
- Run every test in a temporary scratch project inside the container (for example under the session scratchpad or `mktemp -d`), never in the repo tree. Create fixtures there, point the skill's scripts at that path, and delete it afterwards. Don't commit fixtures, generated rulesets, or tool downloads.

## Structure

```
.claude-plugin/
  marketplace.json   # marketplace catalog; lists plugins, one entry with "source": "./"
  plugin.json        # Claude Code plugin manifest (name, version, description, author, license, keywords)
.antigravity-plugin/
  plugin.json        # Antigravity manifest (same metadata plus displayName)
skills/
  <skill-name>/
    SKILL.md         # required; YAML frontmatter + instructions
    references/      # optional; detail files that SKILL.md links to and loads on demand
    scripts/         # optional; helper scripts the skill runs (Python scripts use PEP 723 metadata, run with `uv run --script`)
README.md            # lists every skill and gives the install commands for each agent
CONTRIBUTING.md
```

Key points:
- **The repo root is the plugin.** `marketplace.json` points at `./`, and Claude Code discovers skills automatically from `skills/*/SKILL.md`. Nothing has to register each skill. Antigravity and `npx skills` read the same `skills/` directory, which is why one tree serves all three install paths.
- **The plugin metadata appears in three places:** `.claude-plugin/marketplace.json`, `.claude-plugin/plugin.json`, and `.antigravity-plugin/plugin.json`. Keep name, description, and version in sync, and bump the version in both `plugin.json` files on release. `agy plugin validate .` checks the Antigravity manifest (see "Validating changes" for how to run it); The logo is `assets/icon.png` (512 px PNG), referenced by `icon` in the Claude manifest and `logo` in the Antigravity one.
- The Claude Code and Antigravity manifests are the two this repo ships. Manifests for other agents are optional additions; cloudflare/skills also ships `.codex-plugin/`, `.cursor-plugin/` and `.agents/plugins/`. If you add any, they mirror the same metadata.

## Skill authoring conventions

- The frontmatter has only `name` and `description`. `name` must match the directory name (kebab-case).
- The `description` is the trigger: it decides when an agent loads the skill. State what the skill does and when to use it, including concrete signals such as file names, tools, or user phrasing. Also state when *not* to use it, and name the sibling skill that covers that case.
- Keep `SKILL.md` lean. Put depth in `references/*.md` and link to it with relative paths so it loads only when needed. Topics with many references can use subfolders, such as `references/<topic>/{README,api,configuration,gotchas,patterns}.md`.
- Link to a local file by its path only, never with a `#anchor` (write `see "Add" in [commands.md](commands.md)`, not `[commands.md](commands.md#add)`). Agents and some editors read the anchor as part of the filename, and the link breaks.
- Prefer links to authoritative upstream docs over copies of API signatures, limits, or config that will go stale. Tell the agent to check the project's installed version and docs rather than trust memorized syntax.
- Each skill's instructions follow this sequence: inspect the project, retrieve the relevant docs, apply the change, validate, and report what changed.
- A new skill must also get a row in the README's skill table.
- Each skill ships a `references/skill-feedback.md` (copy it from `skills/skill-authoring/` and change the skill name), and `SKILL.md` ends with a "Skill feedback" section that links to it.
- The `skill-authoring` skill holds the full checklist for adding a skill. Follow it.

## Validating changes

- `claude plugin validate .` checks the marketplace and plugin manifests. It currently passes with one warning that you can ignore: it says this CLAUDE.md isn't loaded as plugin context, which is intended because it's for working on the repo. 
- `agy plugin validate .` checks the Antigravity manifest. In this devcontainer `agy` is not on PATH, so check `command -v agy` first, then `~/.gemini/bin/agy`, then `find ~/.gemini -name agy -type f` (the location can differ between workspaces). It should print `Validation passed`; run it with `claude plugin validate .` on every release, since both `plugin.json` files carry the version.
- **Python helper scripts** are linted and formatted with `uvx`, so nothing is installed in the repo and no config file is needed. Run both from the repo root; each must come back clean:

  ```
  uvx ruff check --line-length 120 skills/*/scripts/*.py
  uvx black --check --line-length 120 skills/*/scripts/*.py
  ```

  Use `uvx black --line-length 120 <file>` to reformat. A script with a shebang must be executable (`chmod +x`), or ruff reports EXE001. Keep the 120-column limit in the command; don't add a `pyproject.toml` or `ruff.toml` for it.
- **Dev Container CLI parse**: the container has no Podman or Docker, and `devcontainer read-configuration` fails with `spawn docker ENOENT` because it runs `<engine> ps`. Don't mount the host's Podman socket for this. Point `--docker-path` at a stub engine in a scratch directory instead:

  ```
  S=$(mktemp -d) && printf '#!/bin/sh\nexit 0\n' > "$S/podman" && chmod +x "$S/podman"
  devcontainer read-configuration --workspace-folder <project-root> --docker-path "$S/podman"
  rm -rf "$S"
  ```

  This shows how the CLI resolves the config, but its parser is lenient: it exits 0 on malformed JSON (a truncated file, or two strings without a comma). The strict check is the skill's own `check_devcontainer.py`. To prove a container starts, run `devcontainer up --docker-path podman` on the host, against a scratch project.
- To test locally, run `/plugin marketplace add ./` from the repo root, install the plugin, and confirm that the skill triggers on a representative prompt.
