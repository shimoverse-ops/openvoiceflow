# Compatibility

This page lists what we test on, what we expect to work, and what we don't support. OpenVoiceFlow is an OSS project with no dedicated QA team, so "tested" means "exercised by maintainers on a real machine"; "expected to work" means "no known reason it wouldn't, but we haven't run it ourselves."

Source of truth for the version constraints: [`pyproject.toml`](../pyproject.toml).

---

## macOS

- **Tested (best-effort by maintainers):** macOS 13 Ventura, macOS 14 Sonoma, macOS 15 Sequoia.
- **Minimum supported:** macOS 12 Monterey. This is the floor because macOS 12 ships Python 3.9, which is our minimum interpreter (see below).
- **Apple Silicon (arm64):** native. We ship a separate arm64 DMG.
- **Intel (x86_64):** supported. We ship a separate x86_64 DMG.
- **Rosetta:** not required for either build.
- **macOS 26 "Tahoe":** the README references it under "Requirements"; it is not part of our regular test pass yet. Expected to work; please file an issue if it doesn't. `[verify]`

## Python

The package metadata enforces `requires-python = ">=3.9"`.

| Version  | Status                                |
| -------- | ------------------------------------- |
| 3.9      | Tested in CI (the floor).             |
| 3.10     | Tested in CI.                         |
| 3.11     | Tested in CI.                         |
| 3.12     | Not tested; expected to work.         |
| 3.13     | Not tested; expected to work.         |
| ≤ 3.8    | Explicitly unsupported (PEP 604 syntax). |

3.9 compatibility relies on `from __future__ import annotations` being present in every module that uses PEP 604 (`X | Y`) type syntax; that wiring is in place in v0.3.

## whisper.cpp

OpenVoiceFlow looks for a whisper.cpp binary by name and by path. Any of the following is accepted:

- **Binary name on `PATH`** (preferred order): `whisper-cli`, `whisper-cpp`, `whisper`.
- **Common install paths:** `/opt/homebrew/bin/whisper-cli`, `/opt/homebrew/bin/whisper-cpp`, `/usr/local/bin/whisper-cli`, `/usr/local/bin/whisper-cpp`, `~/whisper.cpp/build/bin/whisper-cli`.

The Homebrew formula `whisper-cpp` is what `install.sh` bootstraps and what we test against. A self-built `~/whisper.cpp/build/bin/whisper-cli` also works.

**Supported models** (downloaded on first run from HuggingFace):

- English-only: `tiny.en`, `base.en` (default), `small.en`, `medium.en`.
- Multilingual: `tiny`, `base`, `small`, `medium`, `large`.

## whisper-stream

Optional. Required only for the real-time streaming feature. We look for it at `/opt/homebrew/bin/whisper-stream` and via `shutil.which("whisper-stream")`. It is bundled with the Homebrew `whisper-cpp` formula, so a normal `brew install whisper-cpp` gives you both. Without it, OpenVoiceFlow falls back to classic batch transcription.

## LLM backends

OpenVoiceFlow talks to LLM providers over plain HTTPS via `urllib`. No vendor SDK is bundled.

| Backend     | Default model in v0.3            | Auth                         | Region        | Streaming response? | Notes                                                       |
| ----------- | -------------------------------- | ---------------------------- | ------------- | ------------------- | ----------------------------------------------------------- |
| `openrouter` | `google/gemma-4-31b-it`         | `openrouter_api_key` or `OPENROUTER_API_KEY` | OpenRouter global | No (single-shot) | Default for new installs; OpenAI-compatible endpoint.       |
| `groq`      | `llama-3.1-8b-instant`           | `groq_api_key`                | Groq global   | No (single-shot)    | Fastest cloud option; free tier with rate limits.           |
| `openai`    | `gpt-4o-mini`                    | `openai_api_key`              | OpenAI global | No (single-shot)    | Standard OpenAI Chat Completions endpoint.                  |
| `anthropic` | `claude-3-5-haiku-20241022`      | `anthropic_api_key`           | Anthropic     | No (single-shot)    | Standard Messages API.                                      |
| `ollama`    | `llama3.2` (user-configurable)   | none (localhost)              | local only    | No (single-shot)    | Talks to `http://localhost:11434`. Fully offline.           |
| `none`      | —                                | —                             | —             | —                   | Skip cleanup; pass raw whisper output through.              |

