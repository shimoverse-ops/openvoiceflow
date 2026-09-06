import Foundation

/// Local, aggregate "which parts of the app get used" counters.
///
/// This is the in-app half of the website's page/CTA analytics: it answers
/// which panes people open and which features they actually reach for, so a
/// feature nobody opens can be found without guessing. It deliberately cannot
/// answer anything else.
///
/// The shape is the point. A counter is a name and a number — `pane.history`,
/// 42. There is no event log, no timestamps, no ordering, and no payload, so
/// there is nothing here that could reconstruct a session, and nothing that
/// could contain dictated text, a snippet, a dictionary entry, or a profile
/// even by accident: the names are compile-time constants in `Event`, and
/// `record` takes one of those, never a caller-supplied string.
///
/// Counters live in Application Support like every other local store and are
/// only ever transmitted by `AnalyticsClient`, under the same Settings ▸
/// Privacy ▸ "Share anonymous usage & leaderboard rank" switch as the rest of
/// the payload. Off means they stay on the Mac; they are still counted, so the
/// Home pane can show local usage without asking the network anything.
@MainActor
final class UsageCounters: ObservableObject {
    /// Every counter this app can emit. A closed set, so the wire format is
    /// reviewable in one place and the server can reject anything unknown.
    enum Event: String, CaseIterable {
        // Panes — the app's equivalent of a page view.
        case paneHome = "pane.home"
        case paneHistory = "pane.history"
        case panePersonalize = "pane.personalize"
        case paneSettings = "pane.settings"
        case paneLeaderboard = "pane.leaderboard"

        // Personalize tabs, which are panes in all but name.
        case tabDictionary = "tab.dictionary"
        case tabSnippets = "tab.snippets"
        case tabStyles = "tab.styles"
        case tabProfile = "tab.profile"

        // Features and calls to action — what people actually press.
        case dictationCompleted = "action.dictation_completed"
        case historyCopied = "action.history_copied"
        case historyCleared = "action.history_cleared"
        case dictionaryEntryAdded = "action.dictionary_entry_added"
        case snippetAdded = "action.snippet_added"
        case styleApplied = "action.style_applied"
        case knowMeInterviewStarted = "action.know_me_interview_started"
        case knowMeInterviewFinished = "action.know_me_interview_finished"
        case cleanupBackendChanged = "action.cleanup_backend_changed"
        case updateChecked = "action.update_checked"
        case versionHistoryOpened = "action.version_history_opened"
        case feedbackOpened = "action.feedback_opened"
        case feedbackSent = "action.feedback_sent"
        case leaderboardNameChanged = "action.leaderboard_name_changed"
        case onboardingCompleted = "action.onboarding_completed"
    }

    private static let fileName = "usage_counters.json"

    /// Lifetime totals, keyed by `Event.rawValue`. Lifetime rather than
    /// per-session so a dropped or throttled sync can never lose a count: each
    /// upload replaces the previous one with a superset.
    @Published private(set) var counts: [String: Int]

    init(counts: [String: Int]? = nil) {
        self.counts = counts ?? AppSupport.load([String: Int].self, from: UsageCounters.fileName) ?? [:]
    }

    /// Bump a counter. Cheap and non-throwing by design — call sites are UI
    /// actions, and analytics must never be able to break one.
    func record(_ event: Event) {
        counts[event.rawValue, default: 0] += 1
        persist()
    }

    /// Pane and tab views arrive on every re-render of a SwiftUI selection, so
    /// callers use this to count a visit only when the destination changed.
    func recordIfChanged(_ event: Event, from previous: Event?) {
        guard previous != event else { return }
        record(event)
    }

    /// The wire payload: names and totals only, and only counters that moved.
    var payload: [String: Int] {
        counts.filter { $0.value > 0 }
    }

    /// Settings ▸ Privacy ▸ "Delete my leaderboard data" clears the server
    /// copy; this clears the local one, so a user who wants to be forgotten
    /// doesn't have the next sync re-upload the same lifetime totals.
    func reset() {
        counts = [:]
        persist()
    }

    private func persist() {
        AppSupport.save(counts, to: UsageCounters.fileName)
    }
}
