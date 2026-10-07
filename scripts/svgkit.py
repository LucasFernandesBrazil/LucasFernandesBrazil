"""Shared look for the terminal-window SVGs (matrix-green theme)."""

FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
BG_TOP = "#111722"
BG_BOTTOM = "#0d1117"
FRAME = "#14532d"
MUTED = "#7d8590"
INK = "#c9d1d9"
GREEN = "#00FF41"
SOFT_GREEN = "#7ee787"
TITLEBAR_H = 30
PAD = 20


def window(width, height, title, gid):
    """Opening tag, background, border and title bar of a terminal window."""
    dots = "".join(
        f'<circle cx="{PAD + i * 16}" cy="{TITLEBAR_H / 2}" r="5" fill="{c}"/>'
        for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"])
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="{FONT}">'
        f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG_TOP}"/><stop offset="1" stop-color="{BG_BOTTOM}"/>'
        f"</linearGradient></defs>"
        f'<rect width="{width}" height="{height}" rx="12" fill="url(#{gid})"/>'
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12" '
        f'fill="none" stroke="{FRAME}"/>'
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{width}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>'
        f"{dots}"
        f'<text x="{width / 2}" y="{TITLEBAR_H / 2 + 4}" fill="{MUTED}" font-size="12" '
        f'text-anchor="middle">{title}</text>'
    )
