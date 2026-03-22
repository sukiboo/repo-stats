from html import escape

from src.constants import (
    BAR_WIDTH,
    C_ACCENT,
    C_BAR,
    C_ERROR,
    C_LABEL,
    C_LINK,
    C_MUTED,
    C_TEXT,
    FONT_FAMILY,
    FONT_SIZE,
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


def render_html(
    languages: dict[str, int], owner: str = "", repo: str = "", total_files: int = 0
) -> str:
    if not languages:
        return _error_html("No code files found in this repository.")

    total = sum(languages.values())
    threshold = 0.005
    main = {k: v for k, v in languages.items() if v / total >= threshold}
    other = total - sum(main.values())
    if other > 0:
        main["Other"] = other
    sorted_langs = sorted(
        main.items(),
        key=lambda x: (x[0] == "Other", -x[1]),
    )

    lw = max(len(k) for k in main)
    nw = max(len(f"{v:,}") for v in main.values())
    g1, g2, g3 = "    ", "  ", "    "

    repo_url = f"https://github.com/{escape(owner)}/{escape(repo)}"
    lines: list[str] = []

    if total_files:
        pbar = _c("#" * PROGRESS_WIDTH, C_BAR)
        counter = _c(f"{total_files} files", C_TEXT)
        pct_str = _c("100%", C_ACCENT)
        lines.append(f" {pct_str} [{pbar}] {_c('//', C_MUTED)} {counter}")

    repo_link = f'<a href="{repo_url}" target="_blank" style="color:{C_LINK};text-decoration:none">{repo_url}</a>'
    lines += [
        "\n",
        f' {repo_link} {_c("//", C_MUTED)} {_c(f"{total:,} lines of code", C_TEXT)}',
        "",
    ]

    row_width = lw + len(g1) + BAR_WIDTH + len(g2) + 7 + len(g3) + nw
    hdr = (
        _pad(_c("language", C_MUTED), 8, lw)
        + g1
        + " " * BAR_WIDTH
        + g2
        + " " * 7
        + g3
        + _c(f"{'lines':>{nw}s}", C_MUTED)
    )
    lines += [" " + hdr, " " + _c("\u2500" * row_width, C_MUTED)]

    for lang, loc in sorted_langs:
        pct = loc / total
        filled = round(pct * BAR_WIDTH)
        bar = _c("#" * filled, C_BAR) + _c("." * (BAR_WIDTH - filled), C_MUTED)

        lang_col = _pad(_c(escape(lang), C_LABEL), len(lang), lw)
        pct_str = _c(f"{pct:>7.2%}", C_ACCENT)
        loc_str = _c(f"{loc:>{nw},}", C_TEXT)

        lines.append(f" {lang_col}{g1}{bar}{g2}{pct_str}{g3}{loc_str}")

    return _pre("\n".join(lines))


def _error_html(message: str) -> str:
    lines = [
        f"{_c('error:', C_ERROR, bold=True)} {_c(escape(message), C_TEXT)}",
    ]
    return _pre("\n".join(lines))


def _progress_html(progress: ProgressInfo) -> str:
    if progress.total == 0:
        pct = 0.0
    else:
        pct = progress.completed / progress.total
    filled = round(pct * PROGRESS_WIDTH)
    bar = _c("#" * filled, C_BAR) + _c("." * (PROGRESS_WIDTH - filled), C_MUTED)

    counter = _c(f"{progress.completed}/{progress.total} files", C_TEXT)
    pct_str = _c(f"{pct:.0%}", C_ACCENT)

    return _pre(f" {pct_str} [{bar}] {_c('//', C_MUTED)} {counter}")
