import json
import re

import requests

from src.constants import GITHUB_TOKEN, SKIP_DIRS
from src.utils import _get_ext


def parse_repo_url(url: str) -> tuple[str, str]:
    url = url.strip().rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]
    m = re.match(r"^git@github\.com:([^/]+)/([^/]+)$", url)
    if m:
        return m.group(1), m.group(2)
    url = re.sub(r"^https?://", "", url)
    url = re.sub(r"^github\.com/", "", url)
    parts = url.split("/")
    if len(parts) >= 2 and parts[0] and parts[1]:
        return parts[0], parts[1]
    raise ValueError("invalid repository url, use `owner/repo` or `https://github.com/owner/repo`")


def _api_headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    return headers


def get_default_branch(owner: str, repo: str) -> str:
    resp = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}", headers=_api_headers(), timeout=15
    )
    if resp.status_code == 404:
        raise ValueError(f"repository `https://github.com/{owner}/{repo}` not found")
    if resp.status_code == 403:
        raise ValueError("Rate limit exceeded. Try again later or set a GITHUB_TOKEN.")
    resp.raise_for_status()
    return resp.json()["default_branch"]


def get_file_tree(owner: str, repo: str, branch: str) -> list[str]:
    resp = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1",
        headers=_api_headers(),
        timeout=30,
    )
    if resp.status_code == 403:
        raise ValueError("Rate limit exceeded. Try again later or set a GITHUB_TOKEN.")
    resp.raise_for_status()
    data = resp.json()
    paths: list[str] = []
    for item in data.get("tree", []):
        if item["type"] != "blob":
            continue
        path = item["path"]
        parts = path.split("/")
        if any(p in SKIP_DIRS for p in parts):
            continue
        paths.append(path)
    return paths


def fetch_file_lines(owner: str, repo: str, branch: str, path: str) -> int:
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            return 0
        content = resp.text
    except Exception:
        return 0

    ext = _get_ext(path)
    if ext == ".ipynb":
        return _count_notebook_lines(content)
    return content.count("\n") + (1 if content and not content.endswith("\n") else 0)


def _count_notebook_lines(content: str) -> int:
    try:
        nb = json.loads(content)
    except (json.JSONDecodeError, ValueError):
        return 0
    total = 0
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        source = cell.get("source", [])
        if isinstance(source, list):
            total += len(source)
        elif isinstance(source, str):
            total += source.count("\n") + (1 if source and not source.endswith("\n") else 0)
    return total
