---
name: static-analysis
description: Run static analysis on source code with shared complexity thresholds. Java is checked with PMD and Python with Lizard. One config (static-analysis.toml, or [tool.static-analysis] in pyproject.toml) holds the limits for cyclomatic complexity, cognitive complexity, function length, and parameter count, and a helper script applies them to both tools (PMD reports at ">= level" and Lizard warns at "> limit", so the script handles the off-by-one). Use when the user asks for static analysis, a code complexity check, cyclomatic complexity, a PMD ruleset or pmd check, Lizard or a lizard run, "find the most complex functions", or complexity limits for CI, and the project has .java or .py files. Not for linting or formatting (use the project's own linter), type checking, security scanning, or other languages (no sibling skill yet), and not for installing project dependencies (use python-dependency-management for Python).
---

# Static analysis

Use this skill to run PMD on Java and Lizard on Python with the same complexity limits. Lizard has no config file of its own, and PMD takes its limits from a ruleset XML. A small shared config plus [scripts/static_analysis.py](scripts/static_analysis.py) keeps the two in step.

## Inspect the project

- Detect the languages: `*.java` with `pom.xml` or `build.gradle(.kts)`, and `*.py` with `pyproject.toml`. Analyze only the languages present.
- Look for existing setup before adding any: `static-analysis.toml`, `[tool.static-analysis]` in `pyproject.toml`, a PMD ruleset (`pmd-ruleset.xml`, `ruleset.xml`, `config/pmd/`), the `maven-pmd-plugin` or Gradle `pmd` plugin in the build files, and any `lizard` command in CI or scripts. Extend what exists. Ask before replacing a ruleset the team already maintains.
- Check for the tools: `pmd --version`, and `uv --version` (the script pulls Lizard through uv).

## Retrieve the docs

Check the installed versions and upstream docs instead of trusting memorized syntax:

- PMD: [CLI reference](https://docs.pmd-code.org/latest/pmd_userdocs_cli_reference.html) and the [Java design rules](https://docs.pmd-code.org/latest/pmd_rules_java_design.html). Run `pmd check --help` for the installed version.
- Lizard: [README](https://github.com/terryyin/lizard) and `lizard --help`.
- Read [references/thresholds.md](references/thresholds.md) for how each shared setting maps to a PMD property and a Lizard flag. Read [references/pmd.md](references/pmd.md) for PMD install and Maven or Gradle integration.

## Apply the change

1. **Pick the thresholds.** If the user has no preference, use the defaults (`max_ccn = 10`, `max_nloc = 60`, `max_params = 5`, `max_cognitive = 15`, `max_npath = 200`). For a legacy codebase, ask whether to start at the current worst values and tighten later.
2. **Write the config** to `static-analysis.toml` at the project root. Python projects may use `[tool.static-analysis]` in `pyproject.toml` instead. Keys are listed in [references/thresholds.md](references/thresholds.md). Use `exclude` for generated code and migrations.
3. **Run the analysis.** `<skill-dir>` is this skill's directory:
   - `uv run --script <skill-dir>/scripts/static_analysis.py config <root>` prints the resolved thresholds.
   - `... python <root> [paths]` runs Lizard. `... java <root> [paths]` runs PMD with a generated temporary ruleset. `... all <root>` runs both for the languages present.
4. **Commit a PMD ruleset only when Java builds need one.** `... ruleset <root> -o pmd-ruleset.xml` writes it for Maven, Gradle, or an IDE. Regenerate it whenever the config changes, and don't edit the generated thresholds by hand.
5. Don't silence findings with suppressions or by raising limits to make a run pass, unless the user asks. Report the findings instead.

## Validate

- A non-zero exit means findings (Lizard exit 1, PMD exit 4) or a tool problem (PMD exit 1, 2, or 5; the script returns 2 when `pmd` is missing). Read the output before deciding which.
- Spot-check one reported function at the boundary: a function exactly at the limit must pass, and one above it must fail, in both tools.
- Lizard and PMD count slightly differently (see [references/thresholds.md](references/thresholds.md)), so the same function can differ by a point or two between languages. That's expected.

## Report

- Which languages were analyzed, and which tool and version ran for each.
- The thresholds used and where they came from (the config file or the defaults).
- The findings: file, function, and the metric that exceeded its limit, worst first. Summarize if there are many.
- Files you created or changed, and any run you couldn't do (for example, PMD not installed).

## Skill feedback

If the user reports that this skill gave incorrect or outdated guidance, or is missing information, read [references/skill-feedback.md](references/skill-feedback.md).
