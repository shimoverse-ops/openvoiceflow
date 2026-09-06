# OpenVoiceFlow — Threat Model

> **Audience:** security reviewers, contributors, and curious users who want to know what this tool *does* and *doesn't* try to defend against.
>
> **Scope:** OpenVoiceFlow v0.3 (`v0.3-readiness` branch). macOS only. Single-user personal-productivity tool.
>
> **Format:** STRIDE-lite. Plain English. STRIDE category labels appear in parentheses, not as the primary frame.

---

## 1. System overview

OpenVoiceFlow is a five-step pipeline that turns held-hotkey speech into pasted text:

1. **Hotkey held** — `pynput` global listener detects the configured modifier (default Right Cmd / Right Alt) and starts a recording.
2. **Record audio** — `recorder.py` writes a temp WAV to `/tmp` while the key is held; the file is deleted in a `finally` block once transcription completes.
3. **Local transcription** — `transcriber.py` shells out to a validated `whisper-cli` / `whisper-cpp` binary (see §4 Spoofing). Audio never leaves the Mac.
4. **Optional LLM cleanup** — `llm/base.py` builds a system prompt (default + style + dictionary + snippets + profile) and sends `transcript + optional selected-text context + optional app context` to the user's chosen backend: OpenRouter, Groq, OpenAI, Anthropic, Ollama (local), or `none`.
5. **Paste at cursor** — `system.py:paste_text` writes the cleaned text to the pasteboard and synthesizes Cmd+V via `osascript`. **Optional:** `system.py:log_transcript` appends to `~/.openvoiceflow/logs/YYYY-MM-DD.{md,jsonl}` (off by default in v0.3). **Optional:** `learner.py` watches the focused text field for 30 s post-paste and learns single-word substitutions (off by default in v0.3).

Everything runs as the logged-in user. There is no daemon, no privileged helper, and no remote server we operate.

---

## 2. Trust boundaries

| # | Boundary | One-line description |
|---|---|---|
| **TB-1** | User → Mac (local process) | Spoken audio + keypresses cross from the human into a process running with the user's UID. |
| **TB-2** | Mac → LLM provider | Cleaned-up prompt + transcript + optional selected-text context flows over HTTPS to the chosen cloud backend (OpenRouter, Groq, OpenAI, Anthropic). **Exception: Ollama also runs locally** (`http://localhost:11434`), so this boundary collapses for Ollama users. |
| **TB-3** | Mac → HuggingFace | One-time `ggml-*.bin` model download over HTTPS. Re-fetched only if the user changes models. |
| **TB-4** | Mac → GitHub API | `updater.py` calls `api.github.com/repos/shimoverse/openvoiceflow/releases/latest` on launch. **Opt-out** via `--update-check off` (`config["update_check"] = false`). No auth header, no PII in the request — it's a GET on a public endpoint. |

If a user runs `--backend ollama` and `--update-check off`, **only TB-1 and TB-3 (and TB-3 only on first launch / model change) are crossed**. That is the strongest privacy posture currently shippable.

---

## 3. Assets

What is worth protecting, in roughly descending order of sensitivity:

