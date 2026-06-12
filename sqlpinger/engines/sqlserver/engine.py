from sqlpinger.core.connection import ConnectionManager
from sqlpinger.core.engine import Engine
from sqlpinger.engines.sqlserver.connection import SqlServerConnectionManager
from sqlpinger.engines.sqlserver.sql_commands import build_waitfor_delay_sql


class SqlServerEngine(Engine):
    def build_heartbeat_sql(self, seconds: int) -> str:
        return build_waitfor_delay_sql(seconds=seconds)

    def build_healthcheck_sql(self) -> str:
        return "SELECT 1"

    def create_connection_manager(self, conn_str: str, timeout: int) -> ConnectionManager:
        return SqlServerConnectionManager(conn_str, timeout=timeout)
