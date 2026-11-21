#!/usr/bin/env python3
"""Build the absurd-question ticker SVG from assets/ticker-lines.txt."""

from __future__ import annotations

import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINES = ROOT / "assets" / "ticker-lines.txt"
OUT = ROOT / "assets" / "ticker.svg"

WIDTH = 820
HEIGHT = 40
FONT_SIZE = 14
CHAR_W = FONT_SIZE * 0.6
SLOT = 4.2  # seconds per line: 0.4 s reveal + 3.758 s hold
REVEAL = 0.4


def main() -> None:
    lines = [line.strip() for line in LINES.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise SystemExit("ticker-lines.txt is empty")

    total = len(lines) * SLOT
    slot_pct = 100.0 / len(lines)
    show_pct = slot_pct * 0.99
    reveal_pct = REVEAL / total * 100.0

    clip_paths: list[str] = []
    texts: list[str] = []

    for index, line in enumerate(lines):
        label = f"❯ {line}"
        text_length = (len(label) + 1) * CHAR_W  # +1 for the cursor cell
        x = (WIDTH - text_length) / 2
        delay = index * SLOT

        clip_paths.append(
            f'  <clipPath id="c{index}" clipPathUnits="userSpaceOnUse">'
            f'<rect class="clip" style="animation-delay:{delay:.1f}s" '
            f'x="{x:.1f}" y="0" width="{text_length:.1f}" height="{HEIGHT}"/>'
            f"</clipPath>"
        )
        texts.append(
            f'  <text class="line" style="animation-delay:{delay:.1f}s" '
            f'x="{x:.1f}" y="27" textLength="{text_length:.1f}" '
            f'lengthAdjust="spacingAndGlyphs" clip-path="url(#c{index})">'
            f'{html.escape(label)}<tspan class="cursor">▌</tspan></text>'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}"
     viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
  <title id="title">absurd nightly questions</title>
  <desc id="desc">{len(lines)} absurd questions about systems, appliances, night coding and anime.</desc>
  <style>
    text {{
      font-family: "JetBrains Mono", "Fira Code", "Cascadia Code", Consolas, monospace;
      font-size: {FONT_SIZE}px;
      fill: #ff69b4;
    }}
    .line {{
      opacity: 0;
      animation: show {total:.1f}s linear infinite;
    }}
    .clip {{
      transform-box: fill-box;
      transform-origin: left center;
      animation: reveal {total:.1f}s linear infinite;
    }}
    .cursor {{
      animation: blink 1s steps(1) infinite;
    }}
    @keyframes show {{
      0%, {show_pct:.4f}% {{ opacity: 1; }}
      {slot_pct:.4f}%, 100% {{ opacity: 0; }}
    }}
    @keyframes reveal {{
      0% {{ transform: scaleX(0); }}
      {reveal_pct:.4f}% {{ transform: scaleX(1); }}
      100% {{ transform: scaleX(1); }}
    }}
    @keyframes blink {{
      50% {{ opacity: 0; }}
    }}
  </style>
  <defs>
{chr(10).join(clip_paths)}
  </defs>
{chr(10).join(texts)}
</svg>
"""

    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT} — {len(lines)} lines, {total:.1f}s loop, {SLOT:.1f}s per line")


if __name__ == "__main__":
    main()
