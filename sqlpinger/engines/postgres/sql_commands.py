
def build_pg_sleep_sql(seconds: int) -> str:
    return f"SELECT pg_sleep({int(seconds)})"
