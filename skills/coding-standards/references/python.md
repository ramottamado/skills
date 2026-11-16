# Python

Check the project's `pyproject.toml` (ruff, black, mypy, pyright settings) first, and follow [PEP 8](https://peps.python.org/pep-0008/) and [PEP 257](https://peps.python.org/pep-0257/) where the project is silent.

- **Naming:** `snake_case` for functions and variables, `PascalCase` for classes, `UPPER_SNAKE` for constants, a leading underscore for private names.
- **Types:** annotate public functions. Use built-in generics (`list[str]`, `X | None`) on the project's Python version. Avoid `Any` unless the value is truly untyped.
- **Immutability:** prefer tuples, `frozenset`, and `@dataclass(frozen=True)` for value objects. Do not use mutable default arguments (`def f(x=[])`); use `None` and create the value inside.
- **Errors:** catch specific exceptions, never a bare `except:`. Use `raise NewError(...) from err` to keep the cause. Define a small exception hierarchy for a library; do not return error codes.
- **Resources:** use `with` for files, locks, and connections. Use `pathlib` over string paths.
- **Idioms:** comprehensions for simple transforms, a loop when it needs more than one step. Use `enumerate` and `zip` instead of index loops.
- **Logging:** use `logging` with lazy `%s` arguments, not `print`, in library and service code.
- **Docstrings:** one-line summary, then arguments and exceptions in the project's style (Google, NumPy, or reST).
- **Tests:** pytest with plain `assert`, fixtures for setup, and `pytest.raises` for failure paths.
