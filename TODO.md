# TODO — Add Azure PostgreSQL Flexible Server support to sqlpinger

## Context

Today `sqlpinger` is a CLI that monitors SQL Server availability. The whole stack — pyodbc connection, `WAITFOR DELAY` heartbeat, ODBC connection strings, three auth strategies — is wired specifically to SQL Server. We want the same CLI to also probe Azure PostgreSQL Flexible Server, where the heartbeat is `SELECT pg_sleep(seconds)` and the driver is `psycopg2`. PG will support **only native SQL auth** in this first iteration (no Windows, no Azure AD).

The structural goal is to clearly separate **engine-specific** code from **shared core**, so adding a third engine later is mechanical.

Decisions already made:
- Driver: **psycopg2-binary**.
- Rename `SqlAvailabilityMonitor` → `AvailabilityMonitor`.
- Add `--port` (default `5432`) and `--sslmode` (default `require`) CLI options for Postgres.

## Target structure

```
sqlpinger/
  cli.py                          # SHARED: dispatches by --engine
  config.py                       # SHARED (unchanged)
  __init__.py                     # SHARED (version)

  core/                           # SHARED
    __init__.py
    monitor.py                    # was ping.py — renamed; engine-agnostic loop
    downtime.py                   # unchanged
    connection.py                 # NEW: ConnectionManager ABC (interface only)
    engine.py                     # NEW: Engine ABC (build_heartbeat_sql + create_connection_manager)
    auth/
      __init__.py
      base.py                     # unchanged: AuthStrategy ABC

  engines/                        # NEW package
    __init__.py
    sqlserver/
      __init__.py                 # re-exports SqlServerEngine, factory, types
      engine.py                   # SqlServerEngine: pyodbc + WAITFOR DELAY
      connection.py               # SqlServerConnectionManager (pyodbc-based, was core/connection.py)
      sql_commands.py             # build_waitfor_delay_sql (moved from core/sql_commands.py)
      auth/
        __init__.py
        common.py                 # SqlServerAuthTypes, SqlServerAuthFactory (was core/auth/common.py)
        sql_auth.py               # moved from core/auth/sql_auth.py
        windows_auth.py           # moved from core/auth/windows_auth.py
        azure_ad.py               # moved from core/auth/azure_ad.py
    postgres/
      __init__.py                 # re-exports PostgresEngine, factory, types
      engine.py                   # PostgresEngine: psycopg2 + pg_sleep
      connection.py               # PostgresConnectionManager (psycopg2-based)
      sql_commands.py             # build_pg_sleep_sql
      auth/
        __init__.py
        common.py                 # PostgresAuthTypes (only SQL), PostgresAuthFactory
        sql_auth.py               # PostgresSqlAuth: libpq-style connection string

  util/logger.py                  # SHARED (unchanged)
```

Tests mirror this layout under `test/sqlpinger/unit/`:
- `core/test_monitor.py`, `core/test_downtime.py` — engine-agnostic, kept generic.
- `engines/sqlserver/...` — moved `test_connection.py`, `test_sql_commands.py`, and the four `auth/` tests.
- `engines/postgres/...` — new tests mirroring the sqlserver ones, mocking `psycopg2.connect` instead of `pyodbc.connect`.

## Abstractions (the only new code in `core/`)

**`core/connection.py`** — promote `ConnectionManager` to an ABC so the monitor doesn't import any driver:
```python
class ConnectionManager(ABC):
    @abstractmethod
    def execute(self, sql: str) -> None: ...
    @abstractmethod
    def is_connected(self) -> bool: ...
    @abstractmethod
    def disconnect(self) -> None: ...
```

**`core/engine.py`** — bundles the two engine-specific concerns:
```python
class Engine(ABC):
    @abstractmethod
    def build_heartbeat_sql(self, seconds: int) -> str: ...
    @abstractmethod
    def create_connection_manager(self, conn_str: str, timeout: int) -> ConnectionManager: ...
```

**`core/monitor.py`** — `AvailabilityMonitor` (renamed from `SqlAvailabilityMonitor`) takes an `Engine` plus an `AuthStrategy`:
```python
class AvailabilityMonitor:
    def __init__(self, server, database, interval, auth_strategy, engine: Engine):
        conn_str = auth_strategy.get_connection_string(server, database)
        self.connection_manager = engine.create_connection_manager(conn_str, interval)
        self.engine = engine
        ...
    def run_check(self):
        sql = self.engine.build_heartbeat_sql(self.interval)
        self.connection_manager.execute(sql)
```
Loop logic, `handle_exception`, downtime wiring, KeyboardInterrupt summary — all unchanged from current `ping.py:22-54`.

