import datetime as dt
from html import escape

from src.constants import (
    C_ACCENT,
    C_BAR,
    C_ERROR,
    C_LABEL,
    C_LINK,
    C_MUTED,
    C_TEXT,
    FONT_FAMILY,
    FONT_SIZE,
    HISTOGRAM_HEIGHT,
    LANGUAGE_BAR_WIDTH,
    MIN_LANGUAGE_SHARE,
    PROGRESS_WIDTH,
)

_BLOCKS: str = " ▁▂▃▄▅▆▇█"


def _c(text: str, color: str, bold: bool = False, italic: bool = False) -> str:
    style = f"color:{color}"
    if bold:
        style += ";font-weight:bold"
    if italic:
        style += ";font-style:italic"
    return f'<span style="{style}">{text}</span>'


def _pre(text: str, tight: bool = False) -> str:
    lh = "1" if tight else "1.6"
    style = (
        f"font-family:{FONT_FAMILY};"
        f"font-size:{FONT_SIZE};line-height:{lh};color:{C_TEXT};background:transparent;"
        "padding:0;border:none;margin:0;white-space:pre-wrap;word-break:break-word"
    )
    return f'<pre style="{style}">{text}</pre>'


def _pad(text: str, visual_len: int, width: int) -> str:
    return text + " " * max(0, width - visual_len)


def _bucket_histogram(counts: list[int], width: int) -> list[int]:
    n = len(counts)
    if n == 0 or width <= 0:
        return []
    if n >= width:
        return [sum(counts[j * n // width : (j + 1) * n // width]) for j in range(width)]
    return [counts[j * n // width] for j in range(width)]


def _ts_to_iso(ts: int) -> str:
    return (dt.datetime(1970, 1, 1) + dt.timedelta(seconds=ts)).date().isoformat()


def _render_histogram_block(histogram: list[tuple[int, int]], width: int) -> str:
    if not histogram or width <= 0:
        return ""
    nonzero = [i for i, (_, c) in enumerate(histogram) if c > 0]
    if not nonzero:
        return ""
    trimmed = histogram[nonzero[0] : nonzero[-1] + 1]
    counts = [c for _, c in trimmed]

    buckets = _bucket_histogram(counts, width)
    max_count = max(buckets) if buckets else 0
    if max_count == 0:
        return ""

    total_eighths = HISTOGRAM_HEIGHT * 8
    heights = [round(b / max_count * total_eighths) for b in buckets]

    first_iso = _ts_to_iso(trimmed[0][0])
    mid_iso = _ts_to_iso((trimmed[0][0] + trimmed[-1][0]) // 2)
    last_iso = _ts_to_iso(trimmed[-1][0])

    title = "commit history "
    top_dashes = max(0, width - len(title))
    lines: list[str] = [
        "",
        "",
        " " + _c(title + "─" * top_dashes, C_MUTED),
    ]
    for row in range(HISTOGRAM_HEIGHT - 1, -1, -1):
        chars = "".join(_BLOCKS[max(0, min(8, h - row * 8))] for h in heights)
        lines.append(" " + _c(chars, C_BAR))

    total_gap = max(2, width - len(first_iso) - len(mid_iso) - len(last_iso))
    left_gap = total_gap // 2
    right_gap = total_gap - left_gap
    lines.append("")
    lines.append(
        " " + _c(f"{first_iso}{' ' * left_gap}{mid_iso}{' ' * right_gap}{last_iso}", C_MUTED)
    )

    return _pre("\n".join(lines), tight=True)


def render_html(
    languages: dict[str, int],
    owner: str = "",
    repo: str = "",
    completed: int = 0,
    total: int = 0,
    commits: int | None = None,
    branches: int | None = None,
    histogram: list[tuple[int, int]] | None = None,
) -> str:
    sep = _c("//", C_MUTED)
    g1, g2, g3 = "    ", "  ", "    "

    total_loc = sum(languages.values())
    has_langs = bool(languages) and total_loc > 0

    if has_langs:
        main = {k: v for k, v in languages.items() if v / total_loc >= MIN_LANGUAGE_SHARE}
        other = total_loc - sum(main.values())
        if other > 0:
            main["Other"] = other
        sorted_langs = sorted(main.items(), key=lambda x: (x[0] == "Other", -x[1]))
        lw = max(len(k) for k in main)
        nw = max(len(f"{v:,}") for v in main.values())
    else:
        lw, nw = 10, 7

    row_width = lw + len(g1) + LANGUAGE_BAR_WIDTH + len(g2) + 7 + len(g3) + nw

    lines: list[str] = ["", ""]

    stats_title = "stats "
    lines.append(" " + _c(stats_title + "─" * max(0, row_width - len(stats_title)), C_MUTED))

    if owner and repo:
        repo_url = f"https://github.com/{escape(owner)}/{escape(repo)}"
        repo_link = (
            f'<a href="{repo_url}" target="_blank" '
            f'style="color:{C_LINK};text-decoration:none">{repo_url}</a>'
        )
        lines.append(f" URL:{repo_link}")

    if total:
        done = completed >= total
        pct = 1.0 if done else completed / total
        filled = PROGRESS_WIDTH if done else round(pct * PROGRESS_WIDTH)
        pbar = _c("#" * filled, C_BAR) + _c("." * (PROGRESS_WIDTH - filled), C_MUTED)
        pct_str = _c("100%" if done else f"{pct:.0%}", C_ACCENT)
        lines.append(f" [{pbar}] {pct_str}")

    if not has_langs:
        if owner or total:
            return _pre("\n".join(lines))
        return _error_html("No code files found in this repository.")

    stats_parts: list[str] = [""]
    if branches is not None:
        stats_parts.append(_c(f"{branches:,} branches", C_TEXT))
    if commits is not None:
        stats_parts.append(_c(f"{commits:,} commits", C_TEXT))
    if total:
        stats_parts.append(_c(f"{total:,} files", C_TEXT))
    stats_parts.append(_c(f"{total_loc:,} lines of code", C_TEXT))

    lines += [
        f" {sep} ".join(stats_parts),
        "",
    ]

    dashes = max(0, row_width - len("language") - len("lines") - 2)
    hdr = _c(f"language {'─' * dashes} lines", C_MUTED)
    lines.append(" " + hdr)

    for lang, loc in sorted_langs:
        pct = loc / total_loc
        filled = round(pct * LANGUAGE_BAR_WIDTH)
        bar = _c("#" * filled, C_BAR) + _c("." * (LANGUAGE_BAR_WIDTH - filled), C_MUTED)

        lang_col = _pad(_c(escape(lang), C_LABEL), len(lang), lw)
        pct_str = _c(f"{pct:>7.2%}", C_ACCENT)
        loc_str = _c(f"{loc:>{nw},}", C_TEXT)

        lines.append(f" {lang_col}{g1}{bar}{g2}{pct_str}{g3}{loc_str}")

    if histogram:
        lines.append("\n")
        chart_html = _pre("\n".join(lines))
        return chart_html + _render_histogram_block(histogram, row_width)
    return _pre("\n".join(lines))


def _error_html(message: str) -> str:
    lines = [
        f"{_c('error:', C_ERROR, bold=True)} {_c(escape(message), C_TEXT)}",
    ]
    return _pre("\n".join(lines))
