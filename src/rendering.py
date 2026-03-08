from html import escape

from src.models import ProgressInfo

PROGRESS_WIDTH: int = 100
BAR_WIDTH: int = 100
PRE_STYLE: str = (
    "font-family:'JetBrains Mono','Fira Code','SF Mono','Consolas',monospace;"
    "font-size:14px;line-height:1.5;color:#b0b0b0;background:transparent;"
    "padding:0;border:none;margin:0;white-space:pre;overflow-x:auto"
)


def _pre(text: str) -> str:
    return f'<pre style="{PRE_STYLE}">{text}</pre>'


def render_html(languages: dict[str, int], owner: str = "", repo: str = "") -> str:
    if not languages:
        return _error_html("No code files found in this repository.")

    sorted_langs = sorted(languages.items(), key=lambda x: -x[1])
    total = sum(languages.values())

    repo_url = f"https://github.com/{escape(owner)}/{escape(repo)}"
    lines: list[str] = []
    lines.append(f"repo-stats -- lines of code by language")
    lines.append(
        f'Repository: <a href="{repo_url}" target="_blank" style="color:#b0b0b0">{repo_url}</a>'
    )

    for lang, loc in sorted_langs:
        pct = loc / total
        filled = round(pct * BAR_WIDTH)
        bar = "#" * filled + "." * (BAR_WIDTH - filled)
        lines.append(f"    {escape(lang):<12s} {bar}  {pct:>8.2%}  {loc:>10,}")

    lines.append(f"    {'':12s} {'-' * BAR_WIDTH}  {'-' * 8}  {'-' * 10}")
    lines.append(f"    {'Total':<12s} {'':>{BAR_WIDTH}s}  {'100.00%':>8s}  {total:>10,}")
    return _pre("\n".join(lines))


def _error_html(message: str) -> str:
    lines = [
        "repo-stats -- lines of code by language",
        f"error: {escape(message)}",
    ]
    return _pre("\n".join(lines))


def _progress_html(progress: ProgressInfo) -> str:
    if progress.total == 0:
        pct = 0.0
    else:
        pct = progress.completed / progress.total
    filled = round(pct * PROGRESS_WIDTH)
    bar = "#" * filled + "." * (PROGRESS_WIDTH - filled)
    text = f"{progress.desc}\n[{bar}] {pct:.2%}  {progress.completed}/{progress.total} files"
    return _pre(text)
