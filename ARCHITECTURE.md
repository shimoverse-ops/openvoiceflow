# OpenVoiceFlow — Architecture

> **This document describes the legacy Python app (≤ 0.3.6), which is
> end-of-life.** The shipping app is native Swift under `native/` — for its
> architecture, start with the module map in
> [`native/README.md`](native/README.md): HotkeyEngine (CGEvent tap) →
> AudioCapture → Transcriber (WhisperKit) → CleanupProvider (optional) →
> Paster, orchestrated by AppController and surfaced through HUDController,
> DashboardView, and OnboardingView.



> Audience: humans contributing code. For an AI-coding-agent contributor's view, see [`AGENTS.md`](AGENTS.md) at the repo root.

## 1. Elevator pitch

OpenVoiceFlow is a macOS push-to-talk dictation app: hold a hotkey, speak, release, and cleaned text appears at your cursor. Speech-to-text runs locally via `whisper.cpp`. Cleanup runs through whichever LLM you point it at — OpenRouter, OpenAI, Anthropic, Groq, or fully-local Ollama. The core invariant is **audio stays on your Mac, transcripts may go to the LLM you pick, and everything else (logs, learned corrections, profile, snippets) is opt-in and stored in `~/.openvoiceflow/` mode 600**.

## 2. Top-level data flow

```
┌──────────┐   press     ┌──────────────┐
│  Hotkey  │────────────▶│ pynput       │
│ (held)   │             │  Listener    │
└──────────┘             └──────┬───────┘
                                │ on_press / on_release
                                ▼
                       ┌────────────────────┐    streaming?     ┌──────────────────────┐
                       │ app.OpenVoiceFlow  │──── yes ─────────▶│ streamer.py          │
                       │ (orchestrator)     │                   │ (whisper-stream      │
                       └────────┬───────────┘                   │  subprocess)         │
                                │ no                            └──────────┬───────────┘
                                ▼                                          │
                       ┌────────────────────┐                              │ partial
                       │ recorder.py        │                              │ text via
                       │ (sounddevice WAV)  │                              │ callback
                       └────────┬───────────┘                              │
                                │ tempfile.wav                             │
                                ▼                                          │
                       ┌────────────────────┐                              │
                       │ transcriber.py     │                              │
                       │ (whisper.cpp)      │                              │
                       └────────┬───────────┘                              │
                                │ raw_text                                 │
                                ▼                                          ▼
                       ┌─────────────────────────────────────────────────────────┐
                       │ commands.apply_commands()  ← voice commands run BEFORE  │
                       │                              LLM cleanup (zero latency) │
                       └────────┬────────────────────────────────────────────────┘
                                │
                                ▼
                       ┌────────────────────┐ matches?  ┌────────────────────┐
                       │ snippets.match_*() │──────────▶│ skip LLM, expand   │
                       └────────┬───────────┘           └────────┬───────────┘
                                │ no match                       │
                                ▼                                │
                       ┌────────────────────┐                    │
                       │ llm.cleanup_text() │                    │
                       │ (BYOK backend)     │                    │
                       │ + dictionary +     │                    │
                       │   profile + style  │                    │
                       │   + selected text  │                    │
                       │   + per-app ctx    │                    │
                       └────────┬───────────┘                    │
                                │ cleaned                        │
                                ▼                                │
                       ┌────────────────────────────────────────┐│
                       │ overlay.show_result()                  ││
                       └────────┬───────────────────────────────┘│
                                ▼                                ▼
                       ┌────────────────────┐    ┌──────────────────────────┐
                       │ system.paste_text  │───▶│ optional:                │
                       │ (pbcopy + osa Cmd+V)│   │  log_transcript          │
                       └────────────────────┘    │  learner.start_watching  │
                                                 │  stats.record_dictation  │
                                                 └──────────────────────────┘
```

Selected-text capture happens *before* recording starts (clipboard.capture_selected_text), so the original clipboard is restored before the user speaks.

### LLM prompt assembly

Every cleanup call hands the backend one fully-assembled system prompt. The pieces, in order, come from:

