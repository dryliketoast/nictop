from nictop.graph import fmt_rate, nice_ceiling
from nictop.layout import best_columns, split_rows


def test_nice_ceiling_snaps_to_1_2_5():
    assert nice_ceiling(3) == 5
    assert nice_ceiling(5000) == 5000
    assert nice_ceiling(5001) == 10000
    assert nice_ceiling(0) == 1


def test_fmt_rate():
    assert fmt_rate(512) == "512 B/s"
    assert fmt_rate(1024 * 1024) == "1.00 MiB/s"
    assert fmt_rate(125_000, bits=True) == "1.00 Mb/s"


def test_split_rows_is_balanced_and_complete():
    items = list("abcde")
    assert split_rows(items, 4) == [["a", "b", "c"], ["d", "e"]]
    assert sum(split_rows(items, 2), []) == items


def test_best_columns_follows_terminal_shape():
    assert best_columns(1, 200, 50) == 1
    wide = best_columns(4, 240, 40)
    tall = best_columns(4, 60, 100)
    assert wide > tall
