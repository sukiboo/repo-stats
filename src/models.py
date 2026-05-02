from pydantic import BaseModel


class ProgressInfo(BaseModel):
    completed: int
    total: int
    languages: dict[str, int] = {}


class CacheEntry(BaseModel):
    data: dict[str, int]
    files: int
    time: float
