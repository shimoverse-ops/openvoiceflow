# Compliance posture

> Sibling docs: [`PRIVACY.md`](../PRIVACY.md) · [`SECURITY.md`](../SECURITY.md) · [`THREAT_MODEL.md`](THREAT_MODEL.md) · [`legal/DPA-template.md`](legal/DPA-template.md)

## TL;DR

OpenVoiceFlow is a source-available, single-developer macOS dictation tool. Personal and qualifying noncommercial use is available under the OpenVoiceFlow Personal and Reciprocal Source License 1.0; distributed derivatives and modified network versions must publish corresponding source under the same license, and organizational business use requires a separate commercial license even when source is published. It is a **self-managed personal-productivity utility**, not a SaaS. It is **not certified** for any compliance regime (SOC 2, ISO 27001, HIPAA, FedRAMP, PCI-DSS, etc.) and is **not designed for regulated environments**. It uses a **bring-your-own-key (BYOK)** model: when you pick a cloud LLM backend, *you* contract directly with that provider — OpenVoiceFlow is not a controller, processor, or sub-processor on your behalf. If you need a vendor with auditable controls and a real contractual layer, this is not that vendor.

---

## What we are NOT

| Regime | What it would mean | Why we don't qualify |
|---|---|---|
| **SOC 2 Type I / Type II** | An independent auditor attests that the vendor's controls are designed (Type I) and operated over time (Type II) against the AICPA Trust Services Criteria. | A small opt-out analytics/leaderboard API exists, but there is no managed dictation service, controls program, or auditor engagement. |
| **ISO 27001 / 27701** | Certified information-security (27001) or privacy (27701) management system, with documented risk treatment, internal audits, and management review. | No ISMS, no certification body engagement, no defined scope statement. |
| **HIPAA-covered** | The vendor has signed a Business Associate Agreement (BAA) and meets the HIPAA Security and Privacy Rules for handling Protected Health Information (PHI). | We do not sign BAAs, offer a HIPAA service, or assume PHI liability. |
| **FedRAMP** | Authorization to operate within US federal cloud environments at Low / Moderate / High impact levels. | Not a hosted service; no ATO; no agency sponsor. |
| **PCI-DSS** | Controls for handling cardholder data. | We never see, store, or transmit cardholder data — and you should not dictate it into any LLM. |
| **GDPR processor (on your behalf)** | A formal Article 28 processor relationship with a DPA, sub-processor list, and breach-notification commitments. | We do not offer a processor service or DPA. Dictated text flows directly from your Mac to the LLM provider you choose. A separate opt-out analytics API receives limited aggregate metrics described in `PRIVACY.md` §7; it never receives audio or dictated text. |

---

## What we ARE

- **Source available for audit.** The source is public on GitHub: <https://github.com/shimoverse/openvoiceflow>. Personal and qualifying noncommercial use follows the repository license; distributed derivatives and modified network versions must publish corresponding source under the same license, and business or other commercial use requires separate terms from Shimoverse Studios.
- **Transparent.** Build scripts, install scripts, and CI workflows are in-tree. The small analytics/leaderboard API is explicitly disclosed in `PRIVACY.md` §7; it never receives audio or dictated text.
- **BYOK.** You bring your own key for whichever LLM provider you choose; the contract is between you and that provider.
- **Local-first transcription.** Audio is processed on-device by WhisperKit. The audio never leaves your Mac.
- **User-owned content, on user-owned hardware.** Profile, dictionary, snippets, history, and optional logs live in the app's Application Support folder. We do not sync, mirror, or back up that content. If anonymous usage sharing is enabled (the default since v0.5.7), the app sends only the aggregate counters and pseudonymous fields listed in `PRIVACY.md` §7; never audio, dictated text, dictionary, snippets, or profile content.

---

## GDPR considerations (EU users)

When you choose a cloud LLM backend (OpenRouter, OpenAI, Anthropic, Groq), the cleaned transcripts you send for cleanup become **personal data being processed by that provider** under their terms.

