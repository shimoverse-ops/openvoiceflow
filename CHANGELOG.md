# Changelog

All notable changes to OpenVoiceFlow are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
(with the pre-1.0 caveat documented in [VERSIONING.md](VERSIONING.md)).

## [Unreleased]

### Added
- The website now records privacy-safe 30-minute visits, page views, acquisition source, allow-listed navigation/product clicks, and coarse city/region/country when Vercel makes it available. Query strings, IP addresses, typed text, raw click coordinates, and persistent cross-visit browser identifiers are not stored; Global Privacy Control and Do Not Track are honored, and raw events expire after 90 days.
- A bearer-protected analytics report now exposes aggregate website sessions/pages/clicks/locations alongside current opt-in app feature state and usage counters for the private owner dashboard.

## [0.5.22] — 2026-09-06

### Added
- **Which parts of the app get used.** The app now keeps a running count per screen (Home, History, Personalize and its tabs, Settings, Leaderboard) and per feature you press (finished a dictation, added a dictionary word or snippet, started the Know-Me interview, changed the cleanup backend, checked for updates, opened Feedback, and similar), and includes those counts in the anonymous usage summary it already sends. Each counter is a fixed name and a total — `pane.history`, 12 — with **no timestamps and no ordering**, so they show that a feature is used and never when you used it or what you did around it. The names are a closed list compiled into the app, and the server discards any name not already on its own matching list, so dictated text cannot reach them. Same single switch as before (Settings ▸ Privacy ▸ "Share anonymous usage & leaderboard rank"), no new network requests, and "Delete my leaderboard data" now clears the local counters too so a later sync can't re-upload what you deleted.
- The website records anonymous counts for footer links, checksum copies, and opening a release note or FAQ answer, alongside the download/navigation/CTA events it already tracked.

### Fixed
- The maintainer analytics dashboard reported **"Verified installs: Unknown — Native app has no telemetry."** That stopped being true in 0.5.8, when opt-out usage sharing shipped: the install data was in the database the whole time and the dashboard never asked for it. It now reports opted-in installs, active installs, app versions, countries, and which screens and features get used, via a new token-gated aggregate endpoint (`api/analytics/stats.js`). Without the token the dashboard says the source is unavailable rather than asserting the app is silent.

### Changed
- `README.md`, `SECURITY.md`, `docs/ARCHITECTURE.md`, the DPA template, and the website's "Really free?" answer still carried blanket "no telemetry" claims that 0.5.8 had already made false, or that were true only of the legacy Python CLI. Each now says what the Mac app actually sends and how to turn it off, or names the CLI it applies to.

## [0.5.21] — 2026-09-06

