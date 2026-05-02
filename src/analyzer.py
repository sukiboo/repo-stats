import time
from concurrent.futures import Future, ThreadPoolExecutor, as_completed

from src.constants import CACHE, CACHE_TTL, EXTENSION_MAP, MAX_WORKERS
from src.github import fetch_file_lines, get_default_branch, get_file_tree
from src.models import CacheEntry, ProgressState
from src.utils import _get_ext, _should_count


def count_lines_by_language(
    owner: str,
    repo: str,
    state: ProgressState | None = None,
) -> tuple[dict[str, int], int]:
    cache_key = f"{owner}/{repo}"
    now = time.time()
    if cache_key in CACHE and now - CACHE[cache_key].time < CACHE_TTL:
        entry = CACHE[cache_key]
        return entry.data, entry.files

    branch = get_default_branch(owner, repo)
    all_paths = get_file_tree(owner, repo, branch)
    paths = [p for p in all_paths if _should_count(p)]

    if not paths:
        raise ValueError("No code files found in this repository.")

    total = len(paths)
    languages: dict[str, int] = {} if state is None else state.languages
    if state is not None:
        with state.lock:
            state.total = total

    def _fetch(path: str) -> tuple[str, int]:
        lines = fetch_file_lines(owner, repo, branch, path)
        ext = _get_ext(path)
        lang = EXTENSION_MAP.get(ext, "Other")
        return lang, lines

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures: dict[Future[tuple[str, int]], str] = {pool.submit(_fetch, p): p for p in paths}
        for future in as_completed(futures):
            lang, lines = future.result()
            if state is None:
                if lines > 0:
                    languages[lang] = languages.get(lang, 0) + lines
            else:
                with state.lock:
                    if lines > 0:
                        languages[lang] = languages.get(lang, 0) + lines
                    state.completed += 1

    CACHE[cache_key] = CacheEntry(data=languages, files=total, time=time.time())
    return languages, total
