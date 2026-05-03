import time
from concurrent.futures import Future, ThreadPoolExecutor, as_completed

from src.constants import CACHE, CACHE_TTL, EXTENSION_MAP, MAX_WORKERS
from src.github import (
    fetch_file_lines,
    get_commit_histogram,
    get_default_branch,
    get_file_tree,
    get_repo_meta,
)
from src.models import CacheEntry, ProgressState, RepoStats
from src.utils import _get_ext, _should_count


def count_lines_by_language(
    owner: str,
    repo: str,
    state: ProgressState | None = None,
) -> RepoStats:
    cache_key = f"{owner}/{repo}"
    now = time.time()
    if cache_key in CACHE and now - CACHE[cache_key].time < CACHE_TTL:
        return CACHE[cache_key].stats

    branch = get_default_branch(owner, repo)
    all_entries = get_file_tree(owner, repo, branch)
    entries = [(p, s) for p, s in all_entries if _should_count(p)]
    entries.sort(key=lambda e: e[1], reverse=True)
    paths = [p for p, _ in entries]

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

    def _on_meta_done(fut: Future[tuple[int, int]]) -> None:
        try:
            commits, branches = fut.result()
        except Exception:
            return
        if state is not None:
            with state.lock:
                state.commits = commits
                state.branches = branches

    def _on_histo_done(fut: Future[list[tuple[int, int]]]) -> None:
        try:
            histogram = fut.result()
        except Exception:
            return
        if state is not None:
            with state.lock:
                state.histogram = histogram

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        meta_future = pool.submit(get_repo_meta, owner, repo, branch)
        histo_future = pool.submit(get_commit_histogram, owner, repo)
        meta_future.add_done_callback(_on_meta_done)
        histo_future.add_done_callback(_on_histo_done)

        file_futures: dict[Future[tuple[str, int]], str] = {
            pool.submit(_fetch, p): p for p in paths
        }
        for future in as_completed(file_futures):
            lang, lines = future.result()
            if state is None:
                if lines > 0:
                    languages[lang] = languages.get(lang, 0) + lines
            else:
                with state.lock:
                    if lines > 0:
                        languages[lang] = languages.get(lang, 0) + lines
                    state.completed += 1

        try:
            commits, branches = meta_future.result()
        except Exception:
            commits, branches = None, None
        try:
            histogram = histo_future.result()
        except Exception:
            histogram = []

    stats = RepoStats(
        languages=languages,
        files=total,
        commits=commits,
        branches=branches,
        histogram=histogram,
    )
    CACHE[cache_key] = CacheEntry(stats=stats, time=time.time())
    return stats
