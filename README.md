# sqlpinger
A lightweight CLI tool for monitoring SQL Server availability. It continuously executes `WAITFOR DELAY` queries, automatically detecting and logging downtime intervals (with timestamps and total duration). When stopped (e.g., via Ctrl+C), it outputs a summary report.

> In this context, "downtime" refers to any execution failure—not necessarily that the SQL Server is completely down.

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Things to keep in mind](#things-to-keep-in-mind)

# Features
- Continuous connection monitoring
- Detects and logs downtime periods
- Smart error grouping (no repeated messages for same errors)
- JSON-formatted summary with total downtime
- **Supported authentication methods**:
  - **SQL Authentication** - `sql` - Recommended.
  - **Azure AD (interactive login)** - `azure-ad` - May prompt for credentials multiple times during execution.
  - **Windows Authentication** - `windows` - Only available on Windows and generally not suitable for production environments.
- Works with Azure SQL Database, Azure Managed Instance and on-prem SQL Server

# Installation

## Requirements

- [Python](https://www.python.org/downloads/) 3.11 or newer.

## Via GitHub Releases
You can install the tool by downloading the latest `.whl` file from the Releases page and installing it with pip:

```
wget -O "sqlpinger-1.3.0-py3-none-any.whl" "https://github.com/gabrielrih/sqlpinger/releases/download/v1.3.0/sqlpinger-1.3.0-py3-none-any.whl"
pip install --user sqlpinger-1.3.0-py3-none-any.whl
```

By doing that a ```sqlpinger.exe``` file will be created probably on the folder: ```C:\Users\user\AppData\Roaming\Python\Python312\Scripts```. So, you must add this folder on the user PATH.

To see the installed version you can run:

```
pip show sqlpinger
```

# Usage

```
sqlpinger \
    --server my-server.database.windows.net \
    --database database-name \
    --auth sql \
    --username my_user \
    --verbose
```

For a full list of options, run: ```sqlpinger --help```

> Be careful when using the authentication option `azure-ad`. It will open a window prompting you to enter your credentials. However, this prompt may appear at any point during the tool's execution. If you miss it and don't complete the authentication, the tool will get stuck.

## Example output

```
Starting monitor for my-server.database.windows.net/datbase-name every 10s using AzureADInteractive
✅ Connection is healthy
❌ Connection failed: [08S01] ... (error message)
✅ Recovered. Downtime lasted 22s.
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
This CLI will consider as "downtime" anything that prevents a proper connection and execution of the `WAITFOR DELAY` query, including:

- Connection issues: Connection timeout, Network unreachable, host not found, TCP connection refused and more;
- Transient network errors: Temporary disruptions such as packet loss, high latency, or intermittent drops;
- Login failed by invalid credentials or SQL Server authentication issues;
- Query execution timeout: The connection was successful, but the query didn't complete in time;
- Session forcibly closed: Unexpected termination of the connection, possibly due to idle timeout or security policies;
- Firewall or VPN blocking the connection;
- Cursor or connection forcibly closed: The database engine or client unexpectedly closed the session or cursor;
- SQL Server restartes during execution;
- A `kill` on the query execution;

**Recommendations to reduce false positives:**
- Run this CLI on the **same local network** as the SQL Server to avoid VPN or network-related issues;
- Prefer **SQL authentication** to mitigate login failures from other auth methods.
