# TODO — Add Azure PostgreSQL Flexible Server support to sqlpinger

## Context

Today `sqlpinger` is a CLI that monitors SQL Server availability. The whole stack — pyodbc connection, `WAITFOR DELAY` heartbeat, ODBC connection strings, three auth strategies — is wired specifically to SQL Server. We want the same CLI to also probe Azure PostgreSQL Flexible Server, where the heartbeat is `SELECT pg_sleep(seconds)` and the driver is `psycopg2`. PG will support **only native SQL auth** in this first iteration (no Windows, no Azure AD).

The structural goal is to clearly separate **engine-specific** code from **shared core**, so adding a third engine later is mechanical.

Decisions already made:
- Driver: **psycopg2-binary**. Trade-off accepted: the binary package bundles libssl/libcrypto and is officially discouraged for high-traffic production apps, but for a single-connection diagnostic CLI distributed as a wheel it removes the need for users to install build toolchains. If issues arise, switching to `psycopg` (v3) is a future option.
- Rename `SqlAvailabilityMonitor` → `AvailabilityMonitor`.
- Add `--port` (default `5432`) and `--sslmode` (default `require`) CLI options for Postgres.
- **CLI uses subcommands**: `sqlpinger mssql ...` and `sqlpinger pg ...` (Click `@click.group`). Each subcommand exposes only its own flags, so `sqlpinger pg --help` doesn't show `--driver`, and `sqlpinger mssql --help` doesn't show `--port`/`--sslmode`. This is a **breaking change** vs. the current flat CLI (`sqlpinger --server ...`) — semantic-release will likely cut a new major version.
- **Postgres connection string uses URI format** (`postgresql://user:pass@host:port/db?...`) with `urllib.parse.quote(value, safe='')` applied to user/password. Avoids the libpq keyword-format escape rules (spaces, single quotes, backslashes) which would silently break with Azure-generated passwords containing special characters.
- **Factory naming preserves the existing suffix**: new classes are `SqlServerAuthStrategyFactory` and `PostgresAuthStrategyFactory` (mirrors the current `AuthStrategyFactory`), and `SqlServerAuthTypes` / `PostgresAuthTypes` for the enums.
- **Re-exports only at the engine package boundary**: `engines/sqlserver/__init__.py` and `engines/postgres/__init__.py` re-export `Engine`, `AuthStrategyFactory`, `AuthTypes` for the CLI. All other `__init__.py` files stay empty (consistent with the current codebase).
- **README is in scope** for this PR (not a follow-up): the current usage examples become invalid the moment we merge, and semantic-release publishes immediately on push to `main`.

## Target structure

```
sqlpinger/
  cli.py                          # SHARED: Click group with mssql/pg subcommands
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

**`core/auth/base.py`** — keep the `AuthStrategy` ABC; add a small `ListableEnum` mixin so each engine's `AuthTypes` does not duplicate `to_list()`:
```python
class ListableEnum(Enum):
    @classmethod
    def to_list(cls) -> list[str]:
        return [t.value for t in cls]