| Asset | Where it lives | Sensitivity | Why it matters |
|---|---|---|---|
| **API keys** | `~/.openvoiceflow/config.json` (mode 600 in v0.3) | 🔴 Highest | Stolen OpenRouter / OpenAI / Groq / Anthropic keys = direct billing fraud + access to whatever else the user uses that key for. |
| **User's spoken audio** | RAM during recording; `/tmp/*.wav` for ~1 second; deleted in `finally` | 🔴 High | Highly personal. **Local-only** — audio never leaves the Mac, so the threat surface is local code execution / disk forensics, not network. |
| **Cleaned transcript text** | RAM during cleanup; sent to chosen LLM provider over TLS | 🔴 High | This is *what the user is dictating* — emails, code, messages. Egress to the chosen LLM is a deliberate user choice. |
| **Daily transcript logs** | `~/.openvoiceflow/logs/YYYY-MM-DD.{md,jsonl}` (mode 600); **off by default in v0.3** | 🔴 High | Every word the user has dictated, indexed by `--search`. Off by default mitigates this; the user must opt in. |
| **User profile** | `~/.openvoiceflow/profile.json` (mode 600) | 🟡 Medium | PII: name, employer, colleague names, tools, communication style. Not transmitted; appended into the LLM system prompt at every call. |
| **Personal dictionary** | `~/.openvoiceflow/dictionary.json` (mode 600) | 🟡 Medium | May contain personal names and idiosyncratic vocabulary; included in LLM system prompt. |
| **Voice snippets** | `~/.openvoiceflow/snippets.json` (mode 600) | 🟡 Medium | May contain email signature, address, sensitive boilerplate. |
| **Voice commands** | `~/.openvoiceflow/config.json` (mode 600) | 🟢 Low | Mostly action shortcuts ("new line", "paragraph"). Limited PII risk. |
| **Stats** | `~/.openvoiceflow/stats.json` (mode 600) | 🟢 Low | Aggregate counters (dictations, words, time saved). No PII. |

Everything under `~/.openvoiceflow/` is now `chmod 600` thanks to `voiceflow/_secure_io.py:secure_chmod` and `secure_write_json`, called from every save site.

---

## 4. Threats by category (STRIDE)

### Spoofing — pretending to be something you're not

| Threat | Likelihood | Impact | Mitigation today | Residual risk |
|---|---|---|---|---|
| Malicious binary masquerading as `whisper-cli` on the user's `PATH`. A package named "whisper" earlier on `PATH` could intercept audio paths and exfiltrate the WAV. | Low | High (audio leak) | `transcriber.py:_is_whisper_cpp()` runs `<binary> --help`, greps the output for `ggml` / `whisper-cpp` / `whisper.cpp`. Plain `whisper` is **only** accepted if it passes that check. The two preferred names (`whisper-cli`, `whisper-cpp`) are looked up first; explicit Homebrew paths are checked next; bare `whisper` is the last resort. | An attacker who can plant a binary on `PATH` named `whisper-cli` can still bypass this check. That requires write access to a `PATH` directory, which already implies user-equivalent privilege (see "Out of scope"). |
| Phishing site impersonating an LLM provider key page. User pastes a stolen-key into `--set-key`. | Medium | High | Out of scope for the app. Mitigated by user awareness + provider 2FA. | We don't validate that a key actually belongs to the named provider. |

### Tampering — modifying data or code in flight or at rest

| Threat | Likelihood | Impact | Mitigation today | Residual risk |
|---|---|---|---|---|
| A process modifies `~/.openvoiceflow/config.json` to change `*_api_base` (where supported) or alter `llm_prompt` so transcripts are redirected / exfiltrated. | Low | High (silent transcript leak) | `config.json` is `chmod 600` (`_secure_io.secure_chmod`), so non-root other-user processes can't read or write it. The user is the only mutator. | **Malware running as the user can still rewrite it.** The FS doesn't protect against same-UID attackers; see "Out of scope". |
| `llm_prompt` poisoned to instruct the LLM to echo previous transcripts or sensitive context fragments back to the model in some adversarial way. | Low | Medium | The prompt is config-controlled; only the user's own processes can write it (mode 600). | If an attacker has gotten this far, they already have the keys + logs. |
| Tampering with the downloaded `ggml-*.bin` model file mid-download. | Low | Medium | HTTPS to HuggingFace. **No checksum verification today** — flagged below as a v0.4 ask. | An on-path attacker who can break TLS could swap the model. Realistically: state-level attacker, out of scope. |

### Repudiation — "I didn't do that"

Not a meaningful concern for a personal tool. The user is both the actor and the auditor; there's no one to repudiate to.

