# Build runbook — OpenVoiceFlow native (for a Mac-equipped agent/dev)

**Status: this builds and ships.** The app compiles in CI on every PR (the
`native-build` job — macos-15 / Xcode 16.4), has been built locally on a Mac,
and 0.4.3 shipped as a signed, notarized, stapled DMG from
`release-native.yml`. The phases below are kept as the history of how it got
here and as a reference for the build/sign/notarize pipeline — they are no
longer a to-do list, and the "never been compiled" caveat that used to open
this file is obsolete.

Prereqs: macOS 14+, Xcode 15+ (or the matching Command Line Tools), an Apple
Developer ID (for signing/notarization), `git`.

## Phase 0 — compile the core loop

```bash
cd native
swift build            # resolves WhisperKit + Sparkle, compiles Sources/
```

Fix what the compiler flags. Likely first-pass issues to expect and resolve:
- **WhisperKit API drift.** Pin an actual released tag (`swift package
  resolve` then check `Package.resolved`); adjust `WhisperKitConfig` /
  `DecodingOptions` / `transcribe(audioArray:)` to that version's signatures
  in `Transcriber.swift`.
- **Sparkle wiring.** Sparkle needs an `SPUStandardUpdaterController` and the
  `SUFeedURL`/`SUPublicEDKey` in Info.plist; it's declared as a dependency but
  not yet instantiated — add the updater to `OpenVoiceFlowApp` when you host an
  appcast (can be deferred; remove the dependency to build without it first).
- **`MenuBarExtra` label** with a dynamic SF Symbol may need `.menuBarExtraStyle`.

Then run it headless to sanity-check the loop:
```bash
swift run        # grant Accessibility/Input Monitoring/Mic when prompted
```

## Phase 1 — wrap into a proper `.app` (Xcode)

A menu-bar app needs an Info.plist, entitlements, and code signing, so move to
an Xcode app target (keep it building the same `Sources/`):

1. Create a macOS App target "OpenVoiceFlow" (SwiftUI lifecycle, LSUIElement).
2. Add the local package (or the two remote packages) as dependencies.
3. Set the target's Info.plist from [`Info.plist`](Info.plist) and code-signing
   entitlements from [`OpenVoiceFlow.entitlements`](OpenVoiceFlow.entitlements).
