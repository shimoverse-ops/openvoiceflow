![OpenVoiceFlow](native/assets/readme-banner.png)

# OpenVoiceFlow

**Free for personal use only: source-available voice dictation for macOS. Hold a key, talk, release — polished text lands in whatever app you're in. Your audio never leaves your Mac.**

[![macOS 14+](https://img.shields.io/badge/macOS-14%2B-black)](https://openvoiceflow.com/download.html)
[![License](https://img.shields.io/badge/license-Personal%20%26%20Reciprocal%201.0-amber.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/shimoverse/openvoiceflow?filter=native-v*&label=release)](https://github.com/shimoverse/openvoiceflow/releases)

People speak at roughly 150 words a minute and type at roughly 40. OpenVoiceFlow exists because closing that gap shouldn't cost $144 a year or require streaming your voice to someone's cloud. We think voice input should eventually be a default feature of every operating system; until it is, this is our contribution — and contributions are welcome.

## Install

**[Download the DMG](https://openvoiceflow.com/download.html)** — one universal build for Apple Silicon and Intel, Developer-ID signed and Apple-notarized. Drag it to Applications, open it, and a one-minute setup walks you through permissions and a speech-engine choice.

Requires macOS 14 (Sonoma) or newer. On macOS 12–13, the download page offers a retained legacy build.

## What it does

- **Push-to-talk dictation** — hold your chosen key (default: `fn`), speak, release. Text pastes at your cursor in any app.
- **On-device transcription** — [WhisperKit](https://github.com/argmaxinc/WhisperKit) runs Whisper locally, from `tiny` (39 MB) to `large-v3-turbo`. Audio is processed in memory and discarded; nothing is uploaded, nothing is recorded when the key isn't held.
- **Live feedback** — your words appear in the HUD as you speak, so you know it hears you.
- **Optional AI cleanup** — off by default (raw transcript, fully local). Turn it on to polish grammar and filler words via OpenRouter, OpenAI, Anthropic, Groq, or a fully-local Ollama model. Keys live in the macOS Keychain. Only cleaned *text* ever touches an API — never audio.
- **Personal dictionary, snippets, per-app styles** — teach it names and jargon once; spoken shortcuts expand to full text; casual in Slack, formal in Mail.
- **Auto-updates** — signed Sparkle updates from [openvoiceflow.com](https://openvoiceflow.com), verified with an EdDSA key pinned in the app.

No account or consumer subscription — see [the mission](https://openvoiceflow.com/#mission). Anonymous aggregate usage sharing is on by default and takes one switch to turn off; it never includes dictation text (see [PRIVACY.md](PRIVACY.md) §7).

## Build from source

You need a Mac on macOS 14+ with Xcode 16.4+ and [XcodeGen](https://github.com/yonaskolb/XcodeGen) (`brew install xcodegen`).

```bash
git clone https://github.com/shimoverse/openvoiceflow.git
cd openvoiceflow
bash native/scripts/run-local.sh
```

That generates the Xcode project from `native/project.yml`, builds an ad-hoc-signed debug app, and launches it. (Ad-hoc rather than unsigned, because macOS ties the Accessibility and Input Monitoring grants to a code signature — unsigned, the hotkey silently never fires.) For the signed + notarized release pipeline, see [`native/BUILD_RUNBOOK.md`](native/BUILD_RUNBOOK.md).

## How it's put together

Everything shipping lives in `native/Sources/OpenVoiceFlow/` — a small Swift/SwiftUI app with no storyboard and no dependencies beyond WhisperKit and Sparkle:

| Piece | File | Job |
|---|---|---|
| App + menu bar | `OpenVoiceFlowApp.swift` | `MenuBarExtra`, login item, Dock policy |
| State machine | `AppController.swift` | idle → recording → transcribing → cleaning → pasting |
| Hotkey | `HotkeyEngine.swift` | CGEvent tap; one key watched, everything else passes through |
| Audio | `AudioCapture.swift` | 16 kHz mono capture, level metering |
| Transcription | `Transcriber.swift` | WhisperKit lifecycle, model download, live partials |
| Cleanup | `CleanupProvider.swift` | the five backends behind one protocol |
| Paste | `Paster.swift` | ⌘V synthesis with clipboard restore |
| HUD | `HUDController.swift` | the floating waveform pill |
| Dashboard | `DashboardView.swift` | history, stats, dictionary, snippets, styles, settings |
| Onboarding | `OnboardingView.swift` | permissions, engine choice, first dictation |

The repo also contains the **legacy Python app** (`voiceflow/`, ≤ 0.3.6) that the native app replaced. It is end-of-life, receives no security fixes, and its defaults differ from current policy — kept only for reference and for the macOS 12–13 fallback build. Don't start there.

## Contributing

Start with [CONTRIBUTING.md](CONTRIBUTING.md). The short version: pull requests are welcome, CI compiles the Swift app and runs the website tests on every PR, and the maintainer reviews everything. Good first contributions: try the app and file honest bug reports, add an XCTest target (we want one), improve accuracy for your language.

## Privacy and security

The one-page version: audio on-device always; text to a cloud only if you enable cleanup; keys in the Keychain; anonymous aggregate usage sharing on by default, one switch to turn off, never dictation text. Full statements: [PRIVACY.md](PRIVACY.md) · [SECURITY.md](SECURITY.md) · [threat model](docs/THREAT_MODEL.md). To report a vulnerability, see [SECURITY.md](SECURITY.md).

## License

OpenVoiceFlow is source-available under the **[OpenVoiceFlow Personal and
Reciprocal Source License 1.0](LICENSE)**. Personal use only is free under those
terms. Every integration, fork, derivative, or modified version must visibly
credit OpenVoiceFlow and link to the original source code. If you distribute a
derivative or let others use a modified version over a network, you must publish
its complete source under the same license; the free license does not allow
closed-source derivatives. Commercial or organizational use requires separate
written permission or a separate written license from Shimoverse Studios even when the
source is published. Contact **contact@openvoiceflow.com** before commercial or organizational
use.

Copyright © 2025–2026 **Shimoverse Studios**. Keep the required notices with every
copy. The source license does not grant rights to the OpenVoiceFlow name or
logo; derivative distributions and integrations must rebrand where applicable
and state **"Based on OpenVoiceFlow by Shimoverse Studios"** with a working link
to the [original source code](https://github.com/shimoverse/openvoiceflow).
See [LICENSING.md](LICENSING.md), [TRADEMARKS.md](TRADEMARKS.md),
[docs/legal/LEGACY_MIT_PORTIONS.md](docs/legal/LEGACY_MIT_PORTIONS.md), and
[docs/legal/THIRD_PARTY_NOTICES.md](docs/legal/THIRD_PARTY_NOTICES.md).
