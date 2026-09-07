# Security Policy

OpenVoiceFlow is a source-available macOS voice-dictation app. Personal use only
is available under the
[OpenVoiceFlow Personal and Reciprocal Source License 1.0](LICENSE). Commercial
or organizational use, including selling or bundling the software, requires
separate written permission or a separate written license from Shimoverse Studios;
contact **contact@openvoiceflow.com**. This document explains
which versions get security fixes, how to report a vulnerability, what to expect from us,
and what is in scope.

Distributed derivatives and modified network versions must publish complete
corresponding source under the same license. Security reporting and licensing
are separate. See [LICENSING.md](LICENSING.md) for source-sharing,
prior-version, third-party, and brand details.

This is a **single-maintainer project**. Response is best-effort, on a human schedule. We
do **not** offer an SLA, and the project is **not** SOC 2 / ISO 27001 / HIPAA certified.
If your organization requires those, request separate permission before use;
OpenVoiceFlow is probably not the right fit.

---

## Supported versions

Only the current minor line gets security fixes. Older lines are frozen at their last
release.

| Version | Supported          | Notes                                                       |
|---------|--------------------|-------------------------------------------------------------|
| 0.5.x   | ✅ Yes             | Current native line. Fixes ship as in-app updates.          |
| 0.4.x   | ❌ No              | Superseded native line. Update in-app to 0.5.x.             |
| 0.3.x   | ❌ No              | EOL — the legacy Python CLI line.                           |
| ≤ 0.2.x | ❌ No              | Frozen.                                                     |

Only 0.5.x is supported. We do not backport.

---

## Reporting a vulnerability

**Please do not open a public GitHub issue for security problems.**

### Preferred: GitHub private security advisory

Use GitHub's private vulnerability reporting:

> https://github.com/shimoverse/openvoiceflow/security/advisories/new

This goes to the maintainer privately, lets us collaborate on a fix in a private fork,
and is the easiest path to a CVE if one is warranted.

### If you can't use GitHub advisories

GitHub private vulnerability reporting is currently the only private channel.
If you have no GitHub account (or policy forbids it), open a plain GitHub issue
that says only "security report — please open a private channel" with **no
technical details**, and the maintainer will follow up. A dedicated security
email (with PGP key) will be published here if one is established.

### What to include

The more of this we have, the faster we can act:

- Affected version (`openvoiceflow --version`).
- macOS version and chip (Apple Silicon vs. Intel).
- A clear description of the issue and the impact you believe it has.
- Steps to reproduce, or a proof-of-concept.
- Any logs, stack traces, or screenshots that help.
- Whether you'd like credit in the release notes, and under what name/handle.

---

## Disclosure expectations

| Stage                     | Target                                                    |
|---------------------------|-----------------------------------------------------------|
| Acknowledgement           | Within **5 business days** of receipt.                    |
| Triage + initial assessment | Within **10 business days**.                            |
| Fix + coordinated disclosure window | **90 days** from the report, unless we agree otherwise. |
| CVE                       | We'll request one via GitHub if the issue is accepted and warrants it. |
| Credit                    | In the release notes for the fix, if you'd like it.       |

If we can't meet these targets (single-maintainer realities), we'll tell you and propose
a new timeline rather than go silent.

We ask, in return:

- Don't publicly disclose before the fix ships, or before the 90 days are up — whichever
  comes first.
- Don't pivot a vulnerability into actual user harm (no exfiltrating other users' data,
  no running the issue against users who haven't consented).
- Good-faith research is welcome and won't be met with legal threats.

No bug bounty. We can't pay; the project earns $0.

---

## What's in scope

- The native macOS app — everything under `native/` (the shipped `OpenVoiceFlow.app`).
- The Sparkle update feed and release pipeline (`.github/workflows/release-native.yml`, `native/scripts/`).
- The website and its download/appcast serving (`docs/`, `vercel.json`).
- The GitHub Actions workflows under `.github/workflows/`.
- The legacy Python package (`voiceflow/`, `install.sh`, `build-dmg.sh`) is EOL: reports are
  welcome for awareness, but fixes ship only if the macOS 12–13 fallback is affected.