```

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
Loop logic, `handle_exception`, downtime wiring, KeyboardInterrupt summary — all unchanged from current `ping.py:22-54`. Update the startup log line to include the engine class name for observability:
```python
self.logger.info(
    f"Starting monitor for {self.server}/{self.database} every {self.interval}s "
    f"using {engine.__class__.__name__} + {auth_strategy.__class__.__name__}"
)
```

## Per-engine implementations

### `engines/sqlserver/`
- **`connection.py`** — `SqlServerConnectionManager(ConnectionManager)`: lift current `ConnectionManager` from `core/connection.py` verbatim, rename, keep `import pyodbc`.
- **`sql_commands.py`** — move `build_waitfor_delay_sql` from `core/sql_commands.py` verbatim.
- **`engine.py`** — `SqlServerEngine` calls `build_waitfor_delay_sql` and instantiates `SqlServerConnectionManager`.
- **`auth/`** — move `sql_auth.py`, `windows_auth.py`, `azure_ad.py` verbatim. Move `core/auth/common.py` and rename its types: `AuthTypes` → `SqlServerAuthTypes` (extends `ListableEnum`), `AuthStrategyFactory` → `SqlServerAuthStrategyFactory` (keeping the same `sql`/`windows`/`azure-ad` value strings).

### `engines/postgres/`
- **`connection.py`** — `PostgresConnectionManager(ConnectionManager)` using `psycopg2.connect(conn_str, connect_timeout=timeout)`. The `is_connected()` check uses `self.conn is not None and self.conn.closed == 0` (psycopg2's `closed` is an int: `0` = open).
- **`sql_commands.py`** — `build_pg_sleep_sql(seconds: int) -> str` returns `f"SELECT pg_sleep({int(seconds)})"`.
- **`engine.py`** — `PostgresEngine` ties them together.
- **`auth/common.py`** — `PostgresAuthTypes(ListableEnum)` has only `SQL = 'sql'`; `PostgresAuthStrategyFactory.create(...)` uses **named keyword arguments** (matches the existing SQL Server factory style), returns `PostgresSqlAuth` for `auth='sql'`, raises `ValueError("PostgreSQL SQL authentication requires both username and password")` when either credential is empty (mirrors `core/auth/common.py:25-26`), and raises `NotImplementedError` for any other value:
  ```python
  @staticmethod
  def create(auth: str, timeout_in_seconds: int,
             username: str = '', password: str = '',
             port: int = 5432, sslmode: str = 'require') -> AuthStrategy:
      ...
  ```
- **`auth/sql_auth.py`** — `PostgresSqlAuth(AuthStrategy)` builds a **URI connection string** to sidestep libpq keyword-escape rules:
  ```python
  from urllib.parse import quote

  def get_connection_string(self, server: str, database: str) -> str:
      user = quote(self.username, safe='')
      pwd  = quote(self.password, safe='')
      db   = quote(database, safe='')
      return (
          f"postgresql://{user}:{pwd}@{server}:{self.port}/{db}"
          f"?connect_timeout={self.timeout_in_seconds}&sslmode={self.sslmode}"
      )
  ```
  Constructor takes `(username, password, port, sslmode, timeout_in_seconds)` as kwargs. The URI format is consumed natively by `psycopg2.connect()`.

## CLI changes — `sqlpinger/cli.py`

The CLI becomes a Click **group** with one subcommand per engine. Each subcommand exposes only its own flags, so per-engine `--help` is clean and there is no per-engine validation logic at runtime — Click rejects unknown flags automatically.

```python
@click.group()
@click.version_option(__version__)
def cli():
    """Monitor a database continuously and log downtimes."""

@cli.command()
@common_options
@click.option('--auth', type=click.Choice(SqlServerAuthTypes.to_list()),
              default=SqlServerAuthTypes.SQL.value, show_default=True)
@click.option('--driver', default='ODBC Driver 18 for SQL Server', show_default=True,
              help='ODBC driver name (SQL Server only)')
def mssql(server, database, interval, auth, username, password, verbose, driver):
    """Monitor a SQL Server database."""
    config.verbose = verbose
    if auth == SqlServerAuthTypes.SQL.value and not password:
        password = click.prompt(f'Password for user "{username}"', hide_input=True, type=str)
    auth_strategy = SqlServerAuthStrategyFactory.create(
        auth=auth, driver=driver, timeout_in_seconds=interval,
        username=username, password=password,
    )
    AvailabilityMonitor(server, database, interval, auth_strategy, SqlServerEngine()).start_monitoring()

@cli.command()
@common_options
@click.option('--auth', type=click.Choice(PostgresAuthTypes.to_list()),
              default=PostgresAuthTypes.SQL.value, show_default=True)
@click.option('--port', type=int, default=5432, show_default=True,
              help='PostgreSQL server port')
@click.option('--sslmode', default='require', show_default=True,
              help='libpq sslmode (disable | allow | prefer | require | verify-ca | verify-full)')
def pg(server, database, interval, auth, username, password, verbose, port, sslmode):
    """Monitor a PostgreSQL database."""
    config.verbose = verbose
    if auth == PostgresAuthTypes.SQL.value and not password:
        password = click.prompt(f'Password for user "{username}"', hide_input=True, type=str)
    auth_strategy = PostgresAuthStrategyFactory.create(
        auth=auth, timeout_in_seconds=interval,
        username=username, password=password, port=port, sslmode=sslmode,
    )
    AvailabilityMonitor(server, database, interval, auth_strategy, PostgresEngine()).start_monitoring()
