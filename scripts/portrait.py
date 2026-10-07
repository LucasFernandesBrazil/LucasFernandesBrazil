"""
Turn a photo into a monochrome ASCII portrait that types itself in, row by row,
like a terminal printing (assets/ascii-portrait.svg).

Run once, whenever the photo changes -- the output is static:

    pip install -r scripts/requirements-portrait.txt
    python scripts/portrait.py assets/source-photo.jpg

Steps: cut the subject out (rembg) and paste it on white so the background
becomes blank space, lift local contrast (CLAHE) so the face reads, sample the
image into a character grid, then emit one <text> per row revealed by an
animated clip-path with a block cursor riding the edge.
"""
import html
import os
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import remove

from svgkit import GREEN, MUTED, FRAME, PAD, TITLEBAR_H, window

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "assets", "source-photo.jpg")
OUT = os.path.join(HERE, "..", "assets", "ascii-portrait.svg")
USER = "lucas"

COLS, ROWS = 100, 55
CELL_W, CELL_H = 8, 15
RAMP = " .`:-=+*cs#%@"  # light -> dense; the leading space is the background
GAMMA = 1.0
BLANK_ABOVE = 0.88        # luminance above this prints as a space
ROW_DUR = 0.09            # seconds per row wipe; rows run back to back

ART_W, ART_H = COLS * CELL_W, ROWS * CELL_H
STATUS_H = 30
W = ART_W + PAD * 2
H = TITLEBAR_H + 8 + ART_H + STATUS_H + PAD


def prepared_gray(path):
    cut = remove(Image.open(path).convert("RGBA"))
    alpha = np.asarray(cut.split()[-1], dtype=np.float32) / 255.0
    gray = cv2.cvtColor(np.asarray(cut.convert("RGB")), cv2.COLOR_RGB2GRAY)
    gray = cv2.createCLAHE(clipLimit=2.6, tileGridSize=(8, 8)).apply(gray)
    gray = cv2.convertScaleAbs(gray, alpha=1.05, beta=18).astype(np.float32)
    mask = cv2.GaussianBlur(alpha, (0, 0), 1.0)
    out = gray * mask + 255.0 * (1.0 - mask)
    img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), mode="L")
    return frame_subject(img, alpha)


def frame_subject(img, alpha):
    """Crop to the subject and center it on a white canvas with the grid's aspect."""
    ys, xs = np.nonzero(alpha > 0.5)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    sub = img.crop((x0, y0, x1, y1))
    aspect = ART_W / ART_H
    w, h = sub.size
    margin = int(h * 0.05)
    cw, ch = max(w, round((h + margin) * aspect)), h + margin
    if cw / ch > aspect + 0.01:
        ch = round(cw / aspect)
    canvas = Image.new("L", (cw, ch), 255)
    # pin the subject to the bottom edge, like a bust
    canvas.paste(sub, ((cw - w) // 2, ch - h))
    return canvas


def ascii_rows(img):
    px = np.asarray(img.resize((COLS, ROWS), Image.LANCZOS), dtype=np.float32) / 255.0
    px = np.power(px, GAMMA)
    rows = []
    for line in px:
        chars = []
        for lum in line:
            if lum >= BLANK_ABOVE:
                chars.append(" ")
            else:
                chars.append(RAMP[round((1.0 - lum) * (len(RAMP) - 1))])
        rows.append("".join(chars))
    return rows


def main():
    rows = ascii_rows(prepared_gray(SRC))
    top = TITLEBAR_H + 8
    parts = [window(W, H, f"{USER}@github: ~$ ./portrait.sh", "portrait-bg")]

    for i, line in enumerate(rows):
        row_y = top + i * CELL_H
        begin = i * ROW_DUR
        parts.append(
            f'<clipPath id="r{i}"><rect x="{PAD}" y="{row_y}" height="{CELL_H}" width="0">'
            f'<animate attributeName="width" from="0" to="{ART_W}" begin="{begin:.2f}s" '
            f'dur="{ROW_DUR}s" fill="freeze"/></rect></clipPath>'
            f'<g clip-path="url(#r{i})"><text xml:space="preserve" x="{PAD}" '
            f'y="{row_y + CELL_H * 0.74:.1f}" fill="{GREEN}" font-size="{CELL_H * 0.86:.1f}" '
            f'textLength="{ART_W}" lengthAdjust="spacing">{html.escape(line)}</text></g>'
            f'<rect y="{row_y + 1}" width="{CELL_W}" height="{CELL_H - 2}" fill="{GREEN}" opacity="0">'
            f'<animate attributeName="x" from="{PAD}" to="{PAD + ART_W}" begin="{begin:.2f}s" '
            f'dur="{ROW_DUR}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0.85" begin="{begin:.2f}s"/>'
            f'<set attributeName="opacity" to="0" begin="{begin + ROW_DUR:.2f}s"/></rect>'
        )

    status_y = top + ART_H + 8
    prompt = f"{USER}@github:~$ whoami "
    name = "Lucas Fernandes"
    parts.append(
        f'<line x1="0" y1="{status_y}" x2="{W}" y2="{status_y}" stroke="{FRAME}"/>'
        f'<text x="{PAD}" y="{status_y + 20}" fill="{MUTED}" font-size="13">'
        f'{prompt}<tspan fill="{GREEN}">{name}</tspan></text>'
        f'<rect x="{PAD + len(prompt + name) * 7.9:.0f}" y="{status_y + 8}" width="8" height="14" fill="{GREEN}">'
        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
        f'dur="1s" repeatCount="indefinite"/></rect>'
        "</svg>"
    )
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("".join(parts))
    print(f"wrote {OUT} ({W}x{H})")


if __name__ == "__main__":
    main()
