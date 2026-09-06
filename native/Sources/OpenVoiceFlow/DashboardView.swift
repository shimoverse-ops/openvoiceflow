import AppKit
import SwiftUI

/// The dashboard window — design phase 03 (design sources in git history).
///
/// Fixed 212 pt sidebar (text + selection tint, no icons — by design) and a
/// flexible content pane. Data-backed panes render the designed empty states
/// until their stores exist; stats celebrate outcomes (words, time back),
/// never engagement.
struct DashboardView: View {
    @ObservedObject var controller: AppController
    // Observe the stores directly so pane edits refresh live.
    @ObservedObject private var history: HistoryStore
    @ObservedObject private var dictionary: DictionaryStore
    @ObservedObject private var snippets: SnippetStore
    @ObservedObject private var styleStore: StyleStore
    @ObservedObject private var profileStore: ProfileStore
    @ObservedObject private var analyticsClient: AnalyticsClient
    @ObservedObject private var usageCounters: UsageCounters
    @ObservedObject private var analyticsIdentity: AnalyticsIdentityStore
    // Observe the updater so the "Check for updates now" CTA re-enables when a
    // background check finishes.
    @ObservedObject private var updater = UpdaterController.shared
    @State private var pane: Pane = .home
    @State private var personalizeTab: PersonalizeTab = .dictionary
    @State private var showInterview = false
    @State private var showFeedback = false
    @State private var apiKeyDraft = ""       // mirrors the Keychain key for the selected backend
    @State private var showDeleteHistory = false
    @State private var leaderboardNameDraft: String
    @State private var leaderboardNameValidationError: String?
    @State private var isRefreshingLeaderboard = false
    @StateObject private var copyFeedback = HistoryCopyFeedback()
    @FocusState private var leaderboardNameFocused: Bool
    // Live TCC statuses for the Settings permissions card. Polled (not
    // event-driven) because a grant can land in System Settings while this
    // window stays key — see Permission.watch.
    @State private var permissionStatus: [Permission: Permission.Status] = [:]
    @State private var permissionWatch: Task<Void, Never>?
    /// Checked when Home appears; drives the squeezed-out-icon banner.
    @State private var menuBarIconVisible = true
    @Environment(\.colorScheme) private var scheme

    init(controller: AppController) {
        self.controller = controller
        self.history = controller.historyStore
        self.dictionary = controller.dictionaryStore
        self.snippets = controller.snippetStore
        self.styleStore = controller.styleStore
        self.profileStore = controller.profileStore
        self.analyticsClient = controller.analyticsClient
        self.usageCounters = controller.usageCounters
        self.analyticsIdentity = controller.analyticsIdentity
        self._leaderboardNameDraft = State(initialValue: controller.analyticsIdentity.identity.displayName)
    }

    enum Pane: String, CaseIterable {
        case home = "Home"
        case history = "History"
        /// Dictionary, Snippets, and Styles used to be three sidebar rows for
        /// one job — teach the app something once. Now they're tabs inside
        /// this single pane.
        case personalize = "Personalize"
        case settings = "Settings"
        /// Not in the main sidebar loop — it gets its own row below Feedback,
        /// same treatment as the Feedback button itself.
        case leaderboard = "Leaderboard"
    }

    /// The destinations merged into the Personalize pane.
    enum PersonalizeTab: String, CaseIterable, Identifiable, Hashable {
        case dictionary = "Dictionary"
        case snippets = "Snippets"
        case styles = "Styles"
        case knowMe = "Know Me"

        var id: String { rawValue }

        var caption: String {
            switch self {
            case .dictionary: return "Words I keep getting wrong. Fix them once."
            case .snippets: return "Say the short thing, get the long thing."
            case .styles: return "How you sound, per app."
            case .knowMe: return "Teach cleanup your names, jargon, and voice."
            }
        }
    }

    private var dark: Bool { scheme == .dark }
    private var ink: Color { dark ? DT.inkDark : DT.inkLight }
    private var ink2: Color { dark ? DT.ink2Dark : DT.ink2Light }
    private var card: Color { dark ? DT.cardDark : DT.cardLight }
    private var hair: Color { dark ? .white.opacity(0.09) : .black.opacity(0.08) }
    private var fill: Color { dark ? .white.opacity(0.06) : .black.opacity(0.05) }
    private var accent: Color { DT.emberWave }

    var body: some View {
        HStack(spacing: 0) {
            sidebar
            Divider().overlay(hair)
            content
                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
                .padding(.top, 26)
                .padding(.horizontal, 30)
                .background(dark ? DT.winDark : DT.winLight)
        }
        .frame(minWidth: 1000, minHeight: 768)
        // Re-probe the appcast whenever the window comes back, so the footer
        // reflects a release published since the app launched.
        .onAppear {
            updater.refreshUpdateStatus()
            // The window opens on Home without a selection change, so count
            // that visit here or Home would look like the least-used pane.
            usageCounters.record(DashboardView.event(for: pane))
        }
        // Counted on change rather than on render: a pane's body re-runs for
        // any state it reads, and a visit is a navigation, not a redraw.
        .onChange(of: pane) { previous, current in
            usageCounters.recordIfChanged(
                DashboardView.event(for: current), from: DashboardView.event(for: previous)
            )
        }
        .onChange(of: personalizeTab) { previous, current in
            usageCounters.recordIfChanged(
                DashboardView.event(for: current), from: DashboardView.event(for: previous)
            )
        }
    }

    /// Panes and tabs map to counter names here, in one place, so a renamed
    /// case can't silently split one metric into two.
    static func event(for pane: Pane) -> UsageCounters.Event {
        switch pane {
        case .home: return .paneHome
        case .history: return .paneHistory
        case .personalize: return .panePersonalize
        case .settings: return .paneSettings
        case .leaderboard: return .paneLeaderboard
        }
    }

    static func event(for tab: PersonalizeTab) -> UsageCounters.Event {
        switch tab {
        case .dictionary: return .tabDictionary
        case .snippets: return .tabSnippets
        case .styles: return .tabStyles
        case .knowMe: return .tabProfile
        }
    }

    // MARK: sidebar (212 pt, dot + label rows)

    private var sidebar: some View {
        VStack(alignment: .leading, spacing: 2) {
            HStack(spacing: 8) {
                RingGlyph(size: 22)
                Text("OpenVoiceFlow").font(.system(size: 13, weight: .bold)).foregroundStyle(ink)
            }
            .padding(.bottom, 14)
            .padding(.top, 34)  // room for traffic lights

            ForEach(Pane.allCases.filter { $0 != .leaderboard }, id: \.self) { item in
                Button { pane = item } label: {
                    HStack(spacing: 8) {
                        Circle()
                            .fill(pane == item ? accent : .clear)
                            .frame(width: 6, height: 6)
                        Text(item.rawValue)
                            .font(.system(size: 13, weight: pane == item ? .semibold : .regular))
                            .foregroundStyle(ink)
                        Spacer()
                    }
                    .padding(.vertical, 7)
                    .padding(.horizontal, 10)
                    .background(
                        RoundedRectangle(cornerRadius: 8)
                            .fill(pane == item
                                  ? (dark ? DT.emberDark.opacity(0.14) : DT.emberLight.opacity(0.10))
                                  : .clear)
                    )
                }
                .buttonStyle(.plain)
            }

            Button {
                usageCounters.record(.feedbackOpened)
                showFeedback = true
            } label: {
                HStack(spacing: 8) {
                    Circle().fill(.clear).frame(width: 6, height: 6)
                    Text("Feedback")
                        .font(.system(size: 13, weight: .regular))
                        .foregroundStyle(ink)
                    Spacer()
                }
                .padding(.vertical, 7)
                .padding(.horizontal, 10)
            }
            .buttonStyle(.plain)
            .sheet(isPresented: $showFeedback) {
                FeedbackView(controller: controller, onDismiss: { showFeedback = false })
            }

            Button { pane = .leaderboard } label: {
                HStack(spacing: 8) {
                    Circle()
                        .fill(pane == .leaderboard ? accent : .clear)
                        .frame(width: 6, height: 6)
                    Text("Leaderboard")
                        .font(.system(size: 13, weight: pane == .leaderboard ? .semibold : .regular))
                        .foregroundStyle(ink)
                    Spacer()
                }
                .padding(.vertical, 7)
                .padding(.horizontal, 10)
                .background(
                    RoundedRectangle(cornerRadius: 8)
                        .fill(pane == .leaderboard
                              ? (dark ? DT.emberDark.opacity(0.14) : DT.emberLight.opacity(0.10))
                              : .clear)
                )
            }
            .buttonStyle(.plain)

            Spacer()

            versionFooter
                .padding(.bottom, 12)
        }
        .padding(.horizontal, 10)
        .frame(width: 212)
        .background(dark ? DT.sideDark : DT.sideLight)
    }

