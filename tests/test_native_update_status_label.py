"""Contracts for the sidebar's version/update footer.

The footer used to read "v0.5.20 · auto-updating" whether or not the running
build was actually the latest one — a status that told the user nothing they
could act on. It now has three states: an "Update" button when the appcast
offers a newer version, plain "Up to date" when it doesn't, and the bare
version before any check has finished.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NATIVE_SOURCES = ROOT / "native" / "Sources" / "OpenVoiceFlow"


def source(name: str) -> str:
    return (NATIVE_SOURCES / name).read_text(encoding="utf-8")


def test_updater_probes_the_appcast_for_the_latest_version() -> None:
    updater = source("Updater.swift")

    # A silent probe (no Sparkle UI) is what tells the footer whether this
    # build is current.
    assert "func refreshUpdateStatus()" in updater
    assert "controller.updater.checkForUpdateInformation()" in updater
    # Sparkle reports the result through its delegate.
    assert "SPUUpdaterDelegate" in updater
    assert "didFindValidUpdate item: SUAppcastItem" in updater
    assert "func updaterDidNotFindUpdate(_ updater: SPUUpdater)" in updater


def test_updater_publishes_the_state_the_footer_renders() -> None:
    updater = source("Updater.swift")

    assert "@Published private(set) var updateAvailable = false" in updater
    assert "@Published private(set) var hasCheckedForUpdates = false" in updater
    assert "@Published private(set) var availableVersion: String?" in updater
    assert "func installAvailableUpdate()" in updater


def test_probe_respects_the_automatic_updates_opt_out() -> None:
    """The switch is an opt-out of background checks, not just of installs."""
    updater = source("Updater.swift")

    assert "guard controller.updater.automaticallyChecksForUpdates," in updater
    assert "!controller.updater.sessionInProgress else { return }" in updater


def test_footer_offers_update_only_when_one_is_available() -> None:
    dashboard = source("DashboardView.swift")

    assert "auto-updating" not in dashboard
    assert "private var versionFooter: some View" in dashboard
    assert "if updater.updateAvailable {" in dashboard
    assert 'Button { updater.installAvailableUpdate() } label: {' in dashboard
    assert 'Text("Update")' in dashboard


def test_footer_states_up_to_date_without_a_call_to_action() -> None:
    dashboard = source("DashboardView.swift")

    footer = dashboard.split("private var versionFooter: some View", 1)[1]
    up_to_date = footer.split("} else if updater.hasCheckedForUpdates {", 1)[1]
    up_to_date = up_to_date.split("} else {", 1)[0]

    assert "Up to date" in up_to_date
    # The "already current" state is a statement, never a button.
    assert "Button" not in up_to_date


def test_dashboard_refreshes_update_status_when_it_appears() -> None:
    dashboard = source("DashboardView.swift")

    assert ".onAppear { updater.refreshUpdateStatus() }" in dashboard
