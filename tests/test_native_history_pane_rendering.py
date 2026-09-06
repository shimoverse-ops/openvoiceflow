"""Behavior contracts for how the History pane renders its log.

The support question these prevent: "why does the History tab hang for a
second when I click it?" It hung because the pane drew every stored take —
up to `HistoryStore.maxEntries` of them — before it could show the dozen that
fit on screen, resolving an app icon and laying out a full transcript per row.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "native" / "Sources" / "OpenVoiceFlow" / "DashboardView.swift"


def dashboard_source() -> str:
    return DASHBOARD.read_text(encoding="utf-8")


def history_pane_source(source: str) -> str:
    """The body of `historyPane`, up to the next MARK section."""
    start = source.index("@ViewBuilder private var historyPane")
    end = source.index("// MARK: Leaderboard", start)
    return source[start:end]


def test_history_list_is_lazy() -> None:
    """Rows the user cannot see must not be built before the first frame."""
    pane = history_pane_source(dashboard_source())

    assert "LazyVStack" in pane, "History must draw its rows in a LazyVStack"
    lazy_at = pane.index("LazyVStack")
    rows_at = pane.index("ForEach(history.entries)")
    assert lazy_at < rows_at, "The entry ForEach must sit inside the LazyVStack"


def test_history_rows_are_their_own_view() -> None:
    """A copy acknowledgement must redraw one row, not the whole log."""
    source = dashboard_source()
    pane = history_pane_source(source)

    assert "struct HistoryRow: View" in source
    assert "HistoryRow(" in pane
    # The row's chrome belongs to HistoryRow; inlining it back into the pane is
    # what made every take re-render whenever copyFeedback published.
    assert "HStack(spacing: 12)" not in pane


def test_copy_puts_the_whole_take_on_the_pasteboard() -> None:
    """The row truncates for layout only — Copy must not copy a truncated take."""
    source = dashboard_source()
    pane = history_pane_source(source)

    assert "setString(entry.text, forType: .string)" in pane
    row_start = source.index("struct HistoryRow: View")
    row = source[row_start:]
    assert "entry.text.prefix(" in row, "Long transcripts must be bounded for layout"
    assert "setString" not in row, "Copy stays in the pane, working from the whole entry"


def test_home_recent_card_still_shows_three_takes() -> None:
    """Laziness is a History-pane concern; Home's fixed card must not change."""
    source = dashboard_source()
    assert re.search(r"history\.entries\.prefix\(3\)", source)
