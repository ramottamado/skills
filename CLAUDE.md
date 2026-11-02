# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

A compendium of agent skills written in-house for future development work. The repo is distributed two ways, and every change must keep both working:

1. **Claude Code plugin marketplace**: `/plugin marketplace add ramottamado/skills`, then `/plugin install skills@ramottamado`. The marketplace is `ramottamado` and the plugin is `skills`. The license is MIT.
2. **`npx skills`**: `npx skills add https://github.com/ramottamado/skills`

The layout follows [cloudflare/skills](https://github.com/cloudflare/skills). Use that repo as the reference when deciding where something goes.

There is no build, lint, or test tooling. The development environment is `.devcontainer/`, a Python 3.13 uv image (user `vscode`) with Node LTS, Claude Code, and the Dev Container CLI (`devcontainer`) installed. When you add tooling, document its commands here.

Helper scripts in `skills/*/scripts/` carry PEP 723 metadata. Run them with `uv run --script <path>`. For example, `uv run --script skills/devcontainer/scripts/check_devcontainer.py .` checks this repo's own `.devcontainer/devcontainer.json`. Inside the container, `devcontainer read-configuration --workspace-folder .` confirms the file parses, but `devcontainer up` needs Podman on the host.

## Structure

```
.claude-plugin/
  marketplace.json   # marketplace catalog; lists plugins, one entry with "source": "./"
  plugin.json        # Claude Code plugin manifest (name, version, description, author, license, keywords)
plugin.json          # agent-agnostic manifest ($schema: agent-plugins.org plugin schema), same metadata
skills/
  <skill-name>/
    SKILL.md         # required; YAML frontmatter + instructions
    references/      # optional; detail files that SKILL.md links to and loads on demand
    scripts/         # optional; helper scripts the skill runs (Python scripts use PEP 723 metadata, run with `uv run --script`)
README.md            # lists every skill and gives the install commands for each agent
CONTRIBUTING.md
```

Key points:
- **The repo root is the plugin.** `marketplace.json` points at `./`, and Claude Code discovers skills automatically from `skills/*/SKILL.md`. Nothing has to register each skill. `npx skills` reads the same `skills/` directory, which is why one tree serves both install paths.
- **The plugin metadata appears in three places:** `.claude-plugin/marketplace.json`, `.claude-plugin/plugin.json`, and the root `plugin.json`. Keep name, description, and version in sync, and bump the version in both `plugin.json` files on release.
- Manifests for other agents are optional additions; cloudflare/skills ships one each for `.codex-plugin/`, `.cursor-plugin/`, `.agents/plugins/`, and `.antigravity-plugin/`. If you add any, they mirror the same metadata.

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

- `claude plugin validate .` checks the marketplace and plugin manifests. It currently passes with two warnings that you can ignore. One says this CLAUDE.md isn't loaded as plugin context, which is intended because it's for working on the repo. The other says there is no plugin icon (a square PNG of 512–2048 px), which only matters for a plugin directory listing.
- To test locally, run `/plugin marketplace add ./` from the repo root, install the plugin, and confirm that the skill triggers on a representative prompt.
