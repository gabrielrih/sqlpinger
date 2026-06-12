# AGENTS.md

This file provides guidance to coding agents when working with this repository.

## Project

`sqlpinger` is a Python CLI that checks database availability for SQL Server
and PostgreSQL. In continuous mode it repeatedly runs a database-specific
heartbeat query and records execution failures as downtime intervals. It is
distributed as a wheel via GitHub Releases and requires Python >=3.12.

Supported engines:

- `sqlpinger mssql ...`: SQL Server heartbeat uses `WAITFOR DELAY`.
- `sqlpinger pg ...`: PostgreSQL heartbeat uses `SELECT pg_sleep(...)`.
- Both commands support `--once`, which runs one immediate `SELECT 1`
  health check, prints the normal success/failure log message, and exits
  without printing a downtime summary.

## Common commands

Dependencies are managed with Poetry. Runtime dependencies include `pyodbc`,
`azure-identity`, `click`, `psycopg2-binary`, and `keyring`; dev tooling adds
`pytest`, `coverage`, and `freezegun`.

```bash
poetry install --no-interaction --all-groups

poetry run pytest test/sqlpinger/unit
poetry run pytest test/sqlpinger/unit/core/test_monitor.py::TestAvailabilityMonitor::test_run_check_executes_sql
poetry run coverage run -m pytest test/sqlpinger/unit && poetry run coverage report

poetry run sqlpinger mssql --server ... --database ... --auth sql --username ...
poetry run sqlpinger pg --server ... --database ... --auth sql --username ...
poetry run sqlpinger mssql --server ... --database ... --auth sql --username ... --once

poetry build
```

## Python code style

Follow `PYTHON_CODE_STYLE.md` for project-specific Python coding conventions,
including formatting, typing, module boundaries, CLI behavior, logging,
credentials/keyring handling, exceptions, and test patterns. Prefer that guide
over generic style assumptions when generating or reviewing code for this repo.

CI (`.github/workflows/ci.yml`) runs `test/sqlpinger/unit`; the `e2e/`
directory exists but is empty. Versioning and release artifacts are produced
automatically by `python-semantic-release` on pushes to `main`; do not
hand-edit `sqlpinger/__init__.py:__version__` or the version in
`pyproject.toml`.

## Architecture

Runtime wiring starts in `sqlpinger/cli.py`:

1. `common_options` defines shared flags such as `--server`, `--database`,
   `--interval`, `--verbose`, and `--once`.
2. Each subcommand creates the appropriate auth strategy and engine:
   SQL Server uses `SqlServerAuthStrategyFactory` + `SqlServerEngine`;
   PostgreSQL uses `PostgresAuthStrategyFactory` + `PostgresEngine`.
3. `AvailabilityMonitor` (`core/monitor.py`) owns execution:
   - `start_monitoring()` runs the continuous loop.
   - `run_check()` executes `engine.build_heartbeat_sql(interval)`.
   - `run_once()` executes `engine.build_healthcheck_sql()` exactly once.
4. `Engine` (`core/engine.py`) provides two SQL builders:
   - `build_heartbeat_sql(seconds)` for continuous monitoring.
   - `build_healthcheck_sql()` for `--once`; both current engines return
     `SELECT 1`.
5. `ConnectionManager` implementations are lazy: `execute()` reconnects if no
   live connection exists. On failure, the monitor disconnects so the next
   continuous tick reopens the connection.
6. `Downtime`/`DowntimeSummary` (`core/downtime.py`) track downtime only for
   continuous monitoring. `--once` should not finish or print a downtime
   summary; it should return success/failure and let the CLI exit `0` or `1`.

Every error path during a database check should funnel through
`AvailabilityMonitor.handle_exception()` so logging and connection cleanup stay
consistent.

## Conventions worth knowing

- The verbose flag is a module-level global in `sqlpinger/config.py`, mutated
  by the CLI before loggers are constructed. Create loggers inside class
  constructors, not at module import time.
- SQL Server auth strategies include `TrustServerCertificate=yes` where
  applicable, matching the diagnostic use case.
- `AzureADInteractive` may prompt during execution, not only at startup.
- Tests use `freezegun` for time-based assertions in downtime tests. When
  changing code that calls `datetime.now()`, run the downtime and monitor tests.
- For `--once`, keep the query immediate (`SELECT 1`), ignore `--interval` as a
  delay, do not print `Downtime Summary`, and avoid traceback-style exits.
