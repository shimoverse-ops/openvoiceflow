# OpenVoiceFlow — Product Requirements Document

**Version:** 1.0
**Author:** Product Management (Internal)
**Date:** 2026-03-15
**Status:** Active — Engineering Blueprint

---

## Executive Summary

OpenVoiceFlow is a source-available voice dictation app for macOS, free for personal and qualifying noncommercial use, competing against Wispr Flow ($144/yr), Superwhisper ($85/yr), and VoiceInk. Commercial use requires separate terms from Shimoverse Studios. Current state: functional push-to-talk with whisper.cpp STT, LLM cleanup (6 backends), floating overlay, personal dictionary, snippets, multi-language, style modes, stats, auto-update, launch-at-login, tkinter onboarding wizard, and menu bar app.

This PRD defines 7 features that close competitive gaps and establish OpenVoiceFlow as a source-available leader in macOS voice dictation. The features are ordered by priority and dependency chain.

**Positioning:**
- $0-3/yr vs $85-144/yr (40-50x cheaper)
- Public source, free personal and qualifying noncommercial license, PRs welcome (vs VoiceInk's GPL/no-PRs-accepted)
- Python (accessible contributor base) vs Swift (high barrier)
- 6 LLM backends vs locked ecosystems
- Local-first audio (whisper.cpp, never leaves machine)

---

## Architecture Context

Understanding the codebase is critical for engineering. Current file map:

```
voiceflow/
├── __init__.py          # Version, metadata
├── __main__.py          # CLI entry point (argparse)
├── app.py               # Main controller: hotkey listener, record/transcribe/cleanup/paste loop
├── recorder.py          # AudioRecorder: sounddevice InputStream → WAV
├── transcriber.py       # whisper.cpp binary detection, model download, batch transcribe()
├── overlay.py           # PyObjC/AppKit floating HUD (recording/processing/result/error states)
├── menubar.py           # rumps menu bar app (wraps app.py + settings UI)
├── config.py            # JSON config at ~/.openvoiceflow/config.json
├── styles.py            # Style presets (default/casual/formal/code/email)
├── dictionary.py        # Personal dictionary (word + aliases → LLM prompt injection)
├── snippets.py          # Trigger phrase → expansion (pre-LLM, exact match)
├── stats.py             # Cumulative dictation stats (JSON)
├── system.py            # paste_text (pbcopy+osascript), play_sound, log_transcript
├── onboarding.py        # tkinter setup wizard
├── updater.py           # GitHub release checker (background thread)
├── autostart.py         # LaunchAgent plist management
└── llm/
    ├── __init__.py      # Backend registry + cleanup_text()
    ├── base.py          # LLMBackend ABC + DEFAULT_PROMPT + style/dictionary/snippet injection
    ├── gemini.py        # Google Gemini
    ├── openai_backend.py # OpenAI
    ├── anthropic_backend.py # Anthropic
    ├── groq_backend.py  # Groq
    └── ollama_backend.py # Ollama (local)
```

**Key flow (app.py):**
1. `on_key_press()` → `start_recording()` → `AudioRecorder.start()` → overlay shows 🔴
2. `on_key_release()` → `stop_and_process()` → spawns `_process_audio()` thread
3. `_process_audio()`: save WAV → `transcribe()` (whisper.cpp subprocess) → `match_snippet()` → `cleanup_text()` (LLM) → `paste_text()` (pbcopy + Cmd+V)

**Config location:** `~/.openvoiceflow/`
**Logs:** `~/.openvoiceflow/logs/YYYY-MM-DD.jsonl` + `.md`
**Models:** `~/.openvoiceflow/models/ggml-*.bin`

---

## Feature 1: Real-Time Streaming Transcription

**Priority:** P0
**Effort:** L (Large)
**This is the #1 competitive gap.** Wispr Flow and Superwhisper show words appearing as the user speaks. We wait until key release, process the entire audio file, then paste. Users feel like the app is frozen during long dictations.

### User Story

As a user, I want to see my words appearing in the floating overlay in real-time as I speak, so I get immediate visual feedback that the app is hearing me correctly and I can self-correct while still talking.

### Success Metric

- **P50 first-word latency < 1 second** from speech onset to first word appearing in overlay
- **User-perceived responsiveness rating** (qualitative): users should describe the experience as "live" or "instant"
- **Final output quality unchanged** vs current batch mode (LLM cleanup still runs on release)

### Acceptance Criteria

1. When the user holds the hotkey and speaks, partial transcript text appears in the floating overlay within ~0.5-1s of each utterance
2. The overlay updates incrementally (words appear, may be revised as more context arrives)
3. On key release, the full raw transcript is sent to LLM cleanup as before
4. Final cleaned text is pasted at cursor (behavior unchanged)
5. Streaming mode must be toggleable in config (`"streaming": true/false`) with fallback to current batch mode
6. Works with all supported whisper models (tiny.en through large)
7. No regression in final transcription accuracy
8. CPU/GPU usage during streaming stays reasonable (< 50% sustained on M1)
9. Overlay smoothly animates text appearing (no flicker, no full-text replacement jumps)
10. If `whisper-stream` binary is not found, gracefully fall back to batch mode with a one-time warning

### Technical Approach

**Binary:** `whisper-stream` (installed via `brew install whisper-cpp`, confirmed present at `/opt/homebrew/bin/whisper-stream`). Key flags:
- `--step 3000` (audio step size in ms, default 3000; can try 1500-2000 for lower latency)
- `--length 10000` (audio length in ms)
- `--keep 200` (overlap from previous step)
- `--model` / `--language` (same as current batch transcribe)
- `--vad-thold 0.60` (voice activity detection threshold)
- `--capture -1` (default audio device)

**Implementation plan:**

1. **New file: `voiceflow/streamer.py`**
   - Class `StreamingTranscriber` that manages a `whisper-stream` subprocess
   - `start(model_path, language)` → launches `whisper-stream` as subprocess, captures stdout in real-time
   - `stop()` → sends SIGTERM, collects final output
   - Yields partial transcript lines via a callback or queue
   - Parses `whisper-stream` stdout format (it prints partial lines to stdout as it transcribes)

2. **Modify: `voiceflow/overlay.py`**
   - New method `show_streaming_text(text: str)` that updates the label text without hiding/showing the window
   - Auto-resize width based on text length (current `show_result()` already does this)
   - Distinct visual state: e.g., white text on blur background (vs red dot for recording)

3. **Modify: `voiceflow/app.py`**
   - In `start_recording()`: if streaming enabled, start `StreamingTranscriber` instead of (or alongside) `AudioRecorder`
   - Register callback: on each partial transcript → `overlay.show_streaming_text(partial)`
   - In `stop_and_process()`: stop `StreamingTranscriber`, get full raw text, proceed to LLM cleanup as before
   - The `AudioRecorder` may still be needed if we want to save the WAV for logging; alternatively, `whisper-stream --save-audio` can handle this

4. **Modify: `voiceflow/config.py`**
   - Add `"streaming": True` to DEFAULTS
   - Add `"streaming_step_ms": 3000` for tuning

5. **Modify: `voiceflow/__main__.py`**
   - Add `--streaming on/off` CLI flag
   - Add `--streaming-step` flag

6. **Modify: `voiceflow/menubar.py`**
   - Add toggle in menu: "✓ Streaming Mode" / "  Streaming Mode"

**Risk:** `whisper-stream` reads directly from the microphone (via SDL or portaudio). We need to verify it doesn't conflict with our `sounddevice` InputStream. Two approaches:
- **Option A (preferred):** When streaming is on, let `whisper-stream` own the mic entirely. Don't start `AudioRecorder`. Use `whisper-stream --save-audio` to save the recording for logging.
- **Option B (fallback):** Run both in parallel (two separate audio captures). This works on macOS because multiple processes can capture from the same mic.

### Dependencies

- `whisper-stream` binary (bundled with `brew install whisper-cpp`, already a dependency)
- No new Python packages required
- Overlay must support text update without flicker (may need AppKit `setNeedsDisplay` optimization)

---

## Feature 2: Per-App Context Detection

**Priority:** P0
**Effort:** M (Medium)
**Competitive gap:** VoiceInk's "Power Mode" auto-detects the active app and applies different settings. Superwhisper captures app context for LLM. We use one global style.

### User Story

As a user, I want OpenVoiceFlow to automatically switch its style/tone when I move between apps, so that dictation in VS Code produces code-formatted text, dictation in Gmail produces email-formatted text, and dictation in Slack produces casual text, without me manually switching styles.

### Success Metric

- **0 manual style switches needed** for users who configure app mappings
- **Style correctly detected ≥ 95%** of the time (frontmost app detection is deterministic, so this is really about mapping completeness)
- **< 50ms latency** to detect frontmost app (should be near-instant via PyObjC)

### Acceptance Criteria

1. On hotkey press, detect the frontmost application name before starting transcription
2. Look up the app name in a configurable `app_styles` mapping in config.json
3. If a mapping exists, use that style for this dictation (overriding the global default)
4. If no mapping exists, use the global `style` setting
5. The overlay shows which style is active (e.g., "🔴 Recording (Code 💻)")
6. Default mappings ship out of the box for common apps:
   - VS Code, Xcode, IntelliJ, Terminal, iTerm2 → `code`
   - Gmail, Outlook, Mail → `email`
   - Slack, Discord, WhatsApp, iMessage, Telegram → `casual`
   - Word, Google Docs, Notion, Pages → `default`
7. Users can add/edit/remove mappings via CLI (`--app-style "VS Code" code`) and config.json
8. App detection works across Spaces and fullscreen apps
9. Menu bar shows the detected app + active style in a status line
10. The detected app name is passed to the LLM as additional context (e.g., "The user is dictating in VS Code")

### Technical Approach

1. **New file: `voiceflow/context.py`**
   - Function `get_frontmost_app() -> str`: uses `NSWorkspace.sharedWorkspace().frontmostApplication().localizedName()` via PyObjC (already a dependency for overlay.py)
   - Function `get_style_for_app(app_name: str, config: dict) -> str`: looks up app_styles mapping, returns style string
   - Function `get_app_context_prompt(app_name: str) -> str`: returns LLM prompt fragment like "The user is currently in {app_name}. Adjust your output style accordingly."

2. **Modify: `voiceflow/config.py`**
   - Add to DEFAULTS:
     ```python
     "app_styles": {
         "Code": "code",
         "Xcode": "code",
         "Terminal": "code",
         "iTerm2": "code",
         "IntelliJ IDEA": "code",
         "Mail": "email",
         "Gmail": "email",
         "Outlook": "email",
         "Slack": "casual",
         "Discord": "casual",
         "Messages": "casual",
         "WhatsApp": "casual",
     },
     "auto_style": True,
     ```

3. **Modify: `voiceflow/app.py`**
   - In `start_recording()`: call `get_frontmost_app()` and store as `self._current_app`
   - Resolve style via `get_style_for_app(self._current_app, self.config)`
   - Pass resolved style to `_process_audio()` instead of using global config style
   - Pass app context to LLM prompt

4. **Modify: `voiceflow/llm/base.py`**
   - Accept optional `app_context` parameter in `cleanup()` and `_make_prompt()`
   - Append app context to prompt when provided

5. **Modify: `voiceflow/__main__.py`**
   - Add `--app-style APP_NAME STYLE` to set a mapping
   - Add `--remove-app-style APP_NAME` to remove a mapping
   - Add `--list-app-styles` to show all mappings
   - Add `--auto-style on/off` to enable/disable per-app detection

6. **Modify: `voiceflow/menubar.py`**
   - Show detected app in status line
   - Add "Auto Style" toggle menu item
   - Optionally show "App Styles..." submenu

7. **Modify: `voiceflow/overlay.py`**
   - `show_recording()` accepts optional style label, shows it in the overlay text

### Dependencies

- `pyobjc-framework-Cocoa` (already in optional dependencies, used by overlay.py)
- No new packages

---

## Feature 3: Voice Commands

**Priority:** P1
**Effort:** S (Small)
**Competitive gap:** Few source-available competitors handle this well. Dictation-native commands like "new line", "period", "comma" should be instant, not require an LLM round-trip.

### User Story

As a user, I want to say "new line" or "period" or "comma" while dictating and have those commands execute instantly as punctuation/formatting in my text, without waiting for LLM processing, so dictation feels more natural and responsive.

### Success Metric

- **Voice command latency: 0ms additional** (processed pre-LLM via regex)
- **Command recognition accuracy ≥ 98%** (exact string match, not fuzzy)
- **≥ 10 default commands** supported out of the box

### Acceptance Criteria

1. The following voice commands are recognized in raw transcript text and replaced BEFORE LLM cleanup:
   - "new line" / "newline" → `\n`
   - "new paragraph" → `\n\n`
   - "period" / "full stop" → `.`
   - "comma" → `,`
   - "question mark" → `?`
   - "exclamation mark" / "exclamation point" → `!`
   - "colon" → `:`
   - "semicolon" → `;`
   - "open parenthesis" / "open paren" → `(`
   - "close parenthesis" / "close paren" → `)`
   - "dash" / "hyphen" → `-`
   - "open quote" / "open quotes" → `"`
   - "close quote" / "close quotes" → `"`
   - "ellipsis" / "dot dot dot" → `...`
   - "tab" → `\t`
2. Commands are case-insensitive
3. Commands work in any language mode (English command words are recognized even with non-English language setting)
4. Replacement happens before LLM cleanup (the LLM sees the punctuation, not the command words)
5. Users can add custom voice commands via config.json
6. Users can disable voice commands via config (`"voice_commands": false`)
7. Voice commands are processed with zero additional latency (regex replacement on raw string)

### Technical Approach

1. **New file: `voiceflow/commands.py`**
   - `DEFAULT_COMMANDS: dict[str, str]` — maps spoken phrase to replacement text
   - `load_commands(config: dict) -> dict[str, str]` — merges defaults with user-configured custom commands
   - `apply_commands(text: str, commands: dict) -> str` — iterates through commands, applies `re.sub(r'\b{phrase}\b', replacement, text, flags=re.IGNORECASE)` for each
   - Order matters: process longer phrases first to avoid partial matches (e.g., "new paragraph" before "new")

2. **Modify: `voiceflow/app.py`**
   - In `_process_audio()`, after `transcribe()` returns raw text and before `cleanup_text()`:
     ```python
     from .commands import apply_commands, load_commands
     commands = load_commands(self.config)
     raw_text = apply_commands(raw_text, commands)
     ```
   - This is a 3-line change in the hot path

3. **Modify: `voiceflow/config.py`**
   - Add to DEFAULTS:
     ```python
     "voice_commands": True,
     "custom_commands": {},
     ```

4. **Modify: `voiceflow/__main__.py`**
   - Add `--add-command PHRASE REPLACEMENT` to add custom voice command
   - Add `--remove-command PHRASE` to remove
   - Add `--list-commands` to show all
   - Add `--voice-commands on/off` to enable/disable

### Dependencies

- None. Pure Python regex. Zero new packages.

---

## Feature 4: Selected Text Context

**Priority:** P1
**Effort:** M (Medium)
**Competitive gap:** Superwhisper reads selected text before dictation starts and feeds it to the LLM for context-aware corrections. This dramatically improves quality when editing existing text, replying to emails/messages, or continuing a document.

### User Story

As a user, I want OpenVoiceFlow to capture whatever text I have selected (or on my clipboard) when I start dictating, and feed it to the LLM as context, so the AI understands what I'm replying to or editing and produces more relevant, contextually appropriate output.

### Success Metric

- **LLM correction relevance improvement** (qualitative): users report that dictation "understands context" when replying to messages or editing documents
- **Selected text captured ≥ 90%** of the time when text is actually selected (AppleScript/Accessibility limitations may cause occasional misses)

### Acceptance Criteria

1. On hotkey press (before recording starts), attempt to capture the currently selected text in the frontmost application
2. Method: simulate Cmd+C to copy selection, read from pasteboard, then restore the original clipboard contents
3. If no text is selected, capture whatever is on the clipboard as fallback context
4. Pass the captured context to the LLM as additional prompt context:
   - "The user has the following text selected/in context: '{selected_text}'. They are dictating a response, continuation, or edit to this text."
5. Context is capped at 2000 characters to avoid prompt bloat
6. Feature is toggleable: `"selected_text_context": true` in config
7. The overlay shows a subtle indicator when context was captured (e.g., "🔴 Recording (with context)")
8. Original clipboard is restored after context capture (user doesn't lose their clipboard)
9. If context capture fails (Accessibility not granted, no selection), dictation proceeds normally without context
10. Context is logged alongside the transcript in the JSONL logs

### Technical Approach

1. **New file: `voiceflow/clipboard.py`**
   - `capture_selected_text() -> str | None`:
     1. Read current clipboard via `subprocess.run(["pbpaste"], capture_output=True)`
     2. Store as `original_clipboard`
     3. Simulate Cmd+C via `osascript -e 'tell application "System Events" to keystroke "c" using command down'`
     4. Wait 100ms
     5. Read new clipboard via `pbpaste`
     6. If clipboard changed → that's the selected text
     7. Restore original clipboard via `pbcopy`
     8. Return selected text (or None if unchanged / empty)
   - `get_clipboard_context() -> str | None`: just reads current clipboard without simulating Cmd+C (fallback)

2. **Modify: `voiceflow/app.py`**
   - In `start_recording()`:
     ```python
     self._selected_context = None
     if self.config.get("selected_text_context", True):
         from .clipboard import capture_selected_text
         self._selected_context = capture_selected_text()
     ```
   - Pass `self._selected_context` to `_process_audio()`

3. **Modify: `voiceflow/llm/base.py`**
   - Add `context` parameter to `cleanup(text, context=None)`
   - In `_make_prompt()`, if context is provided, prepend:
     ```
     Context — the user had this text selected when they started dictating:
     "{context}"
     
     Clean up the following dictation, taking the above context into account:
     ```

4. **Modify: `voiceflow/llm/__init__.py`**
   - Update `cleanup_text(raw_text, config, context=None)` signature
   - Pass context through to backend

5. **Modify: `voiceflow/config.py`**
   - Add `"selected_text_context": True` to DEFAULTS

6. **Modify: `voiceflow/system.py`**
   - In `log_transcript()`, accept optional `context` parameter, write to JSONL

### Dependencies

- Accessibility permission (already required for paste_text via osascript)
- No new packages

### Risks

- **Clipboard race condition:** If the user is actively copying things, capturing selected text could interfere. Mitigation: fast capture (< 200ms total), always restore clipboard.
- **Accessibility permission:** Simulating Cmd+C requires the same Accessibility permission we already need for Cmd+V paste. No new permission grant needed.
- **Apps that don't support Cmd+C:** Some apps (Terminal with custom key bindings, certain games) may not respond to Cmd+C. Graceful fallback: return None, proceed without context.

---

## Feature 5: Homebrew Tap

**Priority:** P1
**Effort:** S (Small)
**Competitive gap:** VoiceInk has `brew install --cask voiceink`. We have nothing. Users who live in the terminal expect `brew install`.

### User Story

As a developer, I want to install OpenVoiceFlow via `brew install openvoiceflow` (or `brew install --cask openvoiceflow`), so I can manage it alongside my other tools and get updates through Homebrew.

### Success Metric

- **Successful `brew install openvoiceflow`** from tap
- **Auto-resolves whisper-cpp dependency** (no separate manual install step)
- **Installation completes in < 2 minutes** on broadband

### Acceptance Criteria

1. A Homebrew tap repository exists at `shimoverse/homebrew-tap` (or `shimoverse/homebrew-openvoiceflow`)
2. Users can run: `brew tap shimoverse/tap && brew install openvoiceflow`
3. The formula:
   - Depends on `whisper-cpp` (auto-installed)
   - Depends on `python@3.11` (or 3.12)
   - Creates a virtualenv and installs Python dependencies
   - Downloads the default whisper model (base.en)
   - Creates the `openvoiceflow` CLI command
4. `brew upgrade openvoiceflow` works for updates
5. `brew uninstall openvoiceflow` cleanly removes everything
6. Formula passes `brew audit --strict` and `brew test`
7. README is updated with Homebrew install instructions
8. Alternatively (or additionally): a Cask formula that wraps the DMG for `brew install --cask openvoiceflow`

### Technical Approach

1. **New repo: `shimoverse/homebrew-tap`**
   - `Formula/openvoiceflow.rb` — Homebrew formula:
     ```ruby
     class Openvoiceflow < Formula
       desc "Free personal-use, source-available voice dictation for macOS"
       homepage "https://github.com/shimoverse/openvoiceflow"
       url "https://github.com/shimoverse/openvoiceflow/archive/refs/tags/v#{version}.tar.gz"
       license :cannot_represent
       depends_on "whisper-cpp"
       depends_on "python@3.11"
       # ... virtualenv setup, pip install, model download
     end
     ```
   - Optionally: `Casks/openvoiceflow.rb` for DMG-based install

2. **Modify: `.github/workflows/release.yml`**
   - After DMG build, trigger a workflow in the tap repo to update the formula with new version + SHA256

3. **Modify: `README.md`**
   - Add Homebrew install section at top of "Get Started"

### Dependencies

- GitHub repo creation (`shimoverse/homebrew-tap`)
- Release tagging workflow (already exists)

---

## Feature 6: History Search

**Priority:** P2
**Effort:** S (Small)
**Not a competitive gap, but a quality-of-life feature.** Users already have JSONL logs at `~/.openvoiceflow/logs/`. Making them searchable from CLI is low-effort, high-utility.

### User Story

As a user, I want to search my past dictation transcripts from the command line, so I can find something I said last week without manually opening log files.

### Success Metric

- **Search returns results in < 1 second** for typical log volumes (< 1000 entries)
- **Full-text search** across both raw and cleaned transcripts

### Acceptance Criteria

1. `openvoiceflow --search "meeting friday"` searches all JSONL logs and returns matching entries
2. Search is case-insensitive, matches against both `raw` and `cleaned` fields
3. Results show: timestamp, cleaned text (truncated to 100 chars), and which log file
4. `--search-date 2026-03-15` filters to a specific date
5. `--search-last 7` filters to last N days
6. Results are sorted by timestamp (most recent first)
7. Maximum 50 results by default, `--limit N` to change
8. Exit code 0 if matches found, 1 if no matches

### Technical Approach

1. **New file: `voiceflow/search.py`**
   - `search_transcripts(query: str, date: str = None, last_days: int = None, limit: int = 50) -> list[dict]`
   - Reads all `.jsonl` files in LOG_DIR, filters by date range if specified
   - Case-insensitive substring match on `raw` and `cleaned` fields
   - Returns sorted list of matching entries

2. **Modify: `voiceflow/__main__.py`**
   - Add `--search QUERY` argument
   - Add `--search-date DATE` and `--search-last DAYS` filters
   - Add `--limit N` for result count

### Dependencies

- None. Reads existing JSONL files. Pure Python.

---

## Feature 7: Demo GIF/Video

**Priority:** P2
**Effort:** S (Small)
**Not code, but critical for growth.** The README has no visual demo. A 15-second GIF showing the hold-speak-release-paste flow would dramatically increase conversion from README visitor to installer.

### User Story

As a potential user visiting the GitHub repo, I want to see a short demo of OpenVoiceFlow in action, so I can immediately understand what it does and decide if I want to install it.

### Success Metric

- **README has a visual demo** (GIF or video) above the fold
- **Demo file < 5MB** (GitHub renders GIFs inline in README)
- **Demo shows the complete flow** in ≤ 15 seconds

### Acceptance Criteria

1. A demo GIF or MP4 is recorded showing:
   - User holds Right Cmd → overlay shows 🔴 Recording
   - User speaks a sentence with filler words ("um", "like")
   - User releases → overlay shows processing dots
   - Cleaned text appears at cursor in a text editor
2. GIF is ≤ 5MB, 720p or higher, ≤ 15 seconds
3. README updated with `<p align="center"><img src="..." /></p>` near the top
4. GIF stored in repo (e.g., `assets/demo.gif`) or hosted on GitHub releases
5. Optional: side-by-side comparison showing raw vs cleaned output

### Technical Approach

1. Record screen using macOS screenshot tool (Cmd+Shift+5) or OBS
2. Convert to GIF using `ffmpeg`:
   ```bash
   ffmpeg -i demo.mov -vf "fps=15,scale=720:-1:flags=lanczos" -c:v gif demo.gif
   ```
3. Add `assets/` directory to repo
4. Update README.md with image embed

### Dependencies

- None. Manual task.

---

## Non-Goals (What We Explicitly Won't Build)

1. **iOS/iPadOS/watchOS app** — macOS only. Mobile is a different product with different UX paradigms. Won't dilute focus.
2. **Windows/Linux support** — macOS first. Contributors are welcome to port, but we won't invest engineering effort here in this cycle.
3. **Cloud-hosted transcription** — whisper.cpp stays local. Audio never leaves the machine. This is a core differentiator.
4. **User accounts or cloud sync** — no server, no accounts, no data collection. Config is local JSON.
5. **Custom wake word / always-listening mode** — push-to-talk only. Always-on mic is a privacy anti-pattern.
6. **Speaker diarization** — "Speaker 1 said X, Speaker 2 said Y" is interesting but not a dictation feature. Future consideration.
7. **In-app settings GUI** — the menu bar app + CLI is sufficient. A full preferences window adds complexity for marginal UX gain. The tkinter onboarding wizard handles first-run. Config.json handles the rest.
8. **Plugin/extension system** — premature abstraction. The codebase is small enough that contributors can modify directly.
9. **Consumer premium tier** — personal and qualifying noncommercial use remains free; commercial use is licensed separately.
10. **Audio recording/playback** — we're a dictation tool, not a voice recorder. Logs are text-only (JSONL).

---

## Overall Success Metrics (Project-Level KPIs)

| Metric | Current | Target (90 days) | How to Measure |
|--------|---------|-------------------|----------------|
| GitHub stars | ~0 (new) | 500+ | GitHub API |
| Homebrew installs | 0 | 100+ | Homebrew analytics |
| Weekly active dictations (self-reported) | Unknown | 50+ users | Stats.json aggregation (opt-in) |
| Issues closed / opened ratio | N/A | > 0.8 | GitHub Issues |
| Time from clone to first dictation | ~5 min | < 2 min | Onboarding funnel |
| Competitor mention in "alternatives" | 0 | Listed on AlternativeTo, Reddit threads | Manual tracking |
| README demo GIF bounce rate | N/A (no demo) | Reduced scroll-away | GitHub traffic analytics |

**North Star Metric:** Monthly active users who complete ≥ 10 dictations. This proves the tool is sticky, not just installed-and-forgotten.

---

## Risk Assessment

### Technical Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| `whisper-stream` subprocess conflicts with `sounddevice` mic capture | P0 feature blocked | Medium | Option A: let whisper-stream own the mic entirely when streaming is on. Option B: test dual-capture on macOS (historically works). |
| `whisper-stream` output format changes between whisper.cpp versions | Streaming parser breaks | Low | Pin minimum whisper-cpp version. Parse defensively with fallback. |
| PyObjC `NSWorkspace` frontmost app detection fails in certain contexts (e.g., Citrix, VMs, screen sharing) | Per-app context returns wrong app | Low | Graceful fallback to global style. Log app name for debugging. |
| Clipboard capture (Cmd+C simulation) interferes with user workflow | User loses clipboard content | Medium | Always save and restore clipboard. Add 100ms delay. Make feature toggleable. |
| Homebrew formula review/approval takes weeks | Distribution delayed | Medium | Ship tap formula immediately (no review for tap repos). Upstream to homebrew-core later. |
| `whisper-stream` latency > 2s on Intel Macs with large models | Poor streaming UX on Intel | Medium | Default to `base.en` model for streaming. Document that `small.en` or larger may have higher latency on Intel. |

### Product Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Feature scope creep delays all features | Nothing ships | Medium | Strict priority order. Ship P0 features first, P1 next. Don't start P1 until both P0s are merged. |
| Streaming mode UX is janky (text jumping, flickering) | Users disable it, competitive gap remains | Medium | Invest in overlay polish. Test with real users. Ship behind feature flag first. |
| Voice commands conflict with actual speech (user says "period" meaning the time period, not punctuation) | Incorrect text output | Low | LLM cleanup as second pass can fix most false positives. Also: voice commands only match isolated words, not mid-sentence usage. |
| Accessibility permission friction deters new users | High install-to-active drop-off | High (already exists) | Better onboarding. Auto-detect permission status. Show clear instructions with screenshots in onboarding wizard. |

### Competitive Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Wispr Flow or Superwhisper drop price significantly | Our cost advantage shrinks | Low | Our advantage is public source + multi-backend + privacy, not just cost. |
| Apple ships native dictation improvements in macOS 16 | Reduces TAM | Medium | Apple's dictation will never support custom LLMs, multi-backend, voice commands, or app-specific styles. Our power-user niche remains. |
| VoiceInk broadens its source license and accepts PRs | Direct competitor in our niche | Very Low | VoiceInk is Swift; we're Python. Different contributor bases. Our multi-backend approach is architecturally different. |

---

## Implementation Order and Dependency Chain

```
Phase 1 (P0 — ship within 2 weeks):
  ├── Feature 1: Streaming Transcription  [L]  ← no dependencies
  └── Feature 2: Per-App Context          [M]  ← no dependencies
       (can be built in parallel)

Phase 2 (P1 — ship within 4 weeks):
  ├── Feature 3: Voice Commands           [S]  ← no dependencies
  ├── Feature 4: Selected Text Context    [M]  ← depends on Feature 2 (shares context.py pattern)
  └── Feature 5: Homebrew Tap             [S]  ← depends on stable release (Phase 1 merged)

Phase 3 (P2 — ship within 6 weeks):
  ├── Feature 6: History Search           [S]  ← no dependencies
  └── Feature 7: Demo GIF                 [S]  ← depends on Features 1+2 being live (demo should show streaming)
```

**Parallelization:** Features 1 and 2 touch different files and can be developed simultaneously by different engineers. Feature 3 is small enough to slot into either phase. Feature 5 can begin once any tagged release exists.

---

## Open Questions for Engineering

1. **Streaming: subprocess vs library?** The `whisper-stream` binary approach is simplest but couples us to the CLI output format. Alternative: use whisper.cpp's C library via ctypes/cffi for tighter integration. Recommendation: start with subprocess (ship fast), migrate to library binding later if needed.

2. **Overlay framework:** Current overlay uses raw PyObjC/AppKit. For streaming text updates at 2-3Hz, is this performant enough? Should we consider SwiftUI embedded via PyObjC? Recommendation: test current approach first, optimize only if visibly janky.

3. **Config migration:** Adding new config keys (streaming, app_styles, voice_commands, selected_text_context) requires backward compatibility. Current approach (merge with DEFAULTS on load) handles this cleanly. No migration script needed.

4. **Testing:** Current CI is minimal (lint + import check + config validation). Should we add unit tests for the new modules (commands.py, context.py, clipboard.py, search.py)? Recommendation: yes, add pytest tests for pure-logic modules. Skip integration tests that require hardware (mic, screen).

---

## Appendix: Competitor Feature Matrix

| Feature | OpenVoiceFlow (current) | OpenVoiceFlow (after PRD) | Wispr Flow | Superwhisper | VoiceInk |
|---------|:-:|:-:|:-:|:-:|:-:|
| Local STT | ✅ | ✅ | ✅ | ✅ | ✅ |
| LLM cleanup | ✅ (6 backends) | ✅ (6 backends) | ✅ (1) | ✅ (1) | ✅ (1) |
| Streaming transcription | ❌ | ✅ | ✅ | ✅ | ❌ |
| Per-app context | ❌ | ✅ | ❌ | ✅ | ✅ |
| Voice commands | ❌ | ✅ | ❌ | ❌ | ❌ |
| Selected text context | ❌ | ✅ | ❌ | ✅ | ❌ |
| Personal dictionary | ✅ | ✅ | ❌ | ❌ | ❌ |
| Snippets | ✅ | ✅ | ❌ | ❌ | ❌ |
| Multi-language | ✅ | ✅ | ✅ | ✅ | ✅ |
| Style modes | ✅ | ✅ | ❌ | ❌ | ❌ |
| Homebrew | ❌ | ✅ | ❌ | ❌ | ✅ |
| History search | ❌ | ✅ | ❌ | ❌ | ❌ |
| Source available | ✅ | ✅ | ❌ | ❌ | ✅ (GPL) |
| Price | $0-3/yr | $0-3/yr | $144/yr | $85/yr | $0 (GPL) |

After this PRD ships, OpenVoiceFlow will have feature parity or superiority in every category except native Swift performance (which we trade for Python accessibility and contributor friendliness).

---

*End of PRD. This document is the engineering contract. Build to this spec.*
