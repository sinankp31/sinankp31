#!/usr/bin/env python3
"""
Generates a neofetch-style GitHub profile card (dark_mode.svg + light_mode.svg).

1. Edit CONFIG and ROWS below.
2. Run:  python generate_card.py
   (set GH_USERNAME and GH_TOKEN env vars to pull live GitHub stats)
"""
import html
import json
import os
import urllib.request
from pathlib import Path
from string import Template

# ----------------------------------------------------------------------------
# EDIT ME
# ----------------------------------------------------------------------------
CONFIG = {
    "username": os.getenv("GH_USERNAME", "YOUR_GITHUB_USERNAME"),
    "name": "Your Name",
    "quote": '// "Talk is cheap. Show me the code." - Linus Torvalds',
}

# ("kv", key, value, options) | ("sec", title) | ("stat", key, stat_id)
ROWS = [
    ("kv", "Status", "Open to work", {"status": True}),
    ("kv", "Role", "Full Stack Developer (MERN)"),
    ("kv", "Location", "City, Country"),
    ("sec", "Tech Stack"),
    ("kv", "Languages", "Java, JavaScript, TypeScript"),
    ("kv", "Frontend", "React, Redux, Tailwind CSS"),
    ("kv", "Backend", "Node.js, Express.js, REST APIs"),
    ("kv", "Database", "MongoDB"),
    ("kv", "Tools", "Git, GitHub"),
    ("kv", "CS Core", "DSA, System Design"),
    ("sec", "Contact"),
    ("kv", "Email", "your.email@example.com"),
    ("kv", "LinkedIn", "in/your-linkedin"),
    ("kv", "Portfolio", "yourname.dev"),
    ("kv", "Twitter", "@your_handle"),
    ("sec", "GitHub Stats"),
    ("stat", "Repos", "repos"),
    ("stat", "Stars", "stars"),
    ("stat", "Commits", "commits"),
    ("stat", "Followers", "followers"),
]

# ----------------------------------------------------------------------------
# Layout constants (monospace: char width ~= 0.6 * font size)
# ----------------------------------------------------------------------------
W, TOP, LH = 980, 96, 22
FS, CW = 14, 8.4
X0, XV, XR = 430, 570, 940
ART_X, ART_LH = 44, 20

THEMES = {
    "dark": dict(bg="#0d1117", border="#30363d", key="#79c0ff", val="#e6edf3",
                 dim="#6e7681", sec="#d2a8ff", a1="#58a6ff", a2="#bc8cff",
                 green="#3fb950", line="#30363d"),
    "light": dict(bg="#ffffff", border="#d0d7de", key="#0969da", val="#1f2328",
                  dim="#6e7781", sec="#8250df", a1="#0969da", a2="#8250df",
                  green="#1a7f37", line="#d0d7de"),
}

CSS = Template("""
text{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;font-size:${fs}px}
.k{fill:$key}.v{fill:$val}.d{fill:$dim}.s{fill:$sec;font-weight:600}
.hd{fill:$a1;font-weight:700}.gr{fill:$green}
.ln{stroke:$line;stroke-width:1}
.dots{stroke:$dim;stroke-width:1.6;stroke-linecap:round;stroke-dasharray:0.1 6;opacity:.7}
@keyframes fade{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
.row{animation:fade .5s ease backwards}
@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}
.cur{fill:$a1;animation:blink 1.1s steps(1) infinite}
@keyframes pulse{0%{r:4;opacity:.9}70%,100%{r:10;opacity:0}}
.pulse{fill:$green;animation:pulse 1.8s ease-out infinite}
""")


def esc(s):
    return html.escape(s, quote=False)


# ----------------------------------------------------------------------------
# ASCII art: a code editor window
# ----------------------------------------------------------------------------
def build_art(name):
    inner = 40
    code = [
        " 1  const dev = {",
        f' 2    name: "{name}",'[:inner],
        ' 3    stack: ["Java", "MERN"],',
        ' 4    skills: ["DSA", "System Design"],',
        " 5    coffee: Infinity,",
        " 6  };",
        " 7",
        " 8  dev.build();",
        " 9  dev.ship();",
        "10  // repeat",
    ]
    title = "─ dev.js "
    art = ["┌" + title + "─" * (inner - len(title)) + "┐"]
    art += ["│" + c.ljust(inner) + "│" for c in code]
    art += ["├" + "─" * inner + "┤"]
    art += ["│" + " $ npm run dev  ->  ready on :3000".ljust(inner) + "│"]
    art += ["└" + "─" * inner + "┘"]
    art += ["││".center(inner + 2), ("━" * 20).center(inner + 2)]
    return art


# ----------------------------------------------------------------------------
# Optional: live stats from the GitHub API
# ----------------------------------------------------------------------------
def fetch_stats(user):
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-card"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    def get(url):
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=20) as r:
            return json.load(r)

    stats = {}
    try:
        u = get(f"https://api.github.com/users/{user}")
        stats["followers"] = f"{u['followers']:,}"
        stats["repos"] = f"{u['public_repos']:,}"
        repos, page = [], 1
        while True:
            batch = get(f"https://api.github.com/users/{user}/repos?per_page=100&page={page}&type=owner")
            repos += batch
            if len(batch) < 100:
                break
            page += 1
        stats["stars"] = f"{sum(r['stargazers_count'] for r in repos):,}"
        stats["commits"] = f"{get(f'https://api.github.com/search/commits?q=author:{user}&per_page=1')['total_count']:,}"
    except Exception as exc:  # offline / rate-limited -> keep placeholders
        print(f"[stats] could not fetch live stats: {exc}")
    return stats


