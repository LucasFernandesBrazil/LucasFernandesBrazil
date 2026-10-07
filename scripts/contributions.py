"""
Scrape the last year of contributions from GitHub's public calendar fragment
(the same HTML the profile page loads -- no token needed) and render it as an
animated heatmap: boxes slide in on a diagonal sweep, once, then hold.

Writes data/contributions.json and assets/contrib-heatmap.svg. Run daily by
.github/workflows/profile-art.yml.

    python scripts/contributions.py
"""
import datetime as dt
import json
import os
import re

import requests
from bs4 import BeautifulSoup

from svgkit import GREEN, MUTED, FRAME, PAD, SOFT_GREEN, TITLEBAR_H, window

USER = os.environ.get("GH_PROFILE_USER", "LucasFernandesBrazil")
HERE = os.path.dirname(os.path.abspath(__file__))
DATA_OUT = os.path.join(HERE, "..", "data", "contributions.json")
SVG_OUT = os.path.join(HERE, "..", "assets", "contrib-heatmap.svg")

PALETTE = ["#161b22", "#003B00", "#00691b", "#00a82d", "#00d438", "#00FF41"]
CELL, GAP = 12, 3
STEP = CELL + GAP
LABEL_W, MONTH_H, STATS_H = 30, 20, 88
GOLD = "#f2cc60"


def fetch_days():
    resp = requests.get(
        f"https://github.com/users/{USER}/contributions",
        headers={"User-Agent": "profile-readme"},
        timeout=30,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    tips = {t.get("for"): t.get_text(strip=True) for t in soup.find_all("tool-tip")}
    days = []
    for td in soup.select("td.ContributionCalendar-day[data-date]"):
        m = re.match(r"(\d[\d,]*)", tips.get(td.get("id"), ""))
        days.append({"date": td["data-date"], "count": int(m.group(1).replace(",", "")) if m else 0})
    if not days:
        raise SystemExit("no calendar cells found -- GitHub markup may have changed")
    return sorted(days, key=lambda d: d["date"])


def streaks(days):
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] else 0
        longest = max(longest, run)
    current = 0
    tail = days[:-1] if days[-1]["count"] == 0 else days  # today may not be over
    for d in reversed(tail):
        if not d["count"]:
            break
        current += 1
    return current, longest


def level(count, top):
    if count == 0:
        return 0
    return min(5, 1 + int(4 * count / max(top, 1)))


def render(days, current, longest):
    first = dt.date.fromisoformat(days[0]["date"])
    lead = (first.weekday() + 1) % 7  # weeks start on Sunday
    cols = (lead + len(days) + 6) // 7
    # scale to the 90th percentile so one huge day doesn't dim the whole year
    active = sorted(d["count"] for d in days if d["count"])
    top = active[int(len(active) * 0.9)] if active else 1
    total = sum(d["count"] for d in days)
    best = max(days, key=lambda d: d["count"])

    w = PAD * 2 + LABEL_W + cols * STEP
    h = TITLEBAR_H + MONTH_H + 7 * STEP + STATS_H + PAD
    gx, gy = PAD + LABEL_W, TITLEBAR_H + MONTH_H
    parts = [
        window(w, h, "lucas@github: ~$ ./contributions.sh", "heat-bg"),
        "<style>@keyframes in{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:none}}"
        ".c{opacity:0;animation:in .42s cubic-bezier(.2,.8,.2,1) both}</style>",
    ]

    seen = set()
    for i, d in enumerate(days):
        date = dt.date.fromisoformat(d["date"])
        col, row = divmod(lead + i, 7)
        x, y = gx + col * STEP, gy + row * STEP
        if date.day <= 7 and row == 0 and (date.year, date.month) not in seen:
            seen.add((date.year, date.month))
            parts.append(f'<text x="{x}" y="{TITLEBAR_H + 14}" fill="{MUTED}" font-size="10">{date:%b}</text>')
        n = d["count"]
        parts.append(
            f'<rect class="c" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
            f'fill="{PALETTE[level(n, top)]}" style="animation-delay:{col * 0.018 + row * 0.045:.3f}s">'
            f'<title>{d["date"]}: {n} contribution{"" if n == 1 else "s"}</title></rect>'
        )
    for row, name in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        parts.append(f'<text x="{PAD}" y="{gy + row * STEP + 9.5}" fill="{MUTED}" font-size="9">{name}</text>')

    ly = gy + 7 * STEP + 6
    lx = w - PAD - len(PALETTE) * CELL - 34
    parts.append(f'<text x="{lx - 6}" y="{ly + 10}" fill="{MUTED}" font-size="10" text-anchor="end">Less</text>')
    for i, color in enumerate(PALETTE):
        parts.append(f'<rect x="{lx + i * CELL}" y="{ly}" width="{CELL - 1}" height="{CELL - 1}" rx="2.2" fill="{color}"/>')
    parts.append(f'<text x="{lx + len(PALETTE) * CELL + 4}" y="{ly + 10}" fill="{MUTED}" font-size="10">More</text>')

    sy = ly + CELL + 14
    parts.append(f'<line x1="0" y1="{sy}" x2="{w}" y2="{sy}" stroke="{FRAME}"/>')
    parts.append(
        f'<text x="{PAD}" y="{sy + 24}" font-size="13" fill="{GREEN}"><tspan font-weight="700">{total:,}</tspan>'
        f'<tspan fill="{MUTED}"> contributions in the last year</tspan></text>'
        f'<text x="{w - PAD}" y="{sy + 24}" font-size="12" fill="{MUTED}" text-anchor="end">'
        f'{days[0]["date"]} &#8594; {days[-1]["date"]}</text>'
        f'<text x="{PAD}" y="{sy + 48}" font-size="13" fill="{MUTED}">current streak '
        f'<tspan fill="{SOFT_GREEN}" font-weight="700">{current} days</tspan>   &#183;   longest '
        f'<tspan fill="{SOFT_GREEN}" font-weight="700">{longest} days</tspan></text>'
        f'<text x="{w - PAD}" y="{sy + 48}" font-size="12" fill="{MUTED}" text-anchor="end">best day '
        f'<tspan fill="{GOLD}" font-weight="700">{best["count"]}</tspan> on {best["date"]}</text>'
        "</svg>"
    )
    return "".join(parts), total


def main():
    days = fetch_days()
    current, longest = streaks(days)
    svg, total = render(days, current, longest)
    os.makedirs(os.path.dirname(DATA_OUT), exist_ok=True)
    with open(DATA_OUT, "w", encoding="utf-8") as f:
        json.dump({"user": USER, "total": total, "current_streak": current,
                   "longest_streak": longest, "days": days}, f, indent=1)
    with open(SVG_OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {SVG_OUT}: {total} contributions, streak {current}/{longest}")


if __name__ == "__main__":
    main()
