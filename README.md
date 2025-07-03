# sqlpinger
A lightweight CLI tool to monitor SQL Server availability by continuously executing WAITFOR DELAY on the database. It automatically detects and logs downtime periods, including total duration and timestamps — and prints a summary report when the user cancels its execution.

Perfect for testing connectivity, diagnosing intermittent issues or validating failovers.

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)

# Features
- Continuous connection monitoring
- Detects and logs downtime periods
- Smart error grouping (no repeated messages for same errors)
- JSON-formatted summary with total downtime
- Supported authentication method:
  - SQL Authentication - `sql` - Recommended one.
  - Azure AD (interactive login) - `azure-ad` - Be careful when using this option. You should need to enter the credentials more than once during the tool's execution.
  - Windows Authentication - `windows` - This option is probably not allowed in production environments, and you must be using Windows OS to use it.
- Works with Azure SQL Database, Azure Managed Instance and on-prem SQL Server

# Installation

## Requirements

- [Python](https://www.python.org/downloads/): >= 3.11

## Via GitHub Releases
You can install this tool by downloading the latest ```.whl``` file from GitHub Releases and using pip.

- Go to the [Releases page](https://github.com/gabrielrih/sqlpinger/releases/).
- Find the latest version and download the ```.whl``` file (Example, ```sqlpinger-1.0.0-py3-none-any.whl```).

Or you can download it from the terminal:

```
wget -O "sqlpinger-1.2.0-py3-none-any.whl" "https://github.com/gabrielrih/sqlpinger/releases/download/v1.2.0/sqlpinger-1.2.0-py3-none-any.whl"
```

- After downloading the .whl file, install it using pip:

```
pip install --user sqlpinger-1.2.0-py3-none-any.whl
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

Available cli parameters ```sqlpinger --help```

![available cli parameters](.docs/cli_parameters.png)

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
This CLI will consider as downtime anything that prevents a proper connection and execution of the WAITFOR DELAY query. It includes:
- **Connection issues**: Connection timeout, Network unreachable, host not found, TCP connection refused and more;
- **Transient network errors**: Temporary disruptions such as packet loss, high latency, or intermittent drops;
-**Login failed** by invalid credentials or SQL Server authentication issues;
- **Query execution timeout**: The connection was successful, but the query didn't complete in time;
- **Session forcibly closed**: Unexpected termination of the connection, possibly due to idle timeout or security policies;
- **Firewall or VPN blocking the connection**;
- **Cursor or connection forcibly closed**: The database engine or client unexpectedly closed the session or cursor;
- **SQL Server restarted** during execution;
- A `kill` on the query execution;
