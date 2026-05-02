import time
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor

import gradio as gr
import requests

from src.analyzer import count_lines_by_language
from src.constants import (
    APP_SUBTITLE,
    APP_TITLE,
    BG_COLOR,
    C_LINK,
    C_MUTED,
    C_TEXT,
    FONT_FAMILY,
    FONT_SIZE,
    GITHUB_URL,
    PROGRESS_THROTTLE,
)
from src.github import parse_repo_url
from src.models import ProgressState
from src.rendering import _error_html, render_html


def analyze_repo(url: str) -> Generator[str, None, None]:
    if not url or not url.strip():
        yield _error_html("Enter a GitHub repository URL or owner/repo.")
        return
    try:
        owner, repo = parse_repo_url(url)
        state = ProgressState()

        def _run() -> tuple[dict[str, int], int]:
            return count_lines_by_language(owner, repo, state=state)

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run)
            while not future.done():
                time.sleep(PROGRESS_THROTTLE)
                with state.lock:
                    snap_langs = dict(state.languages)
                    snap_completed = state.completed
                    snap_total = state.total
                if snap_total > 0:
                    yield render_html(
                        snap_langs,
                        owner=owner,
                        repo=repo,
                        completed=snap_completed,
                        total=snap_total,
                    )
            languages, total_files = future.result()

        yield render_html(
            languages, owner=owner, repo=repo, completed=total_files, total=total_files
        )
    except ValueError as e:
        yield _error_html(str(e))
    except requests.ConnectionError:
        yield _error_html("Failed to connect to GitHub. Check your network connection.")
    except requests.Timeout:
        yield _error_html("Request timed out. Try again later.")
    except Exception as e:
        yield _error_html(f"Unexpected error: {e}")


_CSS = f"""
* {{ border-radius: 0 !important; }}
.gradio-container {{
    max-width: 100% !important;
    padding: 8px 0 !important;
    background: {BG_COLOR} !important;
    font-family: {FONT_FAMILY} !important;
}}
.main, .contain, .wrap, .block {{ background: transparent !important; padding: 0 !important; max-width: 100% !important; border: none !important; }}
.gradio-container [class*="html-container"] {{ padding: 0 !important; }}
.column {{ gap: 4px !important; padding: 0 16px 0 2ch !important; }}
footer, header {{ display: none !important; }}
#app-title-wrap {{ padding: 0 !important; background: transparent !important; }}
#app-title-wrap > div {{ background: transparent !important; }}

/* kill all gradio wrapper chrome on the input */
#cli {{
    position: relative;
    padding-left: 20ch !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
    overflow: visible !important;
}}
#cli label, #cli .input-container {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
}}
#cli .label-wrap {{ display: none !important; }}
#cli textarea, #cli input {{
    font-family: {FONT_FAMILY} !important;
    font-size: {FONT_SIZE} !important;
    background: transparent !important;
    color: {C_TEXT} !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
    padding: 8px 0 !important;
    caret-color: transparent;
}}
@keyframes blink {{ 50% {{ opacity: 0; }} }}
#cli-cursor {{
    position: absolute;
    left: 20ch;
    top: 50%;
    transform: translateY(-50%);
    color: {C_TEXT};
    font-family: {FONT_FAMILY};
    font-size: {FONT_SIZE};
    pointer-events: none;
    z-index: 1;
    animation: blink 1s step-end infinite;
}}
#cli::before {{
    content: '\\00a0github repository:';
    position: absolute;
    left: 0;
    top: 50%;
    transform: translateY(-50%);
    color: {C_TEXT};
    font-family: {FONT_FAMILY};
    font-size: {FONT_SIZE};
    z-index: 1;
    pointer-events: none;
}}
"""

_HEAD = """
<script>
(function init() {
    const cli = document.getElementById('cli');
    if (!cli) { setTimeout(init, 200); return; }

    function setup() {
        const input = cli.querySelector('textarea') || cli.querySelector('input');
        if (!input) return;

        cli.style.overflow = 'visible';
        input.style.position = 'relative';
        input.style.zIndex = '50';

        if (cli.querySelector('#cli-cursor')) return;

        input.setAttribute('spellcheck', 'false');

        const overlay = document.createElement('div');
        overlay.style.cssText = 'position:absolute;inset:0;pointer-events:none;z-index:1;';

        const cur = document.createElement('span');
        cur.id = 'cli-cursor';
        cur.textContent = '\u2588';
        overlay.appendChild(cur);

        const measure = document.createElement('span');
        measure.id = 'cli-measure';
        measure.style.cssText = 'position:absolute;visibility:hidden;white-space:pre;pointer-events:none;' +
            getComputedStyle(input).font;
        overlay.appendChild(measure);

        cli.appendChild(overlay);

        const update = () => {
            const pos = input.selectionStart ?? input.value.length;
            measure.textContent = input.value.substring(0, pos);
            const ch = parseFloat(getComputedStyle(input).fontSize) * 0.6;
            cur.style.left = (20 * ch + measure.offsetWidth) + 'px';
        };
        input.addEventListener('input', update);
        input.addEventListener('keyup', update);
        input.addEventListener('click', update);
        input.addEventListener('select', update);
        new MutationObserver(update).observe(input, {attributes: true, childList: true});
        update();
        document.addEventListener('keydown', (e) => {
            if (document.activeElement !== input && !e.ctrlKey && !e.metaKey)
                input.focus();
        });
        input.focus();
    }

    setup();
    new MutationObserver(setup).observe(cli, { childList: true, subtree: true });
})();
</script>
"""


_TITLE_HTML = (
    f'<div id="app-title" style="'
    f"font-family:{FONT_FAMILY};"
    f"font-size:{FONT_SIZE};color:{C_MUTED};padding:12px 0 4px 0;"
    f'">'
    f'<a href="{GITHUB_URL}" target="_blank" '
    f'style="color:{C_LINK};text-decoration:none;font-weight:bold">{APP_TITLE}</a>'
    f"</br>"
    f'<span style="color:{C_TEXT};font-style:italic;margin-left:1ch">{APP_SUBTITLE}</span>'
    f"</br></br>"
    f"</div>"
)


def create_app() -> gr.Blocks:
    with gr.Blocks(
        title=APP_TITLE,
    ) as app:
        gr.HTML(_TITLE_HTML, elem_id="app-title-wrap")
        url_input = gr.Textbox(
            show_label=False,
            placeholder="owner/repo",
            elem_id="cli",
            container=False,
            autofocus=True,
        )
        output = gr.HTML()
        url_input.submit(fn=analyze_repo, inputs=url_input, outputs=output)

    return app


def launch_app(app: gr.Blocks) -> None:
    app.launch(
        theme=gr.themes.Monochrome(),  # type: ignore[attr-defined]
        css=_CSS,
        head=_HEAD,
    )
