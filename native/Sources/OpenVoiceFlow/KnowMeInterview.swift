import SwiftUI

/// The Know-Me interview — a short, friendly Q&A that builds the local profile
/// (ported from interview.py, kept deliberately light per the "less texty"
/// direction). One question per screen; answers write straight into the
/// ProfileStore and seed the dictionary. Everything stays on this Mac.
struct KnowMeInterview: View {
    @ObservedObject var controller: AppController
    @Environment(\.dismiss) private var dismiss
    @Environment(\.colorScheme) private var scheme

    @State private var step = 0
    @State private var draft = Profile()
    @State private var textField = ""

    private var dark: Bool { scheme == .dark }
    private var ink: Color { dark ? DT.inkDark : DT.inkLight }
    private var ink2: Color { dark ? DT.ink2Dark : DT.ink2Light }

    private struct Question {
        let eyebrow: String
        let prompt: String
        let placeholder: String
        let hint: String
        let multi: Bool           // comma-separated list vs single line
        let apply: (inout Profile, String) -> Void
    }

    private let questions: [Question] = [
        .init(eyebrow: "ABOUT YOU", prompt: "What should we call you?",
              placeholder: "Alex Chen", hint: "So cleanup signs off the way you do.",
              multi: false) { $0.name = $1 },
        .init(eyebrow: "WORK", prompt: "What do you do?",
              placeholder: "iOS engineer at a small startup", hint: "Sets the tone and vocabulary.",
              multi: false) { $0.occupation = $1 },
        .init(eyebrow: "PEOPLE", prompt: "Who do you mention most?",
              placeholder: "Priya, Sam, Dr. Okafor", hint: "Names Whisper should never misspell.",
              multi: true) { $0.workNames = splitList($1) },
        .init(eyebrow: "JARGON", prompt: "Any words it keeps getting wrong?",
              placeholder: "WhisperKit, TestFlight, Kubernetes", hint: "Your terms, spelled your way.",
              multi: true) { $0.technicalTerms = splitList($1) },
        .init(eyebrow: "TONE", prompt: "How do you like to sound?",
              placeholder: "concise, no exclamation marks, Oxford comma", hint: "Optional — leave blank to skip.",
              multi: false) { $0.communicationStyle = $1 },
    ]

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            // progress dots
            HStack(spacing: 5) {
                ForEach(0..<questions.count, id: \.self) { i in
                    Circle().fill(i <= step ? DT.emberWave : ink2.opacity(0.3)).frame(width: 6, height: 6)
                }
                Spacer()
                Button("Skip") { finish() }.buttonStyle(.plain).font(.system(size: 12)).foregroundStyle(ink2)
            }

            let q = questions[step]
            Text(q.eyebrow).font(.system(size: 11, weight: .bold, design: .monospaced)).kerning(0.8).foregroundStyle(DT.emberWave)
            Text(q.prompt).font(.system(size: 22, weight: .bold)).kerning(-0.3).foregroundStyle(ink)
            Text(q.hint).font(.system(size: 12.5)).foregroundStyle(ink2)

            TextField(q.placeholder, text: $textField)
                .textFieldStyle(.plain)
                .font(.system(size: 15))
                .padding(12)
                .background(RoundedRectangle(cornerRadius: 8).fill(dark ? .white.opacity(0.06) : .black.opacity(0.04)))
                .onSubmit(next)

            Spacer()