- **You are the data controller.** You decide why and how the data is processed.
- **Your chosen LLM provider is the data processor.** They run the inference and retain (or don't retain) data per their terms.
- **OpenVoiceFlow is not in the dictated-content path.** We hand the request from your Mac to the API you configured. Separately, our opt-out analytics API handles only the limited aggregate metrics described in `PRIVACY.md` §7.

The lawful basis for processing is yours to determine. The three most likely to apply for personal/professional dictation:

- **Consent (Art. 6(1)(a))** — you knowingly typed the key in and clicked through onboarding.
- **Legitimate interest (Art. 6(1)(f))** — productivity tooling for your own work.
- **Contract (Art. 6(1)(b))** — performance of a contract you are party to (e.g., dictating a customer email).

If you need a Data Processing Addendum, sign one **with the LLM provider you chose**:

- Anthropic: <https://www.anthropic.com/legal/dpa>
- OpenAI: <https://openai.com/policies/data-processing-addendum>
- OpenRouter: <https://openrouter.ai/terms>
- Groq: contact Groq for their current DPA.

If your situation makes any external processor unacceptable (legal, contractual, or policy reasons), use the **Ollama** backend or leave cleanup **Off** — both keep transcripts on the Mac. To eliminate the app's other routine runtime egress, also disable anonymous usage sharing and automatic update checks in Settings. Initial model download and app installation still require their documented network sources.

---

## HIPAA

**Do not use OpenVoiceFlow for any workflow that involves Protected Health Information unless** *both* of the following are true:

1. Your chosen LLM provider offers a HIPAA-eligible service tier, **and**
2. **You** have signed a Business Associate Agreement (BAA) with that provider.

Provider state at time of writing (verify with the provider before relying on this):

- **Anthropic** — enterprise tiers offer BAAs.
- **OpenAI** — enterprise tiers offer BAAs.
- **OpenRouter** — verify coverage directly with OpenRouter before sending regulated data.
- **Groq** — does not offer BAAs at the time of writing.
- **Ollama** — runs entirely on your Mac; no third party is in the path. Whether that satisfies your covered-entity assessment is a question for your compliance officer.

**OpenVoiceFlow does not sign BAAs.** The project is one developer, not a Business Associate.

---

## For corporate IT teams considering deployment

OpenVoiceFlow can work for low-stakes BYOK-tolerant teams. It is **not** a managed-vendor solution. Before rolling it out:

- **Decide whether the LLM-backend data flow is acceptable** under your DLP, data-residency, and acceptable-use policies. Different employees may pick different backends; the deployment is only as restrictive as the locked configuration.
- **Consider Ollama-only deployments** to keep transcripts on-device. This eliminates the cloud LLM as a sub-processor entirely.
- **Pre-stage `whisper-cpp` and the model file** via your MDM (Jamf, Mosyle) or a `brew bundle` so the bootstrap doesn't pull from external networks at first launch on a managed Mac.
- **Ship a managed config** by writing `~/.openvoiceflow/config.json` during provisioning. For lock-down, pin: `update_check: false`, `log_transcripts: false`, `auto_learn: false`, `llm_backend: "ollama"`. (See [`PRIVACY.md`](../PRIVACY.md) for the full config-key list.)
- **Note that the current v0.3.6 hosted DMGs are Developer ID signed, Apple-notarized, and stapled.** MDM-aware orgs may still want to wrap the install differently (re-sign with an internal Developer ID, ship as a signed `.pkg`, or build from source in-house).
- **There is no enterprise key-management story.** Each employee's API keys land in their own `~/.openvoiceflow/config.json` (mode 600). No central rotation, no SSO, no SCIM.

If any of the above is a deal-breaker, OpenVoiceFlow is not the right fit and you should choose a vendor with a real procurement contract.

---

## Audit trail / observability

There is **no central dictation-content or admin-audit service**. The analytics/leaderboard API receives aggregate counters and pseudonymous fields when sharing is enabled, but it does not receive per-dictation content or provide organizational access reports or admin audit trails.

Per-machine, when `log_transcripts: true` is set by the user, daily transcript logs are written to `~/.openvoiceflow/logs/YYYY-MM-DD.{md,jsonl}` as **local plaintext files (mode 600)**. They live on the user's Mac and can be inspected, exported, or deleted by the user (or by an admin with filesystem access on a managed Mac).

---

## Records / retention

We do not centrally retain audio, dictated text, profile content, dictionary entries, snippets, or local history. The analytics/leaderboard service separately retains the limited aggregate fields described in `PRIVACY.md` §7 while sharing is enabled. On-device:

- Configuration, profile, dictionary, snippets, stats, and logs **exist until the user deletes them**.
- We do not sync, mirror, or back up any of these files. You delete a file, it's gone.
- Each LLM provider has its own retention policy for the transcripts you send through them. Read theirs.

---

## Changes

This document is versioned with the code. Material changes are surfaced under the relevant release in [`CHANGELOG.md`](../CHANGELOG.md). The sibling [`PRIVACY.md`](../PRIVACY.md) carries the matching privacy-side commitments.

---

## Cross-references

- [`PRIVACY.md`](../PRIVACY.md) — what data exists, where it goes, what you can opt out of.
- [`SECURITY.md`](../SECURITY.md) — supported versions, vulnerability reporting, scope.
- [`THREAT_MODEL.md`](THREAT_MODEL.md) — what we defend against and what we explicitly don't.
- [`legal/DPA-template.md`](legal/DPA-template.md) — a fill-in-the-blanks template for documenting an OpenVoiceFlow deployment in your own data-flow inventory.
