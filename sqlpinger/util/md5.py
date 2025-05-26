import hashlib


def calculate_md5(message: str) -> str:
    return hashlib.md5(message.encode("utf-8")).hexdigest()
