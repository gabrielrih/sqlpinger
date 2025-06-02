# sqlpinger
A lightweight CLI tool to monitor SQL Server availability by continuously executing WAITFOR DELAY on the database. It automatically detects and logs downtime periods, including total duration and timestamps — and prints a summary report at the end of execution.

Perfect for testing connectivity, diagnosing intermittent issues or validating failovers.

## Features
- Continuous connection monitoring
- Detects and logs downtime periods
- Smart error grouping (no repeated messages for same errors)
- JSON-formatted summary with total downtime
- Supported authentication method: Azure AD (interactive login) and Windows Authentication
- Works with Azure SQL Database, Azure Managed Instance and on-prem SQL Server

## Installation
```
poetry install
```

## Example Usage
```
sqlpinger \
    --server my-server.database.windows.net \
    --database database-name
```

Available cli parameters ```sqlpinger --help```

![available cli parameters](.docs/cli_parameters.png)

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

## Coming soon
- One more authentication methods: SQL Authentication