```
   DEFAULT_PROMPT (or user override via config["llm_prompt"])
              │
              ▼
   + STYLE_PRESETS[config["style"]]                ← global style suffix
              │
              ▼
   + dictionary.get_dictionary_prompt_fragment()   ← personal spellings
              │
              ▼
   + snippets.get_snippets_prompt_fragment()       ← trigger-phrase hints
              │
              ▼
   + profile.get_profile_prompt_fragment()         ← Know Me context
              │
              ▼
   + (per-call override_style if differs from global → re-runs the chain)
              │
              ▼
   + context.get_app_context_prompt(app, style)    ← "User is in Slack…"
              │
              ▼
   + "\n\nContext - the user had this text selected: '...' "    (if any)
              │
              ▼
   + "\n\nTranscript: <raw_text>"
```

The first four lines are baked once in `LLMBackend.__init__`. The last four are added per-call in `LLMBackend._make_prompt`. Backends that hit a chat-style API (OpenRouter, OpenAI, Anthropic, Groq) use chat-completions-style messages; Ollama sends the whole assembly as a single prompt string.

## 3. Module map

The 28 modules under `voiceflow/`, grouped by role.

### Entry & lifecycle
| Module | Purpose | Public symbols |
|---|---|---|
| `__init__.py` | Package metadata. | `__version__`, `__app_name__` |
| `__main__.py` | Argparse CLI; routes to subcommands or launches CLI/menubar runner. | `main()` |
| `app.py` | `OpenVoiceFlow` orchestrator: hotkey lifecycle, recording, transcription, cleanup, paste. | `OpenVoiceFlow`, `OpenVoiceFlow.run()`, `validate_setup()` |
| `menubar.py` | rumps-based menu bar app; same orchestrator wrapped in a status-bar UI. | `run_menubar()` |
| `autostart.py` | LaunchAgent install/remove for launch-at-login. | `set_autostart(enabled)`, `get_autostart_status()` |

### Capture
| Module | Purpose | Public symbols |
|---|---|---|
| `recorder.py` | sounddevice → 16 kHz mono WAV in memory; saves to a tempfile on stop. | `AudioRecorder` |
| `clipboard.py` | Captures selected text via Cmd+C round-trip and restores the original clipboard. | `capture_selected_text()`, `get_clipboard_context()` |

### Transcription
| Module | Purpose | Public symbols |
|---|---|---|
| `transcriber.py` | Locates the `whisper-cli` / `whisper-cpp` binary, downloads the requested ggml model, runs batch transcription. | `find_whisper_cpp()`, `get_model_path()`, `download_model()`, `transcribe()` |
| `streamer.py` | Manages a `whisper-stream` subprocess for live partial transcripts; thread-safe; falls back silently if binary missing. | `StreamingTranscriber`, `find_whisper_stream()` |

### LLM cleanup pipeline
| Module | Purpose | Public symbols |
|---|---|---|
| `llm/__init__.py` | Backend registry + dispatcher. | `BACKENDS`, `get_backend(config)`, `cleanup_text(...)` |
| `llm/base.py` | Abstract `LLMBackend`; assembles the system prompt from default + style + dictionary + snippets + profile. | `LLMBackend`, `DEFAULT_PROMPT`, `STYLE_PRESETS` |
| `llm/openrouter.py` | OpenRouter Gemma 4 backend (default, `google/gemma-4-31b-it`). | `OpenRouterBackend` |
| `llm/openai_backend.py` | OpenAI chat-completions backend. | `OpenAIBackend` |
| `llm/anthropic_backend.py` | Claude Messages API backend. | `AnthropicBackend` |
| `llm/groq_backend.py` | Groq backend (OpenAI-compatible API). | `GroqBackend` |
| `llm/ollama_backend.py` | Local Ollama daemon backend (`http://localhost:11434`). | `OllamaBackend` |

### Personalization
| Module | Purpose | Public symbols |
|---|---|---|
| `interview.py` | 6-screen Tk wizard that builds `profile.json` and seeds the dictionary. | `InterviewWizard`, `run_interview()` |
| `profile.py` | Load/save `~/.openvoiceflow/profile.json` and assemble its prompt fragment. | `load_profile()`, `save_profile()`, `has_profile()`, `clear_profile()`, `get_profile_prompt_fragment()`, `profile_to_dictionary()` |
| `dictionary.py` | Personal dictionary CRUD + LLM prompt fragment for spelling pinning. | `add_word()`, `remove_word()`, `list_words()`, `load_dictionary()`, `get_dictionary_prompt_fragment()` |
| `snippets.py` | Trigger-phrase → expansion store; consulted *after* LLM cleanup but before paste. | `add_snippet()`, `remove_snippet()`, `list_snippets()`, `match_snippet()`, `get_snippets_prompt_fragment()` |
| `commands.py` | Spoken-punctuation replacement (`"new line"` → `\n`); applied pre-LLM so the LLM sees already-formatted text. | `DEFAULT_COMMANDS`, `load_commands(config)`, `apply_commands(text, commands)` |
| `styles.py` | Style preset prompts and labels (default/casual/formal/code/email). | `STYLE_PROMPTS`, `STYLE_LABELS`, `get_style_prompt()`, `get_style_label()`, `list_styles()` |
| `context.py` | Frontmost-app detection (NSWorkspace) + per-app style resolution + LLM context fragment. | `get_frontmost_app()`, `get_style_for_app()`, `get_app_context_prompt()` |
| `learner.py` | Daemon thread watching the focused text field via the Accessibility API for 30 s after paste; learns word substitutions. | `CorrectionWatcher`, `CorrectionWatcher.start_watching()`, `CorrectionWatcher.stop()` |

