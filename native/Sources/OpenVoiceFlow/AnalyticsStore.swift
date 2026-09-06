import Foundation

/// Opt-out anonymous usage sharing + leaderboard.
///
/// On by default (Settings ▸ Privacy ▸ "Share anonymous usage & leaderboard
/// rank"), turning it off stops every network call this file makes. What's
/// sent is a handful of aggregate counters this app already shows on the
/// Home pane — total words, minutes saved, streak, which features are in
/// use — tagged with a random device ID and a display name the user can
/// change — plus aggregate counters for which panes and features get used
/// (`UsageCounters`: a fixed set of names and totals, no text, no timestamps).
/// Never dictation text, snippets, dictionary entries, or the Know-Me profile.
/// See the Analytics & leaderboard section of the privacy docs for the exact
/// wire format.

// MARK: - Identity

struct AnalyticsIdentity: Codable, Equatable {
    var deviceId: String
    var displayName: String
}

@MainActor
final class AnalyticsIdentityStore: ObservableObject {
    @Published var identity: AnalyticsIdentity { didSet { AppSupport.save(identity, to: "analytics_identity.json") } }

    init() {
        if var saved = AppSupport.load(AnalyticsIdentity.self, from: "analytics_identity.json") {
            let compactName = LeaderboardAlias.compactLegacyDefault(saved.displayName)
            if compactName != saved.displayName {
                saved.displayName = compactName
                AppSupport.save(saved, to: "analytics_identity.json")
            }
            identity = saved
        } else {
            identity = AnalyticsIdentityStore.makeIdentity()
        }
    }

    private static func makeIdentity() -> AnalyticsIdentity {
        AnalyticsIdentity(deviceId: UUID().uuidString, displayName: LeaderboardAlias.random())
    }

    static func randomDisplayName() -> String {
        LeaderboardAlias.random()
    }
}

// MARK: - Wire types

struct LeaderboardRow: Codable, Identifiable {
    var displayName: String
    var minutesSaved: Int
    var rank: Int
    var id: String { "\(rank)-\(displayName)" }

    enum CodingKeys: String, CodingKey { case displayName, minutesSaved, rank }
}

struct YouRow: Codable {
    var displayName: String
    var minutesSaved: Int
    var rank: Int
    var inTop: Bool
}

struct LeaderboardResponse: Codable {
    var top: [LeaderboardRow]
    var you: YouRow?
}

// MARK: - Client

@MainActor
final class AnalyticsClient: ObservableObject {
    @Published private(set) var leaderboard: LeaderboardResponse?
    @Published private(set) var isLoadingLeaderboard = false
    @Published private(set) var leaderboardError: String?
    @Published private(set) var syncError: String?

    /// Base URL for the analytics API. The same Vercel project the docs site
    /// deploys to — see api/analytics/ingest.js and api/leaderboard.js.
    private let baseURL = URL(string: "https://openvoiceflow.com")!
    private var lastSyncedAt: Date?
    /// Don't hammer the endpoint on every single dictation — once every few
    /// minutes is plenty for counters that only move in small increments.
    private let minSyncInterval: TimeInterval = 180

    func syncIfDue(controller: AppController, force: Bool = false) {
        guard controller.settings.shareAnalytics else { return }
        if !force, let last = lastSyncedAt, Date().timeIntervalSince(last) < minSyncInterval { return }
        Task { _ = await syncNow(controller: controller) }
    }

    /// Sends this installation's current aggregate snapshot. Used directly
    /// after a nickname commit; scheduled dictation syncs call through
    /// `syncIfDue` so they remain throttled.
    @discardableResult
    func syncNow(controller: AppController) async -> Bool {
        guard controller.settings.shareAnalytics else { return false }
        let identity = controller.analyticsIdentity.identity
        let history = controller.historyStore
        let settings = controller.settings

        var body: [String: Any] = [
            "deviceId": identity.deviceId,
            "displayName": identity.displayName,
            "wordsTotal": history.totalWords,
            "minutesSaved": history.totalMinutes,
            "streakDays": history.streak,
            "appVersion": UpdaterController.shared.appVersion,
            "featureUsage": [
                "cleanupEnabled": settings.backend != .none,
                "snippetsCount": controller.snippetStore.snippets.count,
                "dictionaryCount": controller.dictionaryStore.entries.count,
                "hasKnowMeProfile": controller.profileStore.hasProfile,
            ],
            // Which panes and features this install actually uses: counter
            // names and totals, nothing else. See UsageCounters.
            "events": controller.usageCounters.payload,
        ]
        if let firstUse = settings.firstUseDate {
            body["firstUseDate"] = ISO8601DateFormatter().string(from: firstUse)
        }

        var req = URLRequest(url: baseURL.appending(path: "api/analytics/ingest"))
        req.httpMethod = "POST"
        req.timeoutInterval = 10
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try? JSONSerialization.data(withJSONObject: body)
        do {
            let (_, response) = try await URLSession.shared.data(for: req)
            guard let http = response as? HTTPURLResponse,
                  (200..<300).contains(http.statusCode) else {
                syncError = "Couldn’t update the leaderboard. Check your connection and try again."
                return false
            }
            lastSyncedAt = Date()
            syncError = nil
            return true
        } catch {
            syncError = "Couldn’t update the leaderboard. Check your connection and try again."
            return false
        }
    }

    /// Deletes this device's row from the leaderboard/analytics table
    /// entirely (right-to-erasure). Does not touch the local sharing
    /// toggle — call this from an explicit "Delete my leaderboard data"
    /// action, separate from just turning sharing off.
    func deleteMyData(deviceId: String, counters: UsageCounters? = nil) async {
        var components = URLComponents(url: baseURL.appending(path: "api/analytics/ingest"), resolvingAgainstBaseURL: false)!
        components.queryItems = [URLQueryItem(name: "deviceId", value: deviceId)]
        guard let url = components.url else { return }
        var req = URLRequest(url: url)
        req.httpMethod = "DELETE"
        req.timeoutInterval = 10
        _ = try? await URLSession.shared.data(for: req)
        // Clear the local counters too. They are lifetime totals, so leaving
        // them behind would have the next sync re-upload the very numbers the
        // user just asked to have deleted.
        counters?.reset()
        leaderboard = nil
    }

    /// Fetches the leaderboard. Safe to call whether or not sharing is on —
    /// the endpoint just won't know this device if it never sent data, and
    /// `you` comes back nil.
    func fetchLeaderboard(deviceId: String) async {
        isLoadingLeaderboard = true
        leaderboardError = nil
        defer { isLoadingLeaderboard = false }
        var components = URLComponents(url: baseURL.appending(path: "api/leaderboard"), resolvingAgainstBaseURL: false)!
        components.queryItems = [URLQueryItem(name: "deviceId", value: deviceId)]
        guard let url = components.url else {
            leaderboardError = "Couldn’t load the leaderboard. Try again."
            return
        }
        do {
            let (data, response) = try await URLSession.shared.data(from: url)
            guard let http = response as? HTTPURLResponse,
                  (200..<300).contains(http.statusCode) else {
                leaderboardError = "Couldn’t load the leaderboard. Check your connection and try again."
                return
            }
            leaderboard = try JSONDecoder().decode(LeaderboardResponse.self, from: data)
            leaderboardError = nil
        } catch {
            leaderboardError = "Couldn’t load the leaderboard. Check your connection and try again."
        }
    }
}