## Per-engine implementations

### `engines/sqlserver/`
- **`connection.py`** — `SqlServerConnectionManager(ConnectionManager)`: lift current `ConnectionManager` from `core/connection.py` verbatim, rename, keep `import pyodbc`.
- **`sql_commands.py`** — move `build_waitfor_delay_sql` from `core/sql_commands.py` verbatim.
- **`engine.py`** — `SqlServerEngine` calls `build_waitfor_delay_sql` and instantiates `SqlServerConnectionManager`.
- **`auth/`** — move `sql_auth.py`, `windows_auth.py`, `azure_ad.py` verbatim. Move `core/auth/common.py` and rename its types to `SqlServerAuthTypes` / `SqlServerAuthFactory` (keeping the same `sql`/`windows`/`azure-ad` value strings — preserves CLI compatibility).

### `engines/postgres/`
- **`connection.py`** — `PostgresConnectionManager(ConnectionManager)` using `psycopg2.connect(conn_str, connect_timeout=timeout)`. The `is_connected()` check uses `self.conn is not None and self.conn.closed == 0` (psycopg2's `closed` is an int: `0` = open).
- **`sql_commands.py`** — `build_pg_sleep_sql(seconds: int) -> str` returns `f"SELECT pg_sleep({int(seconds)})"`.
- **`engine.py`** — `PostgresEngine` ties them together.
- **`auth/common.py`** — `PostgresAuthTypes` enum has only `SQL = 'sql'`; `PostgresAuthFactory.create(...)` returns `PostgresSqlAuth` and raises `NotImplementedError` for anything else.
- **`auth/sql_auth.py`** — `PostgresSqlAuth(AuthStrategy)` builds a libpq keyword-format string:
  ```
  host=<server> port=<port> dbname=<database> user=<u> password=<p> connect_timeout=<n> sslmode=<sslmode>
  ```
  Constructor takes `(username, password, port, sslmode, timeout_in_seconds)`. Defaults handled at the CLI layer.

## CLI changes — `sqlpinger/cli.py`

- Add `--engine` Click choice: `['sqlserver', 'postgres']`, default `sqlserver` (preserves current behavior for existing users).
- Add `--port` (int, default `5432`) and `--sslmode` (string, default `require`). Both are accepted always but only meaningful for postgres; document this in their `help=` strings.
- Keep `--driver` with its current default; mark in help text that it applies only to sqlserver.
- `--auth`: take the union of choices (`sql`, `windows`, `azure-ad`) at the Click level; validate per-engine inside `main()` and raise `click.UsageError` for unsupported combos (e.g., `postgres + windows` or `postgres + azure-ad`).
- Engine dispatch table:
  ```python
  ENGINES = {
      'sqlserver': (SqlServerEngine, SqlServerAuthFactory, SqlServerAuthTypes),
      'postgres':  (PostgresEngine,  PostgresAuthFactory,  PostgresAuthTypes),
  }
  ```
- Wiring per branch:
  - sqlserver → existing flow, just routed through `SqlServerEngine()` and `SqlServerAuthFactory.create(auth, driver, timeout, username, password)`.
  - postgres → `PostgresEngine()`, `PostgresAuthFactory.create(auth='sql', port, sslmode, timeout, username, password)`.
- Update the docstring on line 21 (`"""Monitor a SQL Server database..."""`) to be engine-neutral.

## Files to modify or create

**Move + rename** (logic is unchanged, only the import paths shift):
- `sqlpinger/core/sql_commands.py` → `sqlpinger/engines/sqlserver/sql_commands.py`
- `sqlpinger/core/connection.py` → `sqlpinger/engines/sqlserver/connection.py` (rename class to `SqlServerConnectionManager`)
- `sqlpinger/core/auth/{sql_auth,windows_auth,azure_ad}.py` → `sqlpinger/engines/sqlserver/auth/`
- `sqlpinger/core/auth/common.py` → `sqlpinger/engines/sqlserver/auth/common.py` (rename `AuthTypes`→`SqlServerAuthTypes`, `AuthStrategyFactory`→`SqlServerAuthFactory`)
- `sqlpinger/core/ping.py` → `sqlpinger/core/monitor.py` (rename class `SqlAvailabilityMonitor`→`AvailabilityMonitor`, inject `Engine`)

**Create**:
- `sqlpinger/core/connection.py` (NEW — `ConnectionManager` ABC)
- `sqlpinger/core/engine.py` (NEW — `Engine` ABC)
- `sqlpinger/engines/__init__.py`, `sqlpinger/engines/sqlserver/__init__.py`, `sqlpinger/engines/sqlserver/engine.py`
- `sqlpinger/engines/postgres/{__init__.py, engine.py, connection.py, sql_commands.py}`
- `sqlpinger/engines/postgres/auth/{__init__.py, common.py, sql_auth.py}`

**Modify**:
- `sqlpinger/cli.py` — engine dispatch, new options, validation.
- `pyproject.toml` — add `psycopg2-binary (>=2.9,<3.0)` to `[project] dependencies`.

**Test reorganization** (mirrors the source moves):
- `test/sqlpinger/unit/core/test_ping.py` → `test/sqlpinger/unit/core/test_monitor.py`. Adjust the `MagicMock(spec=AuthStrategy)` setup to also pass a `MagicMock(spec=Engine)` whose `create_connection_manager` returns a `MagicMock(spec=ConnectionManager)` and whose `build_heartbeat_sql` returns a known string. Loop assertions don't change.
- `test/sqlpinger/unit/core/test_sql_commands.py` → `test/sqlpinger/unit/engines/sqlserver/test_sql_commands.py`.
- `test/sqlpinger/unit/core/test_connection.py` → `test/sqlpinger/unit/engines/sqlserver/test_connection.py`. Patch target updates from `sqlpinger.core.connection.pyodbc.connect` to `sqlpinger.engines.sqlserver.connection.pyodbc.connect`.
- `test/sqlpinger/unit/core/auth/{test_sql_auth,test_windows_auth,test_azure_ad,test_common}.py` → `test/sqlpinger/unit/engines/sqlserver/auth/`. No logic changes; only import paths and the `AuthStrategyFactory`/`AuthTypes` references update to the renamed `SqlServerAuthFactory`/`SqlServerAuthTypes`.
- `test/sqlpinger/unit/core/test_downtime.py` and `test/sqlpinger/unit/util/test_logger.py` — unchanged.
- New: `test/sqlpinger/unit/engines/postgres/test_sql_commands.py` (asserts `SELECT pg_sleep(N)` for various inputs), `test_connection.py` (mocks `psycopg2.connect`, checks `connect_timeout` kwarg, `closed == 0` semantics), `auth/test_sql_auth.py` (asserts the libpq keyword string is built correctly), `auth/test_common.py` (factory returns `PostgresSqlAuth` for `sql`, raises for `windows`/`azure-ad`).

## Verification

End-to-end checks before merging:

1. **Tests pass**:
   ```
   poetry run pytest test/sqlpinger/unit
   poetry run coverage run -m pytest test/sqlpinger/unit && poetry run coverage report
   ```
2. **Existing SQL Server flow is byte-compatible**:
   ```
   poetry run sqlpinger --help
   poetry run sqlpinger --engine sqlserver --server <host> --database <db> --auth sql --username <u>
   ```
   `--engine sqlserver` is the default, so users who omit it should see identical behavior.
3. **PostgreSQL flow** against an Azure PG Flexible Server (or local Postgres for smoke):
   ```
   poetry run sqlpinger --engine postgres --server <host> --database <db> --auth sql --username <u> --port 5432 --sslmode require
   ```
   Verify: heartbeat issues `SELECT pg_sleep(<interval>)` (psql/`pg_stat_activity` will show it), Ctrl+C summary JSON renders the same shape.
4. **CLI validation**: `--engine postgres --auth windows` and `--engine postgres --auth azure-ad` both fail fast with a clear `click.UsageError` and non-zero exit code.
5. **Connection failure detection**: kill the server / firewall briefly while the monitor runs; confirm a downtime is recorded, recovery is logged, and the JSON summary on Ctrl+C is correct for both engines.
6. **Build still produces a wheel**: `poetry build` and confirm `dist/*.whl` ships with `psycopg2-binary` declared.

## Out of scope (explicit non-goals for this iteration)

- Azure AD auth for PostgreSQL (deferred — would need `azure-identity` token + `password=<token>` flow with a custom expiration handler).
- Auto-detecting engine from the connection target.
- Renaming `--driver` to `--odbc-driver` (would break existing users of the CLI).
- Updating `README.md` and `CLAUDE.md` — those are docs follow-ups; the user can request them once the implementation is in.
