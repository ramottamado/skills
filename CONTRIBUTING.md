# Contributing

Keep skills small. Their job is to point agents to the right documentation, not to maintain another copy of it.

- Each skill lives in `skills/<name>/SKILL.md`. Its frontmatter holds only `name` and `description`, and `name` matches the directory.
- The `description` decides when an agent loads the skill. State what the skill does, when to use it, and when not to.
- Put long or rarely needed detail in `skills/<name>/references/` and link to it from `SKILL.md`.
- Link to authoritative upstream documentation instead of copying API signatures, limits, or configuration that can go stale.
- Add every new skill to the table in `README.md`. Skills are discovered automatically, so the manifests need no change.
- On release, bump `version` in both `.claude-plugin/plugin.json` and `plugin.json`.
- Before opening a pull request, run `claude plugin validate .` and try the skill locally with `/plugin marketplace add ./`.