    // MARK: sidebar footer (version + update state)
    //
    // Three states, and only one of them is clickable: a new version to
    // install offers "Update"; a verified-current build says "Up to date" and
    // asks nothing of the user; before any check has finished (or with
    // automatic checks off) the version stands alone rather than claiming a
    // freshness nobody confirmed.

    @ViewBuilder private var versionFooter: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(updater.updateAvailable ? accent : DT.moss)
                .frame(width: 6, height: 6)
            if updater.updateAvailable {
                Text("v\(updater.appVersion) ·")
                    .font(.system(size: 11)).foregroundStyle(ink2)
                Button { updater.installAvailableUpdate() } label: {
                    Text("Update")
                        .font(.system(size: 11, weight: .semibold))
                        .foregroundStyle(dark ? DT.emberDark : DT.emberLight)
                }
                .buttonStyle(.plain)
                .disabled(!updater.canCheckForUpdates)
                .help(updater.availableVersion.map { "Update to v\($0)" } ?? "Update")
            } else if updater.hasCheckedForUpdates {
                Text("v\(updater.appVersion) · Up to date")
                    .font(.system(size: 11)).foregroundStyle(ink2)
            } else {
                Text("v\(updater.appVersion)")
                    .font(.system(size: 11)).foregroundStyle(ink2)
            }
            Spacer(minLength: 0)
        }
    }

    // MARK: content router

    @ViewBuilder private var content: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                switch pane {
                case .home: home
                case .history: historyPane
                case .personalize: personalizePane
                case .settings: settingsPane
                case .leaderboard: leaderboardPane
                }
            }
            .padding(.bottom, 30)
        }
        .sheet(isPresented: $showInterview) {
            KnowMeInterview(controller: controller)
        }
        // The first-words card is the one thing a user is likely to miss, so it
        // is a separate, explicit choice rather than collateral damage.
        .confirmationDialog("Delete every dictation from this Mac?",
                            isPresented: $showDeleteHistory, titleVisibility: .visible) {
            Button("Delete, keep my first words") {
                history.clearAll(keepingFirst: true)
                usageCounters.record(.historyCleared)
            }
            Button("Delete everything", role: .destructive) {
                history.clearAll(keepingFirst: false)
                usageCounters.record(.historyCleared)
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("History, stats and the per-app breakdown are cleared. Your first dictation can be kept.")
        }
    }

    private func paneTitle(_ title: String, _ subtitle: String? = nil) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title).font(.system(size: 22, weight: .bold)).kerning(-0.4).foregroundStyle(ink)
            if let subtitle {
                Text(subtitle).font(.system(size: 12.5)).foregroundStyle(ink2)
            }
        }
    }

    // MARK: Home
    //
    // The greeting held the largest type on the pane and said nothing, and four
    // equal stat cards meant no card was the point. What replaces them is one
    // number worth looking at, the user's own first sentence, and where their
    // words actually go.

    private var home: some View {
        VStack(alignment: .leading, spacing: 14) {
            if !menuBarIconVisible { squeezedIconBanner }
            HStack(alignment: .top, spacing: 14) {
                timeBackCard.frame(maxWidth: .infinity)
                firstWordsCard.frame(width: 300)
            }
            .frame(height: 256)

            weekChart

            HStack(alignment: .top, spacing: 14) {
                whereYouDictateCard.frame(maxWidth: .infinity)
                recentCard.frame(maxWidth: .infinity)
            }
            .frame(height: 214)
        }
        .padding(.top, 8)
        .onAppear { menuBarIconVisible = HelloCallout.iconIsVisible }
    }

    /// macOS hides the leftmost menu-bar items when the bar runs out of room
    /// (the notch makes this routine on laptops), and no app can claim
    /// priority — the user's ⌘-drag is the only lever. So when our icon has
    /// been squeezed out, say so and hand them the lever, instead of leaving
    /// "the waveform vanished" a mystery.
    private var squeezedIconBanner: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: "menubar.arrow.up.rectangle")
                .font(.system(size: 16))
                .foregroundStyle(DT.warnAmber)
                .padding(.top, 2)
            VStack(alignment: .leading, spacing: 3) {
                Text("Your menu bar is full, so macOS is hiding the waveform.")
                    .font(.system(size: 13, weight: .semibold)).foregroundStyle(ink)
                Text("Dictation still works — the hotkey doesn't need the icon. To see it "
                     + "again, hold ⌘ and drag other icons off the bar, or drag ours toward "
                     + "the clock: rightmost icons are the last macOS hides. Apps can't "
                     + "set their own priority; where you drop it is where it stays.")
                    .font(.system(size: 12)).foregroundStyle(ink2)
                    .fixedSize(horizontal: false, vertical: true)
            }
            Spacer()
        }
        .padding(14)
        .background(RoundedRectangle(cornerRadius: 12).fill(DT.warnAmber.opacity(0.08)))
        .overlay(RoundedRectangle(cornerRadius: 12).strokeBorder(DT.warnAmber.opacity(0.35)))
    }

    /// Row 1 left — the one number on the pane worth the largest type.
    private var timeBackCard: some View {
        let minutes = history.totalMinutes
        return VStack(alignment: .leading, spacing: 0) {
            eyebrow("TIME BACK", color: ink2)
            HStack(alignment: .firstTextBaseline, spacing: 3) {
                if minutes >= 60 {
                    heroNumber(minutes / 60); heroUnit("h")
                    heroNumber(minutes % 60); heroUnit("m")
                } else {
                    heroNumber(minutes); heroUnit("m")
                }
            }
            .padding(.top, 10)

            Text(timeBackSentence)
                .font(.system(size: 14.5))
                .lineSpacing(8)  // line-height 1.55
                .foregroundStyle(ink2)
                .frame(maxWidth: 340, alignment: .leading)
                .fixedSize(horizontal: false, vertical: true)
                .padding(.top, 14)

            Spacer()

            Rectangle().fill(hair).frame(height: 1)
            HStack(spacing: 16) {
                footnote("\(history.totalWords.grouped) words")
                footnoteDot
                footnote("\(history.entries.count.grouped) takes")
                if history.streak > 0 {
                    footnoteDot
                    // Demoted on purpose: a streak card creates an obligation,
                    // and as a footnote it cannot visibly break.
                    footnote("\(history.streak.grouped) days running")
                }
            }
            .padding(.top, 15)
        }
        .padding(.horizontal, 24).padding(.vertical, 22)
        .background(cardBackground)
    }

    private func heroNumber(_ value: Int) -> some View {
        Text("\(value)")
            .font(.system(size: DT.heroNumberSize, weight: .bold))
            .kerning(DT.heroNumberKerning)
            .foregroundStyle(ink)
    }

    private func heroUnit(_ unit: String) -> some View {
        Text(unit).font(.system(size: 26, weight: .semibold)).foregroundStyle(ink2)
    }

    /// "Two working days you didn't spend typing, since March." — the honest
    /// version degrades gracefully when there is nothing to report yet.
    private var timeBackSentence: String {
        let minutes = history.totalMinutes
        guard minutes > 0 else {
            return "Hold \(controller.settings.hotkey.glyph) anywhere and talk. This is where the time you get back shows up."
        }
        var sentence: String
        let workingDays = Double(minutes) / (60 * 8)
        if workingDays >= 1 {
            let rounded = (workingDays * 10).rounded() / 10
            let label = rounded == 1 ? "One working day" : "\(Self.spelled(rounded)) working days"
            sentence = "\(label) you didn't spend typing"
        } else {
            sentence = "Time you didn't spend typing"
        }
        if let since = controller.settings.firstUseDate {
            sentence += ", since \(Self.monthName(since))"
        }
        return sentence + "."
    }

    private static func spelled(_ value: Double) -> String {
        let words = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
        if value == value.rounded(), Int(value) < words.count { return words[Int(value)] }
        return String(format: "%.1f", value)
    }

    private static func monthName(_ date: Date) -> String {
        let f = DateFormatter()
        f.dateFormat = "MMMM"
        return f.string(from: date)
    }

    /// Row 1 right — the user's own first sentence, kept forever.
    @ViewBuilder private var firstWordsCard: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Moss, the one non-ember accent on the pane.
            eyebrow("YOUR FIRST WORDS", color: DT.moss)
            if let first = history.firstEntry {
                Text(first.text)
                    .font(.system(size: 15, weight: .medium))
                    .lineSpacing(7.5)  // line-height 1.5
                    .foregroundStyle(ink)
                    .fixedSize(horizontal: false, vertical: true)
                    .padding(.top, 12)
                Spacer()
                Text("\(Self.stamp(first.timestamp)) · in \(first.app)")
                    .font(.system(size: 11.5)).foregroundStyle(ink3)
            } else {
                Text("Your first dictation lands here — and stays.")
                    .font(.system(size: 13)).foregroundStyle(ink2)
                    .padding(.top, 12)
                Spacer()
            }
        }
        .padding(.horizontal, 20).padding(.vertical, 22)
        .background(cardBackground)
    }

    private static func stamp(_ date: Date) -> String {
        let f = DateFormatter()
        f.dateFormat = "d MMMM, h:mm a"
        return f.string(from: date)
    }

    /// Row 3 left — where the words actually go. Hidden until there are two apps
    /// to compare, because a single 100% bar says nothing.
    @ViewBuilder private var whereYouDictateCard: some View {
        let dist = history.appDistribution
        if dist.count >= 2 {
            let top = Array(dist.prefix(4))
            VStack(alignment: .leading, spacing: 0) {
                Text("Where you dictate")
                    .font(.system(size: 13, weight: .bold)).foregroundStyle(ink)
                GeometryReader { geo in
                    HStack(spacing: 1.5) {
                        ForEach(Array(top.enumerated()), id: \.offset) { i, row in
                            Rectangle()
                                .fill(DT.emberWave.opacity(1 - Double(i) * 0.13))
                                .frame(width: max(geo.size.width * row.fraction, 2))
                        }
                        if top.reduce(0.0, { $0 + $1.fraction }) < 0.999 {
                            Rectangle().fill(dark ? .white.opacity(0.10) : .black.opacity(0.10))
                        }
                    }
                }
                .frame(height: 10)
                .clipShape(RoundedRectangle(cornerRadius: 5))
                .padding(.top, 14)

                VStack(spacing: 12) {
                    ForEach(Array(top.enumerated()), id: \.offset) { i, row in
                        HStack(spacing: 10) {
                            AppIdentityLabel(
                                name: row.app, iconSize: 24, spacing: 10, ringFraction: row.fraction,
                                ringColor: DT.emberWave.opacity(1 - Double(i) * 0.13),
                                trackColor: hair
                            )
                            .font(.system(size: 12.5)).foregroundStyle(ink)
                            Spacer()
                            Text("\(Int((row.fraction * 100).rounded()))%")
                                .font(.system(size: 12.5, weight: .semibold)).foregroundStyle(ink)
                        }
                        .help("\(row.app) — \(Int((row.fraction * 100).rounded()))% of your dictation, "
                              + "≈\(HistoryStore.minutes(fromWords: row.words))m of typing given back")
                    }
                }
                .padding(.top, 14)
                Spacer()
            }
            .padding(.horizontal, 20).padding(.vertical, 20)
            .background(cardBackground)
        }
    }

    /// Row 3 right — three takes, then the privacy line pinned to the bottom.
    private var recentCard: some View {
        VStack(alignment: .leading, spacing: 0) {
            HStack {
                Text("Recent").font(.system(size: 13, weight: .bold)).foregroundStyle(ink)
                Spacer()
                Button("See all") { pane = .history }
                    .buttonStyle(.plain)
                    .font(.system(size: 11.5)).foregroundStyle(DT.emberLight)
            }
            if history.entries.isEmpty {
                Text("Nothing yet.")
                    .font(.system(size: 13)).foregroundStyle(ink2)
                    .padding(.top, 12)
            } else {
                VStack(spacing: 0) {
                    ForEach(Array(history.entries.prefix(3).enumerated()), id: \.element.id) { i, entry in
                        HStack(spacing: 10) {
                            Text(entry.timestamp, format: .dateTime.hour().minute())
                                .font(.system(size: 11)).foregroundStyle(ink2)
                                .frame(width: 46, alignment: .leading)
                            AppIdentityLabel(name: entry.app, iconSize: 16, spacing: 5)
                                .font(.system(size: 10, weight: .bold)).foregroundStyle(ink2)
                                .padding(.horizontal, 6).padding(.vertical, 2)
                                .background(RoundedRectangle(cornerRadius: 5).fill(fill))
                            Text(entry.text)
                                .font(.system(size: 12.5)).foregroundStyle(ink)
                                .lineLimit(1).truncationMode(.tail)
                            Spacer()
                        }
                        .padding(.vertical, 9)
                        if i < min(2, history.entries.count - 1) {
                            Rectangle().fill(hair).frame(height: 1)
                        }
                    }
                }
                .padding(.top, 6)
            }
            Spacer()
            Text("Stored on this Mac. Audio is discarded the moment it's transcribed.")
                .font(.system(size: 11)).foregroundStyle(ink3)
        }
        .padding(.horizontal, 20).padding(.vertical, 20)
        .background(cardBackground)
    }

    // MARK: card chrome

    private var cardBackground: some View {
        RoundedRectangle(cornerRadius: DT.rCard).fill(card)
            .overlay(RoundedRectangle(cornerRadius: DT.rCard).strokeBorder(hair))
    }

    private func eyebrow(_ text: String, color: Color) -> some View {
        Text(text)
            .font(.system(size: 11, weight: .semibold, design: .monospaced))
            .kerning(0.77)  // 0.07em
            .foregroundStyle(color)
    }

    private func footnote(_ text: String) -> some View {
        Text(text).font(.system(size: 12)).foregroundStyle(ink2)
    }

    private var footnoteDot: some View {
        Circle().fill(ink3).frame(width: 3, height: 3)
    }

    private var ink3: Color { dark ? Color(hex: 0x6B6558) : Color(hex: 0x9A9384) }

    /// This week, in minutes returned rather than words dictated.
    private var weekChart: some View {
        let values = history.minutesLastWeek
        let peak = max(values.max() ?? 1, 1)
        let letters = Self.weekLetters()
        return VStack(alignment: .leading, spacing: 0) {
            HStack(alignment: .firstTextBaseline, spacing: 8) {
                Text("This week").font(.system(size: 13, weight: .bold)).foregroundStyle(ink)
                Text("minutes returned per day").font(.system(size: 11)).foregroundStyle(ink2)
                Spacer()
                Text(Self.hoursMinutes(values.reduce(0, +)) + " total")
                    .font(.system(size: 11.5)).foregroundStyle(ink2)
            }
            HStack(alignment: .bottom, spacing: 10) {
                ForEach(Array(values.enumerated()), id: \.offset) { i, value in
                    let today = i == values.count - 1
                    VStack(spacing: 4) {
                        Text("\(value)")
                            .font(.system(size: 10.5, weight: today ? .semibold : .regular))
                            .foregroundStyle(today ? DT.emberDark : ink3)
                        UnevenRoundedRectangle(topLeadingRadius: 6, bottomLeadingRadius: 2,
                                               bottomTrailingRadius: 2, topTrailingRadius: 6)
                            .fill(today ? DT.emberWave : (dark ? .white.opacity(0.13) : .black.opacity(0.12)))
                            .frame(maxWidth: 52)
                            // 4% floor so a zero day is still a visible tick.
                            .frame(height: max(124 * CGFloat(value) / CGFloat(peak), 124 * 0.04))
                        Text(letters[i])
                            .font(.system(size: 10, weight: today ? .semibold : .regular))
                            .foregroundStyle(today ? ink : ink2)
                    }
                }
            }
            .frame(height: 160)
            .padding(.top, 8)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.horizontal, 20).padding(.vertical, 18)
        .background(cardBackground)
    }

    /// Day initials ending on today, so the last bar is always "now".
    private static func weekLetters() -> [String] {
        let f = DateFormatter()
        f.dateFormat = "EEEEE"
        return (0..<7).reversed().map { offset in
            let day = Calendar.current.date(byAdding: .day, value: -offset, to: Date()) ?? Date()
            return f.string(from: day)
        }
    }

    private static func hoursMinutes(_ minutes: Int) -> String {
        minutes >= 60
            ? "\((minutes / 60).grouped) h \(String(format: "%02d", minutes % 60)) m"
            : "\(minutes.grouped) m"
    }

    // MARK: History

    @ViewBuilder private var historyPane: some View {
        VStack(alignment: .leading, spacing: 14) {
            paneTitle("History", "Stored only on this Mac — never synced to a server.")
            if history.entries.isEmpty {
                emptyPanel(
                    title: "Nothing yet.",
                    body: "Hold \(controller.settings.hotkey.glyph) anywhere and say hello.",
                    button: nil
                )
            } else {
                ForEach(history.entries) { entry in
                    let isCopied = copyFeedback.isCopied(entry.id)
                    HStack(spacing: 12) {
                        Text(entry.timestamp, format: .dateTime.hour().minute())
                            .font(.system(size: 11)).foregroundStyle(ink2).frame(width: 56, alignment: .leading)
                        AppIdentityLabel(name: entry.app, iconSize: 16, spacing: 5)
                            .font(.system(size: 10, weight: .bold)).foregroundStyle(ink2)
                            .padding(.horizontal, 6).padding(.vertical, 2)
                            .background(RoundedRectangle(cornerRadius: 5).fill(fill))
                        Text(entry.text).font(.system(size: 12.5)).foregroundStyle(ink).lineLimit(1)
                        Spacer()
                        Text("\(entry.words)").font(.system(size: 11)).foregroundStyle(ink2)
                        Button {
                            NSPasteboard.general.clearContents()
                            if NSPasteboard.general.setString(entry.text, forType: .string) {
                                copyFeedback.markCopied(entry.id)
                            }
                        } label: {
                            Label(isCopied ? "Copied" : "Copy",
                                  systemImage: isCopied ? "checkmark" : "doc.on.doc")
                        }
                        .buttonStyle(.plain).font(.system(size: 11)).foregroundStyle(DT.emberLight)
                        .animation(.easeOut(duration: 0.15), value: isCopied)
                    }
                    .padding(.vertical, 10)
                    .overlay(Rectangle().fill(hair).frame(height: 1), alignment: .top)
                }
                Text("Raw audio is discarded after transcription. Delete everything from Settings › Privacy.")
                    .font(.system(size: 11)).foregroundStyle(ink2).padding(.top, 6)
            }
        }
    }

    // MARK: Leaderboard
    //
    // The card is a fixed frame on purpose. `api/leaderboard.js` names only
    // devices past a real usage bar and caps the list at five, precisely so the
    // endpoint never hints at the size of the user base — but a card sized to
    // whatever came back hands that number straight back: four rows reads as
    // four users. So `boardSlots` rows always render, and every slot the
    // response doesn't fill is masked.
    //
    // The masking is honest about what it is. A masked slot carries no rank, no
    // name and no total, and the tail fades out instead of ending on a hard
    // edge: it is an ellipsis, not an assertion that some specific person sits
    // there. Nothing here explains the reveal rule either — stating the bar
    // ("named past an hour saved") would have let a reader turn the names they
    // can see back into a population, which is the leak this closes.

    /// Rows the card always draws, named or masked.
    private static let boardSlots = 7

    @ViewBuilder private var leaderboardPane: some View {
        VStack(alignment: .leading, spacing: 14) {
            paneTitle("Leaderboard", "Ranked by time back. Your name is the one you set in Settings.")
            if !controller.settings.shareAnalytics {
                emptyPanel(
                    title: "Sharing is off",
                    body: "Turn on \u{201C}Share anonymous usage & leaderboard rank\u{201D} in Settings ▸ Privacy to join.",
                    button: "Open Settings",
                    action: { pane = .settings }
                )
            } else if (isRefreshingLeaderboard || analyticsClient.isLoadingLeaderboard)
                        && analyticsClient.leaderboard == nil {
                emptyPanel(title: "Loading…", body: "Fetching the current standings.", button: nil)
            } else if let error = analyticsClient.leaderboardError ?? analyticsClient.syncError {
                emptyPanel(
                    title: analyticsClient.leaderboardError == nil
                        ? "Leaderboard update failed"
                        : "Leaderboard unavailable",
                    body: error,
                    button: "Try again",
                    action: {
                        Task {
                            await refreshLeaderboard()
                        }
                    }
                )
            } else if let board = analyticsClient.leaderboard {
                leaderboardCard(board)
            } else {
                emptyPanel(
                    title: "No standings yet",
                    body: "Dictate a bit, then check back — this refreshes automatically.",
                    button: nil
                )
            }
        }
        .task(id: controller.settings.shareAnalytics) {
            guard controller.settings.shareAnalytics else { return }
            await refreshLeaderboard()
        }
    }

    @ViewBuilder private func leaderboardCard(_ board: LeaderboardResponse) -> some View {
        let revealed = Array(board.top.prefix(Self.boardSlots))
        VStack(alignment: .leading, spacing: 0) {
            ForEach(Array(revealed.enumerated()), id: \.offset) { i, row in
                if i > 0 {
                    Rectangle().fill(hair).frame(height: 1)
                }
                leaderboardRow(rank: row.rank, name: row.displayName, minutes: row.minutesSaved,
                                isYou: board.you?.inTop == true && board.you?.rank == row.rank
                                    && board.you?.displayName == row.displayName)
            }
            MaskedBoardTail(count: Self.boardSlots - revealed.count,
                            leadingDivider: !revealed.isEmpty,
                            hair: hair,
                            tint: maskTint)
            if let you = board.you, !you.inTop {
                Rectangle().fill(hair).frame(height: 1)
                HStack {
                    Text("···").font(.system(size: 13, weight: .bold)).foregroundStyle(ink3)
                    Spacer()
                }
                .padding(.vertical, 6).padding(.horizontal, 4)
                Rectangle().fill(hair).frame(height: 1)
                leaderboardRow(rank: you.rank, name: you.displayName, minutes: you.minutesSaved, isYou: true)
            }
        }
        .padding(.horizontal, 20).padding(.vertical, 8)
        .background(cardBackground)
    }

    /// Faint enough to read as a redaction, solid enough not to look broken.
    private var maskTint: Color { dark ? .white.opacity(0.11) : .black.opacity(0.09) }

    private func leaderboardRow(rank: Int, name: String, minutes: Int, isYou: Bool) -> some View {
        HStack(spacing: 12) {
            Text(Self.medal(for: rank) ?? "#\(rank)")
                .font(.system(size: 13, weight: .bold))
                .foregroundStyle(rank <= 3 ? DT.emberWave : ink2)
                .frame(width: 34, alignment: .leading)
            Text(name)
                .font(.system(size: 13, weight: isYou ? .bold : .regular))
                .foregroundStyle(ink)
            if isYou {
                Text("YOU")
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .foregroundStyle(DT.emberWave)
                    .padding(.horizontal, 6).padding(.vertical, 2)
                    .background(RoundedRectangle(cornerRadius: 5).fill(DT.emberWave.opacity(0.12)))
            }
            Spacer()
            Text(Self.hoursMinutes(minutes) + " back")
                .font(.system(size: 12.5, weight: .medium)).foregroundStyle(ink2)
        }
        .padding(.vertical, 11)
        .background(isYou ? (dark ? DT.emberDark.opacity(0.10) : DT.emberLight.opacity(0.08)) : .clear)
    }

    private static func medal(for rank: Int) -> String? {
        switch rank {
        case 1: return "🥇"
        case 2: return "🥈"
        case 3: return "🥉"
        default: return nil
        }
    }

    // MARK: Personalize (Dictionary + Snippets + Styles + Know Me)
    //
    // Dictionary, snippets, styles, and Know Me all teach the app something
    // once. One pane keeps them together as facets of the same job.

    @ViewBuilder private var personalizePane: some View {
        VStack(alignment: .leading, spacing: 16) {
            paneTitle("Personalize", personalizeTab.caption)
            personalizeTabBar
            personalizeCard
        }
    }

    private var personalizeTabBar: some View {
        HStack(spacing: 4) {
            ForEach(PersonalizeTab.allCases) { tab in
                Button {
                    withAnimation(DT.snap) { personalizeTab = tab }
                } label: {
                    HStack(spacing: 6) {
                        Text(tab.rawValue)
                            .font(.system(size: 12.5, weight: personalizeTab == tab ? .semibold : .regular))
                            .foregroundStyle(personalizeTab == tab ? ink : ink2)
                        Text("\(personalizeCount(tab))")
                            .font(.system(size: 10.5, weight: .bold))
                            .foregroundStyle(personalizeTab == tab ? .white : ink2)
                            .padding(.horizontal, 5.5).padding(.vertical, 1.5)
                            .background(Capsule().fill(personalizeTab == tab ? DT.emberWave : fill))
                    }
                    .padding(.vertical, 7).padding(.horizontal, 12)
                    .background(
                        RoundedRectangle(cornerRadius: 8)
                            .fill(personalizeTab == tab ? card : .clear)
                    )
                }
                .buttonStyle(.plain)
            }
            Spacer()
        }
        .padding(4)
        .background(RoundedRectangle(cornerRadius: 10).fill(fill))
    }

    private func personalizeCount(_ tab: PersonalizeTab) -> Int {
        switch tab {
        case .dictionary: return dictionary.entries.count
        case .snippets: return snippets.snippets.count
        case .styles: return styleStore.map.count
        case .knowMe: return profileStore.hasProfile ? 1 : 0
        }
    }

    @ViewBuilder private var personalizeCard: some View {
        VStack(alignment: .leading, spacing: 14) {
            switch personalizeTab {
            case .dictionary: dictionarySection
            case .snippets: snippetsSection
            case .styles: stylesSection
            case .knowMe: knowMe
            }
        }
        .padding(18)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(cardBackground)
        .id(personalizeTab)
        .transition(.opacity)
    }

    @ViewBuilder private var dictionarySection: some View {
        addRow(placeholder: "Add a word (e.g. WhisperKit)") {
            dictionary.add(word: $0)
            usageCounters.record(.dictionaryEntryAdded)
        }
        if dictionary.entries.isEmpty {
            emptyPanel(title: "No corrections yet",
                       body: "Add a word above, or run the Know-Me interview to seed names and jargon automatically.",
                       button: nil)
        } else {
            ForEach(dictionary.entries) { entry in
                HStack {
                    Text(entry.word).font(.system(size: 13, weight: .semibold)).foregroundStyle(ink)
                    if !entry.aliases.isEmpty {
                        Text("↤ \(entry.aliases.joined(separator: ", "))")
                            .font(.system(size: 11)).foregroundStyle(ink2)
                    }
                    Spacer()
                    Button { dictionary.remove(entry) } label: {
                        Image(systemName: "xmark.circle.fill").foregroundStyle(ink2)
                    }.buttonStyle(.plain)
                }
                .padding(.vertical, 9)
                .overlay(Rectangle().fill(hair).frame(height: 1), alignment: .top)
            }
        }
    }

    @ViewBuilder private var snippetsSection: some View {
        SnippetAddRow(fill: fill, ink: ink, ink2: ink2, accent: DT.emberLight) { trigger, expansion in
            snippets.add(trigger: trigger, expansion: expansion)
            usageCounters.record(.snippetAdded)
        }
        if snippets.snippets.isEmpty {
            emptyPanel(title: "No snippets yet",
                       body: "Try \"my address\". Then just say it.",
                       button: nil)
        } else {
            ForEach(snippets.snippets) { snip in
                HStack(alignment: .top, spacing: 12) {
                    Text(snip.trigger).font(.system(size: 11, weight: .bold)).foregroundStyle(DT.emberLight)
                        .padding(.horizontal, 6).padding(.vertical, 2)
                        .background(RoundedRectangle(cornerRadius: 6).fill(fill))
                    Text(snip.expansion).font(.system(size: 12.5)).foregroundStyle(ink)
                    Spacer()
                    Button { snippets.remove(snip) } label: {
                        Image(systemName: "xmark.circle.fill").foregroundStyle(ink2)
                    }.buttonStyle(.plain)
                }
                .padding(.vertical, 10)
                .overlay(Rectangle().fill(hair).frame(height: 1), alignment: .top)
            }
        }
    }

    /// A one-field add row used by the Dictionary tab.
    private func addRow(placeholder: String, onAdd: @escaping (String) -> Void) -> some View {
        InlineAddField(placeholder: placeholder, fill: fill, ink: ink, accent: DT.emberLight, onAdd: onAdd)
    }

    @ViewBuilder private var stylesSection: some View {
        ForEach(styleStore.map.sorted(by: { $0.key < $1.key }), id: \.key) { app, styleID in
            HStack(spacing: 12) {
                AppIdentityLabel(name: app, iconSize: 30, spacing: 12)
                    .font(.system(size: 13, weight: .semibold)).foregroundStyle(ink)
                    .frame(width: 192, alignment: .leading)
                Picker("", selection: styleBinding(for: app)) {
                    Text("Casual").tag("casual")
                    Text("Neutral").tag("default")
                    Text("Formal").tag("formal")
                    Text("Code").tag("code")
                    Text("Email").tag("email")
                }
                .labelsHidden()
                .frame(width: 130)
                Spacer()
            }
            .padding(.vertical, 11)
            .overlay(Rectangle().fill(hair).frame(height: 1), alignment: .top)
        }
        Text("Cleanup uses the frontmost app's style automatically; the menu-bar Style is the fallback.")
            .font(.system(size: 11)).foregroundStyle(ink2)
            .padding(.top, 12)
    }

    private func styleBinding(for app: String) -> Binding<String> {
        Binding(get: { styleStore.map[app] ?? "default" },
                set: { styleStore.map[app] = $0 })
    }

    // MARK: Know-Me

    private var knowMe: some View {
        VStack(alignment: .leading, spacing: 18) {
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 280), spacing: 14)], spacing: 14) {
                VStack(alignment: .leading, spacing: 12) {
                    Text("Profile").font(.system(size: 13, weight: .bold)).foregroundStyle(ink)
                    if profileStore.hasProfile {
                        profileRow("Name", profileStore.profile.name)
                        profileRow("Work", profileStore.profile.occupation)
                        profileRow("People", profileStore.profile.workNames.joined(separator: ", "))
                        profileRow("Jargon", profileStore.profile.technicalTerms.joined(separator: ", "))
                        profileRow("Tone", profileStore.profile.communicationStyle)
                        HStack(spacing: 12) {
                            Button("Re-run interview") {
                                usageCounters.record(.knowMeInterviewStarted)
                                showInterview = true
                            }.buttonStyle(.bordered)
                            Button("Clear") { profileStore.profile = Profile() }
                                .buttonStyle(.plain).font(.system(size: 12)).foregroundStyle(DT.destructive)
                        }
                        .padding(.top, 4)
                    } else {
                        Text("Run the interview and cleanup learns your name, your team's jargon, and how you like to sound.")
                            .font(.system(size: 12.5)).foregroundStyle(ink2)
                        Button("Run interview (2 min)") {
                            usageCounters.record(.knowMeInterviewStarted)
                            showInterview = true
                        }
                            .buttonStyle(.borderedProminent).tint(DT.emberWave)
                    }
                }
                .padding(18)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(RoundedRectangle(cornerRadius: 12).fill(card))
                .overlay(RoundedRectangle(cornerRadius: 12).strokeBorder(hair))

                VStack(alignment: .leading, spacing: 8) {
                    Text("What it does").font(.system(size: 13, weight: .bold)).foregroundStyle(ink)
                    Text("YOU SAID").font(.system(size: 11)).foregroundStyle(ink2)
                    Text("\"um yeah so tell priya we should ship the hud thing on friday i think\"")
                        .font(.system(size: 12.5)).italic().foregroundStyle(ink2)
                    Text("IT TYPES").font(.system(size: 11)).foregroundStyle(ink2)
                    Text("Priya — let's ship the HUD on Friday.")
                        .font(.system(size: 13, weight: .semibold)).foregroundStyle(ink)
                    Text("The profile is a local prompt fragment. It never syncs, and \"None\" backend ignores it entirely.")
                        .font(.system(size: 11)).foregroundStyle(ink2)
                }
                .padding(18)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(RoundedRectangle(cornerRadius: 12).fill(card))
                .overlay(RoundedRectangle(cornerRadius: 12).strokeBorder(hair))
            }
        }
    }

    @ViewBuilder private func profileRow(_ label: String, _ value: String) -> some View {
        if !value.isEmpty {
            HStack(alignment: .top, spacing: 8) {
                Text(label).font(.system(size: 12)).foregroundStyle(ink2).frame(width: 54, alignment: .leading)
                Text(value).font(.system(size: 12.5)).foregroundStyle(ink)
            }
        }
    }

    // MARK: Settings

    static let whisperModels: [(String, String)] = [
        ("tiny", "Tiny — 39 MB"),
        ("small", "Small — 466 MB"),
        ("medium", "Medium — 1.5 GB"),
        ("large-v3-v20240930", "Large v3 turbo — 1.6 GB"),
    ]
    // Whisper's standard 99-language multilingual set — shared by tiny, small,
    // medium, and large-v3-turbo, since all four ship the same tokenizer's
    // language tokens. (large-v3 also added Cantonese as an unofficial 100th,
    // but tiny/small/medium have no token for it, so it's left off this
    // shared list.)
    static let languages: [(String, String)] = [
        ("en", "English"),
        ("af", "Afrikaans"), ("sq", "Albanian"), ("am", "Amharic"), ("ar", "Arabic"),
        ("hy", "Armenian"), ("as", "Assamese"), ("az", "Azerbaijani"), ("ba", "Bashkir"),
        ("eu", "Basque"), ("be", "Belarusian"), ("bn", "Bengali"), ("bs", "Bosnian"),
        ("br", "Breton"), ("bg", "Bulgarian"), ("my", "Burmese"), ("ca", "Catalan"),
        ("zh", "Chinese"), ("hr", "Croatian"), ("cs", "Czech"), ("da", "Danish"),
        ("nl", "Dutch"), ("et", "Estonian"), ("fo", "Faroese"), ("fi", "Finnish"),
        ("fr", "French"), ("gl", "Galician"), ("ka", "Georgian"), ("de", "German"),
        ("el", "Greek"), ("gu", "Gujarati"), ("ht", "Haitian Creole"), ("ha", "Hausa"),
        ("haw", "Hawaiian"), ("he", "Hebrew"), ("hi", "Hindi"), ("hu", "Hungarian"),
        ("is", "Icelandic"), ("id", "Indonesian"), ("it", "Italian"), ("ja", "Japanese"),
        ("jw", "Javanese"), ("kn", "Kannada"), ("kk", "Kazakh"), ("km", "Khmer"),
        ("ko", "Korean"), ("lo", "Lao"), ("la", "Latin"), ("lv", "Latvian"),
        ("ln", "Lingala"), ("lt", "Lithuanian"), ("lb", "Luxembourgish"), ("mk", "Macedonian"),
        ("mg", "Malagasy"), ("ms", "Malay"), ("ml", "Malayalam"), ("mt", "Maltese"),
        ("mi", "Maori"), ("mr", "Marathi"), ("mn", "Mongolian"), ("ne", "Nepali"),
        ("no", "Norwegian"), ("nn", "Norwegian Nynorsk"), ("oc", "Occitan"), ("ps", "Pashto"),
        ("fa", "Persian"), ("pl", "Polish"), ("pt", "Portuguese"), ("pa", "Punjabi"),
        ("ro", "Romanian"), ("ru", "Russian"), ("sa", "Sanskrit"), ("sr", "Serbian"),
        ("sn", "Shona"), ("sd", "Sindhi"), ("si", "Sinhala"), ("sk", "Slovak"),
        ("sl", "Slovenian"), ("so", "Somali"), ("es", "Spanish"), ("su", "Sundanese"),
        ("sw", "Swahili"), ("sv", "Swedish"), ("tl", "Tagalog"), ("tg", "Tajik"),
        ("ta", "Tamil"), ("tt", "Tatar"), ("te", "Telugu"), ("th", "Thai"),
        ("bo", "Tibetan"), ("tr", "Turkish"), ("tk", "Turkmen"), ("uk", "Ukrainian"),
        ("ur", "Urdu"), ("uz", "Uzbek"), ("vi", "Vietnamese"), ("cy", "Welsh"),
        ("yi", "Yiddish"), ("yo", "Yoruba"),
    ]
    /// Cleanup providers offered when cleanup is on (excludes `.none`).
    static let cleanupProviders: [Backend] = [.anthropic, .openai, .groq, .openrouter, .ollama]

    private var settingsPane: some View {
        VStack(alignment: .leading, spacing: 16) {
            paneTitle("Settings")

            permissionsCard

            settingsCard("DICTATION") {
                settingsRow("Hotkey") {
                    Picker("", selection: hotkeyBinding) {
                        ForEach(Hotkey.allCases, id: \.self) { key in Text(key.displayName).tag(key) }
                    }
                    .labelsHidden().pickerStyle(.menu).frame(width: 190)
                }
                settingsRow("Max take length") {
                    Picker("", selection: bind(\.maxRecordingSeconds)) {
                        Text("1 minute").tag(60.0)
                        Text("2 minutes").tag(120.0)
                        Text("5 minutes").tag(300.0)
                        Text("10 minutes").tag(600.0)
                    }
                    .labelsHidden().pickerStyle(.menu).frame(width: 140)
                }
                settingsToggle("Sounds", isOn: bind(\.soundFeedback))
                settingsToggle("Paste automatically", isOn: bind(\.autoPaste))
                settingsToggle("Show words as you speak", isOn: bind(\.liveTranscript))
                settingsToggle("Start when you log in", isOn: launchAtLoginBinding)
                settingsToggle("Show in Dock", isOn: showInDockBinding)
            }

            settingsCard("TRANSCRIPTION — ON THIS MAC") {
                settingsRow("Whisper model") {
                    Picker("", selection: whisperModelBinding) {
                        ForEach(whisperModelOptions, id: \.0) { Text($0.1).tag($0.0) }
                    }
                    .labelsHidden().pickerStyle(.menu).frame(width: 210)
                }
                settingsRow("Language") {
                    Picker("", selection: bind(\.language)) {
                        ForEach(languageOptions, id: \.0) { Text($0.1).tag($0.0) }
                    }
                    .labelsHidden().pickerStyle(.menu).frame(width: 170)
                }
            }

            cleanupCard

            settingsCard("PRIVACY + UPDATES") {
                settingsRow("Your data") {
                    HStack(spacing: 14) {
                        Button("Reveal in Finder") { _ = NSWorkspace.shared.open(AppSupport.dir) }
                            .buttonStyle(.plain).foregroundStyle(DT.emberLight)
                        Button("Delete history…") { showDeleteHistory = true }
                            .buttonStyle(.plain).foregroundStyle(DT.destructive)
                    }
                    .font(.system(size: 12))
                }
                settingsToggle("Show what was typed in the HUD", isOn: bind(\.echoInsertedText))
                settingsToggle("Share anonymous usage & leaderboard rank", isOn: shareAnalyticsBinding)
                if controller.settings.shareAnalytics {
                    settingsRow("Leaderboard name") {
                        TextField("Display name", text: $leaderboardNameDraft)
                            .textFieldStyle(.roundedBorder)
                            .frame(width: 200)
                            .focused($leaderboardNameFocused)
                            .onSubmit { commitLeaderboardName() }
                            .onChange(of: leaderboardNameFocused) { wasFocused, isFocused in
                                if wasFocused && !isFocused { commitLeaderboardName() }
                            }
                    }
                    if let error = leaderboardNameValidationError ?? analyticsClient.syncError {
                        settingsRow("Leaderboard status") {
                            HStack(spacing: 10) {
                                Text(error).foregroundStyle(DT.destructive)
                                Button("Try again") { syncAndRefreshLeaderboard() }
                                    .buttonStyle(.plain).foregroundStyle(DT.emberLight)
                            }
                            .font(.system(size: 11))
                            .frame(maxWidth: 330, alignment: .trailing)
                        }
                    }
                    settingsRow("Delete my leaderboard data") {
                        Button("Delete…") {
                            Task {
                                await analyticsClient.deleteMyData(
                                    deviceId: analyticsIdentity.identity.deviceId,
                                    counters: usageCounters
                                )
                            }
                        }
                        .buttonStyle(.plain).font(.system(size: 12)).foregroundStyle(DT.destructive)
                    }
                }
                settingsToggle("Automatic updates", isOn: autoUpdateBinding)
                settingsRow("You're on v\(updater.appVersion)") {
                    HStack(spacing: 14) {
                        // Reaching the release notes shouldn't require running
                        // an update check first — on a current build Sparkle
                        // buries them behind the "You're up to date" alert.
                        // Anchored at the running version, so the page opens on
                        // "what am I actually on" rather than the newest entry.
                        Button("Version history") {
                            usageCounters.record(.versionHistoryOpened)
                            NSWorkspace.shared.open(ReleaseNotes.url(forVersion: updater.appVersion))
                        }
                        .buttonStyle(.plain).foregroundStyle(ink2)
                        Button("Check for updates now") {
                            usageCounters.record(.updateChecked)
                            updater.checkForUpdates()
                        }
                            .buttonStyle(.plain).foregroundStyle(DT.emberLight)
                            .disabled(!updater.canCheckForUpdates)
                    }
                    .font(.system(size: 12))
                }
            }
        }
        .frame(maxWidth: 620, alignment: .leading)
        .onAppear {
            reloadAPIKeyDraft()
            permissionWatch = Permission.watch { statuses in
                permissionStatus = statuses
                // A revoked permission is also why the key listener would be
                // down, so the moment the user grants it back, come back to
                // life rather than waiting for a relaunch.
                if !controller.isListening && !controller.isPaused {
                    _ = controller.startListening()
                }
            }
        }
        .onDisappear {
            permissionWatch?.cancel()
            permissionWatch = nil
        }
    }

    /// Permissions lived only behind the menu bar's "Setup & Permissions…"
    /// until 0.5.1; Settings is where people actually look when something
    /// stops working, so the three grants are visible here too.
    private var permissionsCard: some View {
        settingsCard("PERMISSIONS") {
            ForEach(Permission.allCases, id: \.self) { permission in
                settingsRow("\(permission.title) — \(permission.why)") {
                    switch permissionStatus[permission] ?? permission.status {
                    case .granted:
                        HStack(spacing: 6) {
                            Circle().fill(dark ? DT.moss : DT.mossLight).frame(width: 6, height: 6)
                            Text("Granted").foregroundStyle(ink2)
                        }
                        .font(.system(size: 12))
                    case .undetermined:
                        Button("Grant…") { permission.request() }
                            .buttonStyle(.plain).foregroundStyle(DT.emberLight)
                            .font(.system(size: 12))
                    case .denied:
                        Button("Open System Settings") { NSWorkspace.shared.open(permission.settingsURL) }
                            .buttonStyle(.plain).foregroundStyle(DT.emberLight)
                            .font(.system(size: 12))
                    }
                }
            }
        }
    }

    // MARK: AI cleanup card (toggle → provider → key → optional model)

    @ViewBuilder private var cleanupCard: some View {
        settingsCard("AI CLEANUP") {
            settingsToggle("Clean up my dictation", isOn: cleanupEnabledBinding)
            if controller.settings.backend != .none {
                settingsRow("Provider") {
                    Picker("", selection: backendBinding) {
                        ForEach(Self.cleanupProviders, id: \.self) { Text(providerLabel($0)).tag($0) }
                    }
                    .labelsHidden().pickerStyle(.menu).frame(width: 200)
                }
                if controller.settings.backend.needsAPIKey {
                    settingsRow("API key") {
                        SecureField("Paste your key", text: $apiKeyDraft)
                            .textFieldStyle(.roundedBorder)
                            .frame(width: 230)
                            .onChange(of: apiKeyDraft) { _, new in
                                Keychain.setKey(new, for: controller.settings.backend)
                            }
                    }
                    settingsRow("Model (optional)") {
                        TextField(
                            CleanupFactory.defaultModel(for: controller.settings.backend),
                            text: bind(\.cleanupModelOverride)
                        )
                        .textFieldStyle(.roundedBorder)
                        .frame(width: 230)
                    }
                } else if controller.settings.backend == .ollama {
                    settingsRow("Endpoint") {
                        Text("localhost:11434 · fully local").foregroundStyle(ink2)
                    }
                }
            } else {
                settingsRow("Off. Raw transcript, nothing leaves this Mac.") { EmptyView() }
            }
        }
    }

    private func providerLabel(_ b: Backend) -> String {
        switch b {
        case .anthropic: return "Anthropic (Claude)"
        case .openai: return "OpenAI"
        case .groq: return "Groq"
        case .openrouter: return "OpenRouter"
        case .ollama: return "Ollama (on-device)"
        case .none: return "Off"
        }
    }

    // Always include the current value so the Picker selection is never orphaned.
    private var whisperModelOptions: [(String, String)] {
        var opts = Self.whisperModels
        let current = controller.settings.whisperModel
        if !opts.contains(where: { $0.0 == current }) { opts.insert((current, current), at: 0) }
        return opts
    }
    private var languageOptions: [(String, String)] {
        var opts = Self.languages
        let current = controller.settings.language
        if !opts.contains(where: { $0.0 == current }) { opts.insert((current, current), at: 0) }
        return opts
    }

    private func reloadAPIKeyDraft() {
        apiKeyDraft = Keychain.key(for: controller.settings.backend) ?? ""
    }

    // MARK: bindings

    /// Generic setting binding that persists on write.
    private func bind<V>(_ keyPath: WritableKeyPath<Settings, V>) -> Binding<V> {
        Binding(
            get: { controller.settings[keyPath: keyPath] },
            set: { controller.settings[keyPath: keyPath] = $0; controller.settings.save() }
        )
    }

    /// Hotkey needs the tap restarted, so it goes through the controller.
    private var hotkeyBinding: Binding<Hotkey> {
        Binding(get: { controller.settings.hotkey }, set: { controller.updateHotkey($0) })
    }

    /// Dock visibility applies immediately by flipping the activation policy —
    /// persisting alone would leave the Dock unchanged until the next launch.
    private var showInDockBinding: Binding<Bool> {
        Binding(
            get: { controller.settings.showInDock },
            set: { show in
                controller.settings.showInDock = show
                controller.settings.save()
                NSApp.setActivationPolicy(show ? .regular : .accessory)
                if show { NSApp.activate(ignoringOtherApps: true) }
            }
        )
    }

    /// Applies immediately via SMAppService, not just at next launch — a
    /// toggle that does nothing until a relaunch reads as broken.
    private var launchAtLoginBinding: Binding<Bool> {
        Binding(
            get: { controller.settings.launchAtLogin },
            set: { enabled in
                controller.settings.launchAtLogin = enabled
                controller.settings.save()
                LoginItem.apply(enabled)
            }
        )
    }

    /// Whisper model swaps the live transcriber, so it goes through the controller
    /// (a plain `bind` would only persist the value, not reload the model).
    private var whisperModelBinding: Binding<String> {
        Binding(get: { controller.settings.whisperModel }, set: { controller.updateModel($0) })
    }

    /// Cleanup on/off: off ⇒ `.none` (local raw), on ⇒ Anthropic by default.
    private var cleanupEnabledBinding: Binding<Bool> {
        Binding(
            get: { controller.settings.backend != .none },
            set: { on in
                controller.settings.backend = on ? .anthropic : .none
                usageCounters.record(.cleanupBackendChanged)
                controller.settings.save()
                reloadAPIKeyDraft()
            }
        )
    }

    private var backendBinding: Binding<Backend> {
        Binding(
            get: { controller.settings.backend },
            set: { b in
                controller.settings.backend = b
                usageCounters.record(.cleanupBackendChanged)
                controller.settings.save()
                reloadAPIKeyDraft()
            }
        )
    }

    /// Turning sharing on sends the first sync immediately rather than
    /// waiting for the next dictation, so the leaderboard has something to
    /// show right away.
    private var shareAnalyticsBinding: Binding<Bool> {
        Binding(
            get: { controller.settings.shareAnalytics },
            set: { on in
                controller.settings.shareAnalytics = on
                controller.settings.save()
                if on { analyticsClient.syncIfDue(controller: controller, force: true) }
            }
        )
    }

    private func refreshLeaderboard() async {
        isRefreshingLeaderboard = true
        defer { isRefreshingLeaderboard = false }
        _ = await analyticsClient.syncNow(controller: controller)
        await analyticsClient.fetchLeaderboard(deviceId: analyticsIdentity.identity.deviceId)
    }

    private func commitLeaderboardName() {
        guard let normalized = LeaderboardDisplayName.normalize(leaderboardNameDraft) else {
            leaderboardNameValidationError = "Enter a nickname to join the leaderboard."
            return
        }
        leaderboardNameValidationError = nil
        leaderboardNameDraft = normalized

        let changed = normalized != analyticsIdentity.identity.displayName
        guard changed || analyticsClient.syncError != nil else { return }
        if changed { usageCounters.record(.leaderboardNameChanged) }
        analyticsIdentity.identity.displayName = normalized
        syncAndRefreshLeaderboard()
    }

    private func syncAndRefreshLeaderboard() {
        Task {
            if await analyticsClient.syncNow(controller: controller) {
                await analyticsClient.fetchLeaderboard(deviceId: analyticsIdentity.identity.deviceId)
            }
        }
    }

    private var autoUpdateBinding: Binding<Bool> {
        Binding(
            get: { controller.settings.automaticUpdates },
            set: {
                controller.settings.automaticUpdates = $0
                controller.settings.save()
                UpdaterController.shared.setAutomaticChecks($0)
            }
        )
    }

    private func settingsCard(_ header: String, @ViewBuilder rows: () -> some View) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            Text(header)
                .font(.system(size: 11, weight: .bold)).kerning(0.5).foregroundStyle(ink2)
                .padding(.horizontal, 16).padding(.vertical, 10)
            Divider().overlay(hair)
            rows()
        }
        .background(RoundedRectangle(cornerRadius: 12).fill(card))
        .overlay(RoundedRectangle(cornerRadius: 12).strokeBorder(hair))
    }

    private func settingsRow(_ label: String, @ViewBuilder trailing: () -> some View) -> some View {
        HStack {
            Text(label).font(.system(size: 13)).foregroundStyle(ink)
            Spacer()
            trailing().font(.system(size: 13))
        }
        .padding(.horizontal, 16).padding(.vertical, 11)
    }

    private func settingsToggle(_ label: String, isOn: Binding<Bool>) -> some View {
        HStack {
            Text(label).font(.system(size: 13)).foregroundStyle(ink)
            Spacer()
            Toggle("", isOn: isOn).toggleStyle(.switch).tint(DT.moss).labelsHidden()
        }
        .padding(.horizontal, 16).padding(.vertical, 8)
    }

    // MARK: shared empty state (dashed border, waveform, CTA)

    private func emptyPanel(title: String, body bodyText: String, button: String?,
                             action: (() -> Void)? = nil) -> some View {
        VStack(spacing: 12) {
            EmptyWave()
                .frame(width: 220, height: 34)
            Text(title).font(.system(size: 14, weight: .semibold)).foregroundStyle(ink)
            Text(bodyText)
                .font(.system(size: 12.5)).foregroundStyle(ink2)
                .multilineTextAlignment(.center)
                .frame(maxWidth: 320)
            if let button {
                Button(button) { action?() }
                    .buttonStyle(.plain)
                    .font(.system(size: 12.5, weight: .semibold))
                    .foregroundStyle(.white)
                    .padding(.horizontal, 16).padding(.vertical, 8)
                    .background(RoundedRectangle(cornerRadius: 8).fill(DT.emberLight))
            }
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 56).padding(.horizontal, 20)
        .overlay(
            RoundedRectangle(cornerRadius: 14)
                .strokeBorder(hair, style: StrokeStyle(lineWidth: 1, dash: [4, 4]))
        )
    }
}

