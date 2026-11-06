# Shared thresholds

The config file is `static-analysis.toml` at the project root, or `[tool.static-analysis]` in `pyproject.toml` when there is no standalone file. Example:

```toml
max_ccn = 10
max_nloc = 60
max_params = 5
max_cognitive = 15
max_npath = 200
exclude = ["*/generated/*", "*/migrations/*"]
```

Every `max_*` value is the largest value still allowed. A function at the limit passes, and one above it fails.

| Key | Default | PMD (Java) | Lizard (Python) |
| --- | --- | --- | --- |
| `max_ccn` | 10 | `CyclomaticComplexity` `methodReportLevel` = max + 1 | `-C max` |
| `max_cognitive` | 15 | `CognitiveComplexity` `reportLevel` = max + 1 | `-Ecognitive -T cognitive_complexity=max` |
| `max_nloc` | 60 | `NcssCount` `methodReportLevel` = max + 1 | `-T nloc=max` |
| `max_params` | 5 | `ExcessiveParameterList` `minimum` = max + 1 | `-a max` |
| `max_npath` | 200 | `NPathComplexity` `reportLevel` = max + 1 | not available |
| `exclude` | none | `--exclude` | `-x` |

## Why max + 1 for PMD

PMD's rules report a method when its metric is `>=` the level (checked against the rule sources: `cyclo >= methodReportLevel`, `cognitive >= reportLevel`, `npath >= reportLevel`, `methodSize >= level`, and the parameter-count rule's `minimum`). Lizard warns when the metric is above the limit. The script adds 1 on the PMD side so both tools agree on what "allowed" means.

## Known differences between the tools

- **Cyclomatic complexity.** Both count decision points plus one. Both count `&&` and `||`. PMD's `cycloOptions` (for example ignoring boolean paths) changes the count, and Lizard's `-m` counts a switch with several cases as one. The script uses neither, so the defaults of both tools apply. Check the rule docs before adding either.
- **Length.** PMD's NCSS counts statements. Lizard's NLOC counts non-blank, non-comment lines. They agree roughly, not exactly.
- **Class-level rules.** `CyclomaticComplexity` and `NcssCount` also have `classReportLevel` (PMD defaults 80 and 1500). The script leaves those at PMD's defaults.
- **NPath** has no Lizard equivalent, so `max_npath` affects Java only.
- **Parameters.** Lizard counts every parameter. PMD's `ExcessiveParameterList` skips private constructors.

## Lizard has no config file

Lizard 1.x reads flags only; it has no `.lizardrc` or pyproject section. If the user wants plain Lizard in CI without this script, give them the equivalent command from the table, for example `lizard -l python -w -C 10 -a 5 -T nloc=60 -x "*/migrations/*" .`, and note the config can then drift from the Java side.
