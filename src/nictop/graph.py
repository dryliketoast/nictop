"""Block-character graph rendering and number formatting."""

import math
from collections.abc import Sequence
from itertools import groupby

from rich.style import Style
from rich.text import Text
from textual.color import Color

BLOCKS = " ▁▂▃▄▅▆▇█"
MIN_SCALE = 4096.0  # bytes/s; keeps an idle link from filling the graph with noise


def nice_ceiling(v: float) -> float:
    """Round up to 1/2/5 x 10^n so the graph scale stays steady between ticks."""
    if v <= 0:
        return 1.0
    exp = 10 ** math.floor(math.log10(v))
    for m in (1, 2, 5, 10):
        if v <= m * exp:
            return m * exp
    return 10 * exp


def fmt_rate(bytes_per_s: float, bits: bool = False) -> str:
    if bits:
        return _fmt(bytes_per_s * 8, 1000, ("b", "Kb", "Mb", "Gb", "Tb"), "/s")
    return _fmt(bytes_per_s, 1024, ("B", "KiB", "MiB", "GiB", "TiB"), "/s")


def fmt_total(n: float) -> str:
    return _fmt(n, 1024, ("B", "KiB", "MiB", "GiB", "TiB", "PiB"), "")


def _fmt(v: float, base: int, units: Sequence[str], suffix: str) -> str:
    i = 0
    while v >= base * 0.995 and i < len(units) - 1:
        v /= base
        i += 1
    return f"{v:.0f} {units[i]}{suffix}" if i == 0 else f"{v:.2f} {units[i]}{suffix}"


def graph_rows(
    values: Sequence[float],
    width: int,
    height: int,
    scale: float,
    low: Color,
    high: Color,
    bg: Color,
    inverted: bool = False,
) -> list[Text]:
    """Render one sample per column; the baseline is the bottom row, or the top row if inverted.

    Inverted graphs hang from the top. There are no upper-eighth block glyphs,
    so a partial cell is the complementary lower block drawn with the
    foreground and background swapped.
    """
    vals = list(values)[-width:]
    vals = [0.0] * (width - len(vals)) + vals
    full = height * 8
    levels = [
        min(full, max(1, round(v / scale * full))) if v > 0 else 0 for v in vals
    ]

    rows = []
    for r in range(height):
        dist = r if inverted else height - 1 - r  # rows away from the baseline
        color = low.blend(high, dist / max(1, height - 1)).hex6
        text = Text(no_wrap=True)
        fills = [min(8, max(0, lv - dist * 8)) for lv in levels]
        for fill, run in groupby(fills):
            n = len(list(run))
            if fill == 0:
                text.append(" " * n)
            elif not inverted or fill == 8:
                text.append(BLOCKS[fill] * n, Style(color=color))
            else:
                text.append(BLOCKS[8 - fill] * n, Style(color=bg.hex6, bgcolor=color))
        rows.append(text)
    return rows