/// The animated brand ring — r = 0.34·size, 0.62 rad gap, ±10% five-lobe
/// wobble drifting at 0.7 rad/s (design phases 03/05/06).
struct RingGlyph: View {
    var size: CGFloat
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        Group {
            if reduceMotion {
                ringCanvas(t: 0)
            } else {
                TimelineView(.animation) { context in
                    ringCanvas(t: context.date.timeIntervalSinceReferenceDate)
                }
            }
        }
        .frame(width: size, height: size)
    }

    private func ringCanvas(t: Double) -> some View {
        Canvas { ctx, canvasSize in
            let w = canvasSize.width, h = canvasSize.height
            let cx = w / 2, cy = h / 2
            let R = min(w, h) * 0.34, gap = 0.62, off = -1.0
            var path = Path()
            var a = off + gap / 2
            var first = true
            while a <= off + 2 * .pi - gap / 2 {
                let r = R * (1 + 0.10 * sin(a * 5 - t * 0.7))
                let p = CGPoint(x: cx + cos(a) * r, y: cy + sin(a) * r)
                if first { path.move(to: p); first = false } else { path.addLine(to: p) }
                a += 0.045
            }
            ctx.stroke(path, with: .color(DT.emberWave),
                       style: StrokeStyle(lineWidth: 2, lineCap: .round))
        }
    }
}

