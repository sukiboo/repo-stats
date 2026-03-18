from html import escape

from src.constants import (
    BAR_WIDTH,
    C_BRIGHT,
    C_CYAN,
    C_DIM,
    C_GREEN,
    C_RED,
    C_TEXT,
    C_YELLOW,
    FONT_FAMILY,
    FONT_SIZE,
    LANG_WIDTH,
    PROGRESS_WIDTH,
)
from src.models import ProgressInfo

PRE_STYLE: str = (
    f"font-family:{FONT_FAMILY};"
    f"font-size:{FONT_SIZE};line-height:1.6;color:{C_TEXT};background:transparent;"
    "padding:0;border:none;margin:0;white-space:pre-wrap;word-break:break-word"
)


def _c(text: str, color: str, bold: bool = False, italic: bool = False) -> str:
    style = f"color:{color}"
    if bold:
        style += ";font-weight:bold"
    if italic:
        style += ";font-style:italic"
    return f'<span style="{style}">{text}</span>'


def _pre(text: str) -> str:
    return f'<pre style="{PRE_STYLE}">{text}</pre>'


def _pad(text: str, visual_len: int, width: int) -> str:
    return text + " " * max(0, width - visual_len)


def render_html(languages: dict[str, int], owner: str = "", repo: str = "") -> str:
    if not languages:
        return _error_html("No code files found in this repository.")

    sorted_langs = sorted(languages.items(), key=lambda x: -x[1])
    total = sum(languages.values())

    repo_url = f"https://github.com/{escape(owner)}/{escape(repo)}"
    lines: list[str] = []

    repo_link = f'<a href="{repo_url}" target="_blank" style="color:{C_CYAN};text-decoration:none">{repo_url}</a>'
    lines.append(
        f'Repository: {repo_link}  {_c("//", C_DIM)}  {_c(f"{total:,} lines of code", C_TEXT)}'
    )
    lines.append("")

    hdr_lang = _pad(_c("language", C_DIM), len("language"), LANG_WIDTH)
    hdr_bar = " " * BAR_WIDTH
    hdr_pct = _c(f"{'%':>7s}", C_DIM)
    hdr_lines = _c(f"{'lines':>10s}", C_DIM)
    lines.append(f"{hdr_lang} {hdr_bar}  {hdr_pct}  {hdr_lines}")
    sep = _c("\u2500" * (LANG_WIDTH + 1 + BAR_WIDTH + 2 + 7 + 2 + 10), C_DIM)
    lines.append(sep)
    lines.append("")

    for lang, loc in sorted_langs:
        pct = loc / total
        filled = round(pct * BAR_WIDTH)
        bar = _c("#" * filled, C_GREEN) + _c("." * (BAR_WIDTH - filled), C_DIM)

        lang_col = _pad(_c(escape(lang), C_BRIGHT), len(lang), LANG_WIDTH)
        pct_str = _c(f"{pct:>7.2%}", C_YELLOW)
        loc_str = _c(f"{loc:>10,}", C_TEXT)

        lines.append(f"{lang_col} {bar}  {pct_str}  {loc_str}")

    return _pre("\n".join(lines))


def _error_html(message: str) -> str:
    lines = [
        f"{_c('error:', C_RED, bold=True)} {_c(escape(message), C_TEXT)}",
    ]
    return _pre("\n".join(lines))


def _progress_html(progress: ProgressInfo) -> str:
    if progress.total == 0:
        pct = 0.0
    else:
        pct = progress.completed / progress.total
    filled = round(pct * PROGRESS_WIDTH)
    bar = _c("#" * filled, C_GREEN) + _c("." * (PROGRESS_WIDTH - filled), C_DIM)

    desc = _c(progress.desc, C_DIM, italic=True)
    counter = _c(f"{progress.completed}/{progress.total} files", C_TEXT)
    pct_str = _c(f"{pct:.2%}", C_YELLOW)

    text = f"{desc}\n[{bar}] {pct_str}  {counter}"
    return _pre(text)
