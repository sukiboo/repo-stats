import time
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor

import gradio as gr
import requests

from src.analyzer import count_lines_by_language
from src.github import parse_repo_url
from src.models import ProgressInfo
from src.rendering import _error_html, _progress_html, render_html


def analyze_repo(url: str) -> Generator[str, None, None]:
    if not url or not url.strip():
        yield _error_html("Enter a GitHub repository URL or owner/repo.")
        return
    try:
        owner, repo = parse_repo_url(url)

        def _on_progress(progress: ProgressInfo) -> None:
            _on_progress.pending = _progress_html(progress)  # type: ignore[attr-defined]

        _on_progress.pending = None  # type: ignore[attr-defined]

        def _run() -> dict[str, int]:
            return count_lines_by_language(owner, repo, on_progress=_on_progress)

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run)
            while not future.done():
                if _on_progress.pending:  # type: ignore[attr-defined]
                    yield _on_progress.pending  # type: ignore[attr-defined]
                    _on_progress.pending = None  # type: ignore[attr-defined]
                time.sleep(0.15)
            languages = future.result()

        yield render_html(languages, owner=owner, repo=repo)
    except ValueError as e:
        yield _error_html(str(e))
    except requests.ConnectionError:
        yield _error_html("Failed to connect to GitHub. Check your network connection.")
    except requests.Timeout:
        yield _error_html("Request timed out. Try again later.")
    except Exception as e:
        yield _error_html(f"Unexpected error: {e}")


_CSS = """
* { border-radius: 0 !important; }
.gradio-container {
    max-width: 100% !important;
    background: #111 !important;
    font-family: 'JetBrains Mono','Fira Code','SF Mono','Consolas',monospace !important;
}
.main, .contain, .wrap { background: transparent !important; }
footer, header { display: none !important; }

/* kill all gradio wrapper chrome on the input */
#cli {
    position: relative;
    padding-left: 1.5em !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
    overflow: visible !important;
}
#cli label, #cli .input-container {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
}
#cli .label-wrap { display: none !important; }
#cli textarea, #cli input {
    font-family: 'JetBrains Mono','Fira Code','SF Mono','Consolas',monospace !important;
    font-size: 14px !important;
    background: transparent !important;
    color: #b0b0b0 !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
    padding: 8px 0 !important;
    caret-color: transparent;
}
@keyframes blink { 50% { opacity: 0; } }
#cli-cursor {
    position: absolute;
    left: 1.5em;
    top: 50%;
    transform: translateY(-50%);
    color: #b0b0b0;
    font-family: 'JetBrains Mono','Fira Code','SF Mono','Consolas',monospace;
    font-size: 14px;
    pointer-events: none;
    z-index: 1;
    animation: blink 1s step-end infinite;
}
#cli::before {
    content: '>';
    position: absolute;
    left: 0;
    top: 50%;
    transform: translateY(-50%);
    color: #b0b0b0;
    font-family: 'JetBrains Mono','Fira Code','SF Mono','Consolas',monospace;
    font-size: 14px;
    z-index: 1;
    pointer-events: none;
}
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
            cur.style.left = (1.5 * 14 + measure.offsetWidth) + 'px';
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


def create_app() -> gr.Blocks:
    with gr.Blocks(
        title="repo-stats",
        theme=gr.themes.Monochrome(),  # type: ignore[attr-defined]
        css=_CSS,
        head=_HEAD,
    ) as app:
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