When `log_transcripts` is opt-in *on* (off by default in v0.3), the daily JSONL+MD logs in `~/.openvoiceflow/logs/` provide a timestamped local trail of every dictation, which a user could use to reconstruct what they did and when. That is *the user's audit log*, not anyone else's.

> **Scope note (2026-07):** the TODOs below were filed against the legacy
> Python app. The native rewrite (0.4.0+) resolved some by construction —
> paste synthesis moved to CGEventPost (A, partially), WhisperKit manages
> model downloads inside the app sandbox path (C) — while B, D, E, F carry
> forward as open items against `native/`. A full re-run of this model
> against the Swift app is tracked work, not yet done; treat the analysis
> below as historical until then.

### Information disclosure — leaking what should stay secret

This is the largest category for OpenVoiceFlow.

| Threat | Likelihood | Impact | Mitigation today | Residual risk |
|---|---|---|---|---|
| **World-readable artifacts** under `~/.openvoiceflow/` — config.json (keys), profile.json (PII), dictionary.json, snippets.json, logs. | High before v0.3 | High | **Fixed in v0.3.** All save paths now go through `_secure_io.secure_chmod` / `secure_write_json` (`chmod 600`). Verified at `system.py:53,64,73`, plus profile/dictionary/snippets/config save sites. | Same-UID attacker still wins; see "Out of scope". A `chmod 600` guarantees no *other* local user account can read these files. |
| **Transcripts to cloud LLM provider** (OpenRouter default, Groq, OpenAI, Anthropic). | High by design | Medium-High | **Documented behavior**, not a bug. The user picks their backend. Ollama is offered as the fully-local option; `--backend none` skips cleanup entirely. README hero copy now says "audio stays local" rather than "your data never leaves your Mac" — `transcripts` are explicitly disclosed. | The user's choice + the LLM provider's privacy policy are the only protection beyond TLS. |
| **Auto-learner reads the focused text field via macOS Accessibility API for 30 seconds after every paste** (`learner.py`). For 5 sample intervals (5/10/15/20/30 s) the watcher reads `kAXValueAttribute` of whatever is focused. | Medium | High (could read text the user did not dictate) | Default-off (`config.py:85 → "auto_learn": False`). The CLI flag `--auto-learn on` and the menubar toggle are explicit consent gates. Watcher stops early if the user switches apps. Only learns *single-word substitutions* with similarity ≥ 0.4 (`learner.py:39`). | If a user opts in and then switches focus to a sensitive field within 30 s without the app-switch detection firing (e.g., focus stays inside the same app), the watcher reads that field's content. Mitigation idea for v0.4: only sample if focused field's `kAXRoleAttribute` matches the original. |
| **Wrong-app paste race** — during LLM cleanup (typically 200-1500 ms) the user can switch focus; `paste_text` then types into whatever is now frontmost. If the new frontmost is a public text field (Slack channel, Tweet composer), the dictation leaks. | Medium | High | Today: none in code. The osascript `keystroke "v" using command down` fires against whatever is frontmost when cleanup completes. | **Real residual risk.** Mitigation idea for v0.4: snapshot frontmost-app + frontmost-window-id at hotkey-release; if it has changed when paste fires, surface a confirmation overlay instead of pasting. **(TODO-v0.4-A)** |
| **Selected-text context fed to LLM** (Feature 4). When the user has text selected at hotkey-release, `clipboard.capture_selected_text()` simulates Cmd+C, copies the selection (capped at 2000 chars), and includes it in the LLM prompt. | Medium | Medium | Documented behavior. Feature is described in README. The capture restores the original clipboard afterward. Capped at 2000 chars to bound the leak. | The user might not realize a selection is included in the LLM payload. Disclosure UI (a flash in the overlay HUD: "context included") would help. **(TODO-v0.4-B)** |
| Clipboard side-effects: a malicious app monitoring `pbpaste` activity could see the temporary clipboard write. | Low | Low | The original clipboard is restored unconditionally in `capture_selected_text` (`clipboard.py:75`). The window of exposure is ~150 ms. | Same-UID attacker still wins. |
| Temp WAV file leaking audio. | Low | High if it leaked | Deleted in `finally` block in `recorder.py`. Lives for ~1 s. | Same-UID attacker who races the deletion can read it. |

