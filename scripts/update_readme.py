#!/usr/bin/env python3
"""Refresh the auto-generated sections of README.md from the GitHub API.

Standard library only. Each section is updated independently: if one API call
fails, that section keeps its previous content instead of breaking the README.
"""
import json
import os
import re
import sys
import urllib.request
from collections import Counter
from pathlib import Path

USER = os.environ.get("GH_USER", "mahinigam")
TOKEN = os.environ.get("GITHUB_TOKEN")
README = Path(__file__).resolve().parent.parent / "README.md"

EXCLUDE_LANGS = {
    "Jupyter Notebook",
    "HTML",
    "CSS",
    "SCSS",
    "Less",
    "Dockerfile",
    "Makefile",
    "TeX",
}  # Exclude markup, styles, and config to reflect real programming code
TOP_LANGS = 5
MAX_EVENTS = 5


def api(url):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "profile-readme-updater",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
        return json.load(r)


def paged(url):
    out, page = [], 1
    while True:
        sep = "&" if "?" in url else "?"
        chunk = api(f"{url}{sep}per_page=100&page={page}")
        out += chunk
        if len(chunk) < 100:
            return out
        page += 1


def own_repos():
    repos = paged(f"https://api.github.com/users/{USER}/repos?type=owner")
    return [r for r in repos if not r["fork"]]


def build_stats(repos):
    user = api(f"https://api.github.com/users/{USER}")
    stars = sum(r["stargazers_count"] for r in repos)
    return (
        f"**{user['public_repos']}** public repositories · "
        f"**{stars}** stars earned · "
        f"**{user['followers']}** followers"
    )


def build_languages(repos):
    totals = Counter()
    rate_limited = False
    for r in repos:
        if r.get("archived") or r.get("fork"):
            continue
        try:
            for lang, n in api(r["languages_url"]).items():
                if lang not in EXCLUDE_LANGS:
                    totals[lang] += n
        except urllib.error.HTTPError as err:
            if err.code in (403, 429):
                rate_limited = True
                break
            continue
        except Exception:
            continue

    if rate_limited:
        raise RuntimeError("GitHub API rate limit encountered during language scan; preserving cached distribution")

    whole = sum(totals.values())
    if not whole:
        raise RuntimeError("no language data")
    lines = []
    for lang, n in totals.most_common(TOP_LANGS):
        pct = n / whole * 100
        filled = round(pct / 100 * 20)
        lines.append(f"{lang:<14}{'█' * filled}{'░' * (20 - filled)} {pct:5.1f}%")
    return "```text\n" + "\n".join(lines) + "\n```"


def build_activity(repos):
    verbs = {
        "PushEvent": "Pushed to",
        "PullRequestEvent": "Pull request in",
        "ReleaseEvent": "Released in",
        "IssuesEvent": "Issue in",
        "CreateEvent": "Created",
    }
    candidates = []
    # Real-time repository pushes from repo metadata (bypasses GitHub events feed delay)
    for r in repos:
        name = r.get("name")
        if not name or name == USER:
            continue
        pushed = r.get("pushed_at")
        if pushed:
            candidates.append((pushed, "Pushed to", f"{USER}/{name}"))

    # Public events stream (PRs, releases, issues, etc.)
    try:
        events = api(f"https://api.github.com/users/{USER}/events/public?per_page=100")
        for e in events:
            verb = verbs.get(e["type"])
            if not verb:
                continue
            if e["type"] == "CreateEvent" and e["payload"].get("ref_type") != "repository":
                continue
            repo = e["repo"]["name"]
            if repo == f"{USER}/{USER}":
                continue
            candidates.append((e["created_at"], verb, repo))
    except Exception:
        pass

    candidates.sort(key=lambda x: x[0], reverse=True)
    seen, rows = set(), []
    for ts, verb, repo in candidates:
        day = ts[:10]
        key = (verb, repo, day)
        if key in seen:
            continue
        seen.add(key)
        rows.append(f"- `{day}` {verb} [{repo}](https://github.com/{repo})")
        if len(rows) == MAX_EVENTS:
            break
    if not rows:
        raise RuntimeError("no recent public activity")
    return "\n".join(rows)


def replace(text, name, body):
    pattern = re.compile(rf"(<!--START:{name}-->)(.*?)(<!--END:{name}-->)", re.S)
    if not pattern.search(text):
        raise RuntimeError(f"markers for '{name}' not found in README")
    return pattern.sub(lambda m: f"{m.group(1)}\n{body}\n{m.group(3)}", text)


def main():
    text = README.read_text(encoding="utf-8")
    try:
        repos = own_repos()
    except Exception as exc:
        print(f"[abort] could not list repositories: {exc}", file=sys.stderr)
        sys.exit(1)
    sections = {
        "stats": build_stats,
        "languages": build_languages,
        "activity": build_activity,
    }
    failures = 0
    for name, fn in sections.items():
        try:
            text = replace(text, name, fn(repos))
        except Exception as exc:
            failures += 1
            print(f"[skip] {name}: {exc}", file=sys.stderr)
    README.write_text(text, encoding="utf-8")
    sys.exit(1 if failures == len(sections) else 0)


if __name__ == "__main__":
    main()
