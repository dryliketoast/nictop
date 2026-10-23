"""Pick a tile arrangement that fills the available area."""

import math

MIN_W = 28
MIN_H = 8
TARGET_ASPECT = 6.0  # cells are about twice as tall as wide, so 6:1 looks ~3:1


def best_columns(n: int, width: int, height: int) -> int:
    """Number of columns giving tiles closest to the target shape while still fitting."""
    if n <= 1 or width <= 0 or height <= 0:
        return 1
    best, best_score = 1, None
    for cols in range(1, n + 1):
        rows = math.ceil(n / cols)
        w, h = width / cols, height / rows
        fit = min(w / MIN_W, h / MIN_H)
        # tiles that fit always beat those that don't; among fitting, prefer the best shape
        score = (fit >= 1, -abs(math.log((w / h) / TARGET_ASPECT)) if fit >= 1 else fit)
        if best_score is None or score > best_score:
            best, best_score = cols, score
    return best


def split_rows(items: list[str], cols: int) -> list[list[str]]:
    """Spread items over the fewest rows, balanced so no row is left nearly empty."""
    rows = math.ceil(len(items) / cols)
    base, extra = divmod(len(items), rows)
    out, i = [], 0
    for r in range(rows):
        k = base + (1 if r < extra else 0)
        out.append(items[i : i + k])
        i += k
    return out
