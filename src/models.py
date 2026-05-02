import threading

from pydantic import BaseModel


class CacheEntry(BaseModel):
    data: dict[str, int]
    files: int
    time: float


class ProgressState:
    def __init__(self) -> None:
        self.languages: dict[str, int] = {}
        self.completed: int = 0
        self.total: int = 0
        self.lock: threading.Lock = threading.Lock()