/// Empty-state waveform: y = mid + sin(0.045x − 1.7t)·1.3·win(u).
private struct EmptyWave: View {
    @Environment(\.colorScheme) private var scheme
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        Group {
            if reduceMotion {
                waveCanvas(t: 0)
            } else {
                TimelineView(.animation) { context in
                    waveCanvas(t: context.date.timeIntervalSinceReferenceDate)
                }
            }
        }
    }

    private func waveCanvas(t: Double) -> some View {
        Canvas { ctx, size in
            let w = size.width, mid = size.height / 2
            var path = Path()
            var x: Double = 0
            var first = true
            while x <= w {
                let y = mid + sin(0.045 * x - 1.7 * t) * 1.3 * Voiceline.window(x / w) * 8
                if first { path.move(to: CGPoint(x: x, y: y)); first = false }
                else { path.addLine(to: CGPoint(x: x, y: y)) }
                x += 2
            }
            let color = scheme == .dark ? DT.dimWaveDark : DT.dimWaveLight
            ctx.stroke(path, with: .color(color), style: StrokeStyle(lineWidth: 2, lineCap: .round))
        }
    }
}

/// The part of the leaderboard that stays anonymous.
///
/// Each row is three redaction bars — no rank, no name, no total — under a
/// highlight that sweeps across them, staggered so the tail cascades rather
/// than pulsing in unison. The bars deliberately do not resolve into content:
/// a skeleton promises data that is coming, and this one is withholding it.
///
/// Rows also dim as they descend, so the board dissolves at the bottom instead
/// of stopping on a countable last row. That fade is the whole point — the
/// tail says "this continues", not "there are exactly this many more".
///
/// One timeline drives every bar. Seven rows of three independently animating
/// `Canvas` views is a lot of redraw for a pane that is otherwise static text.
private struct MaskedBoardTail: View {
    var count: Int
    /// A revealed row sits above us, so the first masked row needs a rule.
    var leadingDivider: Bool
    var hair: Color
    var tint: Color
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    /// Uneven, and prime-ish against `count`, so the column reads as hidden
    /// names of different lengths instead of a repeating pattern.
    private static let nameWidths: [CGFloat] = [104, 78, 122, 88, 68, 112, 94]

