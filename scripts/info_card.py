"""
Render data/profile.json as a neofetch-style info card (assets/info-card.svg).

Each row fades and slides in on a short stagger (SMIL, freezes when done), so
the card "prints" next to the ASCII portrait. GitHub runs SVG animations inside
<img>, but never JavaScript.

    python scripts/info_card.py
"""
import html
import json
import os

from svgkit import GREEN, INK, MUTED, FRAME, PAD, SOFT_GREEN, TITLEBAR_H, window

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "data", "profile.json")
OUT = os.path.join(HERE, "..", "assets", "info-card.svg")

W, H = 490, 400
VAL_X = PAD + 96
LINE_H = 21
SIZE = 12.5


def rise(inner, i):
    delay = 0.2 + i * 0.07
    return (
        f'<g opacity="0" transform="translate(0,5)">{inner}'
        f'<animate attributeName="opacity" from="0" to="1" begin="{delay:.2f}s" dur="0.4s" fill="freeze"/>'
        f'<animateTransform attributeName="transform" type="translate" from="0 5" to="0 0" '
        f'begin="{delay:.2f}s" dur="0.4s" fill="freeze"/></g>'
    )


def rule(x, y):
    return f'<line x1="{x}" y1="{y - 4:.1f}" x2="{W - PAD}" y2="{y - 4:.1f}" stroke="{FRAME}"/>'


def main():
    cfg = json.load(open(SRC, encoding="utf-8"))
    user = html.escape(cfg["username"])
    parts = [window(W, H, f"{user}@github: ~$ neofetch", "card-bg")]

    y = TITLEBAR_H + 30
    for i, row in enumerate(cfg["rows"]):
        kind = row[0]
        if kind == "gap":
            y += LINE_H / 2
            continue
        if kind == "host":
            inner = (
                f'<text x="{PAD}" y="{y:.1f}" font-size="14" font-weight="700">'
                f'<tspan fill="{GREEN}">{user}</tspan><tspan fill="{MUTED}">@</tspan>'
                f'<tspan fill="{SOFT_GREEN}">github</tspan></text>'
                + rule(PAD + (len(user) + 7) * 8.5 + 12, y)
            )
        elif kind == "sec":
            inner = (
                f'<text x="{PAD}" y="{y:.1f}" fill="{SOFT_GREEN}" font-size="{SIZE}" '
                f'font-weight="700">&#8212; {html.escape(row[1])}</text>'
                + rule(PAD + 12 + len(row[1]) * 8 + 12, y)
            )
        elif kind == "kv":
            inner = (
                f'<text x="{PAD}" y="{y:.1f}" fill="{GREEN}" font-size="{SIZE}" '
                f'font-weight="700">{html.escape(row[1])}</text>'
                f'<text x="{VAL_X}" y="{y:.1f}" fill="{INK}" font-size="{SIZE}">'
                f"{html.escape(row[2])}</text>"
            )
        elif kind == "bul":
            inner = (
                f'<text x="{PAD}" y="{y:.1f}" fill="{GREEN}" font-size="{SIZE}">&gt;</text>'
                f'<text x="{PAD + 16}" y="{y:.1f}" fill="{INK}" font-size="{SIZE}">'
                f"{html.escape(row[1])}</text>"
            )
        else:
            raise ValueError(f"unknown row kind: {kind}")
        parts.append(rise(inner, i))
        y += LINE_H

    if y > H - PAD:
        raise SystemExit(f"card content ends at y={y:.0f}, taller than H={H}")
    parts.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("".join(parts))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
