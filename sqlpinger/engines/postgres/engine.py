from sqlpinger.core.connection import ConnectionManager
from sqlpinger.core.engine import Engine
from sqlpinger.engines.postgres.connection import PostgresConnectionManager
from sqlpinger.engines.postgres.sql_commands import build_pg_sleep_sql


class PostgresEngine(Engine):
    def build_heartbeat_sql(self, seconds: int) -> str:
        return build_pg_sleep_sql(seconds=seconds)

    def create_connection_manager(self, conn_str: str, timeout: int) -> ConnectionManager:
        return PostgresConnectionManager(conn_str, timeout=timeout)
