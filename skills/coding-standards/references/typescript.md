# TypeScript

Check the project's `tsconfig.json` (especially `strict`), ESLint, and Prettier config first, and follow them. See the [TypeScript handbook](https://www.typescriptlang.org/docs/) for current syntax.

- **Naming:** `camelCase` for variables and functions, `PascalCase` for types, interfaces, and classes, `UPPER_SNAKE` for true constants. Name files as the project does, and keep to one convention.
- **Types:** avoid `any`. Use `unknown` for untrusted input and narrow it. Model alternatives with union types and discriminated unions rather than optional fields. Let inference work on locals, and annotate exported function signatures.
- **Immutability:** use `const`, `readonly`, `ReadonlyArray`, and `as const`. Create updated copies with spread (`{ ...user, name }`) instead of mutating shared objects. Remember that `sort`, `reverse`, and `splice` mutate in place; copy first.
- **Errors:** throw `Error` subclasses and keep the cause (`new Error("msg", { cause: err })`). Check `response.ok` after `fetch`. Do not catch an error only to log and replace it with a vaguer one.
- **Async:** use `async`/`await`. Run independent calls together with `Promise.all`, and sequentially only when one depends on another. Never leave a promise unhandled.
- **Validation:** validate data at the boundary (network, files, user input) with a schema library or a type guard. Do not trust a type assertion (`as`) for external data.
- **Rendering conditions (React):** `{count && <X />}` renders `0` when `count` is `0`; compare explicitly (`count > 0 &&`). Prefer early returns or a small component over nested ternaries. For hooks, components, and state, use the project's React guidance.
- **Tests:** arrange, act, assert, with behavior-describing names.
