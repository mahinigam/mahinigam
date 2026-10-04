#!/usr/bin/env python3
"""Builds the profile README graphics: classic-Macintosh style SVG windows.

Static windows (header, focus, toolbox) come from PROFILE below.
Live windows (stats, languages, activity) are rebuilt from the GitHub API.
If a live window fails to update, its previous SVG is left untouched.
Standard library only.
"""
import json
import os
import sys
import urllib.request
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import escape

USER = os.environ.get("GH_USER", "mahinigam")
TOKEN = os.environ.get("GITHUB_TOKEN")
ASSETS = Path(__file__).resolve().parent.parent / "assets"

# ---------------------------------------------------------------- content ---
PROFILE = {
    "name": "MAHI NIGAM",
    "tagline": [
        "CS undergraduate · AI/ML · data · backend systems",
        "I take ideas from model to something that runs:",
        "an API, a pipeline, an interface.",
    ],
    "badges": ["AI/ML", "DATA", "SYSTEMS"],
    "status": "OPEN TO INTERNSHIPS & COLLABORATION",
    "focus": [
        ("APPLIED ML", ["Fraud detection", "Computer vision", "Document intelligence"]),
        ("RETRIEVAL & DATA", ["RAG", "Vector search", "Embeddings", "Feature engineering"]),
        ("BACKEND", ["Services & APIs", "Async workflows", "Caching", "Persistence"]),
        ("DEVELOPER TOOLS", ["Repository analysis", "Semantic code search"]),
    ],
    "toolbox": [
        ("LANGUAGES", ["Python", "TypeScript", "JavaScript", "SQL", "R"]),
        ("AI & DATA", ["PyTorch", "TensorFlow", "scikit-learn", "Pandas", "NumPy"]),
        ("BACKEND & INFRA", ["FastAPI", "Flask", "Docker", "Redis", "Neo4j", "Linux", "Git"]),
    ],
}
EXCLUDE_LANGS = {"Jupyter Notebook"}  # notebooks inflate byte counts
TOP_LANGS = 6
MAX_EVENTS = 5

# ----------------------------------------------------------------- drawing ---
FONT = 'ui-monospace, "SF Mono", Menlo, Consolas, "DejaVu Sans Mono", "Courier New", monospace'
W, TB, M, SH = 640, 30, 3, 6  # canvas width, title bar, margin, shadow offset
WW = W - 2 * M - SH  # window width
CW = 0.6  # monospace glyph width as a fraction of font size
GRAY = "#eceded"


def t(x, y, s, size=13, weight="normal", anchor="start", fill="#000", ls=0):
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" '
        f'text-anchor="{anchor}" fill="{fill}" letter-spacing="{ls}">{escape(s)}</text>'
    )