4. Enable **Hardened Runtime**. Do NOT enable App Sandbox (a global
   `CGEventTap` + arbitrary-app paste can't run sandboxed).
5. Build & run; walk the onboarding, grant the three permissions, and verify
   the full loop: **hold hotkey → speak → release → text pastes at the cursor.**
   Explicitly verify the **fn/Globe key** works as push-to-talk (the whole
   point — set System Settings ▸ Keyboard ▸ "Press 🌐 to: Do Nothing" first).

## Phase 2 — bundle the model (offline first launch)

Add a WhisperKit CoreML model to the app's Resources and point
`Transcriber.warmUp()` at `Bundle.main` so there's **no first-run download**.
Verify a fresh Mac, offline, transcribes on first launch.

## Phase 3 — sign, notarize, DMG

```bash
xcodebuild -scheme OpenVoiceFlow -configuration Release \
  -derivedDataPath build archive ...
codesign --force --options runtime --timestamp \
  --entitlements native/OpenVoiceFlow.entitlements \
  --sign "Developer ID Application: …" OpenVoiceFlow.app
xcrun notarytool submit OpenVoiceFlow.app.zip --keychain-profile ovf --wait
xcrun stapler staple OpenVoiceFlow.app        # staple the .app, not just the DMG
# build DMG (reuse the repo's create-dmg approach), staple + notarize the DMG too
```

Gate on `spctl --assess --type execute OpenVoiceFlow.app` before shipping.

## Phase 4 — feature parity (milestones, in priority order)

The scaffold ships the core loop. Port from the Python app next:
1. Per-app style detection (`NSWorkspace.frontmostApplication`).
2. Voice commands + snippets (pre-cleanup text substitution).
3. Streaming partial results in the HUD (WhisperKit streaming API).
4. Know-Me profile + prompt personalization.
5. Auto-learn corrections, statistics, transcript logging (0600), history search.
6. Full Settings window; Sparkle appcast + EdDSA key; launch-at-login (SMAppService).
7. Doctor-equivalent diagnostics.

## Phase 5 — CI

Add a macOS GitHub Actions job: `swift build` + `swift test` on `native/`, and
a signed release workflow mirroring the Python one. Keep the Python app as the
shipping product until native reaches parity + passes a real on-device test.

---

### Map: Python module → native file

| Python | Native |
| --- | --- |
| `app.py` (orchestrator) | `AppController.swift` |
| `recorder.py` | `AudioCapture.swift` |
| `transcriber.py` (whisper.cpp) | `Transcriber.swift` (WhisperKit) |
| hotkey (pynput) | `HotkeyEngine.swift` (CGEventTap — **fn works**) |
| `system.py` paste | `Paster.swift` (CGEventPost) |
| `overlay.py` | `HUDController.swift` |
| `menubar.py` (rumps) | `OpenVoiceFlowApp.swift` MenuBarExtra |
| `onboarding.py`/`interview.py` (tkinter) | `OnboardingView.swift` (SwiftUI) |
| `llm/*` | `CleanupProvider.swift` |
| `config.py` + keys in JSON | `Settings.swift` + **Keychain** |
| doctor / permissions | `Permissions.swift` |

---

## Phase D — Design implementation (added after the Claude Design hand-off)

The full design system's raw sources lived in `native/design/*.dc.html` (now in git history) and
is now implemented in Swift:

- `DesignTokens.swift` — every color/radius/spring token + the shared
  `Voiceline` waveform math (envelope, window, wobble — verbatim from design).
- `HUDController.swift` — all HUD states from phase 01: summon (90 ms fade +
  9 px rise), listening with live RMS-driven wave (dim/ember split at
  amp 0.04), transcribing coil (1.1 rev/s), cleanup shimmer (150 px/s),
  success tick, three error states with action buttons + exact copy,
  long-dictation timer promotion, max-duration amber countdown, Reduce
  Motion variants (9-dot meter / 3 pulsing dots), VoiceOver labels.
- `StatusIcon.swift` — the 24×16 template menu-bar glyph, all six states
  drawn from the phase-02 math, animated at 20 fps only while
  listening/working and never under Reduce Motion.
- `OpenVoiceFlowApp.swift` — the phase-02 dropdown item-for-item (header
  state lines, Start/Stop ⌘⇧D, Pause for 1 hour/Resume, Hotkey/Model/Cleanup
  submenus with captions, Open Dashboard ⌘D, Quit ⌘Q).
- `DashboardView.swift` — phase 03: 212 pt sidebar, Home stats + week chart,
  designed empty states for History/Dictionary/Snippets, Styles rows,
  Know-Me, grouped Settings. Data stores are the next milestone; the empty
  states are the designed default until then.
- `OnboardingView.swift` — phase 04: welcome, three permission primings with
  mock-dialog previews, keycap hotkey picker + 700 ms rehearsal, narrated
  model download checklist, say-hello finale.
- `native/assets/` — phase 06 renders: appicon-1024(+light), dmg-bg@2x,
  og-card, readme-banner, favicon.svg (all generated from the spec's math).

**Mac-build follow-ups for this phase**: wire `ModelDownloadStep` progress to
WhisperKit's real download callback; feed `AudioCapture.onLevel` timing from
`CADisplayLink` if the Canvas timeline judders; convert appicon PNGs via
`iconutil`/Icon Composer into `AppIcon.icon`; export `ovf-mb-*@{1x,2x}.pdf`
from `StatusIconRenderer` if template PDFs are preferred over runtime
drawing; hook `Check for Updates…` to Sparkle.

---

## Phase E — Feature parity port (dictionary, snippets, styles, profile, history)

The Python feature modules are now ported to Swift and wired into the app:

- `FeatureStores.swift` — `ProfileStore`, `DictionaryStore`, `SnippetStore`,
  `StyleStore`, `HistoryStore` (+ derived stats: words today/total, streak,
  last-7-days). All persist as JSON in Application Support/OpenVoiceFlow,
  each an `ObservableObject` with a `promptFragment` mirroring the Python
  `get_*_prompt_fragment` helpers.
- `KnowMeInterview.swift` — the light 5-question interview; answers write the
  profile and seed the dictionary (double coverage, like `profile_to_dictionary`).
- `CleanupProvider.swift` — `cleanup(_:style:context:)` now injects the
  personal-context fragment (profile + dictionary + snippet hints) into the
  system prompt.
- `AppController.process()` — snippet exact-trigger short-circuit (no LLM),
  per-app style resolution from the frontmost app, personal context into
  cleanup, and history/stats logging on every dictation.
- `DashboardView.swift` — Home stats + week chart, History, Dictionary,
  Snippets, Styles, and Know-Me panes are now bound to the live stores
  (add/remove/edit all persist); the interview opens as a sheet.

**Mac-build note for this phase**: this is Linux-authored Swift — expect the
compile to surface real fixes (SwiftUI `Picker` tag types, `@ObservedObject`
init ordering, WhisperKit API drift). Fix without simplifying the behavior;
the stores' JSON shapes intentionally match the Python files so a user's
`~/.openvoiceflow/*.json` data could later be migrated.

---

## Phase F — signed release + in-app updates (the finish line)

Sparkle is now instantiated (`Updater.swift`; started at launch in
`OpenVoiceFlowApp`; the menu-bar **Check for Updates…** drives a manual check),
and a full release pipeline exists:

- **`.github/workflows/release-native.yml`** — push a `native-v*` tag → a
  macOS runner builds a **universal, Developer-ID-signed, Apple-notarized,
  stapled** DMG and attaches it (plus `appcast.xml`) to the GitHub Release.
  A `-rc*`/`-beta*` suffix marks it a pre-release. It **reuses the same Apple
  secrets as `release.yml`** — no new signing secrets.
- **`native/scripts/build-app.sh`** — `xcodegen → archive (arm64+x86_64) →
  export (developer-id) → notarize app → staple → DMG → notarize DMG →
  staple`. Runnable locally: `OVF_NOTARIZE=0 bash native/scripts/build-app.sh`
  for an unsigned smoke build.
- **`native/scripts/appcast.sh`** — signs the DMG with the Sparkle EdDSA key
  and writes `dist/appcast.xml`. **Required:** the release now fails if
  `SPARKLE_ED_PRIVATE_KEY` is unset (shipping without a signed feed silently
  breaks in-app updates), so the key must be configured before tagging.

**The only remaining Mac-gated steps** (see `RELEASE.md`
for the copy-paste version):

1. **Generate the Sparkle keypair once** (`generate_keys` from the Sparkle
   tools). Add the printed **public** key to `Info.plist` as `SUPublicEDKey`
   (uncomment the placeholder) in the same commit; add the **private** key as
   the repo secret `SPARKLE_ED_PRIVATE_KEY`.
2. **Confirm the Apple secrets** already used by `release.yml` are present
   (they are, since the Python DMGs ship signed).
3. **Push the tag** `native-v0.4.0` (a `native-v0.4.0-rc1` first is wise). Tag
   pushes are blocked from the Linux agent — this is yours.
4. The pipeline publishes the notarized DMG + appcast to the Release. Then, in
   the private `shimoverse/openvoiceflow-web` repo, drop the DMG into
   `docs/downloads/` and the appcast into `docs/appcast.xml` and merge — that
   merge is what starts updates. See RELEASE.md.

CI note: `ci.yml` compiles the *Python* app only — the native Swift is not in
CI, so a `swift build` (or the archive step above) on your Mac is what
validates `Updater.swift` and the Phase E stores.