```

**Shared options** live in a `common_options` decorator. Note that Click stacks decorators bottom-up, so the *last* `click.option` listed appears *first* in `--help`:
```python
def common_options(f):
    f = click.option('--verbose', is_flag=True, help='Enable verbose output')(f)
    f = click.option('--password', required=False, help='Password for SQL authentication')(f)
    f = click.option('--username', required=False, help='Username for SQL authentication')(f)
    f = click.option('--interval', default=5, show_default=True, help='Seconds between each check')(f)
    f = click.option('--database', required=True, help='Database name')(f)
    f = click.option('--server', required=True, help='Database server hostname or IP')(f)
    return f
```

**Password prompting** (the existing behavior at `cli.py:23-24`: prompt interactively when `--auth sql` and `--password` was not passed) lives in each subcommand body and is preserved for both engines.

**`config.verbose`** is set at the top of each subcommand body before any `Logger.get_logger` call — same constraint as today.

**Entry point** in `pyproject.toml` changes from `sqlpinger = "sqlpinger.cli:main"` to `sqlpinger = "sqlpinger.cli:cli"` (the new group).

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
- `sqlpinger/cli.py` — convert to a `@click.group` with `mssql` and `pg` subcommands; extract a `common_options` decorator for shared flags.
- `sqlpinger/core/auth/base.py` — add the `ListableEnum` mixin alongside `AuthStrategy`.
- `pyproject.toml` — add `psycopg2-binary (>=2.9,<3.0)` to `[project] dependencies`; change entry point from `sqlpinger.cli:main` to `sqlpinger.cli:cli`.
- `README.md` — update the `# Usage` section to use subcommand syntax (`sqlpinger mssql ...` and `sqlpinger pg ...`); add Postgres to `# Features`; update the `# Development` section (`poetry run sqlpinger --help` now lists subcommands).

**Test reorganization** (mirrors the source moves):
- `test/sqlpinger/unit/core/test_ping.py` → `test/sqlpinger/unit/core/test_monitor.py`. The setup now passes a `MagicMock(spec=Engine)` whose `create_connection_manager` returns a `MagicMock(spec=ConnectionManager)` and whose `build_heartbeat_sql` returns a known sentinel string. Existing tests are kept and these **contract tests are added**:
  - `test_init_calls_get_connection_string_once_with_server_and_database` — `auth_strategy.get_connection_string.assert_called_once_with(server, database)`.
  - `test_init_creates_connection_manager_via_engine_once` — `engine.create_connection_manager.assert_called_once_with("mock_conn_str", interval)`.
  - `test_run_check_executes_heartbeat_sql_from_engine` — calls `run_check()`, asserts `engine.build_heartbeat_sql` was called with `interval` and `connection_manager.execute` was called with the sentinel string returned by it.
- `test/sqlpinger/unit/core/test_sql_commands.py` → `test/sqlpinger/unit/engines/sqlserver/test_sql_commands.py`.
- `test/sqlpinger/unit/core/test_connection.py` → `test/sqlpinger/unit/engines/sqlserver/test_connection.py`. Patch target updates from `sqlpinger.core.connection.pyodbc.connect` to `sqlpinger.engines.sqlserver.connection.pyodbc.connect`.
- `test/sqlpinger/unit/core/auth/{test_sql_auth,test_windows_auth,test_azure_ad,test_common}.py` → `test/sqlpinger/unit/engines/sqlserver/auth/`. No logic changes; only import paths and the references to the renamed `SqlServerAuthStrategyFactory` / `SqlServerAuthTypes`.
- `test/sqlpinger/unit/core/test_downtime.py` and `test/sqlpinger/unit/util/test_logger.py` — unchanged.

**New tests under `test/sqlpinger/unit/engines/postgres/`**:
- `test_sql_commands.py` — `build_pg_sleep_sql(N)` returns `"SELECT pg_sleep(N)"` for several inputs (including `0` and a large number).
- `test_connection.py` — mocks `sqlpinger.engines.postgres.connection.psycopg2.connect`; verifies `connect_timeout=<timeout>` kwarg, `is_connected()` true when `closed == 0` and false when `closed != 0`, and the disconnect-swallows-exception behavior (mirrors the existing sqlserver test).
- `auth/test_sql_auth.py` — three cases for `PostgresSqlAuth.get_connection_string`:
  1. Trivial username/password produces `postgresql://u:p@host:5432/db?connect_timeout=5&sslmode=require`.
  2. **Special chars in password** (e.g., `p@ss word!` and `pa'ss\\x`) are percent-encoded — this is the key regression guard for the libpq escape issue.
  3. Non-default `port` and `sslmode` flow through into the URI.
