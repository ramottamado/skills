# PMD setup

Read this when `pmd` is missing or the Java project should run PMD from its build.

## Standalone CLI

- Download the binary release from the [PMD releases page](https://github.com/pmd/pmd/releases), unzip it, and put its `bin/` directory on `PATH`. PMD needs a JRE (check the release notes for the minimum Java version).
- In a dev container, the Java feature already provides the JRE. See the `devcontainer` skill for the container itself.
- Confirm with `pmd --version`.
- Command shape: `pmd check -d <src> -R <ruleset.xml> -f text`. Add `--cache <file>` for incremental runs. Exit code 4 means violations, and 5 means a recoverable error such as a parse failure. See the [CLI reference](https://docs.pmd-code.org/latest/pmd_userdocs_cli_reference.html).

## Build integration

If the project already uses a build plugin, point it at the generated ruleset instead of adding the CLI:

- Maven: [maven-pmd-plugin](https://maven.apache.org/plugins/maven-pmd-plugin/) with `<rulesets><ruleset>pmd-ruleset.xml</ruleset></rulesets>`.
- Gradle: the [pmd plugin](https://docs.gradle.org/current/userguide/pmd_plugin.html) with `ruleSetFiles = files("pmd-ruleset.xml")` and `ruleSets = []`.

Generate the file with `uv run --script <skill-dir>/scripts/static_analysis.py ruleset <root> -o pmd-ruleset.xml`. Check the plugin's PMD version against the rule names in the generated file, because older PMD 6 releases use different property names.

## Adding more rules

The generated ruleset holds only the complexity rules. To add other PMD rules, create a second ruleset the team owns and pass both to `-R` (comma-separated). Don't merge hand edits into the generated file.
