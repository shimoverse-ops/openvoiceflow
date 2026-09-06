"""The in-app usage counters are a contract across three languages.

`UsageCounters.Event` (Swift) decides what the app can count, `EVENT_KEYS`
(JavaScript) decides what the server will store, and the dashboard groups the
result by name prefix. Nothing at build time connects them: adding a Swift case
and forgetting the JS allowlist produces a counter that is emitted, silently
dropped, and never appears on the dashboard — a failure with no error message
anywhere. These tests are that missing link.

The allowlist also carries a privacy job. A counter name is the only
client-supplied string that reaches the events column, so "server stores just
the names it already knew" is what keeps dictated text out of it. A test that
lets the two lists drift would quietly retire that guarantee.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SWIFT = ROOT / "native" / "Sources" / "OpenVoiceFlow" / "UsageCounters.swift"
INGEST = ROOT / "api" / "analytics" / "ingest.js"
DASHBOARD = ROOT / "scripts" / "analytics_dashboard.py"


def swift_event_names() -> list[str]:
    return re.findall(r'case \w+ = "([^"]+)"', SWIFT.read_text(encoding="utf-8"))


def javascript_event_names() -> list[str]:
    block = re.search(r"const EVENT_KEYS = \[(.*?)\];", INGEST.read_text(encoding="utf-8"), re.S)
    assert block, "api/analytics/ingest.js no longer defines EVENT_KEYS"
    return re.findall(r'"([^"]+)"', block.group(1))


def test_app_and_server_agree_on_every_counter_name():
    swift = swift_event_names()
    javascript = javascript_event_names()
    assert swift, "UsageCounters.Event defines no cases"
    missing_on_server = sorted(set(swift) - set(javascript))
    unknown_to_app = sorted(set(javascript) - set(swift))
    assert not missing_on_server, (
        "these counters would be dropped silently by the server — add them to "
        f"EVENT_KEYS in api/analytics/ingest.js: {missing_on_server}"
    )
    assert not unknown_to_app, (
        "the server accepts counters the app cannot emit; remove them from "
        f"EVENT_KEYS or add the Swift cases: {unknown_to_app}"
    )


def test_counter_names_stay_machine_shaped():
    """A name is stored verbatim and rendered on the dashboard. Constraining the
    shape keeps it a stable identifier rather than a place a sentence could go."""
    for name in swift_event_names():
        assert re.fullmatch(r"[a-z]+\.[a-z0-9_]+", name), f"unexpected counter name: {name}"
        assert len(name) <= 60, f"counter name too long: {name}"


def test_every_counter_is_grouped_by_the_dashboard():
    """The dashboard splits counters into "Screens opened" and "Features used"
    by prefix. A name outside those prefixes is collected, stored, and then
    displayed nowhere."""
    dashboard = DASHBOARD.read_text(encoding="utf-8")
    assert 'startswith(("pane.", "tab."))' in dashboard
    assert 'startswith("action.")' in dashboard
    for name in swift_event_names():
        assert name.startswith(("pane.", "tab.", "action.")), (
            f"{name} matches no dashboard group and would be invisible"
        )


def test_every_declared_counter_is_actually_recorded_somewhere():
    """A case in the enum is a promise that the dashboard will have data for it.
    Five counters shipped in 0.5.22 declared but never wired — history copies,
    style applications, finished interviews, sent feedback, completed
    onboarding — so those metrics could only ever render as absent, which reads
    on the dashboard as "nobody does this" rather than "nobody measured it".

    Panes and tabs are recorded through the `event(for:)` mappings rather than
    by name, so they are satisfied by that indirection instead."""
    sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "native" / "Sources" / "OpenVoiceFlow").glob("*.swift")
    )
    recorded = set(re.findall(r"record\((?:IfChanged\()?\.(\w+)", sources))
    mapped = set(re.findall(r"return \.(\w+)", sources))
    declared = re.findall(r"case (\w+) = \"([^\"]+)\"", SWIFT.read_text(encoding="utf-8"))

    missing = [
        name for name, raw in declared
        if name not in recorded
        and not (raw.startswith(("pane.", "tab.")) and name in mapped)
    ]
    assert not missing, (
        "declared but never recorded, so the dashboard can only show them as "
        f"absent — wire them to their UI action or drop the case: {missing}"
    )


def test_counters_ride_the_existing_opt_out_switch():
    """No second network path and no second consent: counters go out with the
    payload that Settings ▸ Privacy already gates, and a data deletion clears
    them locally so the next sync cannot re-upload them."""
    analytics = (ROOT / "native" / "Sources" / "OpenVoiceFlow" / "AnalyticsStore.swift").read_text(encoding="utf-8")
    assert '"events": controller.usageCounters.payload' in analytics
    assert "guard controller.settings.shareAnalytics else { return false }" in analytics
    assert "counters?.reset()" in analytics

    counters = SWIFT.read_text(encoding="utf-8")
    # The store must not learn how to make requests of its own.
    assert "URLSession" not in counters
    assert "URLRequest" not in counters