    private static let barHeight: CGFloat = 9
    /// Matches the rank column in `leaderboardRow`.
    private static let rankColumn: CGFloat = 34

    @ViewBuilder var body: some View {
        if count > 0 {
            if reduceMotion {
                rows(t: 0)
            } else {
                // 30 fps, not `.animation`: the sweep is slow and the tail is
                // twenty-odd canvases, so display-rate redraw buys nothing.
                TimelineView(.periodic(from: .now, by: 1.0 / 30)) { context in
                    rows(t: context.date.timeIntervalSinceReferenceDate)
                }
            }
        }
    }

    private func rows(t: Double) -> some View {
        VStack(spacing: 0) {
            ForEach(Array(0..<count), id: \.self) { i in
                if i > 0 || leadingDivider {
                    Rectangle().fill(hair).frame(height: 1).opacity(fade(i))
                }
                row(index: i, t: t)
            }
        }
        // One announcement for the whole tail. Seven identical "anonymous
        // entry" rows would be noise, and the count is not the point.
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Anonymous entries. Names below the top are hidden.")
    }

    /// Scaled to `count` so the ramp lands in the same place whether two rows
    /// are masked or seven. It stops short of zero on purpose: a row that
    /// vanished outright would put a hard edge back at a countable position.
    private func fade(_ index: Int) -> Double {
        1 - 0.74 * (Double(index) / Double(max(1, count - 1)))
    }