Typical in-scope issues: path traversal or command injection in any of the above; a
config or env var that lets a local attacker escalate privileges or read another
user's files; API keys / transcripts / profile data ending up world-readable, leaked
over the network, or shipped somewhere we don't document; a compromised release
pipeline; a malicious LLM response or clipboard payload escaping its intended
boundary (arbitrary code execution rather than just bad text).

## What's out of scope

These are real concerns, but **not** ours to fix — please report them upstream:

- **Third-party LLM providers** (OpenRouter, OpenAI, Anthropic, Groq, Ollama). Report to
  the provider. We just send HTTPS requests to their published APIs.
- **whisper.cpp / ggml / whisper-stream.** Report upstream at
  https://github.com/ggerganov/whisper.cpp.
- **Homebrew** and packages it installs. Report to Homebrew or the package's upstream.
- **macOS itself** — kernel issues, Accessibility-API bypasses at the OS level, code
  signing infrastructure, Keychain. Report to Apple.
- **Your own LLM prompts.** `llm_prompt` is config-controlled; a hostile prompt is a
  config-tampering risk against yourself, not a vendor bug. Self-jailbreak is between
  you and your LLM.

If you're not sure, send it anyway and we'll route it.

---

## Threat model

A short pointer, not a full document. The full version lives at
[`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md).

OpenVoiceFlow holds three strong privileges on the user's Mac:

1. **Microphone access** — to capture audio for whisper.cpp.
2. **Accessibility API** — to paste cleaned text at the cursor and (when enabled) to
   read the focused text field for ~30 seconds after a paste so the auto-learner can
   notice user corrections.
3. **Apple Events** — to detect the frontmost app for per-app context.

Together those mean a compromise of OpenVoiceFlow is roughly equivalent to a
compromise of the user's interactive desktop session. The threat model documents how
we limit blast radius (local-only audio, default-off transcript logging, default-off
auto-learner, mode-600 config files, no dictation content in the Mac app's opt-out usage
sharing) and what we explicitly don't
defend against (a malicious operator who already has shell access as the user; a user
who configures a hostile `llm_prompt`; supply-chain compromise of a chosen LLM
provider).

---

## Data minimization defaults

A v0.3.0 fresh install ships with:

- `log_transcripts: false` — no daily JSONL/MD transcript logs are written.
- `auto_learn: false` — the Accessibility-API correction watcher is dormant until you
  opt in via the Know Me interview.
- `~/.openvoiceflow/*.json` — written with mode `600` (owner read/write only).
- **No telemetry.** No usage pings, no crash reports, no install beacons. This applies to the
  Python CLI described in this section. The native Mac app *does* share anonymous aggregate
  usage counters (opt-out, on by default since 0.5.8) — see `PRIVACY.md` §7 for exactly what
  it sends and how to turn it off.
- `update_check: true` — the only outbound request we make on your behalf, hitting
  `https://api.github.com/repos/shimoverse/openvoiceflow/releases/latest` once per
  launch. Set `update_check: false` in `~/.openvoiceflow/config.json` to disable.

Everything else — sending cleaned transcripts to a cloud LLM, indexing daily logs with
`--search`, etc. — is opt-in or follows from a configuration choice the user made.

The README's "Privacy at a glance" panel is the authoritative summary; this section
exists so a security reviewer doesn't have to take a marketing page at face value.

---

## CVE history

No advisories yet.

When we have one, it'll be linked here, in the relevant `CHANGELOG.md` entry, and as a
GitHub Security Advisory on the repo.

---

## Notes for reviewers

- The project uses the OpenVoiceFlow Personal and Reciprocal Source License 1.0; the maintainer is Shimoverse Studios (see `LICENSE` and `LICENSING.md`).
- The repo lives at `github.com/shimoverse/openvoiceflow` today and may move to a
  personal account before public release. URLs in this file will be updated if so.
- This document is part of the v0.3 readiness bundle. Pair reading:
  [`PRIVACY.md`](PRIVACY.md), [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md),
  [`COMPLIANCE.md`](COMPLIANCE.md).