### Denial of service — making the tool unavailable or causing it to do harm

| Threat | Likelihood | Impact | Mitigation today | Residual risk |
|---|---|---|---|---|
| **Prompt injection via clipboard** — a malicious webpage puts adversarial instructions on the user's clipboard before the user dictates over a selection. The cleanup LLM ingests it as `Context - the user had this text selected: '...'`. | Low | Bounded | The LLM has **no tools** in OpenVoiceFlow. The model can only return text, which is then pasted at the cursor. The user reviews the paste visually. The selected-text block is wrapped in a single-quoted string in the prompt (`base.py:99-104`). | The injected text could change the *cleaned-up output* in subtle, hard-to-spot ways (e.g. swapping a name). It cannot exfiltrate to the network because the LLM has no network tools. |
| LLM provider rate-limits the user's key, breaking dictation. | Medium | Low (UX) | Each backend's `validate()` returns a useful error string. Not a security issue. | — |
| `whisper.cpp` invocation hangs on a malformed WAV. | Low | Low | `subprocess.run(..., timeout=N)` is used in `_is_whisper_cpp` (5 s); main transcription is bounded by the recording length. | — |

### Elevation of privilege — gaining permissions you shouldn't have

Not directly applicable. OpenVoiceFlow has no privilege boundary internal to the app.

- The app runs as the user.
- The hotkey listener (`pynput`) and Accessibility API access (for `paste_text` / `learner`) are **user-granted** via macOS System Settings → Privacy & Security. Granting Accessibility is a one-time decision the user makes consciously.
- There is no setuid binary, no helper daemon, no network server.

If macOS itself or the Accessibility framework has a privilege bug, that's a CVE in the OS, not in OpenVoiceFlow.

---

## 5. Out-of-scope threats

Threats we **do not** try to defend against, because either the threat is the user's own environment or the defense would require infrastructure we don't have.

1. **Malware running with the same UID as the user.** It can read every file in the user's home directory regardless of `chmod 600`. The filesystem doesn't protect a process from another process running as the same user. If your Mac is owned, OpenVoiceFlow's keys + logs + dictionary are the least of your problems.

2. **Compromised LLM provider keys.** Once you give a key to OpenVoiceFlow, you are the only one responsible for rotating it. We do not store keys remotely. We do not transmit keys anywhere except as the `Authorization` header to the provider you pointed them at. If a key leaks (laptop theft, malware, careless paste), revoke it at the provider's dashboard.

3. **Compromised HuggingFace model.** The `ggml-*.bin` files are downloaded over HTTPS from HuggingFace. We do not pin checksums. A successful TLS-MITM attack against HuggingFace could substitute a backdoored model. **Checksum verification is a v0.4 ask. (TODO-v0.4-C)**

4. **State-level attackers.** TLS-breaking adversaries, hardware implants, supply-chain attacks against Apple's signing infrastructure, etc. Out of scope for a single-developer source-available personal tool.

5. **Side-channel attacks on `whisper.cpp` inference.** Power analysis, timing attacks, or acoustic side channels against the local Whisper inference. Not a meaningful threat model for a desktop dictation tool.

6. **Supply-chain attack on PyPI.** v0.3 is **not on PyPI yet**, so this is moot today. **It will be the dominant supply-chain concern at v0.4** when we publish. Today, `pip install -e .` from the GitHub repo and the DMG installer are the two entry points; neither pulls a typo-squat-able package name. **(TODO-v0.4-D: sign the GitHub Release and publish to PyPI under the reserved `openvoiceflow` name with Trusted Publisher OIDC.)**

7. **DMG signing / notarization.** The current v0.3.6 website-hosted DMGs are signed with Developer ID, notarized by Apple, and stapled so macOS Gatekeeper can verify them. The release workflow supports the same path when Apple Developer credentials are configured.