    private func row(index: Int, t: Double) -> some View {
        let stagger = Double(index) * 0.42
        return HStack(spacing: 12) {
            bar(width: 18, t: t - stagger)
                .frame(width: Self.rankColumn, alignment: .leading)
            bar(width: Self.nameWidths[index % Self.nameWidths.count], t: t - stagger - 0.18)
            Spacer(minLength: 12)
            bar(width: 52, t: t - stagger - 0.34)
        }
        .padding(.vertical, 11)
        .opacity(fade(index))
    }

    /// A redaction bar lit by a highlight travelling left→right at 90 pt/s.
    private func bar(width: CGFloat, t: Double) -> some View {
        Canvas { ctx, size in
            let shape = Path(roundedRect: CGRect(origin: .zero, size: size),
                             cornerRadius: size.height / 2)
            ctx.fill(shape, with: .color(tint))
            let span = size.width + 150
            let head = (t * 90).truncatingRemainder(dividingBy: span) - 75
            let gradient = Gradient(stops: [
                .init(color: tint.opacity(0), location: 0),
                .init(color: tint.opacity(0.85), location: 0.5),
                .init(color: tint.opacity(0), location: 1),
            ])
            ctx.fill(shape, with: .linearGradient(gradient,
                                                  startPoint: CGPoint(x: head - 38, y: 0),
                                                  endPoint: CGPoint(x: head + 38, y: 0)))
        }
        .frame(width: width, height: Self.barHeight)
    }
}

