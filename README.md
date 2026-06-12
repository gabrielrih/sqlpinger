# sqlpinger
A lightweight CLI tool for monitoring database availability.

- For SQL Server it continuously executes `WAITFOR DELAY` queries;
- For Azure PostgreSQL Flexible Server it issues `SELECT pg_sleep(...)`.

In both cases it automatically detects and logs downtime intervals (with timestamps and total duration). When stopped (e.g., via Ctrl+C), it outputs a summary report. Perfect for connectivity testing, diagnosing intermittent failures or validating failover scenarios.

> In this context, "downtime" refers to any execution failure-not necessarily that the database is completely down.

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Things to keep in mind](#things-to-keep-in-mind)
- [Development](#development)

# Features
- Continuous connection monitoring
- Single immediate health check with `--once`
- Secure default SQL credentials per engine for quick checks
- Detects and logs downtime periods
- Smart error grouping (no repeated messages for same errors)
- JSON-formatted summary with total downtime in continuous mode
- **Supported engines**:
  - **SQL Server** (`sqlpinger mssql ...`) - heartbeat: `WAITFOR DELAY`. Works with Azure SQL Database, Azure Managed Instance and on-prem SQL Server.
  - **PostgreSQL** (`sqlpinger pg ...`) - heartbeat: `SELECT pg_sleep(...)`. Targeted at Azure PostgreSQL Flexible Server (or any standard Postgres).
- **Supported authentication methods**:
  - **SQL Server**:
    - **SQL Authentication** - `sql` - Recommended.
    - **Azure AD (interactive login)** - `azure-ad` - May prompt for credentials multiple times during execution.
    - **Windows Authentication** - `windows` - Only available on Windows and generally not suitable for production environments.
  - **PostgreSQL**:
    - **SQL Authentication** - `sql` - Native username/password (only method supported in this iteration).

# Installation

## Requirements

- [Python](https://www.python.org/downloads/) 3.12 or newer.

## Via GitHub Releases
You can install the tool by downloading the latest `.whl` file from the Releases page and installing it with pip:

```
wget -O "sqlpinger-1.6.0-py3-none-any.whl" "https://github.com/gabrielrih/sqlpinger/releases/download/v1.6.0/sqlpinger-1.6.0-py3-none-any.whl"
pip install --user sqlpinger-1.6.0-py3-none-any.whl
```

By doing that a ```sqlpinger.exe``` file will be created probably on the folder: ```C:\Users\user\AppData\Roaming\Python\Python312\Scripts```. So, you must add this folder on the user PATH.

To see the installed version you can run:

```
pip show sqlpinger
```

# Usage

The CLI exposes one subcommand per engine: `mssql` and `pg`.

## SQL Server

```
sqlpinger mssql \
    --server my-server.database.windows.net \
    --database database-name \
    --auth sql \
    --username my_user \
    --verbose
```

## PostgreSQL

```
sqlpinger pg \
    --server my-server.postgres.database.azure.com \
    --database database-name \
    --auth sql \
    --username my_user \
    --port 5432 \
    --sslmode require \
    --verbose
```

For a full list of options, run:

```
sqlpinger --help
sqlpinger mssql --help
sqlpinger pg --help
```

To run a single immediate health check and exit, add `--once`. In this mode
the CLI executes `SELECT 1`, prints the usual success or failure message, and
does not use `--interval` as a delay:

```
sqlpinger mssql --server my-server.database.windows.net --database database-name --auth sql --username my_user --once
sqlpinger pg --server my-server.postgres.database.azure.com --database database-name --auth sql --username my_user --once
```

## Default credentials for quick checks

For SQL authentication, you can save one default username/password pair per
engine in the operating-system keyring. This is useful when many servers share
the same diagnostic account:

```
sqlpinger credentials set --engine mssql --username dbm_user
sqlpinger credentials set --engine pg --username dbm_user
sqlpinger credentials status
sqlpinger credentials clear --engine mssql
```

The `set` command prompts for the password without echoing it. After defaults
are configured, omit `--username` and `--password` to use the saved credentials:

```
sqlpinger mssql --server my-server.database.windows.net --database database-name --auth sql --once
sqlpinger pg --server my-server.postgres.database.azure.com --database database-name --auth sql --once
```

If `--username` is provided, the saved defaults are ignored and the CLI uses
`--password` or prompts for one as before. Passing `--password` without
`--username` is rejected to avoid mixing explicit and default credentials.

> Be careful when using the authentication option `azure-ad` (SQL Server only). It will open a window prompting you to enter your credentials. However, this prompt may appear at any point during the tool's execution. If you miss it and don't complete the authentication, the tool will get stuck.

## Example output

```
Starting monitor for my-server.database.windows.net/database-name every 10s using SqlServerEngine + AzureADInteractive
Connection is healthy
Connection failed: [08S01] ... (error message)
Recovered. Downtime lasted 22s.
```

On Ctrl + C:
```json
{
  "summary": {
    "downtimes_quantity": 1,
    "total_downtime": "22 seconds"
  },
  "downtimes": [
    {
      "from": "2025-05-26 14:42:07",
      "to": "2025-05-26 14:42:29",
      "time": "22 seconds"
    }
  ]
}
```

# Things to keep in mind
In continuous mode, this CLI will consider as "downtime" anything that prevents a proper connection and execution of the heartbeat query (`WAITFOR DELAY` for SQL Server or `SELECT pg_sleep(...)` for PostgreSQL), including:

- Connection issues: Connection timeout, Network unreachable, host not found, TCP connection refused and more;
- Transient network errors: Temporary disruptions such as packet loss, high latency, or intermittent drops;
- Login failed by invalid credentials or authentication issues;
- Query execution timeout: The connection was successful, but the query didn't complete in time;
- Session forcibly closed: Unexpected termination of the connection, possibly due to idle timeout or security policies;
- Firewall or VPN blocking the connection;
- Cursor or connection forcibly closed: The database engine or client unexpectedly closed the session or cursor;
- Database restarts during execution;
- A `kill` on the query execution;

**Recommendations to reduce false positives:**
- Run this CLI on the **same local network** as the database to avoid VPN or network-related issues;
- Prefer **SQL authentication** to mitigate login failures from other auth methods.

# Development

This project uses [Poetry](https://python-poetry.org/) to manage dependencies and the virtual environment.

## Requirements
- [Python](https://www.python.org/downloads/) 3.12 or newer.
- [Poetry](https://python-poetry.org/docs/#installation).

## Installing dependencies

Install the runtime and development dependencies (pytest, coverage, freezegun):

```
poetry install
```

## Running the CLI from source

Once dependencies are installed, run the CLI through Poetry to use the local source instead of an installed wheel. The top-level `--help` lists the engine subcommands:

```
poetry run sqlpinger --help
poetry run sqlpinger mssql --help
poetry run sqlpinger pg --help
```

Example with arguments (SQL Server):

```
poetry run sqlpinger mssql \
    --server my-server.database.windows.net \
    --database database-name \
    --auth sql \
    --username my_user \
    --verbose
```

Example with arguments (PostgreSQL):

```
poetry run sqlpinger pg \
    --server my-server.postgres.database.azure.com \
    --database database-name \
    --auth sql \
    --username my_user \
    --verbose
```

## Running tests

```
poetry run pytest test/sqlpinger/unit
```

To run with coverage report:

```
poetry run coverage run -m pytest test/sqlpinger/unit
poetry run coverage report
```

## Building the wheel

```
poetry build
```

The generated `.whl` will be placed in the `dist/` folder.