### Output / system
| Module | Purpose | Public symbols |
|---|---|---|
| `system.py` | macOS paste (pbcopy + osascript Cmd+V), system sound feedback, transcript logging. | `paste_text()`, `play_sound()`, `log_transcript()` |
| `overlay.py` | PyObjC floating HUD pill (recording / streaming text / processing / result / error / learned). | `FloatingOverlay`, `OverlayState`, `get_overlay()` |

### Configuration & migration
| Module | Purpose | Public symbols |
|---|---|---|
| `config.py` | `DEFAULTS`, validation, load/save, schema versioning, and one-time migrations (`cleanup_prompt` → `llm_prompt`, retired Gemini → OpenRouter, v0.3.2 streaming default → batch). | `DEFAULTS`, `CONFIG_SCHEMA_VERSION`, `VALID_HOTKEYS`, `VALID_MODELS`, `VALID_BACKENDS`, `VALID_STYLES`, `load_config()`, `save_config()`, `validate_config()`, `get_api_key()`, `CONFIG_DIR`, `CONFIG_PATH`, `LOG_DIR`, `MODELS_DIR` |
| `_secure_io.py` | Centralized chmod-600 + JSON write helpers for every file under `~/.openvoiceflow/`. | `secure_chmod()`, `secure_write_json()` |

### Telemetry / lifecycle
| Module | Purpose | Public symbols |
|---|---|---|
| `updater.py` | Non-blocking GitHub-Releases version check on launch (no analytics, no fingerprinting). | `check_for_updates()` |
| `stats.py` | Local-only counters (dictations, words, recorded seconds). | `load_stats()`, `save_stats()`, `record_dictation()`, `show_stats()` |
| `search.py` | Full-text search over JSONL transcript logs. | `search_transcripts()` |

### Onboarding UX
| Module | Purpose | Public symbols |
|---|---|---|
| `onboarding.py` | First-run Tk wizard: pick backend → enter API key → pick hotkey. | `OnboardingWizard`, `run_onboarding()`, `needs_onboarding()` |
| `interview.py` | (Listed above under Personalization.) Reachable from the onboarding "Personalize" button or via `--profile`. | — |

## 4. Persistence model

Everything the app writes lives under `~/.openvoiceflow/`. v0.3+ enforces mode 600 on every file via `_secure_io.secure_write_json` / `secure_chmod`.

| Path | Format | Created by | Read by | Mode |
|---|---|---|---|---|
| `config.json` | JSON | `config.save_config` (first launch + every setter) | `config.load_config` (everywhere) | 600 |
| `profile.json` | JSON | `profile.save_profile` (interview finish) | `profile.load_profile`, `LLMBackend` | 600 |
| `dictionary.json` | JSON list | `dictionary.save_dictionary` (CLI / learner / interview) | `dictionary.load_dictionary`, `LLMBackend` | 600 |
| `snippets.json` | JSON dict | `snippets.save_snippets` (CLI) | `snippets.load_snippets`, `LLMBackend` | 600 |
| `stats.json` | JSON | `stats.save_stats` (after each dictation) | `stats.load_stats`, menubar, CLI | 600 |
| `models/ggml-*.bin` | binary | `transcriber.download_model` (lazy, on first miss) | `transcriber.transcribe`, `streamer` | filesystem default |
| `logs/YYYY-MM-DD.jsonl` | JSON Lines | `system.log_transcript` (only if `log_transcripts: true`) | `search.search_transcripts` | 600 |
| `logs/YYYY-MM-DD.md` | Markdown | `system.log_transcript` | humans / Finder | 600 |
| `logs/launchagent*.log` | text | macOS launchd | humans | filesystem default |
| `~/Library/LaunchAgents/com.openvoiceflow.app.plist` | plist | `autostart._enable_autostart` | launchd | filesystem default |

