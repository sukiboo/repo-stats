import threading

from pydantic import BaseModel, Field


class RepoStats(BaseModel):
    languages: dict[str, int]
    files: int
    commits: int | None = None
    branches: int | None = None
    histogram: list[tuple[int, int]] = Field(default_factory=list)


class CacheEntry(BaseModel):
    stats: RepoStats
    time: float


class ProgressState:
    def __init__(self) -> None:
        self.languages: dict[str, int] = {}
        self.completed: int = 0
        self.total: int = 0
        self.lock: threading.Lock = threading.Lock()
        self.commits: int | None = None
        self.branches: int | None = None
        self.histogram: list[tuple[int, int]] | None = None
