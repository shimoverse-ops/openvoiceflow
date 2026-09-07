# Privacy

OpenVoiceFlow is a native macOS app that runs on your Mac. We wrote this document to be readable in one sitting: no legalese, no "we may collect" clauses that turn out to mean everything. If anything below is unclear or wrong, open a GitHub Discussion and we'll fix it.

This policy applies to the native OpenVoiceFlow macOS app (`v0.4.0` and later, including the current `v0.5.x` line). For the older Python CLI (`v0.3.x` and earlier), check `git log PRIVACY.md` or the corresponding tagged release.

Privacy behavior and licensing are separate. The current project is
source-available for personal use only under the
[OpenVoiceFlow Personal and Reciprocal Source License 1.0](LICENSE). Commercial or organizational use, including selling or bundling the
software, requires separate written permission or a separate written license from
Shimoverse Studios; contact **contact@openvoiceflow.com**. Distributed derivatives and modified
network versions must publish complete corresponding source under the same
license. See [LICENSING.md](LICENSING.md).

---

## 1. TL;DR

- **Your audio never leaves your Mac.** Transcription happens on-device via **WhisperKit**. The recording is discarded the moment the transcript exists. There is no audio upload, ever.
- **Cleanup is Off by default.** Out of the box, OpenVoiceFlow pastes the raw on-device transcript with no LLM step and no network call. You have to turn cleanup on yourself.
- **Cloud cleanup is opt-in and bring-your-own-key.** If you enable **OpenRouter** cleanup, only the transcript text (plus your personal context — see below) is sent, under your own key, to a provider you contract with directly. You can instead run **Ollama** locally, or leave cleanup **Off**.
- **No accounts, no cloud sync, no crash reporting.** OpenVoiceFlow has no sign-up and doesn't sync your settings or profile anywhere. It checks for updates through Sparkle (see §3).
- **Since v0.5.7: an opt-out anonymous usage summary, on by default.** Word/time totals, which features you use, your country, and a display name you can change — powering an in-app leaderboard. Never audio, never dictated text, never your dictionary/snippets/profile content. Turn it off in Settings ▸ Privacy. See §7.
- **Your keys are in the Keychain; your data is on your disk.** API keys are stored in the macOS **Keychain**. Settings, history, and your personal context live locally in the app's **Application Support** folder.

---

## 2. Data inventory

Everything OpenVoiceFlow knows about you lives in one of the rows below.

