---
name: skill-authoring
description: Create, edit, or review a skill in the ramottamado/skills repository (a repo with skills/<name>/SKILL.md and a .claude-plugin/marketplace.json). Use when the user asks to add a new skill, rewrite a skill's description or triggers, split a skill into references, or check a skill against the repo's conventions. Not for skills in other repositories or for personal skills under ~/.claude/skills.
---

# Skill authoring

Use this skill to add or change skills in this repository so they install cleanly through both the Claude Code plugin marketplace and `npx skills`.

## Inspect the repository

- Read `README.md`, `CONTRIBUTING.md`, and the existing `skills/*/SKILL.md` files before writing. Match their tone, length, and structure.
- Check whether an existing skill already covers the request. Extend it or tighten its scope before adding an overlapping skill.

## Write the skill

- Create `skills/<name>/SKILL.md`. Use a kebab-case `name`, and make it match the directory name.
- The frontmatter holds only `name` and `description`.
- Write the `description` as the trigger. Say what the skill does and when to use it, with concrete signals such as file names, tools, or user phrasing. Say when not to use it, and name the sibling skill that covers that case.
- Keep the body short and procedural: inspect the project, retrieve the relevant docs, apply the change, validate, and report what changed.
- Move long or rarely needed detail into `skills/<name>/references/*.md`. Link each file from `SKILL.md` with a relative path, and say when to read it.
- Prefer links to authoritative upstream documentation over copied API signatures, limits, or configuration that will go stale.
- Copy [references/skill-feedback.md](references/skill-feedback.md) into the new skill's `references/` folder and replace the skill name in it. Then end `SKILL.md` with a "Skill feedback" section that links to the copy.

## Register and release

- Add the skill to the skill list in `README.md`.
- Do not register the skill in any manifest. The plugin discovers `skills/*/SKILL.md` automatically.
- For a release, bump `version` in both `.claude-plugin/plugin.json` and the root `plugin.json`, and keep the two files in sync.

## Validate

- Run `claude plugin validate .` from the repository root.
- Install the plugin locally with `/plugin marketplace add ./` and `/plugin install skills@ramottamado`. Confirm that the skill triggers on a representative prompt and stays quiet on a near miss.
- Report the files that changed and any validation you could not run.

## Skill feedback

If the user reports that this skill gave incorrect or outdated guidance, or is missing information, read [references/skill-feedback.md](references/skill-feedback.md).
