import time
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor, as_completed

from src.constants import CACHE, CACHE_TTL, EXTENSION_MAP, MAX_FILES, MAX_WORKERS
from src.github import fetch_file_lines, get_default_branch, get_file_tree
from src.models import CacheEntry, ProgressInfo
from src.utils import _get_ext, _should_count


def count_lines_by_language(
    owner: str,
    repo: str,
    on_progress: Callable[[ProgressInfo], None] | None = None,
) -> dict[str, int]:
    cache_key = f"{owner}/{repo}"
    now = time.time()
    if cache_key in CACHE and now - CACHE[cache_key].time < CACHE_TTL:
        return CACHE[cache_key].data

    if on_progress:
        on_progress(ProgressInfo(desc="Fetching repository info...", completed=0, total=0))
    branch = get_default_branch(owner, repo)

    if on_progress:
        on_progress(ProgressInfo(desc="Fetching file tree...", completed=0, total=0))
    all_paths = get_file_tree(owner, repo, branch)
    paths = [p for p in all_paths if _should_count(p)]

    if not paths:
        raise ValueError("No code files found in this repository.")

    if len(paths) > MAX_FILES:
        paths = paths[:MAX_FILES]

    languages: dict[str, int] = {}
    completed = 0
    total = len(paths)

    def _fetch(path: str) -> tuple[str, int]:
        lines = fetch_file_lines(owner, repo, branch, path)
        ext = _get_ext(path)
        lang = EXTENSION_MAP.get(ext, "Other")
        return lang, lines

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures: dict[Future[tuple[str, int]], str] = {pool.submit(_fetch, p): p for p in paths}
        for future in as_completed(futures):
            lang, lines = future.result()
            if lines > 0:
                languages[lang] = languages.get(lang, 0) + lines
            completed += 1
            if on_progress and completed % 10 == 0:
                on_progress(
                    ProgressInfo(desc="Counting lines...", completed=completed, total=total)
                )

    CACHE[cache_key] = CacheEntry(data=languages, time=time.time())
    return languages
