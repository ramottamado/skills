---
name: coding-standards
description: Apply baseline, language-neutral coding conventions (naming, readability, error handling, immutability, constants, comments, tests) when writing, refactoring, or reviewing code in Python, Java, or TypeScript. Use when the user asks for a code review, a style or quality pass, naming or readability cleanup, "follow best practices", or conventions for a new module. Not for linter or formatter configuration, complexity limits, or finding complex functions (use static-analysis), framework- or architecture-specific design, or dependency changes (use python-dependency-management).
---

# Coding standards

A shared floor of conventions. The project's own rules always win over this skill.

## Workflow

1. **Inspect the project.** Find its linter, formatter, and type-checker config (`pyproject.toml`, `.editorconfig`, `checkstyle.xml`, `eslint` config), its contributing docs, and the surrounding code. Match the existing style. Where the project and this skill disagree, follow the project.
2. **Retrieve the language detail.** Read the matching file only: [python.md](references/python.md), [java.md](references/java.md), or [typescript.md](references/typescript.md). For the language's own style rules, prefer its official guide (PEP 8, Google Java Style, the TypeScript handbook) over memorized syntax.
3. **Apply.** Make the smallest change that meets the principles below. In a review, report findings and do not rewrite code the user did not ask you to change.
4. **Validate.** Run the project's formatter, linter, type-checker, and tests. For complexity and function-size limits, use `static-analysis` instead of picking numbers here.
5. **Report.** List what changed and why, which checks ran, and anything you left alone because the project's conventions differ.

## Principles

### Naming
- Names say what a thing is or does: `retryCount`, `isExpired`, `fetch_invoice`, not `n`, `flag`, `doIt`.
- Functions are verbs, values and types are nouns, booleans read as questions (`is`, `has`, `can`).
- Use the language's casing convention and the project's vocabulary. One concept gets one name.

### Readability, KISS, YAGNI
- Write for the next reader. Pick the simplest code that works over the clever one.
- Do not build for needs that do not exist yet. Add abstraction when a second real use appears.
- Prefer early returns and guard clauses over deep nesting. Extract a well-named function when a block needs a comment to explain what it does.

### DRY, without overdoing it
- Remove duplicated logic that must change together. Leave coincidental similarity alone: a wrong shared abstraction costs more than a copy.

### Errors
- Handle errors where you can act on them, and let them propagate otherwise. Never swallow an exception silently.
- Keep the cause when you wrap or rethrow (`raise ... from err`, `new X(msg, cause)`, `new Error(msg, { cause })`).
- Fail early on invalid input with a message that names the value and the expectation. Do not log and rethrow the same error at every layer.
- Never put secrets or personal data in error messages or logs.

### State and mutation
- Default to immutable values and `final`/`const`/frozen types. Do not mutate arguments the caller still owns.
- Mutate deliberately, for example in a hot loop or a builder, and say why in a short comment.

### Constants
- Give magic numbers and repeated strings a named constant that includes the unit (`TIMEOUT_SECONDS`).

### Comments
- Comment why, not what: the constraint, the trade-off, the link to the bug. Delete comments that restate the code.
- Document public APIs: purpose, parameters, return value, and what can be raised or thrown.

### Tests
- Structure each test as arrange, act, assert. Test one behavior per test.
- Name tests for the behavior: `returns_empty_list_when_no_match`, not `test_search`.
- Cover the edge and failure paths, not just the happy path.

## Review checklist

When reviewing, check in this order: correctness and error paths, naming and clarity, duplication, hidden mutation, missing tests, then style the formatter would catch. Report style-only findings last and only if the project has no formatter.

## Skill feedback

If the user reports that this skill gave incorrect or outdated guidance, or is missing information, read [references/skill-feedback.md](references/skill-feedback.md).