Audio (`.wav`) is written only as a NamedTemporaryFile during batch processing and `os.unlink`'d in the `finally` block — it never persists.

## 5. Permissions model

OpenVoiceFlow is unsandboxed and uses standard macOS TCC prompts. The DMG app starts through a small native launcher so macOS attributes Microphone, Accessibility, and Apple Events consent to the stable `com.openvoiceflow.dictation` bundle rather than to its Python bootstrap process. Signed builds carry the narrow audio-input and Apple Events entitlements required by the hardened runtime. Each feature requires exactly the set below; the app degrades cleanly when a permission is missing.

| Permission | Required for | Where | Failure mode if missing |
|---|---|---|---|
| **Microphone** | All recording (batch + streaming). | `recorder.AudioRecorder.start()`, `streamer.start()` | macOS shows the input device as silent; no transcript. |
| **Accessibility** | Auto-paste (osascript Cmd+V); selected-text capture (osascript Cmd+C); auto-learn (AX focused-element read). | `system.paste_text`, `clipboard.capture_selected_text`, `learner._read_focused_text` | `system.paste_text` plays an error sound and prints a stderr hint pointing the user to System Settings. Selected-text capture and learner silently no-op. |
| **Apple Events** | The osascript calls in paste / clipboard capture target System Events. | Same call sites as Accessibility. | Same as Accessibility. |
| **Notification Center** | Update-available toast and menubar notifications (rumps + osascript `display notification`). | `updater._send_notification`, `menubar.rumps.notification` | Notifications silently drop. |

## 6. Extension points

### Add an LLM backend
1. Create `voiceflow/llm/<name>_backend.py`. Subclass `voiceflow.llm.base.LLMBackend`. Set `name = "<name>"` and `default_model = "..."`.
2. Implement `validate(self) -> tuple[bool, str]` and `cleanup(self, raw_text, *, context, app_context, override_style) -> str`. Use `self._make_prompt(...)` to assemble the system prompt — that hook is where dictionary/profile/snippets/style get folded in.
3. Register in `voiceflow/llm/__init__.py:BACKENDS`.
4. Add the backend name to `config.VALID_BACKENDS` so `validate_config` accepts it, and update `onboarding.py:BACKENDS` if you want it in the wizard.

The `cleanup()` signature is part of the public extension contract — see invariants below.

### Voice commands / snippets / dictionary
These are runtime-only. No code changes needed for users; just `--add-command`, `--add-snippet`, `--add-word`. Defaults live in `commands.py:DEFAULT_COMMANDS`. If you change that count, update the README so `tests/test_voice_commands_count.py` stays green.

### Style preset
Adding a new style is a two-place edit:
- `voiceflow/styles.py:STYLE_PROMPTS` — the prompt suffix.
- `voiceflow/llm/base.py:STYLE_PRESETS` — the same suffix used during prompt assembly.
- `voiceflow/styles.py:STYLE_LABELS` — the human-readable label (with optional emoji).
- Add the id to `config.VALID_STYLES`.

The duplication between `STYLE_PROMPTS` and `STYLE_PRESETS` is a known minor wart (audit §3) — collapsing it is a v0.4 backlog candidate.

## 7. Concurrency model

OpenVoiceFlow is **single-process, multi-threaded, no asyncio**.

- **Main thread** runs the menubar/Tk GUI event loop, or sits in `Listener.join()` in CLI mode.
- **`pynput.Listener` thread** receives global key events and calls `OpenVoiceFlow.on_key_press / on_key_release` on a worker thread it manages itself.
- **Per-dictation daemon thread** is spawned in `stop_and_process()` to run `_process_audio` or `_process_streaming_result` so the keypress handler returns immediately and the next dictation can start.
- **Streaming reader thread** (`whisper-stream-reader`) is spawned by `StreamingTranscriber.start()` to consume `whisper-stream` stdout and fire the partial-text callback at ~2-3 Hz.
- **Auto-learner daemon thread** (`ovf-correction-watcher`) is spawned in `_process_*` after a successful paste; it samples the focused text field at 5/10/15/20/30 s and dies on its own.
- **Updater daemon thread** is spawned at startup by `updater.check_for_updates`.

