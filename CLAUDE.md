# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`sqlpinger` is a Python CLI that monitors SQL Server availability by repeatedly running `WAITFOR DELAY` queries against a target database, recording any execution failure as a "downtime" interval. Distributed as a wheel via GitHub Releases. Requires Python >=3.11.

## Common commands

Dependencies are managed with Poetry. The package itself depends on `pyodbc`, `azure-identity`, and `click`; dev tooling adds `pytest`, `coverage`, and `freezegun`.

```bash
poetry install --no-interaction --all-groups   # install (incl. dev deps)

poetry run pytest test/sqlpinger/unit          # run unit tests
poetry run pytest test/sqlpinger/unit/core/test_ping.py::TestName::test_x   # single test
poetry run coverage run -m pytest test/sqlpinger/unit && poetry run coverage report

poetry run sqlpinger --server ... --database ... --auth sql --username ...   # run CLI from source
poetry build                                   # produce wheel in ./dist/
```

CI (`.github/workflows/ci.yml`) only runs `test/sqlpinger/unit`; the `e2e/` directory exists but is empty. Versioning and release artifacts are produced automatically by `python-semantic-release` on pushes to `main` — do **not** hand-edit `sqlpinger/__init__.py:__version__` or the version in `pyproject.toml`; semantic-release rewrites both.

## Architecture

The runtime is a single monitoring loop wired together in `cli.py:main`:

1. **`AuthStrategyFactory.create(...)`** (`core/auth/common.py`) picks an `AuthStrategy` subclass — `SqlAuth`, `AzureADInteractive`, or `WindowsAuth` — based on `--auth`. Each strategy's only job is to return a pyodbc connection string via `get_connection_string(server, database)`. Adding an auth method = new subclass of `AuthStrategy` (`core/auth/base.py`) + a branch in the factory + an entry in the `AuthTypes` enum.
2. **`SqlAvailabilityMonitor`** (`core/ping.py`) owns the loop. It builds the connection string from the strategy, hands it to a `ConnectionManager`, and on each tick calls `run_check()` which executes `WAITFOR DELAY HH:MM:SS` (built by `build_waitfor_delay_sql`) for `--interval` seconds. The `WAITFOR DELAY` *is* the heartbeat — its execution time is what the connection timeout must accommodate.
3. **`ConnectionManager`** (`core/connection.py`) is lazy: `execute()` reconnects if no live connection exists. On any exception, the monitor calls `disconnect()` so the next tick will reopen.
4. **Downtime tracking** (`core/downtime.py`) is a small state machine:
   - `Downtime.start()` is called on the first failing tick; subsequent failing ticks see `is_active() == True` and do not re-start.
   - The first successful tick after a failure calls `Downtime.finish()`, which appends a record `{from, to, time}` to the shared `DowntimeSummary`.
   - On `KeyboardInterrupt`, the monitor logs `summary` (its `__str__` is JSON) — this is the final report users see.

This design means **every error path during a check must funnel through `handle_exception`** so downtime state stays consistent. If you add new check logic in `ping.py`, do not bypass that try/except.

## Conventions worth knowing

- **Verbose flag is a module-level global**: `sqlpinger/config.py` holds `verbose = False`, mutated by `cli.main` before any logger is constructed. `Logger.get_logger` reads it once at logger-creation time, so loggers built before `--verbose` is applied won't pick up DEBUG. Construct loggers inside class `__init__`s (current pattern), not at module import.
- **Connection string assumes `TrustServerCertificate=yes`** in `SqlAuth` — fine for the diagnostic use case but note it if you reuse the strategy elsewhere.
- **`AzureADInteractive` may pop the auth prompt mid-run**, not only at startup; the README warns users explicitly. Don't "fix" this by caching tokens without understanding why interactive was chosen.
- Tests use `freezegun` for time-based assertions in `test_downtime.py` / `test_ping.py`. When changing anything that calls `datetime.now()`, run those tests.