"Streaming response" here means whether the LLM streams tokens back. The audio-side streaming (live transcription) is independent and handled by whisper-stream.

## PyObjC / AppKit

`pyobjc-framework-Cocoa>=9.0` is required for:

- the floating overlay HUD that shows live transcription,
- frontmost-app detection (per-app voice styling),
- the auto-learner's Accessibility-API reads.

Install via `pip install -e ".[overlay]"` or `pip install -e ".[all]"`. When PyObjC is absent, those features degrade gracefully: no overlay, no per-app auto-styling, no auto-learn. The hotkey + transcribe + paste path still works.

## Tkinter

Required for the GUI onboarding wizard and the Know Me interview. It ships with the macOS system Python and with the `python.org` installer, so on a normal macOS setup you already have it. Headless Linux Pythons would not — but Linux is unsupported here anyway (see below).

## Network requirements

OpenVoiceFlow may contact these hosts. None are required after first-run setup if you stay offline-only with `--backend ollama` or `--backend none`.

| Host                                    | Why                                                          | Frequency                                |
| --------------------------------------- | ------------------------------------------------------------ | ---------------------------------------- |
| `huggingface.co`                        | Whisper model download (`ggml-base.en.bin` ≈ 142 MB).        | Once per chosen model.                   |
| `api.github.com`                        | Update check against the latest GitHub Release.              | On launch; opt out via `--update-check off`. |
| `raw.githubusercontent.com`, `formulae.brew.sh`, etc. | Homebrew, only when `install.sh` bootstraps `whisper-cpp`.   | Install time.                            |
| The LLM provider you picked             | Transcript cleanup (skip with `--backend none` or `ollama`). | Per dictation.                           |

## What we don't support

- **Windows.** No PortAudio/WASAPI work, no rumps, no PyObjC.
- **Linux.** Same reason; the entire UI surface is AppKit.
- **iOS / iPadOS / Android.** Not a mobile app.
- **Web.** No browser build; the dictation model is system-wide hotkey + paste.

### Behavior on unsupported operating systems

Unsupported does not mean "crashes". If you pip-install OpenVoiceFlow on
Linux or Windows and run it, the CLI detects the OS at startup
(`voiceflow/platform_support.py`), prints an explanation of why dictation
cannot work there plus uninstall guidance (`pip uninstall openvoiceflow`,
`rm -rf ~/.openvoiceflow`), and exits with code 1 — no traceback, no
background process, no config files written. Diagnostic commands
(`--doctor`, `--show-config`, `--version`) keep working so you can inspect
state before removing it. A CI job on `ubuntu-latest` pins this guarantee.

## Doctor checks (`openvoiceflow --doctor`)

The self-check covers, in order: operating system + version (fails below
macOS 12, notes releases newer than our tested range), architecture
(warns when Python runs under Rosetta or when Intel Homebrew is installed
on Apple Silicon — both silently cost you Metal acceleration), Homebrew,
whisper.cpp, the whisper model file, the LLM backend/API key, PyObjC,
tkinter, the three macOS permissions dictation depends on (Microphone,
Accessibility, Input Monitoring — each with a click-to-fix System
Settings link), and config file modes. The Microphone check needs
`pyobjc-framework-AVFoundation` to give a definitive answer; without it
the doctor reports that macOS will prompt on first recording.

## "What about X?" mini-FAQ

- **Linux PortAudio support?** Out of scope for v0.3. The transcription core (`sounddevice` + whisper.cpp) is portable in principle, but the menubar, overlay, and Accessibility-API integrations are AppKit-only.
- **Windows WASAPI support?** Out of scope for v0.3. Same reasoning.
- **VS Code extension instead of the menubar?** Out of scope for v0.3. The product is a system-wide dictation tool, not an editor extension.
- **whisper.cpp Vulkan backend?** Out of scope for v0.3. We rely on whichever backend the Homebrew formula was built with (Metal on Apple Silicon).
- **CoreML acceleration?** Out of scope for v0.3. Possible future work once the Homebrew formula ships CoreML by default.