            HStack {
                if step > 0 {
                    Button("‹ Back") { back() }.buttonStyle(.plain).foregroundStyle(ink2)
                }
                Spacer()
                Button(step == questions.count - 1 ? "Finish" : "Next") { next() }
                    .buttonStyle(.borderedProminent)
                    .tint(DT.emberWave)
            }
        }
        .padding(28)
        .frame(width: 460, height: 380)
        .onAppear { textField = value(for: step) }
    }

    private func value(for step: Int) -> String {
        switch step {
        case 0: return draft.name
        case 1: return draft.occupation
        case 2: return draft.workNames.joined(separator: ", ")
        case 3: return draft.technicalTerms.joined(separator: ", ")
        default: return draft.communicationStyle
        }
    }

    private func commit() { questions[step].apply(&draft, textField.trimmingCharacters(in: .whitespaces)) }

    private func next() {
        commit()
        if step < questions.count - 1 {
            step += 1
            textField = value(for: step)
        } else {
            finish()
        }
    }

    private func back() {
        commit()
        step -= 1
        textField = value(for: step)
    }

    private func finish() {
        commit()
        controller.profileStore.profile = draft
        controller.usageCounters.record(.knowMeInterviewFinished)
        // Double coverage: names + terms also seed the dictionary.
        controller.dictionaryStore.seed(with: controller.profileStore.dictionaryWords)
        dismiss()
    }
}

private func splitList(_ s: String) -> [String] {
    s.split(separator: ",").map { $0.trimmingCharacters(in: .whitespaces) }.filter { !$0.isEmpty }
}

// MARK: - Shared question chrome
//
// Extracted so the two-question inline form in onboarding and the five-question
// sheet in the dashboard render identical controls. The sheet keeps its own
// step machine; only the field chrome and the commit path are shared.

/// The interview's text field: 36 pt tall, radius 8, accent focus ring.
struct KnowMeTextField: View {
    let label: String
    let placeholder: String
    @Binding var text: String
    let ink: Color
    let ink2: Color
    let fill: Color
    let accent: Color
    var onCommit: () -> Void = {}

    @FocusState private var focused: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(label).font(.system(size: 12.5)).foregroundStyle(ink2)
            TextField(placeholder, text: $text)
                .textFieldStyle(.plain)
                .font(.system(size: 14))
                .foregroundStyle(ink)
                .padding(.horizontal, 12)
                .frame(height: 36)
                .background(RoundedRectangle(cornerRadius: 8).fill(fill))
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .strokeBorder(focused ? accent.opacity(0.45) : .clear)
                )
                .focused($focused)
                .onSubmit(onCommit)
        }
    }
}

/// A wrapping row of word chips with a trailing "+ add" affordance.
struct KnowMeTokenRow: View {
    let label: String
    @Binding var tokens: [String]
    let ink2: Color
    let ink3: Color
    let chipInk: Color
    let chipFill: Color

    @State private var adding = false
    @State private var draft = ""

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(label).font(.system(size: 12.5)).foregroundStyle(ink2)
            // A plain wrapping HStack would clip; a LazyVGrid with adaptive
            // columns wraps at the card's width without measuring text.
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 64), spacing: 7)],
                      alignment: .leading, spacing: 7) {
                ForEach(tokens, id: \.self) { token in
                    HStack(spacing: 5) {
                        Text(token).font(.system(size: 12)).foregroundStyle(chipInk)
                        Button {
                            tokens.removeAll { $0 == token }
                        } label: {
                            Image(systemName: "xmark").font(.system(size: 7, weight: .bold))
                        }
                        .buttonStyle(.plain).foregroundStyle(ink3)
                        .accessibilityLabel("Remove \(token)")
                    }
                    .padding(.horizontal, 10).padding(.vertical, 5)
                    .background(RoundedRectangle(cornerRadius: DT.rControl).fill(chipFill))
                }
                if adding {
                    TextField("Name or word", text: $draft)
                        .textFieldStyle(.plain)
                        .font(.system(size: 12))
                        .frame(minWidth: 90)
                        .padding(.horizontal, 10).padding(.vertical, 5)
                        .background(RoundedRectangle(cornerRadius: DT.rControl).fill(chipFill))
                        .onSubmit(commit)
                } else {
                    Button("+ add") { adding = true }
                        .buttonStyle(.plain)
                        .font(.system(size: 12)).foregroundStyle(ink3)
                }
            }
        }
    }

    private func commit() {
        let value = draft.trimmingCharacters(in: .whitespaces)
        if !value.isEmpty, !tokens.contains(value) { tokens.append(value) }
        draft = ""
        adding = false
    }
}
