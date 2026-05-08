
def build_waitfor_delay_sql(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"WAITFOR DELAY '{hours:02}:{minutes:02}:{secs:02}'"
