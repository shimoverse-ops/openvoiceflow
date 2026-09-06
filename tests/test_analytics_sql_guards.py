"""SQL-level guards for the aggregate telemetry queries.

These queries read two JSONB columns written by clients across many app
versions, so a value of the wrong type is a normal thing to find, not a
corruption. The first version of `readInstallStats` guarded its casts with
`jsonb_typeof(x) = 'number' AND (x)::numeric > 0` — which reads as safe and is
not. SQL's AND does not short-circuit: the planner may evaluate the cast on a
row the type check would have excluded, and one `{"pane.home": "lots"}` row
anywhere in the table fails the whole query with

    ERROR: cannot cast jsonb string to type numeric

Verified against PostgreSQL 16 with a mixed-type fixture: the AND form errored,
the CASE form returned correct totals with the bad values ignored. CASE is
defined to skip unselected branches, so it is the form that actually holds.

The unit tests run against an in-memory JavaScript double that cannot reproduce
this — it is a property of the SQL, not of the handler — so it is asserted here
on the query text.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "api" / "_db.js"


def stats_sql() -> str:
    """The query text only. Comments are stripped first: the code comments here
    quote the broken form in order to explain it, and a scan that reads prose
    would flag the explanation instead of the SQL."""
    source = DB.read_text(encoding="utf-8")
    assert "export async function readInstallStats" in source
    body = source.split("export async function readInstallStats", 1)[1]
    lines = [line for line in body.splitlines() if not line.lstrip().startswith(("//", "--"))]
    return "\n".join(lines)


def test_no_jsonb_cast_is_guarded_only_by_and():
    """The exact shape that fails: a type check ANDed with a cast."""
    sql = stats_sql()
    offenders = re.findall(r"jsonb_typeof\([^)]*\)\s*=\s*'number'\s*\n?\s*AND[^\n]*::numeric", sql)
    assert not offenders, (
        "AND does not short-circuit in SQL — guard the cast with CASE WHEN "
        f"jsonb_typeof(...) = 'number' THEN ... ELSE ... END instead: {offenders}"
    )


def test_every_jsonb_numeric_cast_sits_inside_a_case_guard():
    sql = stats_sql()
    casts = re.findall(r"\((?:entry\.value|feature_usage->'[A-Za-z]+')\)::numeric", sql)
    assert casts, "expected the feature/event queries to cast JSONB values to numeric"
    guards = re.findall(r"CASE WHEN jsonb_typeof\(", sql)
    assert len(guards) >= len(casts), (
        f"{len(casts)} JSONB numeric casts but only {len(guards)} CASE guards — "
        "every cast of a client-written JSONB value needs one"
    )


def test_event_totals_are_summed_over_a_type_checked_subquery():
    """Casting inside a subquery and comparing outside keeps the type check and
    the arithmetic in separate steps, so neither can be reordered into the
    other."""
    sql = stats_sql()
    assert "FROM devices, LATERAL jsonb_each(devices.events) AS entry" in sql
    assert "WHERE value > 0" in sql
    assert "SUM(value)::bigint" in sql
