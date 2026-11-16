# Java

Check the project's formatter and checks first (Checkstyle, Spotless, PMD, `.editorconfig`), and follow the [Google Java Style Guide](https://google.github.io/styleguide/javaguide.html) or the project's existing style where it is silent. Check the project's Java version before using newer language features.

- **Naming:** `lowerCamelCase` for methods and fields, `UpperCamelCase` for types, `UPPER_SNAKE` for `static final` constants, lowercase package names.
- **Immutability:** make fields `final`, prefer immutable value types (`record`) and `List.of`/`Map.of` for unmodifiable collections, and copy mutable inputs defensively.
- **Null handling:** do not return `null` for "nothing"; return `Optional` for single values and an empty collection for lists. Validate arguments with `Objects.requireNonNull`. Do not use `Optional` as a field or parameter type.
- **Errors:** catch the narrowest exception. Wrap with the cause (`new XException(msg, cause)`). Use unchecked exceptions for programming errors and checked ones only when the caller can recover. Never leave a `catch` block empty.
- **Resources:** use try-with-resources for anything `AutoCloseable`.
- **Collections and streams:** declare variables by interface (`List`, `Map`). Use a stream for a clear transform, and a loop when the stream needs side effects or nested lambdas.
- **Logging:** use SLF4J with parameterized messages (`log.info("id={}", id)`), not string concatenation or `System.out`.
- **Javadoc:** on public types and methods, with `@param`, `@return`, and `@throws`.
- **Tests:** JUnit 5 with descriptive method names. Prefer real objects over mocks for simple collaborators.