- `auth/test_common.py` — mirrors `test/sqlpinger/unit/core/auth/test_common.py`:
  - `test_create_when_sql_authentication` — returns `PostgresSqlAuth`.
  - `test_create_when_sql_authentication_missing_inputs` — raises `ValueError` with the expected message.
  - `test_invalid_auth_method` — raises `NotImplementedError` for `windows` and `azure-ad`.

**New CLI tests** (`test/sqlpinger/unit/test_cli.py`) using `click.testing.CliRunner`. Each test patches `AvailabilityMonitor` at module level so `start_monitoring` is never actually invoked:
- `test_root_help_lists_both_subcommands` — `--help` output contains `mssql` and `pg`.
- `test_mssql_help_includes_driver_excludes_port` — `mssql --help` mentions `--driver` and not `--port`/`--sslmode`.
- `test_pg_help_includes_port_and_sslmode_excludes_driver` — symmetric assertion for `pg --help`.
- `test_pg_rejects_windows_auth` — `pg --auth windows ...` exits non-zero with a Click error mentioning the invalid choice.
- `test_pg_rejects_unknown_driver_option` — `pg --driver foo ...` fails with "no such option".
- `test_mssql_wires_sqlserver_components` — patches `SqlServerEngine`, `SqlServerAuthStrategyFactory`, and `AvailabilityMonitor`; verifies they were instantiated/called with the CLI inputs.
- `test_pg_wires_postgres_components` — symmetric assertion for `pg`.

## Verification

End-to-end checks before merging:

1. **Tests pass**:
   ```
   poetry run pytest test/sqlpinger/unit
   poetry run coverage run -m pytest test/sqlpinger/unit && poetry run coverage report
   ```
2. **CLI surface** — the help screens are clean and engine-specific:
   ```
   poetry run sqlpinger --help          # lists subcommands: mssql, pg
   poetry run sqlpinger mssql --help    # only sqlserver flags (incl. --driver)
   poetry run sqlpinger pg --help       # only postgres flags (incl. --port, --sslmode); no --driver
   ```
3. **SQL Server flow**:
   ```
   poetry run sqlpinger mssql --server <host> --database <db> --auth sql --username <u>
   poetry run sqlpinger mssql --server <host> --database <db> --auth azure-ad
   poetry run sqlpinger mssql --server <host> --database <db> --auth windows
   ```
4. **PostgreSQL flow** against an Azure PG Flexible Server (or local Postgres for smoke):
   ```
   poetry run sqlpinger pg --server <host> --database <db> --auth sql --username <u>
   poetry run sqlpinger pg --server <host> --database <db> --auth sql --username <u> --port 5432 --sslmode require
   ```
   Verify: heartbeat issues `SELECT pg_sleep(<interval>)` (psql/`pg_stat_activity` will show it), Ctrl+C summary JSON renders the same shape.
5. **Click rejects invalid combinations automatically** (no manual validation needed):
   ```
   poetry run sqlpinger pg --auth windows ...    # fails: 'windows' not in choices for `pg`
   poetry run sqlpinger pg --driver ... ...      # fails: no such option
   poetry run sqlpinger mssql --port 5432 ...    # fails: no such option
   ```
6. **Connection failure detection**: kill the server / firewall briefly while the monitor runs; confirm a downtime is recorded, recovery is logged, and the JSON summary on Ctrl+C is correct for both engines.
7. **Build still produces a wheel**: `poetry build` and confirm `dist/*.whl` ships with `psycopg2-binary` declared and the `sqlpinger` entry point bound to `sqlpinger.cli:cli`.

## Out of scope (explicit non-goals for this iteration)

- Azure AD auth for PostgreSQL (deferred — would need `azure-identity` token + `password=<token>` flow with a custom expiration handler).
- Auto-detecting engine from the connection target.
- Renaming `--driver` to `--odbc-driver`.
- Updating `CLAUDE.md` — can be done as a follow-up after the implementation lands and the architecture is finalized.
