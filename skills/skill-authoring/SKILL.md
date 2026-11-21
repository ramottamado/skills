---
name: skill-authoring
description: Create, edit, or review a skill in the ramottamado/skills repository (a repo with a skills folder of SKILL.md files and a .claude-plugin/marketplace.json). Use when the user asks to add a new skill, rewrite a skill's description or triggers, split a skill into references, or check a skill against the repo's conventions. Not for skills in other repositories or for personal skills under ~/.claude/skills.
---

# Skill authoring

Use this skill to add or change skills in this repository so they install cleanly through the Claude Code plugin marketplace, the Antigravity plugin (`agy`), and `npx skills`.

## Inspect the repository

- Read `README.md`, `CONTRIBUTING.md`, and the existing `skills/*/SKILL.md` files before writing. Match their tone, length, and structure.
- Check whether an existing skill already covers the request. Extend it or tighten its scope before adding an overlapping skill.

## Write the skill

- Create `skills/<name>/SKILL.md`. Use a kebab-case `name`, and make it match the directory name.
- The frontmatter holds only `name` and `description`.
- Write the `description` as the trigger. Say what the skill does and when to use it, with concrete signals such as file names, tools, or user phrasing. Say when not to use it, and name the sibling skill that covers that case.
- Keep the `description` under 1,024 characters (the Agent Skills limit; the validators don't check it) and free of tag-like text such as `<name>`, which some skill uploads reject. Leave implementation detail to the body.
- Keep the body short and procedural: inspect the project, retrieve the relevant docs, apply the change, validate, and report what changed.
- Move long or rarely needed detail into `skills/<name>/references/*.md`. Link each file from `SKILL.md` with a relative path, and say when to read it.
- Link to a local file by its path only, never with a `#anchor`. To point at a section, name it in the text, as in `see "Add" in [commands.md](commands.md)`. Agents and some editors read the anchor as part of the filename, and the link breaks.
- Prefer links to authoritative upstream documentation over copied API signatures, limits, or configuration that will go stale.
- Copy [references/skill-feedback.md](references/skill-feedback.md) into the new skill's `references/` folder and replace the skill name in it. Then end `SKILL.md` with a "Skill feedback" section that links to the copy.

## Register and release

- Add the skill to the skill list in `README.md`.
- Do not register the skill in any manifest. The plugin discovers `skills/*/SKILL.md` automatically.
- For a release, bump `version` in `.claude-plugin/plugin.json`, and `.antigravity-plugin/plugin.json`, and keep the two in sync.

## Validate

- Run `claude plugin validate .` from the repository root.
- Run `agy plugin validate .`. Find `agy` first (`command -v agy`); if it is not on `PATH`, look for it in `~/.gemini/bin/agy` (where this repo's devcontainer keeps it), then search the Antigravity data folder (`find ~/.gemini -name agy -type f`), since the location can differ between workspaces, before concluding it is not installed, and say so in your report if you cannot run it. It should pass, including with `--strict`.
- If the skill ships Python scripts under `skills/<name>/scripts/`, lint and format them from the repository root, and fix what they report: `uvx ruff check --line-length 120 skills/*/scripts/*.py` and `uvx black --check --line-length 120 skills/*/scripts/*.py`. Give any script that has a shebang the executable bit (`chmod +x`). Run each script's `--help` or a representative case in a scratch directory, not in the repo tree.
- Install the plugin locally with `/plugin marketplace add ./` and `/plugin install skills@ramottamado`. Confirm that the skill triggers on a representative prompt and stays quiet on a near miss.
- Report the files that changed and any validation you could not run.

## Skill feedback

If the user reports that this skill gave incorrect or outdated guidance, or is missing information, read [references/skill-feedback.md](references/skill-feedback.md).