# ----------------------------------------------------------------------------
# SVG rendering
# ----------------------------------------------------------------------------
def render(theme, cfg, stats):
    p = THEMES[theme]
    user = cfg["username"]
    parts, i = [], 0

    def y_of(idx):
        return TOP + idx * LH

    def grp(idx, inner):
        return f'<g class="row" style="animation-delay:{0.07 * idx:.2f}s">{inner}</g>'

    def txt(x, y, s, cls, fixed=True):
        tl = f' textLength="{len(s) * CW:.1f}" lengthAdjust="spacing"' if fixed else ""
        return f'<text x="{x:.1f}" y="{y}" class="{cls}"{tl}>{esc(s)}</text>'

    # header row
    head = f"{user}@github"
    y = y_of(0)
    parts.append(grp(0, txt(X0, y, head, "hd") +
                     f'<line class="ln" x1="{X0 + len(head) * CW + 10:.1f}" y1="{y - 5}" x2="{XR}" y2="{y - 5}"/>'))
    i = 1

    for row in ROWS:
        y = y_of(i)
        kind = row[0]
        if kind == "sec":
            t = f"- {row[1]} "
            parts.append(grp(i, txt(X0, y, t, "s") +
                             f'<line class="ln" x1="{X0 + len(t) * CW + 4:.1f}" y1="{y - 5}" x2="{XR}" y2="{y - 5}"/>'))
        else:
            key = row[1]
            leader = (f'<line class="dots" x1="{X0 + len(key) * CW + 10:.1f}" y1="{y - 4}" '
                      f'x2="{XV - 10}" y2="{y - 4}"/>')
            if kind == "stat":
                val = str(stats.get(row[2], "-"))
                body = txt(X0, y, key, "k") + leader + txt(XV, y, val, "v", fixed=False)
            else:
                val = row[2]
                opts = row[3] if len(row) > 3 else {}
                if opts.get("status"):
                    body = (txt(X0, y, key, "k") + leader +
                            f'<circle cx="{XV + 5}" cy="{y - 5}" r="4" class="pulse"/>'
                            f'<circle cx="{XV + 5}" cy="{y - 5}" r="4" class="gr" style="fill:{p["green"]}"/>' +
                            txt(XV + 18, y, val, "gr"))
                else:
                    body = txt(X0, y, key, "k") + leader + txt(XV, y, val, "v")
            parts.append(grp(i, body))
        i += 1

    # footer: quote + prompt with blinking cursor
    i += 1
    parts.append(grp(i, txt(X0, y_of(i), cfg["quote"], "d")))
    i += 1
    y = y_of(i)
    parts.append(grp(i, txt(X0, y, "$", "gr") +
                     f'<rect class="cur" x="{X0 + 2 * CW:.1f}" y="{y - 13}" width="9" height="17" rx="1.5"/>'))

    H = y_of(i) + 36
    content_h = (i + 1) * LH

    # ASCII art (vertically centered), gradient across the whole art area
    art = build_art(cfg["name"])
    art_h = len(art) * ART_LH
    art_top = TOP + (content_h - art_h) / 2 - 10
    art_w = (40 + 2) * CW
    art_svg = []
    for n, line in enumerate(art):
        # one explicit x per glyph -> exact grid regardless of the viewer's font
        glyphs = [(k, ch) for k, ch in enumerate(line) if ch != " "]
        if not glyphs:
            continue
        xs = " ".join(f"{ART_X + k * CW:.1f}" for k, _ in glyphs)
        chars = "".join(ch for _, ch in glyphs)
        art_svg.append(
            f'<text x="{xs}" y="{art_top + (n + 1) * ART_LH:.1f}" fill="url(#art)">{esc(chars)}</text>')
    cx, cy = ART_X + art_w / 2, art_top + art_h / 2

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(user)} profile card">
<style>{CSS.substitute(fs=FS, **p)}</style>
<defs>
  <linearGradient id="art" gradientUnits="userSpaceOnUse" x1="{ART_X}" y1="{art_top:.0f}" x2="{ART_X + art_w:.0f}" y2="{art_top + art_h:.0f}">
    <stop offset="0" stop-color="{p['a1']}"/><stop offset="1" stop-color="{p['a2']}"/>
  </linearGradient>
  <radialGradient id="glow">
    <stop offset="0" stop-color="{p['a2']}" stop-opacity=".22"/><stop offset="1" stop-color="{p['a2']}" stop-opacity="0"/>
  </radialGradient>
</defs>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="16" fill="{p['bg']}" stroke="{p['border']}" stroke-width="1.5"/>
<circle cx="28" cy="26" r="6" fill="#ff5f56"/><circle cx="48" cy="26" r="6" fill="#ffbd2e"/><circle cx="68" cy="26" r="6" fill="#27c93f"/>
<text x="{W / 2}" y="31" text-anchor="middle" class="d">{esc(user)}@github  -  zsh</text>
<line class="ln" x1="1" y1="52" x2="{W - 1}" y2="52"/>
<circle cx="{cx:.0f}" cy="{cy:.0f}" r="230" fill="url(#glow)"/>
{chr(10).join(art_svg)}
{chr(10).join(parts)}
</svg>
"""
    return svg


def main():
    out = Path(__file__).resolve().parent
    stats = fetch_stats(CONFIG["username"]) if CONFIG["username"] != "YOUR_GITHUB_USERNAME" else {}
    for theme in THEMES:
        path = out / f"{theme}_mode.svg"
        path.write_text(render(theme, CONFIG, stats), encoding="utf-8")
        print("wrote", path)


if __name__ == "__main__":
    main()
