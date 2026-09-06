import AppKit
import Combine
import Foundation
import os

/// Orchestrates the dictation loop and owns app state. The single source of
/// truth wired into the menu bar, HUD, and dashboard.
///
///   idle → (hotkey down) recording → (hotkey up) transcribing → cleaning
///        → pasting → idle
@MainActor
final class AppController: ObservableObject {
    @Published private(set) var isListening = false
    @Published private(set) var isRecording = false
    @Published private(set) var isWorking = false
    @Published private(set) var pausedUntil: Date?
    @Published private(set) var lastError: String?
    /// The most recent delivered text. Lets the UI show what was actually heard
    /// (onboarding's "say hello" confirms the loop works even when the paste
    /// lands in another app).
    @Published private(set) var lastTranscript: String?
    /// Live partial transcript, published only while `streamPartials` is on.
    /// Onboarding's ink fill is the sole consumer — see `streamPartials`.
    @Published private(set) var partialTranscript: String?
    /// How long the last take was held, for onboarding's spoken-vs-typed line.
    @Published private(set) var lastSpeechSeconds: Double = 0

    /// Opt-in live partials. Off everywhere except the onboarding try-it step:
    /// re-transcribing a growing buffer every 300 ms costs real CPU, and the
    /// normal dictation path has no use for it (the HUD shows a coil, not text).
    var streamPartials = false
    @Published var settings: Settings

    // Ported feature stores (dictionary, snippets, styles, profile, history).
    let profileStore = ProfileStore()
    let dictionaryStore = DictionaryStore()
    let snippetStore = SnippetStore()
    let styleStore = StyleStore()
    let historyStore = HistoryStore()
    let analyticsIdentity = AnalyticsIdentityStore()
    /// Which panes and features get used. Local counters; shared only under
    /// the same opt-out switch as the rest of the analytics payload.
    let usageCounters = UsageCounters()
    let analyticsClient = AnalyticsClient()

    /// Today's dictated words — read straight from the persisted stats.
    var wordsToday: Int { historyStore.wordsToday }

    private let log = Logger(subsystem: "app.openvoiceflow", category: "controller")
    private let hotkey: HotkeyEngine
    private let audio = AudioCapture()
    private let transcriber: Transcriber
    private let hud = HUDController()

    /// Hard ceiling so a missed hotkey-up can't record forever (Python H2).
    private var maxRecordingSeconds: Double { settings.maxRecordingSeconds }
    /// Below this a take is too brief to transcribe reliably — nudge, don't error.
    private let minSpeakSeconds: Double = 0.5
    private var maxRecordTask: Task<Void, Never>?
    private var partialTask: Task<Void, Never>?
    private var resumeTask: Task<Void, Never>?
    private var pressTime = Date.distantPast
    private var lastSamples: [Float] = []

    /// Menu-bar icon state derived from the controller state (design 02).
    var iconState: StatusIconState {
        if lastError != nil { return .error }
        if pausedUntil != nil { return .paused }
        if isRecording { return .listening }
        if isWorking { return .working }
        return .idle
    }

    var isPaused: Bool { pausedUntil != nil }

    init(settings: Settings = .load()) {
        self.settings = settings
        self.hotkey = HotkeyEngine(hotkey: settings.hotkey)
        self.transcriber = Transcriber(model: settings.whisperModel)
        hotkey.onPress = { [weak self] in self?.startRecording() }
        hotkey.onRelease = { [weak self] in self?.stopAndProcess() }
        audio.onLevel = { [weak self] level in
            Task { @MainActor [weak self] in self?.hud.updateLevel(level) }
        }
        NotificationCenter.default.addObserver(
            forName: .ovfRetryTranscription, object: nil, queue: .main
        ) { [weak self] _ in
            Task { @MainActor [weak self] in self?.retryLastTranscription() }
        }
    }

    // MARK: listening lifecycle

    /// Prepares the local speech engine for onboarding, forwarding WhisperKit's
    /// real byte counts so the view can show size, rate and ETA.
    func prepareModelForOnboarding(
        progress: @escaping Transcriber.DownloadProgressObserver
    ) async throws {
        try await transcriber.warmUp(progress: progress)
    }

    /// Onboarding's engine choice. Unlike `updateModel` this awaits the swap,
    /// so the download the caller starts next fetches the chosen model instead
    /// of racing the transcriber's async set.
    func selectModel(_ name: String) async {
        guard name != settings.whisperModel else { return }
        settings.whisperModel = name
        settings.save()
        await transcriber.setModel(name)
    }