8. **Compromised dependencies (unpinned `>=`).** `pyproject.toml` uses `>=` rather than exact pins. A malicious update to a transitive dep could land on next install. **(TODO-v0.4-E: lockfile + Dependabot.)**

9. **Network operators (corporate proxies, hostile WiFi).** TLS is sufficient against most of these. We don't certificate-pin and won't.

---

## 6. Notes for security reviewers

### Where to start

- **`SECURITY.md`** (repo root) — vulnerability disclosure: where to report, supported versions, response SLA.
- **`PRIVACY.md`** (planned for v0.3 wave 3) — full data-flow diagram, sub-processor list, retention, opt-outs.
- **This document (`docs/THREAT_MODEL.md`)** — the page you are reading.

### Strong-privilege source files (read these to verify the mitigations above)

| Surface | File | Notes |
|---|---|---|
| Hotkey listener | `voiceflow/app.py` | Global keypress capture via `pynput`. User-granted Accessibility permission. |
| Audio capture | `voiceflow/recorder.py` | Writes temp WAV; `finally` block deletes. |
| Whisper.cpp invocation | `voiceflow/transcriber.py` | `_is_whisper_cpp()` validation gate at lines 12-23. |
| Paste at cursor | `voiceflow/system.py:paste_text` | Synthesized Cmd+V via osascript. Wrong-app race risk lives here. |
| Transcript logging | `voiceflow/system.py:log_transcript` | Off by default. `secure_chmod` applied to every write (lines 53, 64, 73). |
| Auto-learner | `voiceflow/learner.py` | Off by default. Reads focused field via Accessibility API for 30 s post-paste. |
| Selected-text context capture | `voiceflow/clipboard.py` | Simulates Cmd+C, restores clipboard. 2000-char cap (line 14). |
| Config / API key storage | `voiceflow/config.py` + `voiceflow/_secure_io.py` | `secure_write_json` enforces `chmod 600`. |
| LLM prompt construction | `voiceflow/llm/base.py` | Where dictionary + snippets + profile + selected-text-context get assembled into the outbound payload. |
| Update check | `voiceflow/updater.py` | GET `api.github.com/repos/shimoverse/openvoiceflow/releases/latest`. Opt-out via `config["update_check"] = false`. |

### Questions a reviewer should ask the maintainer

1. What's your PII redaction roadmap? (Not present today.)
2. What's your retention policy for `~/.openvoiceflow/logs/` when the user opts in? (None today; user manages.)
3. What's your incident-response process for a leaked API key reported by a user?
4. Have the hosted DMGs been rebuilt from the signing/notarization-enabled release workflow?
5. When will model checksums be verified at download?

---

## 7. Outstanding TODOs flagged for v0.4

| ID | Description | Source |
|---|---|---|
| **TODO-v0.4-A** | Snapshot frontmost-app at hotkey-release; surface a confirmation overlay if it changed by paste-time. | §4 Information disclosure (wrong-app paste race) |
| **TODO-v0.4-B** | Visible disclosure in the overlay HUD when selected-text context is included in the LLM payload. | §4 Information disclosure (selected-text context) |
| **TODO-v0.4-C** | Checksum verification for HuggingFace `ggml-*.bin` model downloads. | §5 out-of-scope #3 |
| **TODO-v0.4-D** | Reserve `openvoiceflow` on PyPI; publish via Trusted Publisher OIDC; sign the GitHub Release. | §5 out-of-scope #6 |
| **TODO-v0.4-E** | Lockfile + Dependabot; pin transitive dependencies. | §5 out-of-scope #8 |
| **TODO-v0.4-F** | Restrict the auto-learner to fields with the same `kAXRoleAttribute` as the original target, to avoid reading unrelated focused fields within the 30 s window. | §4 Information disclosure (auto-learner) |

---

*Last updated: 2026-04-27 against branch `v0.3-readiness`.*