### Fixed
- The **Version History** button on the "You're up to date!" update alert now opens the [Releases page](https://openvoiceflow.com/releases.html) instead of the "How it works" marketing page, which listed no versions at all. Sparkle fills that button from the appcast's `fullReleaseNotesLink`, which the feed never set, so it fell back to a `releaseNotesLink` that pointed at marketing copy. The appcast now sets both, and this fix reaches every installed build the moment the site deploys — the button reads the website's feed, not the app.
- The release notes shown inside the update sheet are now that version's actual notes, generated from this changelog, rather than the same marketing page.

### Added
- Settings ▸ "You're on vX.Y.Z" now has a **Version history** link that opens the Releases page at the running version, so the notes no longer sit behind an update check that reports there is nothing to install.
- Every release on the Releases page is individually linkable (`releases.html#v0.5.21`), and opening such a link expands that release rather than landing on a collapsed card.

### Changed
- The dashboard sidebar footer now says whether the running build is current instead of always reading "auto-updating". When the appcast offers a newer version it shows an **Update** action that installs it; when the build is the latest, it reads "Up to date" with nothing to click. Before a check has finished — including when automatic updates are off, which stays an opt-out of background checks — the footer shows the version alone rather than claiming a freshness nothing verified.

## [0.5.20] — 2026-09-02

### Changed
- The leaderboard now labels its figure "time back" instead of "time saved", matching Home, onboarding, and the manual. The number is how long the same words would have taken to type at 40 wpm; nothing subtracts the time dictating them actually took, so calling it a saving overstated it. The number itself is unchanged, as are the `minutesSaved` field and `minutes_saved` column that already-shipped clients depend on.

## [0.5.19] — 2026-09-02

### Changed
- The leaderboard now draws a fixed seven rows whatever the standings return, so the height of the card no longer reveals how many people use OpenVoiceFlow. Rows the service doesn't name are masked — a shimmering placeholder with no rank, name, or total — and the tail fades out rather than ending on a countable last row. The card states no rule and shows no threshold: naming the bar would let anyone counting the visible names work out what population they were counting.

## [0.5.18] — 2026-08-31

### Fixed
- Public leaderboard standings now include only rows with at least 60 minutes saved and show no more than five entries, while still showing your own row separately.
- Legacy auto-generated leaderboard names now use the same exact 10–99 suffix range as the native app, preserving custom-looking names ending in 00–09.

## [0.5.17] — 2026-08-30

### Added
- App names across Home, History, and Personalize now use recognizable app or company logos, including Claude, Discord, Notion, and Outlook. Installed macOS app icons remain the first choice, with bundled brand marks as reliable fallbacks.

### Changed
- Leaderboard nicknames now save when Return is pressed or the field loses focus, immediately publish that installation's aggregate totals, and refresh the standings after a successful update. Each installation keeps its own row even when multiple computers use the same nickname.
- Opening Leaderboard now republishes that installation's saved aggregate totals before fetching standings, restoring existing local usage without requiring another dictation or nickname change.
- The leaderboard service now uses Neon's supported serverless database client and accepts both current and legacy Vercel database environment-variable names.

### Fixed
- History's Copy action now changes to “Copied” with a checkmark after a successful copy and resets automatically after 1.5 seconds.
- Leaderboard loading and nickname-sync failures now show an honest retry action instead of appearing as empty standings.

## [0.5.16] — 2026-08-29

### Fixed
- Personalized Styles now shows recognizable Discord and Gmail icons, using installed app icons first and bundled brand marks when those apps are unavailable.
- Clicking the dashboard outside the centered Feedback sheet now dismisses it, while clicks inside the sheet or in unrelated OpenVoiceFlow windows keep their normal behavior.

## [0.5.15] — 2026-08-29

### Fixed
- Restored Feedback as a centered native modal instead of a left-anchored popover, while retaining the always-visible optional email field and Cancel, Send, and Escape dismissal.

## [0.5.14] — 2026-08-29

### Changed
- Simplified feedback to one optional email field in a native macOS popover that dismisses with Cancel, Send, Escape, or an outside click.
- Moved Know Me into Personalize so related controls stay together.
- Changed generated leaderboard aliases to compact one-token handles while preserving custom names during legacy migration.

## [0.5.13] — 2026-08-29

### Changed
- Settings no longer exposes the anonymous analytics device ID or the long
  leaderboard-sharing explanation, and the Feedback sheet no longer shows its
  usage-snapshot explainer. The sharing toggle, leaderboard name, deletion
  action, and feedback behavior are unchanged.

## [0.5.12] — 2026-08-29

### Changed
- “Where you dictate” now shows each app’s real icon with a time-share ring,
  making the per-app breakdown easier to scan while preserving the existing
  local-only usage data and accessibility labels.

## [0.5.11] — 2026-08-29

### Changed
- The History pane now carries a subtitle: "Stored only on this Mac —
  never synced to a server." Scoped deliberately to what's true
  unconditionally (this list is local storage, full stop) rather than a
  blanket "nothing leaves this machine" claim, since cloud AI cleanup
  (opt-in, off by default) does send dictated text to the selected
  provider before it lands here — that's covered separately by the
  existing footer line and the privacy docs.

## [0.5.10] — 2026-08-29

### Changed
- Dictionary, Snippets, and Styles are now one **Personalize** pane in the
  dashboard sidebar, switched with tabs instead of three separate rows.
  Each tab keeps its item count, the content area now sits in a single card,
  and switching tabs animates instead of jumping. No data or behavior
  changes — same stores, same add/remove actions, same empty states. Docs
  updated to describe the new location (`Dashboard ▸ Personalize`).

## [0.5.9] — 2026-08-29

### Fixed
- The Feedback sheet's category picker ("Something's broken" / "Feature
  idea" / "Just saying thanks" / "Something else") overflowed a 440pt-wide
  sheet, truncating the leading and trailing segments. Segmented control now
  shows short labels (Bug/Idea/Thanks/Other); the full wording still goes
  into the email subject and body. Sheet widened to 480pt for margin.

## [0.5.8] — 2026-08-28

### Added
- Anonymous usage sharing and an in-app Leaderboard, ranked by time saved.
  **On by default** — a real, disclosed change from every prior release,
  which sent nothing. Settings ▸ Privacy ▸ "Share anonymous usage &
  leaderboard rank" turns it off, deletes nothing retroactively but stops
  every future request immediately; a "Delete my leaderboard data" button
  removes a past submission outright. What's sent: a random per-device ID,
  a display name you can change, aggregate word/time/streak/feature-usage
  counters already shown on Home, and a server-derived country (no IP
  stored). Never dictation text, snippets, dictionary entries, or the
  Know-Me profile. Full detail in `PRIVACY.md` §7 and the docs site's
  Privacy architecture ▸ Analytics & leaderboard section.

### Changed
- Docs and `PRIVACY.md` updated to describe the above plainly, replacing
  the "no telemetry" claims that were accurate through 0.5.7 and are not
  anymore.

## [0.5.7] — 2026-08-28

### Added
- A Feedback item in the sidebar, below Settings. Opens a short form (bug /
  idea / praise / other, plus an optional reply email) and, only on Send,
  opens a `mailto:` with the message and a small aggregate usage snapshot
  (words dictated, time saved, streak, last 7 days, first-use date) —
  never dictation text, snippets, dictionary entries, or the Know-Me
  profile, and nothing is sent until Send is pressed.

## [0.5.6] — 2026-08-25

### Added
- The language picker now offers all 99 languages in Whisper's multilingual
  set (previously eleven), including Ukrainian. Tiny, Small, Medium, and
  Large turbo all share the same tokenizer, so the list applies to every
  engine offered in Settings.

## [0.5.5] — 2026-07-27

### Fixed
- The progress bar no longer parks at 100% with no way forward. WhisperKit
  compiles the model for your chip after the download — minutes on a first
  large-model run, with no progress signal — so the transfer now owns 0–90%
  and the compile creeps through the 90s under "Downloaded — now optimizing
  for your Mac. First run only." 100% arrives only with the Try It button.

### Changed
- RECOMMENDED now adapts to the Mac: Large turbo on Apple Silicon with disk
  headroom, Small on Intel or a tight disk. No permissions involved.

## [0.5.4] — 2026-07-27

### Fixed
- The download meter showed "0 of 0 MB · 0.0 MB/s" over a moving bar:
  WhisperKit reports abstract progress units for multi-file model downloads,
  not bytes. The meter now shows percent (and the always-honest ETA) when
  units can't be bytes, instead of inventing megabytes.

## [0.5.3] — 2026-07-27

### Fixed
- **Large turbo could never download.** Its model id didn't exist in the
  WhisperKit repo; every user who chose it hit "no models found" disguised as
  a connection error. Correct id shipped, saved settings migrate silently.
- Browsing the engine chooser no longer starts a download per click: a 1.5 s
  grace window ("Starting in a moment — switch engines freely") starts the
  transfer only once the choice rests, and switching cancels the superseded
  download outright. Model loads are single-flight, so overlapping transfers
  can no longer corrupt each other's cache.
- Download failure copy points at Details instead of guessing "check your
  connection" — the guess was wrong exactly when it mattered.

## [0.5.2] — 2026-07-26

The first-run field-notes release.

### Added
- Live transcript in the HUD while the key is held ("Show words as you speak",
  default on; respects the text-echo privacy setting).
- Speech-engine choice in onboarding — four models with size and benefit,
  nothing preselected, nothing downloading until you pick.
- Launch at login (SMAppService), default on, with a Settings toggle.
- Onboarding's "I live up there" now anchors a callout to the real menu-bar
  icon, with a mock menu-bar illustration when the icon is squeezed out.
- Dashboard banner explaining when macOS hides the menu-bar icon (full bar /
  notch) and the ⌘-drag fix.

### Changed
- Onboarding ends in the dashboard instead of an empty desktop; the try-it
  card acknowledges key-down instantly.
- The "names I'd get wrong" question moved out of onboarding (Know-Me keeps it).

## [0.5.1] — 2026-07-26

### Fixed
- **The hotkey now works from launch.** Previously nothing started the key
  listener after first run — every relaunch came up deaf until Start
  Dictation was clicked in the menu. The Start/Stop menu item is gone
  (Pause remains); a Turn On Dictation button appears only if a permission
  was revoked.

### Added
- PERMISSIONS card in dashboard Settings with live status per grant;
  re-granting revives dictation without a relaunch.

## [0.5.0] — 2026-07-26

The phase-06 redesign: new onboarding (sequential permissions, download-
while-interviewing, ink-fill first dictation), redesigned HUD (path-morph
waveform, spine countdown, text tail), menu-bar hello animation, and a
restructured dashboard Home. Also the release that made DMG signing itself
a hard gate: the disk image (not just the app) is now Developer-ID signed,
and the pipeline fails loudly if Gatekeeper rejects it.

## [0.4.3] — 2026-07-26

### Fixed
- Dock presence obeys the setting; `fn` is the default hotkey; onboarding
  gives real feedback while permissions land.

## [0.4.2] — 2026-07-25

### Added
- Automatic background updates (Sparkle) with honest in-app update cues.
- Per-app dictation breakdown ("Where you dictate").

### Fixed
- Failed pastes recover; the transcription model hot-swaps without restart.

## [0.4.1] — 2026-07-25

Website/site release wiring for the native line; guarded the legacy Python
release pipeline against 0.4.0+ tags; native app added to CI.

## [0.4.0] — 2026-07-24

**The native rewrite.** OpenVoiceFlow became a Swift/SwiftUI menu-bar app:
on-device WhisperKit transcription, CGEvent-tap hotkey, Keychain-held API
keys, signed + notarized + stapled DMG from a tag-driven release pipeline.
The Python app (≤ 0.3.6) is EOL from this point.

## [0.3.6] — 2026-07-18

### Fixed — Fn / 🌐 Globe key no longer fails silently
- **Fn was never a working hotkey.** macOS doesn't deliver the Fn/Globe key to
  `pynput`, so selecting it left dictation permanently dead with no feedback.
  Choosing Fn now surfaces an immediate modal explaining the limitation and
  pointing at Right Command (the default), the menu-bar picker hides Fn unless
  it's the current (legacy) selection, and onboarding no longer offers it.

### Fixed — production-hardening pass (end-to-end audit follow-up)
- **Hotkey can't be wedged by a consent dialog.** The microphone is now armed
  on the event-tap thread and the ~150 ms of `osascript` context capture runs
  on a worker, so a stalled Automation/Accessibility dialog can no longer block
  (and let macOS disable) the global hotkey.
- **Runaway recordings self-terminate.** A max-duration watchdog force-stops a
  dictation whose key-release was lost, instead of leaving the mic and
  `whisper-stream` running indefinitely.
- **No PortAudio stream leak.** `recorder.stop()` always releases the audio
  stream even when the input device is unplugged mid-recording; that failure is
  now surfaced instead of silently freezing the overlay.
- **Clipboard data-loss fixed.** Selected-text capture no longer overwrites a
  non-text clipboard (image/file) and never restores empty text over the
  selection.
- **Security defense-in-depth.** Secrets are written with `O_EXCL|O_NOFOLLOW`
  (symlink-swap safe); `~/.openvoiceflow/logs/` is `0700`; LLM/Ollama responses
  are read with a 16 MB cap; `ollama_url` rejects non-HTTP schemes and warns
  when it points off-box. Hung `pbcopy` children are reaped, not orphaned.
- **Upgrades actually reinstall dependencies.** The DMG venv marker is now
  version-stamped, so a release that adds or bumps a dependency reinstalls for
  existing upgraders instead of breaking on import.
- **Overlay polish.** HUD timers run in the common run-loop mode (no freeze
  during menu tracking), fades honor Reduce Motion, and the window is ordered
  out after fading so it doesn't linger in every Space.
- **Know-Me interview no longer self-destructs** when Escape is pressed while a
  text field is focused.

See git history (`PRODUCTION_READINESS.md`, since removed) for the full audit and
the remaining roadmap (native onboarding, self-contained bundle, Sparkle, etc.).

## [0.3.5] — 2026-07-13

### Fixed — first launch could silently do nothing (no menu bar icon, no wizard)
These fix the DMG bootstrap layer (`build-dmg.sh` launcher + native launcher),
complementing the app-level visibility work below.
- **Stale bootstrap lock.** `~/.openvoiceflow/.bootstrap.lock` survives reboots,
  and its stored pid could be reused by an unrelated live process — the alive
  check then matched, so every launch exited silently forever. The lock now
  only counts when the pid is alive *and* is really our `launcher.sh`.
- **Command Line Tools stub.** `command -v python3` always succeeds on macOS
  (Apple ships an installer stub), so a Mac without the Command Line Tools got
  past the check and failed later with no message. First launch now probes
  `xcode-select`, triggers the CLT installer, and shows instructions.
- **Broken venv skipped as "installed".** A macOS/CLT update can break the
  venv's interpreter or native wheels while the `.ovf-deps-installed` marker
  stays present, so the bootstrap was skipped and every launch died on import.
  The launcher now health-checks the venv (imports numpy/sounddevice/pynput/
  rumps/objc) and rebuilds it when the check fails.
- **Silent progress + silent fallbacks.** First launch now shows an up-front
  dialog explaining the ~5-minute setup and where the menu bar icon appears
  (including the 14"/16" notch tip); the venv/pip steps fail with a visible
  dialog instead of exiting quietly; a skipped setup wizard and a menu-bar
  (rumps) failure now say so instead of dropping to an invisible background
  process.
- **Input Monitoring permission (native launcher).** The native launcher now
  proactively requests Input Monitoring (`IOHIDRequestAccess`) at first launch,
  in addition to Microphone and Accessibility, so the grant is in place before
  the dead-listener watchdog would ever need to fire.

### Fixed
- Startup now checks the **Input Monitoring** permission — the one the
  global hotkey listener actually needs. It was never verified (only the
  doctor knew about it), so a missing grant produced a "Ready" menu with a
  hotkey that silently never fired. A denied probe warns loudly with a
  one-click System Settings link but never blocks startup, because
  Accessibility trust can also grant listen access.
- A new dead-listener watchdog catches the same failure by measuring
  reality: if no key events at all arrive within 15 seconds of the
  listener starting *and* macOS reports Input Monitoring denied, the menu
  bar shows a front-and-center alert with the fix. An idle user without
  the permission problem gets a one-time gentle tip instead. (Previously
  this self-check existed only for the fn/Globe key, never for the
  default Right Command hotkey.)
- Setup failures at launch now surface as a **modal alert** with a
  one-click settings link instead of only a Notification Center banner —
  notifications require a permission of their own and the status item can
  hide behind a MacBook notch, so the old failure path could be entirely
  invisible.
- A corrupt or wrong-shaped file in `~/.openvoiceflow/` (snippets, stats,
  profile, dictionary aliases, transcript logs, seen-tips) can no longer make
  every dictation fail with a generic error: all user-data loaders now
  validate shape, drop malformed entries, and degrade to safe defaults.
  `--show-profile` prints recovery guidance instead of a literal `null` when
  the profile file is corrupt.
- Every `osascript`/`launchctl`/`open` subprocess call now has a timeout, so
  a pending macOS consent dialog or a wedged `launchd` can no longer freeze
  the hotkey thread permanently. If auto-paste times out, a notification
  explains that the text is already on the clipboard, ready for ⌘V.
- Auto-learn no longer records ordinary content edits (e.g. "june" → "july")
  as permanent corrections: the word-similarity threshold was raised from
  0.4 to 0.55, calibrated so genuine mishearings ("mir" → "Meer",
  "recieve" → "receive") are still learned.
- Setup wizard: an `llm_backend` of `none` no longer breaks the backend
  screen; switching backends clears the previous backend's prefilled API key
  instead of finishing without saving a key; a failed final config write now
  shows an error dialog instead of a Finish button that silently does
  nothing.
- Know Me interview: no longer clobbers a configured `--style` (the style
  radio preselects from config, and styles the interview can't express, like
  `code` or `email`, are preserved unless actively changed); Enter-key
  bindings no longer leak between screens; context-menu paste into
  multi-line fields is no longer dropped; a hand-edited profile can't crash
  the wizard.
- Menu bar: notifications fall back to the osascript path when
  `rumps.notification` is unavailable (non-framework Python installs), and
  **Check for Updates…** can no longer get stuck on unexpected
  network/response errors. The duplicate startup update check in menu-bar
  mode was removed.
- Overlay: the compact auto-learn pill no longer permanently shrinks the
  font of every subsequent HUD message.
- CLI: value-taking flags now reject empty strings (`--search ""` used to
  launch the app; `--add-command ""` corrupted every dictation); config
  setters combined with an action flag now print a warning instead of being
  silently ignored; `--auto-learn`, `--update-check`, and
  `--log-transcripts` now compose on one command line.
- Doctor: macOS version detection resolves the "10.16" Big Sur
  compatibility shim via `sysctl kern.osproductversion` and reports
  "unknown" (a WARN) rather than false-failing supported systems; bare-major
  versions ("12") no longer compare below the (12, 0) minimum.

### Added
- CI now compiles the native launcher (`clang -fsyntax-only`) and runs a
  functional test suite (`tests/test_launcher_flows.py`) that renders the real
  `launcher.sh` and exercises the stale-lock, missing-CLT, broken-venv, and
  first-run-visibility paths with shimmed macOS commands.
- The menu-bar app now shows a **Dock icon** while running (toggleable via
  **Advanced → Show in Dock**, default on). A menu-bar-only icon can hide
  behind a MacBook notch, leaving no visible sign the app is running;
  clicking the Dock icon opens the native status summary with the active
  dictation shortcut.
- 17 regression tests pinning the defensive-loader, learner-threshold,
  updater, and macOS-version behaviors (`tests/test_defensive_loaders.py`),
  plus 12 pinning the Input Monitoring gate, dead-listener watchdog, and
  Dock default (`tests/test_visibility_and_watchdog.py`).

### Changed
- CI lint now covers the entire repository (`ruff check .`), not just
  `voiceflow/`.

## [0.3.4] — 2026-07-10

### Added
- A polished native menu-bar experience led by **Open OpenVoiceFlow**, with
  grouped Dictation Shortcut, AI Cleanup, Writing Style, Personalization, and
  Advanced menus.
- A user-triggered **Check for Updates…** action that always reports whether a
  release is available, the app is current, or the service could not be
  reached.
- Direct menu links to macOS Microphone and Accessibility settings.

### Changed
- The status item now uses dark-mode-safe SF Symbols with accessible labels:
  a waveform while ready, a pause symbol while paused, and a warning symbol
  when setup needs attention. A visible `OpenVoiceFlow` text label remains as
  the fallback if symbols are unavailable.
- Menu selections now use native macOS checkmarks, clean human-readable names,
  every supported dictation shortcut, standard separators, and **⌘Q** for
  **Quit OpenVoiceFlow** instead of emoji-prefixed labels.
- The long-lived Python UI process now stays out of the Dock and uses the
  bundled OpenVoiceFlow icon for native dialogs. The Current App row refreshes
  as focus changes without mistaking the UI process for the user's app.

### Fixed
- The waveform status item is created before backend validation begins, so a
  slow local backend no longer makes launch look unresponsive.
- **Edit Profile** now runs its Tk interview in an isolated process instead of
  risking a native Tk crash in the menu-bar process.
- The **Download** button in the update alert now recognizes AppKit's native
  button result and opens the release page correctly.

## [0.3.3] — 2026-07-10

### Added
- The menu-bar menu now includes a persistent **How to Use** guide, and the
  first-run hotkey tip also appears in the floating HUD instead of relying
  only on a potentially hidden macOS notification.
- `voiceflow/platform_support.py`: one place for OS, macOS-version,
  architecture (Apple Silicon / Intel / Rosetta), and permission detection.
- CLI platform gate: on Linux/Windows, `openvoiceflow` now prints a clear
  "macOS-only" explanation with uninstall guidance and exits cleanly instead
  of crashing with a traceback. `--doctor` and `--show-config` keep working
  so users can inspect state first.
- New doctor checks: operating system + version, architecture (warns on
  Rosetta-translated Python and Intel Homebrew on Apple Silicon), and the
  three macOS permissions dictation depends on (Microphone, Accessibility,
  Input Monitoring) with click-to-fix System Settings links.
- A launch below the supported macOS floor (12 Monterey) now prints an
  upgrade warning.
- CI: new `non-macos-guard` job on `ubuntu-latest` pins the "friendly
  message, never a traceback" guarantee and runs the full suite on Linux.
- Website: the download page now detects the visitor's OS. Windows, Linux,
  ChromeOS, Android, and iPhone/iPad visitors get an inert "Not available
  for <OS>" notice instead of a live DMG button; Safari-on-Mac visitors get
  an Apple Silicon / Intel recommendation via a WebGL renderer fallback
  (Chromium browsers already used architecture hints).

### Fixed
- Short streaming dictations no longer lose the final transcript fragment
  when `whisper-stream` exits without a trailing newline.
- Fresh installs now use the reliable batch recorder by default. Experimental
  real-time streaming remains available through the menu bar or
  `--streaming on`. Existing v0.3.2 installs are reset to batch mode once and
  can opt back into streaming afterward.
- `voiceflow.recorder` no longer imports `sounddevice` at module load —
  the import crashed the whole app (`OSError: PortAudio library not found`)
  on machines without PortAudio before any error handling could run.
- `find_whisper_cpp` / the doctor's Homebrew check use `shutil.which`
  instead of spawning `which`, which crashed on Windows.
- The keyboard-listener (pynput) import is now guarded in CLI and menu-bar
  modes: a missing input backend produces a clear error instead of a crash.
- Clipboard/keystroke/sound helpers (`pbcopy`, `pbpaste`, `osascript`,
  `afplay`) no longer propagate `FileNotFoundError` when the binaries are
  missing; failures surface as user-visible notifications.
- `--autostart` refuses politely off-macOS instead of writing a
  `~/Library/LaunchAgents` folder on Linux; on macOS it now prefers the
  supported `launchctl bootstrap`/`bootout` verbs, falling back to the
  deprecated `load`/`unload`.
- `validate_setup` reports a broken audio backend (`OSError`) instead of
  only a missing `sounddevice` package.

## [0.3.2] — 2026-07-09

### Fixed
- The DMG bootstrap now executes the virtual-environment Python interpreter at
  its original path, preventing a silent dynamic-library crash on launch.
- Native startup failures now show an alert with a direct link to the launcher
  log instead of making the app appear to do nothing.
- First-run Tk onboarding runs in an isolated process, so an incompatible
  system Tk build falls back to local transcription without killing the app.
- Menu-bar settings no longer clear uninitialized native submenus during
  startup.

## [0.3.1] — 2026-07-09

### Fixed
- The notarized macOS app now carries the hardened-runtime entitlements for
  microphone input and Apple Events, allowing recording and auto-paste to
  pass macOS privacy enforcement.
- DMGs now use a small native launcher so macOS attributes Microphone and
  Accessibility consent to OpenVoiceFlow instead of its Python bootstrap.
- First launch uses the native macOS consent prompts and no longer stacks two
  conflicting custom permission dialogs.

## [0.3.0] — 2026-07-08

The pre-publish readiness pass.

### Added
- Pytest scaffold under `tests/` with regression tests for every
  Wave-1 ship-stopper (`test_python39_compat`, `test_install_sh`,
  `test_config_migration`, `test_onboarding`, `test_voice_commands_count`,
  `test_updater`) plus privacy invariants (`test_chmod_600`,
  `test_privacy_defaults`) and package smoke tests. 60 tests total,
  green on Python 3.9, 3.10, and 3.11.
- `[dev]` extras in `pyproject.toml` (pytest, pytest-cov, ruff, build, twine).
- CI Python matrix: 3.9, 3.10, 3.11 on macos-latest. Lint is now a
  blocking step. A separate `build` job exercises `python -m build` and
  `twine check`.
- `--update-check on/off` CLI flag and matching `update_check` config key
  for opting out of the daily GitHub-Releases ping.
- `--log-transcripts on/off` CLI flag for explicit control of the
  `~/.openvoiceflow/logs/` daily files.
- "Privacy at a glance" panel in the README that maps every on-disk file
  and every network egress in one table.
- `voiceflow/_secure_io.py` — `secure_write_json()` and `secure_chmod()`
  helpers that all config / profile / dictionary / snippets / stats /
  daily-log writes now go through, enforcing mode 600.
- Community-health docs: SECURITY, PRIVACY, CONTRIBUTING, CODE_OF_CONDUCT,
  SUPPORT, VERSIONING, AGENTS, plus docs/COMPLIANCE, docs/COMPATIBILITY,
  docs/THREAT_MODEL, docs/ARCHITECTURE, docs/legal/DPA-template,
  docs/legal/THIRD_PARTY_NOTICES. ~14 files, ~2,100 lines.
- `RELEASE.md` — maintainer's three-command playbook plus
  when-things-go-wrong table.
- `.github/workflows/release.yml` rebuilt: tag-driven, Trusted Publisher
  PyPI publish on non-pre-release tags, split arm64/x86_64 DMG attach,
  `verify-version` gate that fails the release if tag ↔ pyproject ↔
  `__version__` disagree.

### Changed
- **Config-key migration:** `cleanup_prompt` → `llm_prompt`. Existing
  `~/.openvoiceflow/config.json` files are migrated transparently on load;
  the rename was the v0.2.0 schema change that previously dropped users'
  custom prompts on upgrade. (Fixes SS5.)
- **Privacy defaults flipped to off for fresh installs.** New users get
  `log_transcripts: False` and `auto_learn: False` until they opt in via the
  Know Me onboarding interview. **Existing users keep their setting** — the
  migration logic only applies the new defaults when no config exists.
- `install.sh` shim now `exec`s the pip-installed `openvoiceflow` console
  script directly instead of `python3 -m openvoiceflow` (which never existed —
  the module is `voiceflow`). (Fixes SS2.)
- **Lint is now blocking in CI.** Previously `ruff check` was advisory; the
  43-finding backlog meant noise floor only ever climbed.
- README hero rewritten so the privacy framing matches the actual data flow
  (audio is local; transcripts go to whatever LLM backend you pick; default
  Gemini is cloud, Ollama is local).

### Fixed
- **Code-review pass (2026-07)** — full-codebase review; the notable fixes:
  - Streaming mode + snippet match no longer crashes with a `NameError`
    (the dictation was silently lost with only an error sound).
  - OpenAI, Anthropic, and Groq backends now honor per-app style and app
    context (previously silently dropped — the per-app style feature only
    worked on OpenRouter/Ollama).
  - Empty LLM responses fall back to the raw transcript instead of pasting
    nothing.
  - Custom voice commands containing backslashes no longer crash every
    dictation; command expansions are no longer re-processed by later
    commands (single-pass replacement).
  - Snippet triggers only match on word boundaries — a trigger like `sig`
    no longer swallows a dictation starting with "significant…".
  - Menu bar: LLM Backend / Hotkey / Style submenus are now populated at
    startup (previously empty until first use); Streaming/Auto-Style/
    Auto-Learn toggles now apply to the running session; stopping or
    quitting aborts an in-flight recording instead of orphaning the
    whisper-stream process (hot mic).
  - Corrupt `config.json` no longer bricks every CLI entry point — the bad
    file is preserved as `config.json.corrupt` and defaults are restored.
  - Whisper model downloads use `curl --fail` with a temp file, so an HTTP
    error page or interrupted transfer can't be mistaken for a valid model
    forever after (fixed in `transcriber.py`, `install.sh`, and the DMG
    launcher).
  - Batch transcription timeout raised 30 s → 300 s so long dictations
    aren't discarded; Ollama cleanup timeout raised 30 s → 120 s for cold
    model loads.
  - Mic failures during recording start are surfaced (notification + error
    sound) instead of being silently swallowed with stale state.
  - Overlay no longer sticks on screen after too-short/no-speech/error
    aborts.
  - Selected-text capture no longer erases image/file clipboards when
    nothing was selected; `pbpaste`/`pbcopy` calls have timeouts.
  - `--show-config` no longer masks `hotkey` (over-broad secret matching);
    `--streaming-step` validates its value and `0` is no longer ignored;
    `--language` no longer crashes on a null `whisper_model`; env-var-only
    API-key setups aren't forced through onboarding on every launch.
  - Onboarding: re-running the wizard and switching backends no longer
    saves the old backend's key under the new backend's field; the Finish
    button survives a corrupt config; headless runs fail with instructions
    instead of a traceback (also fixed for `--profile`).
  - Interview: pressing Escape on the final screen no longer mislabels a
    saved profile as skipped.
  - `--autostart on` fails with a clear message when the executable can't
    be resolved (previously installed a LaunchAgent that silently never
    launched); the plist is generated with `plistlib` so paths containing
    `&` can't produce invalid XML.
  - `install.sh` works under `curl | bash` (wizard prompts read from
    `/dev/tty`), installs from the script's own directory instead of the
    CWD, creates `~/.zshrc` when no shell rc exists, and uses
    `set -euo pipefail`.
  - Release workflow: DMG job sequenced after the PyPI job so the two
    release-upload steps can't race creating the same GitHub Release.

### Changed (code-review pass)
- The typed 🎙 recording indicator is now opt-in
  (`"recording_indicator": true`): it edits the frontmost document and
  could delete a user character when focus changed mid-dictation; the
  overlay HUD remains the default recording feedback.
- `paste_text` no longer moves the caret to end-of-line before pasting —
  text is pasted at the cursor, as documented.
- `--set-key BACKEND -` reads the key from stdin so it stays out of shell
  history and `ps` output (used by `install.sh`, which also hides key input).

### Security (code-review pass)
- Config/profile/dictionary writes are atomic and created with mode 600
  from the first byte (previously created 644 then chmod'd — a crash
  mid-write could truncate the file or leave secrets world-readable).
- `~/.openvoiceflow/` is chmod 700; LaunchAgent stdout/stderr logs are
  pre-created with mode 600 (they capture dictated text via stdout).
- Update-notification strings from the GitHub API are escaped before
  AppleScript interpolation (a crafted release tag/URL could otherwise
  break out of the string literal).
- Internal `docs/superpowers/` documents removed from the repository, and
  the website build excludes any such directory as defense-in-depth.

- **SS2** — `install.sh` shim no longer crashes with
  `ModuleNotFoundError: No module named 'openvoiceflow'`.
- **SS3** — `from __future__ import annotations` added to all 30 modules
  using `X | None` syntax. `pip install .` and `openvoiceflow --version`
  now work on Python 3.9 (macOS 12 default) in addition to 3.10 / 3.11.
- **SS5** — Silent loss of custom `cleanup_prompt` on v0.1 → v0.2 upgrade.
  Migration now preserves the user's prompt under the new key.
- **SS6** — Onboarding "Personalize OpenVoiceFlow" button no longer
  silently swallows every exception from `interview.run_interview()`.
  Errors surface with a logged traceback and an in-app message.
- The cargo-culted PyObjC import in `overlay.py` that broke the module
  for anyone installing without the `[overlay]` extra.
- 43 lint findings (37 unused imports, 4 placeholder-less f-strings,
  1 multiple-statements, 1 unused variable). All resolved; lint now gates CI.

### Security
- All `~/.openvoiceflow/*.json` files (config, profile, dictionary,
  snippets, stats) and the daily transcript logs are written with
  mode 600 — owner-only — instead of inheriting umask 022. API keys
  and personal data are no longer world-readable on default macOS
  user accounts.
- Lint gating in CI closes the "style debt grew silently" loop.
- Twelve community-health files added so a procurement reviewer can find
  the answers they need without filing an issue: `SECURITY.md`,
  `PRIVACY.md`, `THREAT_MODEL.md`, `COMPLIANCE.md`, `CODE_OF_CONDUCT.md`,
  `CONTRIBUTING.md`, `SUPPORT.md`, `CHANGELOG.md` (this file),
  `VERSIONING.md`, `COMPATIBILITY.md`, `legal/DPA-template.md`,
  `legal/THIRD_PARTY_NOTICES.md`.

---

## [0.2.0] — 2026-03-15

**Know Me, Auto-Learn, Streaming.** Personalization stack landed. The
arc shifted from "hotkey-to-text utility" to "personal-context-aware
dictation that gets smarter the more you use it."

### Added
- **Know Me** — tkinter onboarding interview. Captures name, occupation,
  industry, frequently-mentioned names/tools, communication style.
  Output is injected into every LLM cleanup prompt as system context.
- **Auto-learn** — watches the focused text field via the macOS
  Accessibility API for 30 seconds after every paste and learns
  word-level substitutions from your edits. Levenshtein-gated,
  substitutions only (never inserts/deletes), 5-sample minimum.
- **Streaming transcription** via `whisper-stream` with
  refinement-replacement and Jaccard-overlap deduplication. Falls back
  to non-streaming for the canonical text.
- **Per-app context + per-app styles** — frontmost-app detection via
  Apple events; the cleanup prompt picks up the right style automatically
  (e.g. terse in Slack, formal in Mail).
- **Voice commands** — say "new line", "period", "delete that", etc.
  Configurable via `--add-command` / `--remove-command` /
  `--list-commands` / `--voice-commands on/off`.
- **Clipboard / selected-text context** — whatever's selected when you
  start dictating gets handed to the LLM as context.
- **History search** — `--search QUERY` greps the daily transcript logs.
- **Voice snippets** — trigger-phrase → expansion. `--add-snippet` /
  `--remove-snippet` / `--list-snippets`.
- **Personal dictionary** — proper-noun and acronym table.
  `--add-word` / `--remove-word` / `--list-words`.
- **Launch-at-login** — `--autostart on/off`; writes a LaunchAgent plist.
- **Statistics** — `--stats` shows dictations, words, time saved.
- **Auto-update notifier** — once-a-day check against the GitHub
  Releases API; quiet on failure.
- **Floating macOS overlay HUD** — visual feedback during recording,
  streaming, and auto-learn moments.
- New CLI flags across the board: `--version`, `--show-config`,
  `--set-prompt`, `--clear-prompt`, `--set-key`, `--app-style`,
  `--remove-app-style`, `--list-app-styles`, `--auto-style on/off`,
  `--streaming on/off`, `--auto-learn on/off`.

### Changed
- DMG installer split into separate `arm64` and `x86_64` artifacts —
  one-click install on any Mac, no Rosetta dance.
- `pyproject.toml` gained an `[overlay]` extra for the optional PyObjC
  dependencies (Cocoa, Quartz). `rumps` (the menubar lib) transitively
  installs Cocoa, so menubar users get the HUD by default.
- Codebase grew from ~13 modules to ~28. Backend `cleanup()` interface
  now accepts `context`, `app_context`, `override_style`; all 5 existing
  backends were updated consistently.
- Anthropic default model: `claude-3-5-haiku-20241022`.
- Groq default model: `llama-3.1-8b-instant`.

### Fixed
- 22 bugs from a deep QA audit (#3): debounce on the recording hotkey,
  auto-paste timing window, error reporting in `system.py`, and a long
  tail of small UX papercuts.

---

## [0.1.1] — 2026-03-01

Bug-fix release.

### Fixed
- Rosetta + macOS compatibility. The launcher now smart-detects
  architecture (Apple Silicon vs Intel) and bootstraps the right venv.
- First-launch dependency installation: `brew`, `whisper-cpp`, the
  `ggml-*.bin` model, and the Python venv now install on demand
  instead of failing if anything is missing.
- DMG install path on Intel Macs.
- Several broken GitHub URLs across the README and install scripts.

---

## [0.1.0] — 2026-02-22

Initial release.

### Added
- 13-module Python package (`voiceflow/`).
- Local transcription via `whisper.cpp`. Audio never leaves the Mac.
- Five LLM cleanup backends: Gemini, Groq, OpenAI, Anthropic, Ollama,
  plus a "none" pass-through.
- tkinter onboarding wizard for first-run setup.
- DMG installer (universal, with Rosetta fallback on Intel).
- Hotkey-driven dictation with auto-paste at the cursor.
- Configurable prompt, model, hotkey, language, and style.
- MIT licensed.

---

## Compare links

[Unreleased]: https://github.com/shimoverse/openvoiceflow/compare/v0.3.6...HEAD
[0.3.6]: https://github.com/shimoverse/openvoiceflow/compare/v0.3.5...v0.3.6
[0.3.5]: https://github.com/shimoverse/openvoiceflow/compare/v0.3.4...v0.3.5
[0.3.4]: https://github.com/shimoverse/openvoiceflow/compare/v0.3.3...v0.3.4
[0.3.3]: https://github.com/shimoverse/openvoiceflow/compare/v0.3.2...v0.3.3
[0.3.2]: https://github.com/shimoverse/openvoiceflow/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/shimoverse/openvoiceflow/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/shimoverse/openvoiceflow/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/shimoverse/openvoiceflow/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/shimoverse/openvoiceflow/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/shimoverse/openvoiceflow/releases/tag/v0.1.0