    /// Whether the speech model is already resident — lets onboarding skip the
    /// download card on a reinstall.
    func isModelReady() async -> Bool { await transcriber.isReady }

    /// Begin listening for the hotkey. Returns false if the tap couldn't start
    /// (missing Accessibility/Input Monitoring) so the UI can surface it.
    @discardableResult
    func startListening() -> Bool {
        hotkey.hotkey = settings.hotkey
        guard hotkey.start() else {
            isListening = false
            return false
        }
        isListening = true
        lastError = nil
        Task { try? await transcriber.warmUp() }  // preload model off the hot path
        return true
    }

    func stopListening() {
        hotkey.stop()
        isListening = false
        if isRecording { _ = audio.stop(); isRecording = false }
    }

    /// "Pause for 1 hour" (design 02, item 4). Hotkey is ignored while paused.
    func pause(for interval: TimeInterval = 3600) {
        stopListening()
        pausedUntil = Date().addingTimeInterval(interval)
        resumeTask?.cancel()
        resumeTask = Task { [weak self] in
            try? await Task.sleep(for: .seconds(interval))
            if !Task.isCancelled { self?.resume() }
        }
    }

    func resume() {
        resumeTask?.cancel()
        pausedUntil = nil
        _ = startListening()
    }

    func updateHotkey(_ newHotkey: Hotkey) {
        guard newHotkey != settings.hotkey else { return }
        settings.hotkey = newHotkey
        // A new key has to be learned from scratch, so the chip comes back for
        // another 7 days rather than staying gone.
        settings.hotkeyLearnedAt = nil
        settings.save()
        if isListening { stopListening(); startListening() }
    }

    /// Change the transcription model at runtime so a Settings change takes
    /// effect without an app restart: the live `Transcriber` drops its loaded
    /// model and reloads the new one off the hot path.
    func updateModel(_ name: String) {
        guard name != settings.whisperModel else { return }
        settings.whisperModel = name
        settings.save()
        // setModel no longer loads (onboarding needs the swap and the download
        // decoupled); the Settings path still wants the hot-swap immediately.
        Task { await transcriber.setModel(name); try? await transcriber.warmUp() }
    }

    // MARK: dictation loop

    private func startRecording() {
        guard !isRecording, pausedUntil == nil else { return }
        pressTime = Date()
        do {
            try audio.start()
            isRecording = true
            hud.setMaxSeconds(maxRecordingSeconds)
            hud.setShowChip(shouldShowHotkeyChip)
            hud.show(.recording(hotkey: settings.hotkey))
            if streamPartials || settings.liveTranscript { startPartialStream() }
            maxRecordTask = Task { [weak self] in
                try? await Task.sleep(for: .seconds(self?.maxRecordingSeconds ?? 300))
                if !Task.isCancelled { self?.stopAndProcess() }  // finish + insert, never drop audio
            }
        } catch {
            log.error("audio start failed: \(error.localizedDescription)")
            lastError = "Microphone unavailable"
            hud.show(.error(.microphone))
        }
    }

    private func stopAndProcess() {
        guard isRecording else { return }
        isRecording = false
        maxRecordTask?.cancel()
        partialTask?.cancel()
        partialTask = nil
        let samples = audio.stop()
        let elapsed = Date().timeIntervalSince(pressTime)
        lastSpeechSeconds = elapsed
        guard !samples.isEmpty else { hud.hide(); return }
        // Released too soon to catch speech — nudge to keep talking, don't transcribe.
        guard elapsed >= minSpeakSeconds else {
            hud.show(.tooShort)
            return
        }
        lastSamples = samples
        hud.show(.transcribing)
        Task { await process(samples) }
    }

