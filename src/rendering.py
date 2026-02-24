from html import escape

from src.models import ProgressInfo

BAR_WIDTH: int = 46
PRE_STYLE: str = (
    "font-family:'JetBrains Mono','Fira Code','SF Mono','Consolas',monospace;"
    "font-size:14px;line-height:1.5;color:#b0b0b0;background:transparent;"
    "padding:0;border:none;margin:0;white-space:pre;overflow-x:auto"
)
CURSOR: str = '<span style="animation:blink 1s step-end infinite">\u2588</span>'
BLINK_CSS: str = "<style>@keyframes blink{50%{opacity:0}}</style>"
PROGRESS_WIDTH: int = 40


def _pre(text: str) -> str:
    return f'{BLINK_CSS}<pre style="{PRE_STYLE}">{text}</pre>'


def render_html(languages: dict[str, int], url: str = "") -> str:
    if not languages:
        return _error_html("No code files found in this repository.")

    sorted_langs = sorted(languages.items(), key=lambda x: -x[1])
    total = sum(languages.values())

    lines: list[str] = []
    lines.append(f"repo-stats -- lines of code by language")
    lines.append(f"Repository: {escape(url)}")

    first = True
    for lang, loc in sorted_langs:
        pct = loc / total * 100
        filled = round(pct / 100 * BAR_WIDTH)
        bar = "#" * filled + "." * (BAR_WIDTH - filled)
        prefix = " &gt;" if first else "  "
        first = False
        lines.append(f"{prefix} {escape(lang):<20s} {bar}  {loc:>10,}  {pct:>6.1f}%")

    lines.append(f"   {'':20s} {'_' * BAR_WIDTH}  {'_' * 10}  {'_' * 6}")
    lines.append("")
    lines.append(f"{'Total':<20s} {'':>{BAR_WIDTH}s}  {total:>10,}  100.0%")
    lines.append(f"&gt; {CURSOR}")

    return _pre("\n".join(lines))


def _error_html(message: str) -> str:
    lines = [
        "repo-stats \u2014 lines of code by language",
        f"error: {escape(message)}",
        f"{CURSOR}",
    ]
    return _pre("\n".join(lines))


def _progress_html(progress: ProgressInfo) -> str:
    if progress.total == 0:
        pct = 0.0
    else:
        pct = progress.completed / progress.total
    filled = round(pct * PROGRESS_WIDTH)
    bar = "#" * filled + "." * (PROGRESS_WIDTH - filled)
    pct_str = f"{pct * 100:5.1f}%"
    text = (
        f"{progress.desc}\n[{bar}] {pct_str}  {progress.completed}/{progress.total} files\n{CURSOR}"
    )
    return _pre(text)