/// A single-field "type + Enter (or Add)" row used by the Dictionary pane.
private struct InlineAddField: View {
    let placeholder: String
    let fill: Color
    let ink: Color
    let accent: Color
    let onAdd: (String) -> Void
    @State private var text = ""

    var body: some View {
        HStack(spacing: 8) {
            TextField(placeholder, text: $text)
                .textFieldStyle(.plain)
                .font(.system(size: 13))
                .padding(9)
                .background(RoundedRectangle(cornerRadius: 8).fill(fill))
                .onSubmit(commit)
            Button("Add") { commit() }
                .buttonStyle(.plain)
                .font(.system(size: 12, weight: .semibold))
                .foregroundStyle(.white)
                .padding(.horizontal, 14).padding(.vertical, 8)
                .background(RoundedRectangle(cornerRadius: 8).fill(accent))
        }
    }

    private func commit() {
        let value = text.trimmingCharacters(in: .whitespaces)
        guard !value.isEmpty else { return }
        onAdd(value)
        text = ""
    }
}

/// A trigger + expansion add row used by the Snippets pane.
private struct SnippetAddRow: View {
    let fill: Color
    let ink: Color
    let ink2: Color
    let accent: Color
    let onAdd: (String, String) -> Void
    @State private var trigger = ""
    @State private var expansion = ""

    var body: some View {
        HStack(spacing: 8) {
            TextField("trigger", text: $trigger)
                .textFieldStyle(.plain).font(.system(size: 13)).frame(width: 140)
                .padding(9).background(RoundedRectangle(cornerRadius: 8).fill(fill))
            TextField("expands to…", text: $expansion)
                .textFieldStyle(.plain).font(.system(size: 13))
                .padding(9).background(RoundedRectangle(cornerRadius: 8).fill(fill))
                .onSubmit(commit)
            Button("Add") { commit() }
                .buttonStyle(.plain)
                .font(.system(size: 12, weight: .semibold)).foregroundStyle(.white)
                .padding(.horizontal, 14).padding(.vertical, 8)
                .background(RoundedRectangle(cornerRadius: 8).fill(accent))
        }
    }

    private func commit() {
        let t = trigger.trimmingCharacters(in: .whitespaces)
        let e = expansion.trimmingCharacters(in: .whitespaces)
        guard !t.isEmpty, !e.isEmpty else { return }
        onAdd(t, e)
        trigger = ""; expansion = ""
    }
}