| Artifact | Where it lives | What it contains | Default state | Goes off the Mac? |
|---|---|---|---|---|
| **Audio buffers** | RAM only, while you hold the hotkey | Your raw microphone audio | Always on (it's how dictation works) | **No.** Transcribed on-device by WhisperKit, then discarded. Never written to a network. |
| **Cleaned transcripts (Off)** | Nowhere new | The WhisperKit output is pasted directly with no LLM cleanup | **Default** | **No.** No cleanup call is made at all. |
| **Cleaned transcripts (Ollama)** | In transit to `http://localhost:11434` | The transcribed text + your profile / dictionary / snippet context | If you enable Ollama cleanup | **No.** Stays on the Mac (or wherever you point Ollama). |
| **Cleaned transcripts (OpenRouter)** | In transit to `openrouter.ai` | The transcribed text + your profile / dictionary / snippet context | If you enable OpenRouter cleanup | **Yes** — to OpenRouter, under your own key. You contract directly with OpenRouter under its terms. |
| **API keys** | macOS **Keychain** | Your OpenRouter key (if you set one) | Empty until you enable cloud cleanup | **No.** Stored by the system Keychain, not in a settings file. |
| **Settings** | App **Application Support** folder | Hotkey, model choice, cleanup backend choice, feature toggles | Created on first run | **No.** |
| **Know-Me profile** | App Application Support folder | Your name, occupation, industry, people/tools you mention, communication style | Empty until you complete the **Know Me** interview | **No** — but the profile is injected into every cleanup call, so an enabled cloud backend sees it. |
| **Dictionary** | App Application Support folder | Words and aliases you've added | Empty until you add words | **No** — but added words are injected into cleanup calls, like the profile. |
| **Snippets** | App Application Support folder | Voice triggers and their expansions. May contain signature blocks. | Empty until you add snippets | **No** — but expansions become part of dictated text and follow whatever path you've set for that text. |
| **History / stats** | App Application Support folder | Recent dictations and aggregate counters | Local | **No.** Never sent anywhere. |
| **Sparkle update check** | In transit to the appcast host | A request for the update feed to see if a newer signed build exists | On by default | **Yes** — an anonymous request for the update manifest. No PII, no key, no user ID. |
| **Anonymous usage summary** | App Application Support folder (device ID + display name), synced to our leaderboard API | Total words, total time back, streak, feature-usage counts, a random device ID, a display name you choose | **On by default** since v0.5.7 — toggle in Settings ▸ Privacy | **Yes, if the toggle is on.** Never dictated text, snippets, dictionary, or profile content. Country is derived server-side from the request; no IP address is stored. |

### Data flow for a single dictation

```
  mic audio  ──►  WhisperKit (on-device)  ──►  raw transcript (RAM)
                                                     │
                                                     ▼
                                     voice-command replacement (local)
                                                     │
                                                     ▼
        profile + dictionary + selected text  ──►  cleanup backend
                                                     │
                                      ┌──────────────┼───────────────┐
                                      ▼              ▼               ▼
                                     Off          Ollama         OpenRouter
                                  (no call)      (local)         (cloud, BYO key)
                                                     │
                                                     ▼
                                          cleaned text  ──►  paste at cursor
```

With cleanup **Off** (the default) or set to **Ollama**, no byte of your dictation crosses the machine boundary. Baseline network egress consists of the Sparkle update check and, while the privacy toggle remains on, the anonymous aggregate usage summary described in §7.

---

## 3. Sub-processors — who else sees your data

OpenVoiceFlow has no copy of anything you dictate, and never has. We do run one small server-side service as of v0.5.7 — the anonymous usage/leaderboard API described in §7 — which is the one exception to "no servers, no database" below. When you point the app at a cloud LLM, you are contracting directly with that provider under their terms; we are not in the middle of that path.

The third parties your install can talk to:

- **OpenRouter** (`openrouter.ai`) — the recommended cloud gateway. **Only if** you enable OpenRouter cleanup, it receives your transcript plus your profile / dictionary / snippet context every time you dictate. One OpenRouter key reaches any model it hosts (you pick the model in the app). Governed by OpenRouter's terms.
- **Other cloud providers** — some builds also let you point cleanup directly at Anthropic, OpenAI, or Groq instead of OpenRouter. Whichever provider you select is the one that receives your transcript + context, under your own API key. OpenRouter is the recommended path.
- **Ollama** (`http://localhost:11434` by default) — runs on your machine. No third party.
- **Off** — no cleanup call. The raw WhisperKit output is pasted without cleanup.
- **WhisperKit model download** (`huggingface.co`) — used **once**, during first-run onboarding, to download the on-device speech model. No account required, no PII sent. After that, the model is on disk and never re-fetched unless you change models.
- **Sparkle updates** — the app checks a signed appcast for newer builds and can download and install them in place. The request is anonymous (no auth, no key, no user ID); updates are Developer-ID-signed and verified before install.
- **OpenVoiceFlow's own analytics API** (`openvoiceflow.com/api/...`) — **only if** "Share anonymous usage & leaderboard rank" is on (Settings ▸ Privacy, on by default since v0.5.7). Receives a device ID, a display name you choose, and aggregate counters — see §7 for the exact fields and how to turn it off.

Cleanup is **Off by default** — the raw on-device transcript is pasted as-is and no dictation content leaves your Mac. A cloud provider only receives transcript text if you turn cleanup on and select one; the separate aggregate usage summary never contains dictated content.

---

## 4. Permissions you grant macOS

OpenVoiceFlow asks macOS for these privileges. You grant them in **System Settings → Privacy & Security**, and you can revoke them at any time.

- **Microphone** — to capture audio while you hold the hotkey. Required for dictation.
- **Accessibility** — to paste the cleaned text into the focused text field (a synthetic ⌘V). The app does not read your screen or the contents of other apps.
- **Input Monitoring** — to detect the global push-to-talk hotkey in every app.

---

## 5. Defaults you can change

Every privacy-relevant default is a toggle in the app's menu-bar settings. There is no CLI to configure.

| Setting | Default | What it controls |
|---|---|---|
| **Cleanup backend** | **Off** | Whether — and how — your transcript is cleaned up. Off = raw local transcript; Ollama = local model; OpenRouter (or OpenAI / Anthropic / Groq) = cloud cleanup with your key. |
| **Auto-learn** | **off** | Reads the focused text field briefly post-paste to learn corrections. |
| **Voice commands** | on | Replaces spoken punctuation phrases ("new line", "comma") locally, before any cleanup call. |
| **Update check (Sparkle)** | on | Checks the signed appcast for a newer build. |

Because cleanup ships **Off**, a fresh install sends no dictation content over the network. The baseline runtime requests are the Sparkle update check and, while the privacy toggle remains on, the anonymous aggregate usage summary in §7; audio and dictated text stay on the Mac regardless.

---

## 6. What the app doesn't do

- **No dictation content ever leaves the Mac, sharing on or off.** Not your words, not your audio. The anonymous usage summary (§7) is aggregate counts only, and it's a real, disclosed exception to the rest of this list — not something folded in quietly.
- **No crash reports from the app.** macOS may keep a system-level crash log under `~/Library/Logs/DiagnosticReports/`; that's Apple's, not ours.
- **No shared keys.** OpenVoiceFlow ships with no embedded API keys. You bring your own, and it lives in your Keychain.
- **No cloud sync of settings or profile.** Those stay local regardless of the usage-sharing toggle.
- **No accounts.** There is no sign-up, no login, no email collected. The usage summary's device ID identifies one app installation, not a person; installations are never merged by nickname.
- **No third-party analytics or tracking SDKs** inside the app. The usage summary goes to our own API, described in §7 — not a third party.

Anything you've already sent to OpenRouter lives by that provider's retention policy — delete it through their account or API.

---

## 7. App analytics & the website

**In-app usage summary & leaderboard (since v0.5.7).** With "Share anonymous usage & leaderboard rank" on in Settings ▸ Privacy — **on by default** — the app periodically sends:

- A random device ID generated for this installation, and a display name you choose (shown to other users on the leaderboard). There is no account: installations remain separate even when they use the same nickname, so three computers produce three independent leaderboard rows.
- Aggregate counters: total words dictated, total time back, streak, and which features are on (cleanup enabled, snippet/dictionary counts, whether you've completed Know Me) — counts only, never content.
- **Which parts of the app get used (since v0.5.22).** Counters for the screens you open (Home, History, Personalize and its tabs, Settings, Leaderboard) and the features you press (finished a dictation, added a dictionary word or snippet, started the Know Me interview, changed the cleanup backend, checked for updates, opened Feedback, and so on). Each is a fixed name and a running total — `pane.history`, 12 — and nothing else. There are no timestamps and no ordering, so these cannot reconstruct a session or show what you did when; they answer "does anyone use this feature", not "what did you do today". The names are a closed list compiled into the app ([`UsageCounters.swift`](native/Sources/OpenVoiceFlow/UsageCounters.swift)), and the server discards any name that isn't already on its matching list, so no text you type or dictate can end up here even if something went wrong.
- Your country, derived server-side from the request at the moment it arrives. We do not log or store your IP address.

This never includes dictated text, snippets, dictionary entries, Know-Me profile content, or anything from the cleanup path. Aggregate totals sync periodically during active dictation. Opening Leaderboard sends the same aggregate snapshot before fetching standings, so saved local totals can restore that installation's row. Changing a nickname also sends the snapshot once when you press Return or leave the field; individual keystrokes are not uploaded. Turn the toggle off and every one of these requests stops immediately — nothing queues up to send later; the usage counters keep counting locally so Home still works, they just stop leaving your Mac. "Delete my leaderboard data" clears the local counters as well as the server row, so the next sync cannot re-upload the totals you just deleted. The leaderboard itself does not disclose how many people use OpenVoiceFlow in total.

**The website.** The download site (`openvoiceflow.com`) separately uses **Vercel Analytics** and **Vercel Speed Insights** for anonymous page views, aggregated visitor/referrer/geography trends, and performance — no advertising cookies or cross-site profile. Its interactive marketing, documentation, blog, download, and privacy pages also send a minimized first-party event to our own API for each page view and a fixed set of meaningful actions (downloads, install-guide and navigation links, calls to action, GitHub links, demo plays, footer links, checksum copies, and release-note or FAQ opens). Minimal release-note embeds opened inside the app updater do not load this first-party analytics script and are excluded from those page totals. Each collected event contains only the page path without query parameters, an allow-listed action/target, the acquisition category, a random visit ID that rotates after 30 minutes of inactivity, and coarse city/region/country derived by Vercel when available. Tagged outreach links may also carry short, opaque campaign and recipient tokens so campaign visits and downloads can be counted; these pseudonymous per-recipient tokens never contain a person's name or email address and are removed from the visible URL after capture. We do not request device location, store an IP address, retain typed text or form values, record raw click coordinates, or keep a persistent cross-visit browser ID. Global Privacy Control and Do Not Track disable these first-party events, including outreach attribution. Raw first-party website events, including any outreach tokens, are deleted after 90 days. This is independent of the in-app usage summary above. Vercel's analytics privacy notice: <https://vercel.com/docs/analytics/privacy-policy>.

---

## 8. GDPR posture

OpenVoiceFlow is a **bring-your-own-key (BYOK), self-managed, personal-productivity tool**. Practically:

- **OpenVoiceFlow is not a controller or processor of your dictation data** under GDPR — we have no copy of anything you dictate, store, or configure.
- **We are a controller for the minimized analytics that reach us: the app usage summary and website events in §7.** App data is pseudonymous (a random device ID, not an account) and deliberately minimized; its Settings control and delete action are described above. Website events use a visit-scoped ID that expires after 30 minutes of inactivity rather than a persistent browser identifier, honor Global Privacy Control / Do Not Track, and are deleted after 90 days. Neither system stores IP addresses, dictated content, typed text, form values, or raw click coordinates.
- **You are the controller** of the data on your Mac. You decide whether to fill out the Know Me interview and whether to enable cloud cleanup.
- **If you enable OpenRouter cleanup, OpenRouter is an independent controller / processor** for the text you send it. If you need a Data Processing Addendum (DPA), Standard Contractual Clauses, or any other GDPR paperwork, you negotiate that **directly with OpenRouter** under your own account. OpenVoiceFlow cannot sign a DPA on their behalf and does not pretend to.
- **EU users:** if your dictations contain personal data and you enable cloud cleanup, you are responsible for the lawful basis and the international-transfer story. The simplest way to take every cloud provider out of the picture is to leave cleanup **Off** or use **Ollama**.
- **Regulated industries (healthcare, legal, financial, government):** OpenVoiceFlow has no SOC 2, no ISO 27001, no HIPAA BAA, and no FedRAMP. Don't use it for regulated data unless you have your own compliance overlay (your own DPA with OpenRouter, your own air-gapped Ollama deployment, your own organizational controls) and have obtained the required separate written permission or a separate written license.

---

## 9. Children's privacy / COPPA

OpenVoiceFlow is not designed for, and not directed to, children under 13. We do not knowingly collect data from anyone (kids included), but we also don't perform any age verification. If a child under 13 is using your Mac and dictating through cloud cleanup, the LLM provider's children's-privacy policy applies, not ours.

---

## 10. Changes to this policy

This file is versioned alongside the code. Material changes get a line in `CHANGELOG.md` under the release that introduces them, and the diff is visible in `git log PRIVACY.md`. There is no email list, no banner, no "we've updated our privacy policy" pop-up — if you want to track changes, watch the repo or read the changelog when you upgrade.

---

## 11. Contact

- **Security issues** (vulnerabilities, exposed-key bugs, anything that needs a private disclosure channel): see [`SECURITY.md`](SECURITY.md).
- **General privacy questions** (what does this setting do, why does this connection happen, can we add an option for X): open a [GitHub Discussion](https://github.com/shimoverse/openvoiceflow/discussions).
- **Repo:** <https://github.com/shimoverse/openvoiceflow>

If something on this page is wrong, out of date, or doesn't match what the code actually does, that's a bug. Tell us.