def window(title, body_h, body, desc):
    h = TB + body_h
    total = h + 2 * M + SH
    cx = M + WW / 2
    tw = len(title) * (12 * CW + 2)
    label_w = tw + 60
    left = cx - label_w / 2
    stripes = "".join(
        f'<line x1="{M + 38}" y1="{y}" x2="{M + WW - 38}" y2="{y}"/>'
        for y in range(M + 7, M + TB - 4, 3)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{total}" viewBox="0 0 {W} {total}" font-family='{FONT}' role="img" aria-label="{escape(desc)}">
<title>{escape(desc)}</title>
<rect x="{M + SH}" y="{M + SH}" width="{WW}" height="{h}" fill="#000"/>
<rect x="{M}" y="{M}" width="{WW}" height="{h}" fill="#fff" stroke="#000" stroke-width="2"/>
<g stroke="#000" stroke-width="1">{stripes}</g>
<rect x="{left:.1f}" y="{M + 5}" width="{label_w:.1f}" height="{TB - 10}" fill="#fff"/>
<circle cx="{left + 18:.1f}" cy="{M + TB / 2}" r="4" fill="#000"/>
{t(left + 32, M + TB / 2 + 4.5, title, 12, "bold", ls=2)}
<rect x="{M + 12}" y="{M + (TB - 14) / 2}" width="14" height="14" fill="#fff" stroke="#000" stroke-width="2"/>
<rect x="{M + WW - 26}" y="{M + (TB - 14) / 2}" width="14" height="14" fill="#000"/>
<line x1="{M}" y1="{M + TB}" x2="{M + WW}" y2="{M + TB}" stroke="#000" stroke-width="2"/>
<g transform="translate({M},{M + TB})">
{body}
</g>
</svg>
"""


def chip_rows(items, max_w, fs=12, pad=10, gap=6):
    rows, cur, curw = [], [], 0
    for s in items:
        w = len(s) * fs * CW + 2 * pad
        add = w if not cur else w + gap
        if cur and curw + add > max_w:
            rows.append((cur, curw))
            cur, curw, add = [], 0, w
        cur.append((s, w))
        curw += add
    if cur:
        rows.append((cur, curw))
    return rows


def draw_chips(rows, x_left, y, max_w, align="left", fs=12, h=26, gap=6, rowgap=8):
    out = []
    for cur, curw in rows:
        x = x_left if align == "left" else x_left + (max_w - curw) / 2
        for s, w in cur:
            out.append(
                f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" fill="#fff" stroke="#000" stroke-width="2"/>'
            )
            out.append(t(x + w / 2, y + h / 2 + fs * 0.35, s, fs, "bold", "middle"))
            x += w + gap
        y += h + rowgap
    return "".join(out), y


# ------------------------------------------------------------ static pages ---
def build_header():
    p = PROFILE
    parts = [t(WW / 2, 66, p["name"], 44, "bold", "middle", ls=6)]
    y = 100
    for line in p["tagline"]:
        parts.append(t(WW / 2, y, line, 13, anchor="middle"))
        y += 21
    chips, y = draw_chips(chip_rows(p["badges"], WW), 0, y - 6, WW, align="center")
    parts.append(chips)
    fy = y + 6
    parts.append(f'<line x1="0" y1="{fy}" x2="{WW}" y2="{fy}" stroke="#000" stroke-width="2"/>')
    text = p["status"]
    tw = len(text) * (11 * CW + 1.5)
    start = WW / 2 - (tw + 16) / 2
    parts.append(f'<circle cx="{start + 4:.1f}" cy="{fy + 17}" r="4" fill="#000"/>')
    parts.append(t(start + 16, fy + 21, text, 11, "bold", ls=1.5))
    return window(
        "README.TXT", fy + 34, "\n".join(parts),
        f"{p['name'].title()}: " + " ".join(p["tagline"]),
    )


def build_rows_window(title, rows, desc):
    parts, y = [], 24
    for label, items in rows:
        parts.append(t(24, y, label, 11, "bold", ls=2))
        chips, y2 = draw_chips(chip_rows(items, WW - 48), 24, y + 10, WW - 48)
        parts.append(chips)
        y = y2 + 14
    return window(title, y - 8, "\n".join(parts), desc)


def build_focus():
    return build_rows_window("FOCUS", PROFILE["focus"], "Focus areas: " + ", ".join(l.lower() for l, _ in PROFILE["focus"]))


def build_toolbox():
    flat = ", ".join(i for _, items in PROFILE["toolbox"] for i in items)
    return build_rows_window("TOOLBOX", PROFILE["toolbox"], "Toolbox: " + flat)


# --------------------------------------------------------------- live data ---
def api(url):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-readme-updater"}
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
    return [r for r in paged(f"https://api.github.com/users/{USER}/repos?type=owner") if not r["fork"]]


def build_stats(repos):
    user = api(f"https://api.github.com/users/{USER}")
    stars = sum(r["stargazers_count"] for r in repos)
    cells = [
        (f"{user['public_repos']:,}", "REPOSITORIES"),
        (f"{stars:,}", "STARS"),
        (f"{user['followers']:,}", "FOLLOWERS"),
    ]
    cw, parts = WW / 3, []
    for i, (num, label) in enumerate(cells):
        cx = cw * i + cw / 2
        parts.append(t(cx, 56, num, 40, "bold", "middle"))
        parts.append(t(cx, 80, label, 11, "bold", "middle", ls=2))
        if i:
            parts.append(f'<line x1="{cw * i:.1f}" y1="16" x2="{cw * i:.1f}" y2="86" stroke="#000" stroke-width="2"/>')
    desc = ", ".join(f"{n} {l.lower()}" for n, l in cells)
    return window("AT A GLANCE", 104, "\n".join(parts), "GitHub stats: " + desc)


def build_languages(repos):
    totals = Counter()
    for r in repos:
        if r["archived"]:
            continue
        try:
            for lang, n in api(r["languages_url"]).items():
                if lang not in EXCLUDE_LANGS:
                    totals[lang] += n
        except Exception:
            continue
    whole = sum(totals.values())
    if not whole:
        raise RuntimeError("no language data")
    top = totals.most_common(TOP_LANGS)
    bx, bw = 150, WW - 150 - 96
    parts = []
    for i, (lang, n) in enumerate(top):
        pct = n / whole * 100
        base = 32 + i * 30
        fill_w = max(3, (bw - 4) * pct / 100)
        parts.append(t(24, base, lang[:14], 13, "bold"))
        parts.append(f'<rect x="{bx}" y="{base - 12}" width="{bw}" height="16" fill="{GRAY}" stroke="#000" stroke-width="2"/>')
        parts.append(f'<rect x="{bx + 2}" y="{base - 10}" width="{fill_w:.1f}" height="12" fill="#000"/>')
        parts.append(t(WW - 24, base, f"{pct:.1f}%", 13, anchor="end"))
    desc = "Languages: " + ", ".join(f"{l} {n / whole * 100:.0f}%" for l, n in top)
    return window("LANGUAGES", 20 + len(top) * 30 + 8, "\n".join(parts), desc)


def build_activity(_repos):
    tags = {"PushEvent": "PUSH", "PullRequestEvent": "PR", "ReleaseEvent": "RELEASE",
            "IssuesEvent": "ISSUE", "CreateEvent": "NEW"}
    events = api(f"https://api.github.com/users/{USER}/events/public?per_page=100")
    events.sort(key=lambda e: e["created_at"], reverse=True)
    seen, rows = set(), []
    for e in events:
        tag = tags.get(e["type"])
        if not tag:
            continue
        if e["type"] == "CreateEvent" and e["payload"].get("ref_type") != "repository":
            continue
        repo, day = e["repo"]["name"], e["created_at"][:10]
        if (tag, repo, day) in seen:
            continue
        seen.add((tag, repo, day))
        rows.append((day, tag, repo.split("/", 1)[1] if repo.startswith(USER + "/") else repo))
        if len(rows) == MAX_EVENTS:
            break
    if not rows:
        raise RuntimeError("no recent public activity")
    parts = []
    for i, (day, tag, repo) in enumerate(rows):
        base = 34 + i * 32
        if len(repo) > 44:
            repo = repo[:43] + "…"
        parts.append(t(24, base, day, 12, fill="#444"))
        parts.append(f'<rect x="112" y="{base - 15}" width="66" height="21" fill="#000"/>')
        parts.append(t(145, base, tag, 11, "bold", "middle", fill="#fff", ls=1))
        parts.append(t(194, base, repo, 13))
    desc = "Latest activity: " + ", ".join(f"{tag.lower()} {repo}" for _, tag, repo in rows)
    return window("LATEST ACTIVITY", 20 + len(rows) * 32 + 4, "\n".join(parts), desc)


# -------------------------------------------------------------------- main ---
def write(name, svg):
    ASSETS.mkdir(exist_ok=True)
    path = ASSETS / name
    if not path.exists() or path.read_text(encoding="utf-8") != svg:
        path.write_text(svg, encoding="utf-8")


def main():
    write("header.svg", build_header())
    write("focus.svg", build_focus())
    write("toolbox.svg", build_toolbox())
    try:
        repos = own_repos()
    except Exception as exc:
        print(f"[abort] could not list repositories: {exc}", file=sys.stderr)
        sys.exit(1)
    live = {"stats.svg": build_stats, "languages.svg": build_languages, "activity.svg": build_activity}
    failures = 0
    for name, fn in live.items():
        try:
            write(name, fn(repos))
        except Exception as exc:
            failures += 1
            print(f"[skip] {name}: {exc}", file=sys.stderr)
    sys.exit(1 if failures == len(live) else 0)


if __name__ == "__main__":
    main()
