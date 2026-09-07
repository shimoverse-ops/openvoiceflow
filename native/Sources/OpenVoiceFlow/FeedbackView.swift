import AppKit
import SwiftUI

/// "Send Feedback" — a short form presented from the sidebar, below Settings.
///
/// OpenVoiceFlow ships no telemetry and no backend (see privacy-architecture
/// docs), so there is nowhere to POST a submission to. Feedback goes out the
/// same door the docs already point people to — a `mailto:` to
/// contact@openvoiceflow.com — opened only when the user taps Send. Nothing is
/// gathered passively or on a timer.
///
/// What rides along is a small, aggregate usage snapshot (word/time totals,
/// streak, first-use date, last 7 days) so a report arrives with context.
/// It never includes dictation text, snippets, dictionary entries, or the
/// Know-Me profile — only counters already shown on the dashboard.
struct FeedbackView: View {
    @ObservedObject var controller: AppController
    let onDismiss: () -> Void
    @Environment(\.colorScheme) private var scheme

    enum Category: String, CaseIterable, Identifiable {
        case bug = "Something's broken"
        case idea = "Feature idea"
        case praise = "Just saying thanks"
        case other = "Something else"
        var id: String { rawValue }

        /// Short enough that all four segments fit a 480pt-wide sheet without
        /// truncating — the full rawValue is still what goes in the email
        /// subject/body, this is only what the segmented control displays.
        var shortLabel: String {
            switch self {
            case .bug: return "Bug"
            case .idea: return "Idea"
            case .praise: return "Thanks"
            case .other: return "Other"
            }
        }
    }

    @State private var category: Category = .idea
    @State private var message = ""
    @State private var contact = ""

    private var dark: Bool { scheme == .dark }
    private var ink: Color { dark ? DT.inkDark : DT.inkLight }
    private var ink2: Color { dark ? DT.ink2Dark : DT.ink2Light }
    private var fill: Color { dark ? .white.opacity(0.06) : .black.opacity(0.05) }

    private var canSend: Bool { !message.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("Send feedback").font(.system(size: 20, weight: .bold)).foregroundStyle(ink)
                Spacer()
                Button("Cancel") { onDismiss() }.buttonStyle(.plain).foregroundStyle(ink2)
            }

            Picker("", selection: $category) {
                ForEach(Category.allCases) { Text($0.shortLabel).tag($0) }
            }
            .labelsHidden().pickerStyle(.segmented)

            TextEditor(text: $message)
                .font(.system(size: 13))
                .scrollContentBackground(.hidden)
                .padding(8)
                .frame(height: 130)
                .background(RoundedRectangle(cornerRadius: 8).fill(fill))
                .overlay(alignment: .topLeading) {
                    if message.isEmpty {
                        Text("What happened, or what would help?")
                            .font(.system(size: 13)).foregroundStyle(ink2)
                            .padding(.horizontal, 12).padding(.vertical, 14)
                            .allowsHitTesting(false)
                    }
                }

            TextField("Email (optional)", text: $contact)
                .textFieldStyle(.roundedBorder)
                .font(.system(size: 13))

            Spacer(minLength: 0)

            HStack {
                Spacer()
                Button("Send") { send() }
                    .buttonStyle(.borderedProminent).tint(DT.emberWave)
                    .disabled(!canSend)
            }
        }
        .padding(24)
        .frame(width: 480, height: 380)
        .background(SheetOutsideClickDismissal(onOutsideClick: onDismiss))
    }

    private func send() {
        let body = Self.emailBody(
            category: category.rawValue,
            message: message.trimmingCharacters(in: .whitespacesAndNewlines),
            contact: contact.trimmingCharacters(in: .whitespacesAndNewlines),
            snapshot: UsageSnapshot(controller: controller)
        )
        var components = URLComponents()
        components.scheme = "mailto"
        components.path = "contact@openvoiceflow.com"
        components.queryItems = [
            URLQueryItem(name: "subject", value: "OpenVoiceFlow feedback: \(category.rawValue)"),
            URLQueryItem(name: "body", value: body),
        ]
        if let url = components.url {
            NSWorkspace.shared.open(url)
        }
        controller.usageCounters.record(.feedbackSent)
        onDismiss()
    }

    static func emailBody(category: String, message: String, contact: String?, snapshot: UsageSnapshot) -> String {
        var lines = [message, "", "—"]
        if let contact, !contact.isEmpty {
            lines.append("Reply to: \(contact)")
        }
        lines.append(contentsOf: [
            "",
            "Usage snapshot (aggregate counts only — no dictated text):",
            "  App version: \(snapshot.appVersion)",
            "  Using since: \(snapshot.usingSince)",
            "  Total words dictated: \(snapshot.totalWords)",
            "  Total time back: \(snapshot.timeBack)",
            "  Current streak: \(snapshot.streakDays) day(s)",
            "  Last 7 days (minutes returned): \(snapshot.lastWeekMinutes.map(String.init).joined(separator: ", "))",
            "  Total takes recorded: \(snapshot.totalTakes)",
        ])
        return lines.joined(separator: "\n")
    }
}

/// A small, aggregate slice of on-device usage stats — the same figures
/// already shown on the Home pane — bundled into a feedback submission.
/// No dictation text, snippets, dictionary, or profile data.
struct UsageSnapshot {
    let appVersion: String
    let usingSince: String
    let totalWords: Int
    let timeBack: String
    let streakDays: Int
    let lastWeekMinutes: [Int]
    let totalTakes: Int

    @MainActor
    init(controller: AppController) {
        let history = controller.historyStore
        appVersion = "v\(UpdaterController.shared.appVersion)"
        if let since = controller.settings.firstUseDate {
            let f = DateFormatter()
            f.dateFormat = "MMMM yyyy"
            usingSince = f.string(from: since)
        } else {
            usingSince = "unknown"
        }
        totalWords = history.totalWords
        let minutes = history.totalMinutes
        timeBack = minutes >= 60 ? "\(minutes / 60)h \(minutes % 60)m" : "\(minutes)m"
        streakDays = history.streak
        lastWeekMinutes = history.minutesLastWeek
        totalTakes = history.entries.count
    }
}
