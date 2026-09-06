import Combine
import Sparkle

/// Receives Sparkle's appcast results.
///
/// Sparkle wants its delegate at construction time, before `UpdaterController`
/// finishes initializing, so this is a small forwarding object rather than the
/// controller itself. The protocol is main-actor annotated, hence `@MainActor`.
@MainActor
private final class UpdaterProbe: NSObject, SPUUpdaterDelegate {
    var onFound: ((SUAppcastItem) -> Void)?
    var onNotFound: (() -> Void)?
    var onAborted: (() -> Void)?

    func updater(_ updater: SPUUpdater, didFindValidUpdate item: SUAppcastItem) {
        onFound?(item)
    }

    func updaterDidNotFindUpdate(_ updater: SPUUpdater) {
        onNotFound?()
    }

    /// Every ended check lands here, including the ones that ended badly — an
    /// appcast that wouldn't load or parse reports neither found nor
    /// not-found, so this is the only signal that the check told us nothing.
    /// "No update found" aborts through here too; the controller tells the
    /// cases apart by whether a result already arrived.
    func updater(_ updater: SPUUpdater, didAbortWithError error: any Error) {
        onAborted?()
    }
}

/// In-app updates via Sparkle 2 with an EdDSA-signed appcast.
///
/// `SUFeedURL` (the appcast) and `SUPublicEDKey` (the signature-verification
/// key) live in Info.plist; the matching private key signs each build in the
/// release pipeline. Created once at launch so Sparkle polls on its schedule;
/// the menu-bar "Check for Updates…" item drives a manual check.
///
/// Ships in the *notarized DMG* path only — a menu-bar app with a global event
/// tap can't be sandboxed, so it updates itself via Sparkle rather than the App
/// Store (native/README.md). Until an appcast is hosted and `SUPublicEDKey` is
/// set, checks simply find nothing — Sparkle refuses unsigned updates by design.
@MainActor
final class UpdaterController: ObservableObject {
    static let shared = UpdaterController()

    private let controller: SPUStandardUpdaterController
    private let probe: UpdaterProbe
    private var canCheckObservation: NSKeyValueObservation?

    /// Mirrors Sparkle's `canCheckForUpdates` so SwiftUI re-renders the
    /// "Check for updates now" CTA when a launch/scheduled check finishes —
    /// otherwise the button, in a persistent window, could stay disabled until
    /// the view happened to reload.
    @Published private(set) var canCheckForUpdates = false

    /// True once the appcast has offered a version newer than the running one.
    /// Drives the sidebar's "Update" call to action.
    @Published private(set) var updateAvailable = false

    /// The version waiting to be installed, when one is (e.g. "0.5.21").
    @Published private(set) var availableVersion: String?

    /// False until a check has actually finished. The sidebar stays quiet
    /// rather than claiming "Up to date" on a version it has not verified.
    @Published private(set) var hasCheckedForUpdates = false

    /// True from the moment a silent probe starts until the appcast answers
    /// it. A probe that aborts while this is set answered nothing, so the
    /// status it was meant to refresh is dropped rather than left to go stale.
    private var probeAwaitingResult = false

    private init() {
        let probe = UpdaterProbe()
        self.probe = probe
        // startingUpdater: true → background appcast checks begin immediately.
        controller = SPUStandardUpdaterController(
            startingUpdater: true,
            updaterDelegate: probe,
            userDriverDelegate: nil
        )
        probe.onFound = { [weak self] item in
            guard let self else { return }
            self.probeAwaitingResult = false
            self.hasCheckedForUpdates = true
            self.updateAvailable = true
            self.availableVersion = item.displayVersionString
        }
        probe.onNotFound = { [weak self] in
            guard let self else { return }
            self.probeAwaitingResult = false
            self.hasCheckedForUpdates = true
            self.updateAvailable = false
            self.availableVersion = nil
        }
        probe.onAborted = { [weak self] in
            // A result already in hand means this is the abort that follows
            // "no update found" — the status stands. Otherwise the check
            // failed, and an unverified status is worse than none.
            guard let self, self.probeAwaitingResult else { return }
            self.probeAwaitingResult = false
            self.clearVerifiedStatus()
        }
        // Honor the user's saved preference for automatic updates.
        apply(automatic: Settings.load().automaticUpdates)
        // Keep the published flag in sync with Sparkle's KVO-observable state.
        canCheckForUpdates = controller.updater.canCheckForUpdates
        canCheckObservation = controller.updater.observe(
            \.canCheckForUpdates, options: [.new]
        ) { [weak self] _, change in
            guard let value = change.newValue else { return }
            Task { @MainActor in self?.canCheckForUpdates = value }
        }
        // Sparkle explicitly allows a check on the runloop cycle that starts
        // the updater, so the sidebar label is honest from the first window.
        refreshUpdateStatus()
    }

    /// The running app's marketing version (e.g. "0.4.2"), read from the bundle
    /// so the UI never hardcodes it.
    var appVersion: String {
        Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "—"
    }

    /// Silent appcast probe: no Sparkle UI, just the delegate callbacks that
    /// tell the sidebar whether this build is the latest one.
    ///
    /// Skipped when the user has turned automatic updates off — that switch is
    /// an opt-out of background network checks, not just of silent installs —
    /// and while a check is already running, where Sparkle would ignore it.
    func refreshUpdateStatus() {
        guard controller.updater.automaticallyChecksForUpdates,
              !controller.updater.sessionInProgress else { return }
        probeAwaitingResult = true
        controller.updater.checkForUpdateInformation()
    }

    /// Manual "Check for Updates…" / "Check for updates now" — shows Sparkle's
    /// standard UI so an on-demand check always has clear feedback.
    func checkForUpdates() { controller.checkForUpdates(nil) }

    /// The sidebar's "Update" action. Sparkle owns the download, signature and
    /// notarization checks, and the relaunch, so this hands the user straight
    /// to that flow for the version the probe already found.
    func installAvailableUpdate() { checkForUpdates() }

    /// Toggle automatic updates (Settings ▸ Automatic updates): both the daily
    /// scheduled check and the silent background download+install.
    func setAutomaticChecks(_ enabled: Bool) {
        apply(automatic: enabled)
        if enabled {
            refreshUpdateStatus()
        } else {
            // The status was learned from a check the user has now opted out
            // of; stop asserting it rather than letting it go stale.
            probeAwaitingResult = false
            clearVerifiedStatus()
        }
    }

    /// Drop what the last check established, so the footer falls back to the
    /// bare version instead of vouching for a build nothing verified.
    private func clearVerifiedStatus() {
        hasCheckedForUpdates = false
        updateAvailable = false
        availableVersion = nil
    }

    /// "Automatic" means check on the schedule AND download+install in the
    /// background (installed on next relaunch). Sparkle requires downloads to be
    /// gated behind checks, so both flip together. Signature + notarization are
    /// still verified before any install.
    private func apply(automatic: Bool) {
        controller.updater.automaticallyChecksForUpdates = automatic
        controller.updater.automaticallyDownloadsUpdates = automatic
    }
}
