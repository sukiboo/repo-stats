---
title: repo-stats
emoji: 🩻
colorFrom: yellow
colorTo: indigo
sdk: gradio
sdk_version: 6.9.0
app_file: app.py
pinned: false
short_description: Visualize lines of code by language for a GitHub repo
---

# repo-stats

A simple app to visualize lines of code by language and other basic stats for any public GitHub repo.

I was kinda annoyed that it doesn't exist already, or at least not in the way I imagined.

The issue with GitHub's language breakdown is that it approximates language contribution based on file size, not actual lines of code -- especially noticeable with Jupyter notebooks.
This app fixes that by counting actual lines.


## How It Works

1. Fetches the full file tree via the GitHub API
2. Filters out binary files, vendored directories (`node_modules`, `vendor`, `dist`, etc.), and non-code files
3. Downloads each source file from `raw.githubusercontent.com` concurrently
4. Counts newlines in each file, mapping file extensions to languages


## Running Locally

```bash
pip install -r requirements.txt
python app.py
```

Optionally set a `GITHUB_TOKEN` environment variable to avoid GitHub API rate limits:

```bash
export GITHUB_TOKEN=ghp_...
python app.py
```
