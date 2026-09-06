import os


def executable() -> str:
    return os.getenv("ADB_PATH", "adb")


def endpoints() -> list[str]:
    return [value.strip() for value in os.getenv("ADB_ENDPOINTS", "").split(",") if value.strip()]
