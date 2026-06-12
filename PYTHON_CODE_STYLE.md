# Python Code Style

This guide captures the coding style already used in `sqlpinger`. Follow it
when adding or changing Python code in this repository.

## Baseline

- Target Python 3.12 or newer.
- Prefer small, explicit modules with one clear responsibility.
- Keep code readable over clever. This is a diagnostic CLI; behavior should be
  obvious from the call site.
- Use ASCII for source, logs, CLI output, and documentation unless a file
  already requires non-ASCII.
- Do not hand-edit generated release versions in `sqlpinger/__init__.py` or
  `pyproject.toml`.

## Formatting

- Use 4 spaces for indentation.
- Use blank lines between import groups, top-level constants, classes, and
  functions.
- Prefer readable multi-line calls when arguments are numerous:

```python
auth_strategy = PostgresAuthStrategyFactory.create(
    auth=auth,
    timeout_in_seconds=effective_interval,
    username=username,
    password=password,
    port=port,
    sslmode=sslmode,
)
```

- Keep constants at module level in `UPPER_SNAKE_CASE`, for example
  `DEFAULT_INTERVAL`, `HEALTHCHECK_SQL`, and `SUPPORTED_CREDENTIAL_ENGINES`.
- Match the quote style of the surrounding file. Do not rewrite strings only to
  change single quotes to double quotes or the other way around.

## Imports

- Group imports in this order: standard library, third-party packages, then
  local `sqlpinger` imports.
- Use absolute local imports such as `from sqlpinger.core.monitor import ...`.
- Avoid importing runtime objects only to satisfy typing if it creates cycles.
  Use the existing package boundaries instead.

## Typing

- Add type hints for public constructors, public methods, helpers, and abstract
  contracts.
- Use modern Python typing for new code:
  `str | None`, `tuple[str | None, str | None]`, `list[dict[str, str]]`.
- Do not use `typing.List`, `typing.Dict`, or `typing.Optional` in new code.
  Prefer built-in generics (`list`, `dict`, `tuple`) and the `| None` union
  syntax.
- Existing modules may still have legacy typing imports; migrate them only when
  you are already editing that area.
- Abstract methods should declare return types and use `...` as their body.

## Architecture

- Keep CLI wiring in `sqlpinger/cli.py`. It should assemble auth strategies,
  engines, and monitors, but should not own persistence or database-specific
  behavior.
- Put feature-specific CLI groups in their own module when they grow beyond
  simple command wiring, as with `sqlpinger/credentials_cli.py`.
- Keep database-specific behavior under `sqlpinger/engines/<engine>/`.
- Keep cross-engine contracts and shared behavior under `sqlpinger/core/`.
- Preserve the engine abstraction:
  - `Engine.build_heartbeat_sql(seconds)` builds continuous-mode SQL.
  - `Engine.build_healthcheck_sql()` builds one-time healthcheck SQL.
  - `Engine.create_connection_manager(...)` returns the engine-specific
    connection manager.
- Keep connection managers lazy. `execute()` should connect when needed, and
  failure handling should disconnect so the next tick reconnects.

## CLI Behavior

- Use `click` options and commands consistently.
- Convert user-facing validation errors at the CLI boundary into
  `click.ClickException`; avoid traceback-style exits for expected user errors.
- Keep `--once` immediate. It should run `SELECT 1`, ignore `--interval` as a
  delay, return exit code `0` or `1`, and avoid downtime summaries.
- Do not print secrets, passwords, connection strings, tokens, or keyring
  values.
- When saved default credentials are used, log an INFO message that identifies
  the engine and username, but never the password.

## Logging

- Use `Logger.get_logger(...)` instead of creating `logging` handlers directly.
- Create loggers inside constructors or functions after `config.verbose` has
  been set by the CLI.
- Use module names for loggers (`__name__`) unless shared base classes need the
  concrete subclass module.
- Keep log messages ASCII and human-readable.
- Use INFO for high-level lifecycle and selected credential/profile context,
  DEBUG for repeated or low-level details, WARNING for recovery/stop events,
  and ERROR for first failure in a downtime interval.

## Exceptions

- Database check failures should flow through
  `AvailabilityMonitor.handle_exception()` so downtime state and cleanup stay
  consistent.
- Auth factories may raise `ValueError` for missing required inputs and
  `NotImplementedError` for unsupported auth methods.
- CLI commands should catch domain/storage errors and re-raise
  `click.ClickException` with actionable messages.
- Never use bare `except:`. Catch `Exception` only when the code has a clear
  cleanup or user-facing error path.

## Credentials And Secrets

- Store default credentials via `DefaultCredentialStore`; do not access
  `keyring` directly from general CLI or engine code.
- Keep keyring service names namespaced to the project and engine.
- Store and retrieve credentials per engine (`mssql`, `pg`).
- Inject or mock keyring backends in tests. Unit tests must not read or write
  the developer's real operating-system keyring.
- Preserve the precedence rules:
  - Explicit `--username` uses explicit or prompted password.
  - Missing `--username` may use saved default SQL credentials.
  - `--password` without `--username` is invalid.
  - Non-SQL auth modes do not use saved SQL credentials.

## Tests

- Put unit tests under `test/sqlpinger/unit/...`, mirroring the source module
  where practical.
- Use `unittest.TestCase` as the base style.
- Use `MagicMock` and `patch` for runtime dependencies, database drivers,
  keyring, engines, and monitors.
- Use `pytest.raises` only where that pattern already exists in the surrounding
  test module; otherwise prefer `self.assertRaises`.
- Test behavior and wiring, not implementation trivia. Assert important calls,
  generated SQL, exit codes, and user-facing messages.
- For time-based downtime tests, use `freezegun`; do not rely on real sleeps.
- For new credential/keyring behavior, cover both successful paths and backend
  failure paths.
- Run targeted tests first, then the full unit suite:

```bash
poetry run pytest test/sqlpinger/unit
poetry run coverage run -m pytest test/sqlpinger/unit
poetry run coverage report
```

If local cache permissions cause pytest or coverage cache warnings, use a
temporary cache/coverage file for local validation instead of changing
production code.

## Documentation

- Keep README examples aligned with actual CLI behavior.
- When adding public CLI behavior, update `README.md` and tests together.
- Keep AGENTS-facing implementation guidance here rather than duplicating
  detailed style rules in `AGENTS.md`.