All these threads are `daemon=True`, so quitting the app tears them down without explicit join. AppKit calls in `overlay.py` are dispatched to the main thread via `PyObjCTools.AppHelper.callAfter`.

## 8. Key invariants

Preserve these — most have explicit tests, the rest are load-bearing for trust.

1. **Audio never leaves the Mac.** Only `transcriber.py` and `streamer.py` touch audio, and both call local subprocess binaries. No HTTP client takes audio bytes anywhere.
2. **Every file under `~/.openvoiceflow/` is mode 600.** New persistence sites must go through `_secure_io.secure_write_json` / `secure_chmod`. Enforced by `tests/test_chmod_600.py`.
3. **Config migrations run at most once.** The cleanup-prompt, retired-Gemini,
   and v0.3.2 streaming-default migrations mutate and persist the stored dict.
   The streaming reset is fixed to schema v1 so future schema bumps do not
   override a later user opt-in. Tests in `tests/test_config_migration.py`,
   `tests/test_privacy_defaults.py`, and `tests/test_onboarding.py` pin this.
4. **`LLMBackend.cleanup` signature is fixed:** `cleanup(raw_text, context=None, app_context=None, override_style=None) -> str`. All backends conform; the orchestrator passes all four args. Don't break this.
5. **Voice commands run BEFORE LLM cleanup.** That's how `"new line"` becomes an actual newline at zero added latency, and the LLM sees the formatted text as input.
6. **Snippets run AFTER cleanup (well, instead of it) and BEFORE paste.** A matched snippet short-circuits the LLM call. Don't move that check.
7. **Privacy defaults are opt-in.** `log_transcripts` is `False` for fresh installs; `auto_learn` is `False` by default. `tests/test_privacy_defaults.py` pins this. Existing stored settings override DEFAULTS, except for explicitly documented one-time migrations such as the v0.3.3 reset of v0.3.2's unreliable streaming default.
8. **`from __future__ import annotations`** is present in every module so `str | None` annotations don't break Python 3.9. `tests/test_python39_compat.py` asserts this.

## 9. Build, ship, and CI

OpenVoiceFlow ships two ways:

- **PyPI / source install** — `pip install -e ".[all,dev]"` from a clone, or `pip install openvoiceflow` from PyPI. Drives the `openvoiceflow` console script entry point declared in `pyproject.toml`.
- **DMG download** — `bash build-dmg.sh` produces `dist/OpenVoiceFlow-<version>.dmg` and `release.yml` uploads it to the GitHub Release on tag push.

CI (`.github/workflows/ci.yml`) runs on `macos-latest` against Python 3.9 / 3.10 / 3.11. The pipeline is: install editable + dev extras → `ruff check voiceflow/` (blocking) → import smoke → assert `validate_config(DEFAULTS) == []` → `pytest -q`. A separate `build` job runs `python -m build` and `twine check` to keep the wheel/sdist publishable.

Version lives in two places — `pyproject.toml` (`[project] version`) and `voiceflow/__init__.py:__version__`. They must agree; the updater reads the latter and the wheel embeds the former.

## 10. What we deliberately don't have

- **No plugin system.** Backends are the one extension point and they live in-tree. Snippets/commands/dictionary are config, not code.
- **No remote config.** No call-home for prompt updates or model lists.
- **No async runtime.** Threads + subprocesses, no `asyncio` event loop.
- **No background daemon.** When the menubar app quits, the process exits; the LaunchAgent only re-launches on next login.
- **No telemetry** (this document describes the Python CLI; the native Mac app's opt-out usage sharing is documented in `PRIVACY.md` §7). Stats are local. The single network call the app initiates without a user action is `updater.check_for_updates` against `api.github.com/repos/shimoverse/openvoiceflow/releases/latest`, gated by `update_check: true` in config.
- **No analytics.** No Sentry, no PostHog, no anonymized usage events. The egress surface is exactly: whisper.cpp model download (HuggingFace, on first use), the LLM backend you chose, and the GitHub release check.

## See also

- [`README.md`](README.md) — user-facing overview and CLI cheat sheet.
- [`PRIVACY.md`](PRIVACY.md) — privacy posture in plain English.
- [`THREAT_MODEL.md`](THREAT_MODEL.md) — what we defend against and what we don't.
- [`AGENTS.md`](AGENTS.md) — contributor guide for AI coding agents.
