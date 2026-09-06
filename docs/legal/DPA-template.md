# OpenVoiceFlow deployment record (DPA-style template)

> Sibling docs: [`../../PRIVACY.md`](../../PRIVACY.md) · [`../COMPLIANCE.md`](../COMPLIANCE.md) · [`../../SECURITY.md`](../../SECURITY.md)

## Purpose of this template

This is a **fill-in-the-blanks template** small businesses can use to document an OpenVoiceFlow deployment inside their own data-flow inventory, vendor register, or DPIA workpapers. It captures who does what, what data flows where, and which third parties are in the path.

**It is not a contract with the OpenVoiceFlow project.** OpenVoiceFlow is a source-available, single-developer tool. Organizational business use requires a separate commercial software license from Shimoverse Studios, but that software license does not make the project your privacy counterparty, controller, processor, or sub-processor. When you choose a cloud LLM backend, the data-processing relationship is between **your organization** and **the LLM provider you chose** (see [`../COMPLIANCE.md`](../COMPLIANCE.md) for links to each provider's DPA).

Treat this as your record, not ours. Replace each italicized placeholder, then keep it with your other vendor documentation. Have your lawyer sanity-check it before relying on it.

---

## 1. Parties and roles

| Role | Filled in by you |
|---|---|
| **Controller** (your organization) | *e.g. Acme Ltd, registered at …, Data Protection contact: …* |
| **End users** (whose dictation flows through the tool) | *e.g. Acme employees on macOS workstations* |
| **Chosen LLM provider** (data processor for cleaned transcripts) | *e.g. Anthropic / OpenAI / Google / Groq / Ollama (local) / none* |
| **Region of LLM-provider processing** | *e.g. US / EU / on-device* |
| **Tool** | OpenVoiceFlow `<version>` (record the applicable noncommercial or commercial license; not a data-processing counterparty) |
| **Date of this record** | *YYYY-MM-DD* |
| **Owner of this record** | *Name, role* |

---

## 2. Configuration choices that affect data flow

These are the OpenVoiceFlow settings (in `~/.openvoiceflow/config.json` on each user's Mac) that materially change what leaves the device. Record what you've locked or recommended.

| Setting | Default in v0.3 | Your deployment | Effect |
|---|---|---|---|
| `llm_backend` | `openrouter` | *e.g. `ollama`* | Determines which third party (if any) sees transcripts. |
| `log_transcripts` | `false` | *true / false* | Writes daily plaintext transcript logs to `~/.openvoiceflow/logs/`. |
| `auto_learn` | `false` | *true / false* | Reads the focused text field via macOS Accessibility API for ~30s after each paste. |
| `update_check` | `true` | *true / false* | Pings GitHub once per launch to check for new releases. |
| `selected_text_context` | `true` | *true / false* | Sends currently selected text to the LLM along with the dictation. |
| **Retention defaults** | Files persist until deleted by the user. | *e.g. "users instructed to clear `logs/` weekly"* | We do not auto-rotate. |
| **Ollama-only mode** | No | *yes / no* | If yes, no transcript ever leaves the Mac. |

---

## 3. Data categories processed

| Category | Where it lives | Who can see it |
|---|---|---|
| **Audio (voice)** | RAM during capture; temp WAV deleted in `finally` block. Never written to disk past the dictation. | The user only. Never leaves the Mac. |
| **Cleaned transcripts** | In transit to the chosen LLM provider; response pasted to the user's cursor. | The user + the chosen LLM provider (per their terms). If `log_transcripts: true`, also a local plaintext file. |
| **User profile** (`profile.json`) | `~/.openvoiceflow/profile.json`, mode 600. Name, occupation, industry, frequently used names. | The user. Injected into LLM system prompt at every cleanup call. |
| **Personal dictionary** (`dictionary.json`) | `~/.openvoiceflow/dictionary.json`, mode 600. May contain names. | The user. Injected into LLM system prompt. |
| **Snippets** (`snippets.json`) | `~/.openvoiceflow/snippets.json`, mode 600. May contain signatures, contact details, boilerplate. | The user. Expanded locally; never sent to the LLM. |
| **Daily transcript logs** (opt-in) | `~/.openvoiceflow/logs/YYYY-MM-DD.{md,jsonl}`, mode 600. | The user (and anyone with filesystem access on that Mac). |
| **Stats** (`stats.json`) | `~/.openvoiceflow/stats.json`, mode 600. Counters only (dictations, words, time saved). | The user. |

---

## 4. Sub-processor list

| Sub-processor | Purpose | Frequency | Opt-out |
|---|---|---|---|
| **Hugging Face** | Initial download of the `ggml-*.bin` Whisper model file. | Once, at first run. | Pre-stage the model file via MDM and skip the download. |
| ***Chosen LLM provider*** | Cleanup of transcribed text. | Per dictation, when an LLM backend is configured. | Switch `llm_backend` to `ollama` or `none`. |
| **GitHub** | Update check (`api.github.com/repos/shimoverse/openvoiceflow/releases/latest`). | Once per launch. | Set `update_check: false`. |
| **Homebrew** | Install of `whisper-cpp` and `whisper-stream` binaries. | Once, at install. | Pre-install via your MDM. |

OpenVoiceFlow itself is **not** a sub-processor. The maintainer does not receive any of your data.

---

## 5. Security measures (technical and organizational)

In v0.3, OpenVoiceFlow ships with the following on each Mac:

- `~/.openvoiceflow/*.json` written with **mode 600** (owner read/write only).
- **No telemetry in the v0.3 CLI.** No usage pings, no crash reports, no install beacons. The
  native Mac app (0.5.8+) shares anonymous aggregate usage counters by default — a random
  device ID, counters, and app version, never Customer Personal Data or dictation content —
  and a single setting disables it. Controllers who require zero outbound usage data should
  turn it off as part of deployment.
- **Update check is opt-out-able** via `update_check: false`.
- **Audio never leaves the Mac.** Whisper.cpp processes locally; temp WAV is deleted in the `finally` block of each dictation.
- **No central server.** There is nothing for the maintainer to compromise that would expose your data.
- **Public source** is auditable at <https://github.com/shimoverse/openvoiceflow>; see [`../../LICENSING.md`](../../LICENSING.md) for the applicable use rights.

Your organization adds (fill in):

- *Code signing of the DMG with our internal Developer ID:* *yes / no / N/A.*
- *MDM enforcement of `update_check`, `log_transcripts`, `auto_learn`, `llm_backend`:* *yes / no.*
- *Endpoint detection / DLP coverage on macOS hosts:* *yes / no — vendor:* …
- *Disk encryption (FileVault) required org-wide:* *yes / no.*
- *Microphone and Accessibility permission grants reviewed by IT:* *yes / no.*

---

## 6. Note on amendments

This template is a snapshot. As your deployment evolves — different LLM provider, change to Ollama-only, log retention policy added, MDM enforcement strengthened — replace the affected sections in place and bump the date in §1. You don't need to notify the OpenVoiceFlow project; we are not a counterparty, and there is nothing on our side to update.

If you change which LLM provider you use, also update or sign a fresh DPA **with the new provider**. Their terms are the binding ones; this template only records what your deployment looks like.

---

## Cross-references

- [`../COMPLIANCE.md`](../COMPLIANCE.md) — full compliance posture (what we are, what we are not, GDPR/HIPAA notes).
- [`../../PRIVACY.md`](../../PRIVACY.md) — what data exists, where it goes, what you can opt out of.
- [`../../SECURITY.md`](../../SECURITY.md) — supported versions and vulnerability reporting.