    /// Re-transcribe the growing buffer on a 300 ms beat so the ink fill has
    /// words to reveal while the key is still held. Every partial is
    /// best-effort: a failure or a slow pass is skipped, never surfaced, and
    /// never allowed to delay the real transcription on release.
    private func startPartialStream() {
        partialTranscript = nil
        partialTask?.cancel()
        partialTask = Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(for: .milliseconds(300))
                guard let self, !Task.isCancelled, self.isRecording else { return }
                let buffer = self.audio.snapshot()
                guard let text = await self.transcriber.partial(buffer, language: self.settings.language),
                      !text.isEmpty else { continue }
                if !Task.isCancelled {
                    self.partialTranscript = text
                    // Echo the words into the HUD while the key is held —
                    // unless the user turned text echo off, which covers the
                    // dictating-passwords case for live words too.
                    if self.settings.liveTranscript && self.settings.echoInsertedText {
                        self.hud.updateLiveTail(text)
                    }
                }
            }
        }
    }

    private func retryLastTranscription() {
        guard !lastSamples.isEmpty else { return }
        hud.show(.transcribing)
        Task { await process(lastSamples) }
    }

    private func process(_ samples: [Float]) async {
        isWorking = true
        defer { isWorking = false }
        // The app the user dictated into — for per-app style + history.
        let frontApp = NSWorkspace.shared.frontmostApplication?.localizedName ?? "Unknown"
        do {
            let raw = try await transcriber.transcribe(samples, language: settings.language)
            guard !raw.isEmpty else {
                // Whisper heard nothing usable (very short/quiet) — a nudge, not an error.
                hud.show(.tooShort)
                return
            }

            // Voice snippet: an exact trigger expands directly, no LLM call.
            if let expansion = snippetStore.match(raw) {
                deliver(expansion, app: frontApp)
                return
            }

            hud.show(.cleaning)
            // Per-app style overrides the manual default (design 03 "Styles").
            let style = styleStore.styleForFrontmostApp(fallback: settings.style)
            // Personal context: profile + dictionary + snippet hints.
            let context = profileStore.promptFragment
                + dictionaryStore.promptFragment
                + snippetHints()
            let provider = CleanupFactory.make(settings)
            let cleaned = (try? await provider.cleanup(raw, style: style, context: context)) ?? raw
            deliver(cleaned, app: frontApp)
        } catch {
            log.error("dictation failed: \(error.localizedDescription)")
            lastError = "Dictation failed"
            hud.show(.error(.timeout))
        }
    }

    /// Paste, log to history, bump stats, and flash the success HUD.
    private func deliver(_ text: String, app: String) {
        let words = text.split(whereSeparator: \.isWhitespace).count
        // Paste (if enabled). If the synthetic ⌘V couldn't be delivered — e.g.
        // Accessibility was revoked — Paster keeps the text on the clipboard and
        // returns false, and we nudge the user to paste it manually.
        let pasted = settings.autoPaste ? Paster.paste(text) : true
        historyStore.record(app: app, text: text, words: words)
        usageCounters.record(.dictationCompleted)
        analyticsClient.syncIfDue(controller: self)
        lastError = nil
        lastTranscript = text
        partialTranscript = nil
        markFirstSuccess()
        if pasted {
            hud.setShowChip(shouldShowHotkeyChip)
            hud.show(.result(tail: Self.tail(of: text, words: words,
                                             echo: settings.echoInsertedText)))
        } else {
            hud.show(.error(.pasteBlocked))
        }
    }

    /// The last five words of what landed, ellipsised when truncated — proof
    /// rather than a receipt. Falls back to a count when the user has asked not
    /// to have their text echoed.
    static func tail(of text: String, words: Int, echo: Bool) -> String {
        guard echo else { return words == 1 ? "1 word" : "\(words.grouped) words" }
        let parts = text.split(whereSeparator: \.isWhitespace)
        guard parts.count > 5 else { return parts.joined(separator: " ") }
        return "…" + parts.suffix(5).joined(separator: " ")
    }

    /// Stamp the two "first time" dates once, on the first dictation that
    /// actually worked.
    private func markFirstSuccess() {
        var changed = false
        if settings.firstUseDate == nil {
            // Home reads "…since <month>" off this date against an all-time
            // word total, and an upgrade install arrives with months of daily
            // totals already on disk. Stamping today would credit every one of
            // those words to this minute. Backdate to the first day anything
            // was actually dictated; only a genuinely new install has none.
            settings.firstUseDate = historyStore.firstDictationDay ?? Date()
            changed = true
        }
        if settings.hotkeyLearnedAt == nil { settings.hotkeyLearnedAt = Date(); changed = true }
        if changed { settings.save() }
    }

    /// The chip is a reminder, and a reminder that never leaves is furniture:
    /// show it for 7 days from when the hotkey was learned, then never.
    private var shouldShowHotkeyChip: Bool {
        guard let learned = settings.hotkeyLearnedAt else { return true }
        return Date() < learned.addingTimeInterval(7 * 24 * 60 * 60)
    }

    /// Tell the LLM to echo a snippet trigger verbatim so match() can expand it
    /// even after cleanup rewording (mirrors get_snippets_prompt_fragment).
    private func snippetHints() -> String {
        let triggers = snippetStore.snippets.map { "  - \"\($0.trigger)\"" }
        guard !triggers.isEmpty else { return "" }
        return "\n\nVoice snippets — if the user says EXACTLY one of these triggers "
            + "(and nothing else meaningful), output the trigger unchanged:\n"
            + triggers.joined(separator: "\n")
    }
}
