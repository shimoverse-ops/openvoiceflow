"""Content for the OpenVoiceFlow manual. Rendered by build_docs.py.

Ground rules, from AGENTS.md: every claim here must be true of the shipped
app (v0.5.24). Where behaviour is surprising, say so plainly rather than
describing the version we wish we shipped. When in doubt, understate.
"""
from __future__ import annotations

DL = "../download.html"
IN = "../install.html"

PAGES: dict[str, dict] = {}

# ── Getting started ────────────────────────────────────────────────────

PAGES["index"] = {
    "head_title": "OpenVoiceFlow Documentation — Setup, Features, Troubleshooting",
    "title": "OpenVoiceFlow documentation",
    "description": "OpenVoiceFlow's manual for the on-device macOS dictation app, free for personal and qualifying noncommercial use: install, permissions, models, personalization, cleanup, and troubleshooting.",
    "lede": "Everything about running OpenVoiceFlow on your Mac — from first launch to the exact bytes that do and don't leave your machine. Written against the shipping app, version 0.5.24.",
    "body": """
        <p>OpenVoiceFlow is a source-available push-to-talk dictation app for macOS, free for personal and qualifying noncommercial use. You hold a key, speak, release, and cleaned text lands at your cursor in whatever app you were using. Whisper runs on your Mac, so your audio never leaves it. Business or other commercial use requires a separate license from Shimoverse Studios.</p>

        <div class="callout tip">
          <span class="callout-label">New here?</span>
          <p>Two minutes gets you dictating: <a href="quickstart.html">Quickstart</a>. If you haven't downloaded the app yet, start at the <a href="%s">download page</a>.</p>
        </div>

        <h2 id="start">Start here</h2>
        <div class="docs-cards">
          <a class="docs-card" href="quickstart.html"><span class="docs-card-title">Quickstart</span><span class="docs-card-desc">Download to first dictated sentence, in about two minutes.</span></a>
          <a class="docs-card" href="installation.html"><span class="docs-card-title">Installation</span><span class="docs-card-desc">The DMG, the Gatekeeper prompt, and the macOS 12–13 fallback build.</span></a>
          <a class="docs-card" href="permissions.html"><span class="docs-card-title">Permissions</span><span class="docs-card-desc">The three macOS permissions, what each one buys, and how to fix a stuck grant.</span></a>
          <a class="docs-card" href="models.html"><span class="docs-card-title">Whisper models</span><span class="docs-card-desc">Which of the four engines to pick for your Mac, and what changes between them.</span></a>
        </div>

        <h2 id="what">What OpenVoiceFlow does</h2>
        <table>
          <thead><tr><th scope="col">Capability</th><th scope="col">Where it runs</th><th scope="col">Details</th></tr></thead>
          <tbody>
            <tr><td>Push-to-talk dictation</td><td>Your Mac</td><td><a href="dictation-basics.html">Hold a key, speak, release</a> — works in any app with a text cursor.</td></tr>
            <tr><td>Speech-to-text</td><td>Your Mac</td><td><a href="how-transcription-works.html">On-device Whisper via WhisperKit</a>, four model sizes.</td></tr>
            <tr><td>Personal dictionary</td><td>Your Mac + cleanup</td><td><a href="dictionary.html">Names and jargon it should never misspell</a>.</td></tr>
            <tr><td>Snippets</td><td>Your Mac</td><td><a href="snippets.html">Say a short trigger, get the long text</a>. No network call.</td></tr>
            <tr><td>Per-app styles</td><td>Cleanup</td><td><a href="styles.html">Casual in Slack, formal in Mail</a>.</td></tr>
            <tr><td>AI cleanup</td><td>Off by default</td><td><a href="ai-cleanup.html">Optional</a> — your own API key, or a fully local model.</td></tr>
          </tbody>
        </table>

        <h2 id="honest">What it does not do</h2>
        <p>An honest manual saves you the trouble of looking for something that isn't there. As of 0.5.24:</p>
        <ul>
          <li><strong>macOS only.</strong> macOS 14 (Sonoma) or newer, Apple Silicon and Intel. There is no Windows or Linux build. iOS and Android are in development and cannot be downloaded today.</li>
          <li><strong>No spoken punctuation commands.</strong> Saying &ldquo;comma&rdquo; types the word &ldquo;comma&rdquo;. Whisper punctuates from sentence structure on its own, and <a href="ai-cleanup.html">AI cleanup</a> handles the rest if you turn it on.</li>
          <li><strong>No meeting recording, no cloud sync, no accounts.</strong> There is no server your dictation history syncs to.</li>
          <li><strong>Dictation itself is never reported anywhere.</strong> As of 0.5.7, an opt-out anonymous usage summary (word/time totals, which features you use, a display name you choose) powers an in-app leaderboard — never audio, never dictated text. Off in one toggle: <a href="privacy-architecture.html#analytics">details and how to turn it off</a>.</li>
        </ul>

        <h2 id="map">The whole manual</h2>
        <div class="docs-cards">
          <a class="docs-card" href="dictation-basics.html"><span class="docs-card-title">Dictation basics</span><span class="docs-card-desc">The hold-and-speak loop, the HUD, limits, and what each state means.</span></a>
          <a class="docs-card" href="accuracy.html"><span class="docs-card-title">Improving accuracy</span><span class="docs-card-desc">The changes that actually move the needle, in order of effect.</span></a>
          <a class="docs-card" href="settings.html"><span class="docs-card-title">Settings reference</span><span class="docs-card-desc">Every setting, its default, and what it changes.</span></a>
          <a class="docs-card" href="privacy-architecture.html"><span class="docs-card-title">Privacy architecture</span><span class="docs-card-desc">Every file written and every byte that can leave your Mac.</span></a>
          <a class="docs-card" href="troubleshooting.html"><span class="docs-card-title">Troubleshooting</span><span class="docs-card-desc">Symptoms, causes, and fixes for the problems people actually hit.</span></a>
          <a class="docs-card" href="faq.html"><span class="docs-card-title">FAQ</span><span class="docs-card-desc">Short answers to the questions we get most.</span></a>
        </div>
""" % DL,
}

PAGES["quickstart"] = {
    "head_title": "OpenVoiceFlow Quickstart — Dictating in Two Minutes",
    "title": "Quickstart",
    "description": "Install OpenVoiceFlow and dictate your first sentence in about two minutes: download the DMG, grant three permissions, pick a speech model, and hold the fn key.",
    "lede": "From a fresh Mac to your first dictated sentence. The only slow part is the one-time model download, and the app tells you how long that will take.",
    "howto": (
        "Set up OpenVoiceFlow and dictate for the first time",
        "Install OpenVoiceFlow for personal or qualifying noncommercial use on macOS, grant the three required permissions, download an on-device Whisper model, and dictate a first sentence.",
        "PT5M",
        [
            ("Download and install", "Download the universal DMG from openvoiceflow.com, open it, and drag OpenVoiceFlow into your Applications folder."),
            ("Open it from Applications", "Launch the app from Applications. macOS shows a one-time 'downloaded from the Internet' confirmation; click Open."),
            ("Grant three permissions", "Onboarding asks for Microphone, Accessibility, and Input Monitoring in order. Each unlocks when the previous one is granted."),
            ("Pick a speech engine", "Choose a Whisper model. The one marked RECOMMENDED is chosen for your Mac's chip and free disk space. It downloads once."),
            ("Hold the key and talk", "Click into any text field, hold the fn key, say a sentence, then release. The text appears at your cursor."),
        ],
    ),
    "body": """
        <h2 id="install">1. Install the app</h2>
        <p><a href="%s">Download the DMG</a> — one universal build for Apple Silicon and Intel, Developer-ID signed and Apple-notarized. Open it and drag OpenVoiceFlow into Applications.</p>
        <div class="callout warn">
          <span class="callout-label">Expect one macOS prompt</span>
          <p>Open the app <em>from Applications</em>, not from the disk image — macOS cannot launch an app off a mounted DMG. The first launch shows a &ldquo;downloaded from the Internet&rdquo; confirmation. That is normal for every notarized app outside the App Store; click <strong>Open</strong>. Nothing is broken.</p>
        </div>

        <h2 id="permissions">2. Grant three permissions</h2>
        <p>Onboarding walks you through them one at a time, and each row unlocks only when the previous one is granted:</p>
        <ol>
          <li><strong>Microphone</strong> — so the app can hear you. It listens only while the key is held.</li>
          <li><strong>Accessibility</strong> — so it can paste at your cursor. It presses <kbd>⌘V</kbd> on your behalf; it does not read your screen.</li>
          <li><strong>Input Monitoring</strong> — so the push-to-talk key works in every app. One key is watched; every other keystroke passes straight through.</li>
        </ol>
        <p>If you click Allow and nothing seems to happen, the screen has an <strong>Open System Settings</strong> escape hatch — full detail in <a href="permissions.html">Permissions</a>.</p>

        <h2 id="model">3. Pick a speech engine</h2>
        <p>Four Whisper models are offered. One is marked <strong>RECOMMENDED</strong>, chosen from your Mac's chip and free disk space: <code>Large turbo</code> on Apple Silicon with room to spare, <code>Small</code> otherwise.</p>
        <table>
          <thead><tr><th scope="col">Engine</th><th scope="col">Size</th><th scope="col">Best for</th></tr></thead>
          <tbody>
            <tr><td>Tiny</td><td>39 MB</td><td>Fastest. Fine for quick notes.</td></tr>
            <tr><td>Small</td><td>466 MB</td><td>Everyday dictation on any Mac.</td></tr>
            <tr><td>Medium</td><td>1.5 GB</td><td>Hears more, asks more of your Mac.</td></tr>
            <tr><td>Large turbo</td><td>1.6 GB</td><td>Hears the most. Best on Apple Silicon.</td></tr>
          </tbody>
        </table>
        <p>The download runs once and shows size, speed, and an estimate. When the bar reaches the top it keeps working for a moment — that is macOS compiling the model for your Mac, and it only happens on first run. Details in <a href="models.html">Whisper models</a>.</p>

        <h2 id="talk">4. Say something</h2>
        <p>The last onboarding screen asks you to hold the key and talk. Words appear as you speak them. Release, and the text is inserted.</p>
        <p>After that, the loop is the same everywhere: click into any text field, hold <kbd>fn</kbd>, speak, release.</p>

        <div class="callout tip">
          <span class="callout-label">If fn does something else on your Mac</span>
          <p>By default macOS may open the emoji picker or Dictation when you press <kbd>fn</kbd>. Set <strong>System Settings ▸ Keyboard ▸ Press 🌐 to</strong> → <strong>Do Nothing</strong>, or pick a different key in <a href="hotkeys.html">Hotkeys</a>.</p>
        </div>

        <h2 id="next">What to do next</h2>
        <ul>
          <li>Teach it the names it gets wrong — <a href="dictionary.html">Personal dictionary</a> (needs <a href="ai-cleanup.html">cleanup</a> on).</li>
          <li>Make a spoken shortcut for text you type constantly — <a href="snippets.html">Snippets</a> (works with cleanup off).</li>
          <li>Decide whether you want <a href="ai-cleanup.html">AI cleanup</a> at all. It ships <strong>off</strong>, and off is a perfectly good place to stay.</li>
        </ul>
""" % DL,
}

PAGES["installation"] = {
    "head_title": "Install OpenVoiceFlow on macOS — DMG, Gatekeeper, Requirements",
    "title": "Installation",
    "description": "How to install OpenVoiceFlow on macOS: system requirements, the signed DMG, the one-time Gatekeeper prompt, the macOS 12–13 fallback build, and where the app puts its files.",
    "lede": "One universal DMG, drag to Applications, done. This page covers the requirements, the prompts macOS shows, and the older-macOS fallback.",
    "body": """
        <h2 id="requirements">Requirements</h2>
        <table>
          <thead><tr><th scope="col">Item</th><th scope="col">Requirement</th></tr></thead>
          <tbody>
            <tr><td>macOS</td><td>14 (Sonoma) or newer</td></tr>
            <tr><td>Chip</td><td>Apple Silicon or Intel — one universal build covers both</td></tr>
            <tr><td>Disk</td><td>~40 MB for the app, plus 39 MB – 1.6 GB for the speech model you choose</td></tr>
            <tr><td>Network</td><td>Only to download the app and its model. Dictation itself works offline.</td></tr>
            <tr><td>Account</td><td>None. There is nothing to sign up for.</td></tr>
          </tbody>
        </table>

        <h2 id="dmg">Install from the DMG</h2>
        <ol>
          <li><a href="%s">Download the DMG</a>. The download page also lists the SHA-256 checksum if you want to verify it.</li>
          <li>Open the DMG and drag <strong>OpenVoiceFlow</strong> into <strong>Applications</strong>.</li>
          <li><strong>Open the app from your Applications folder</strong> — not from the disk-image window. macOS cannot run an app from a mounted image, and this is the single most common first-run confusion.</li>
          <li>Click <strong>Open</strong> at the &ldquo;downloaded from the Internet&rdquo; prompt. You will see it exactly once.</li>
        </ol>
        <div class="callout">
          <span class="callout-label">Why that prompt appears</span>
          <p>The app is Developer-ID signed and notarized by Apple, which is why you get a simple confirmation rather than a block. Every notarized app distributed outside the App Store shows this the first time. If you instead see a hard refusal, you likely have an older unsigned copy — delete it and re-download the current build.</p>
        </div>

        <h2 id="legacy">macOS 12–13</h2>
        <p>The current app requires macOS 14. If you are on Monterey or Ventura, the download page keeps a retained <strong>0.3.6 Apple Silicon</strong> build available. It is end-of-life: it receives no fixes, and its defaults differ from current policy. Updating macOS to 14 is the better path where possible — every Mac that can run OpenVoiceFlow can install Sonoma.</p>
        <p>There is no Intel fallback for macOS 12–13.</p>

        <h2 id="files">Where the app puts things</h2>
        <table>
          <thead><tr><th scope="col">What</th><th scope="col">Where</th></tr></thead>
          <tbody>
            <tr><td>The app</td><td><code>/Applications/OpenVoiceFlow.app</code></td></tr>
            <tr><td>Settings, history, dictionary, snippets, styles, profile</td><td><code>~/Library/Application Support/OpenVoiceFlow/</code></td></tr>
            <tr><td>Downloaded speech models</td><td><code>~/Documents/huggingface/models/argmaxinc/whisperkit-coreml/</code></td></tr>
            <tr><td>API keys (only if you enable cloud cleanup)</td><td>macOS Keychain, service <code>app.openvoiceflow.apikeys</code></td></tr>
          </tbody>
        </table>
        <p>Nothing is written outside your user account, and no installer scripts, kernel extensions, or background daemons are installed. Full detail in <a href="privacy-architecture.html">Privacy architecture</a>; removal in <a href="uninstall.html">Uninstalling</a>.</p>

        <h2 id="menubar">Where the app lives once running</h2>
        <p>OpenVoiceFlow appears as a monochrome waveform icon in the <strong>menu bar</strong> at the top right, and by default also in the <strong>Dock</strong> (click it to open the dashboard). Prefer menu-bar only? Turn off <strong>Show in Dock</strong> in Settings.</p>
        <div class="callout tip">
          <span class="callout-label">Can't find the menu-bar icon?</span>
          <p>On laptops with a notch, a crowded menu bar can hide icons entirely. The dashboard shows a banner when it detects this. Quitting a menu-bar app or two makes room.</p>
        </div>
""" % DL,
}

PAGES["permissions"] = {
    "head_title": "OpenVoiceFlow Permissions on macOS — Microphone, Accessibility, Input Monitoring",
    "title": "Permissions",
    "description": "The three macOS permissions OpenVoiceFlow needs — Microphone, Accessibility, and Input Monitoring — what each one enables, its exact limits, and how to fix a permission that won't take.",
    "lede": "Three switches, granted once. Each one buys exactly one capability, and this page says plainly what each does and does not allow.",
    "faq": [
        ("Why does a dictation app need Accessibility?",
         "Accessibility is the macOS permission that lets one app send keystrokes to another. OpenVoiceFlow uses it to press Command-V on your behalf so text lands at your cursor. It does not read your screen contents. Without it, the app copies the text to your clipboard and asks you to paste manually."),
        ("Why does it need Input Monitoring?",
         "Input Monitoring lets the app notice your push-to-talk key being held while you are working in a different app. Only the one key you choose is acted on; every other keystroke passes straight through untouched."),
        ("Can I revoke a permission later?",
         "Yes. Open System Settings, Privacy and Security, then the relevant pane, and turn OpenVoiceFlow off. The app detects the change within about a second and updates its status. Revoking Microphone or Input Monitoring stops dictation; revoking Accessibility falls back to clipboard paste."),
    ],
    "body": """
        <h2 id="three">The three permissions</h2>
        <table>
          <thead><tr><th scope="col">Permission</th><th scope="col">What it buys</th><th scope="col">Its limit</th></tr></thead>
          <tbody>
            <tr><td>Microphone</td><td>Hearing you</td><td>The app listens only while the key is held. Nothing is captured before or after.</td></tr>
            <tr><td>Accessibility</td><td>Typing for you</td><td>It presses <kbd>⌘V</kbd> on your behalf. It does not read what is on your screen.</td></tr>
            <tr><td>Input Monitoring</td><td>Feeling the key</td><td>One key — the one you choose. Every other keystroke passes straight through.</td></tr>
          </tbody>
        </table>
        <p>All three are macOS-level grants. macOS holds the keys, not the app: you can inspect or revoke any of them at any time in System Settings, and the app has no way to grant itself anything.</p>

        <h2 id="granting">Granting them</h2>
        <p>First-run onboarding asks in order — Microphone, then Accessibility, then Input Monitoring — and unlocks each row only when the previous one is granted. That ordering is deliberate: it keeps three simultaneous system dialogs from stacking up on top of each other.</p>
        <p>You can also grant or re-check them later from <strong>Dashboard ▸ Settings ▸ Permissions</strong>, which shows each one as granted, or offers a <strong>Grant…</strong> button, or an <strong>Open System Settings</strong> button when a permission was previously denied.</p>

        <div class="callout warn">
          <span class="callout-label">Clicked Allow and nothing happened?</span>
          <p>This is the most common permissions snag, and it is usually Accessibility or Input Monitoring. macOS sometimes shows the prompt but does not add the app to the list. The fix: open the relevant pane in <strong>System Settings ▸ Privacy &amp; Security</strong>, click <strong>+</strong>, and pick <strong>OpenVoiceFlow</strong> from your Applications folder. The app watches for the change and picks it up within about a second — no relaunch needed.</p>
        </div>

        <h2 id="checking">Checking them by hand</h2>
        <p>Open <strong>System Settings ▸ Privacy &amp; Security</strong> and look in:</p>
        <ul>
          <li><strong>Microphone</strong> — OpenVoiceFlow should be on.</li>
          <li><strong>Accessibility</strong> — OpenVoiceFlow should be on.</li>
          <li><strong>Input Monitoring</strong> — OpenVoiceFlow should be on.</li>
        </ul>
        <p>If a toggle is present but off, turning it on is enough. If the app is missing from a list entirely, add it with <strong>+</strong>.</p>

        <div class="callout tip">
          <span class="callout-label">After a macOS update or an app move</span>
          <p>macOS ties these grants to the app's code signature and location. Moving the app out of <code>/Applications</code>, or restoring it from a backup, can invalidate a grant. If dictation suddenly stops after an update, re-checking these three panes is the first thing to try.</p>
        </div>

        <h2 id="notgranted">What is never asked for</h2>
        <p>OpenVoiceFlow does not request Screen Recording, Full Disk Access, Automation, Contacts, Calendar, or Photos. It is not sandboxed, but its entitlements request only two capabilities: audio input, and outbound network access used solely for model downloads, update checks, and — if you turn it on — <a href="ai-cleanup.html">cloud cleanup</a>.</p>
""",
}

# ── Using OpenVoiceFlow ────────────────────────────────────────────────

PAGES["dictation-basics"] = {
    "head_title": "Dictation Basics — Push-to-Talk in OpenVoiceFlow",
    "title": "Dictation basics",
    "description": "How push-to-talk dictation works in OpenVoiceFlow: the hold-speak-release loop, what the HUD is telling you, recording limits, and how to pause listening.",
    "lede": "One key, held. Everything else the app does is in service of that gesture, and the floating HUD tells you which stage you are in.",
    "body": """
        <h2 id="loop">The loop</h2>
        <ol>
          <li><strong>Click where the text should go</strong> — any app, any text field.</li>
          <li><strong>Hold the key</strong> (<kbd>fn</kbd> by default) and speak normally.</li>
          <li><strong>Release.</strong> The app transcribes on your Mac and inserts the text at your cursor.</li>
        </ol>
        <p>Because the microphone is live only while the key is down, there is no timeout to race and no mode to remember exiting. Pause mid-sentence to think for as long as you like; the app is still listening as long as you are still holding.</p>

        <h2 id="hud">Reading the HUD</h2>
        <p>A small floating pill appears while you dictate. Its states, in order:</p>
        <table>
          <thead><tr><th scope="col">State</th><th scope="col">Meaning</th></tr></thead>
          <tbody>
            <tr><td>Waveform moving</td><td>Recording. The wave tracks your voice, so a flat line means the app is not hearing you.</td></tr>
            <tr><td>Words appearing</td><td>Live partial transcript — proof it is hearing you, refreshed about three times a second.</td></tr>
            <tr><td>Spool spinning</td><td>Transcribing on your Mac after you released the key.</td></tr>
            <tr><td>Cleaning</td><td>Only if <a href="ai-cleanup.html">AI cleanup</a> is on. Skipped entirely when it is off.</td></tr>
            <tr><td>Result</td><td>The tail of what was inserted, shown briefly before the HUD hides itself.</td></tr>
          </tbody>
        </table>
        <p>Errors surface here too, each with a one-tap action: <strong>No microphone</strong> (opens Sound settings), <strong>Took too long — audio kept</strong> (retry), and <strong>Copied instead — press ⌘V</strong> (see <a href="text-insertion.html">How text is inserted</a>).</p>

        <h2 id="limits">Length limits</h2>
        <ul>
          <li><strong>Minimum:</strong> about half a second. Anything shorter is treated as a mis-tap and discarded — the HUD says so rather than pasting noise.</li>
          <li><strong>Maximum:</strong> five minutes per take by default, adjustable to 1, 2, 5, or 10 minutes in Settings. When the cap is reached the app <em>finishes the take and inserts it</em> — your audio is never thrown away. The cap exists so a key that gets stuck down can't record forever.</li>
        </ul>
        <p>The HUD counts down toward the cap while you hold, so a long take never ends as a surprise.</p>

        <h2 id="pausing">Pausing</h2>
        <p>The menu-bar menu has <strong>Pause for 1 hour</strong>, which stops the app from responding to the hotkey — useful when you are handing your Mac to someone, or when the key you chose is needed for something else. The menu-bar icon shows the paused state, and you can resume from the same menu at any time.</p>

        <div class="callout tip">
          <span class="callout-label">Speak in phrases, not words</span>
          <p>Whisper uses surrounding context to choose between homophones, so dictating a whole clause at natural speed is markedly more accurate than word-by-word delivery. More in <a href="accuracy.html">Improving accuracy</a>.</p>
        </div>

        <h2 id="punctuation">Punctuation</h2>
        <p>Whisper adds punctuation from sentence structure — you generally do not need to do anything. Note that OpenVoiceFlow 0.5.24 has <strong>no spoken-punctuation commands</strong>: saying &ldquo;comma&rdquo; produces the word &ldquo;comma&rdquo;, not the mark. If you want filler words removed and grammar tidied, that is what <a href="ai-cleanup.html">AI cleanup</a> is for.</p>
""",
}

PAGES["hotkeys"] = {
    "head_title": "OpenVoiceFlow Hotkeys — Choosing Your Push-to-Talk Key",
    "title": "Hotkeys",
    "description": "Every push-to-talk key OpenVoiceFlow supports on macOS, how to change it, and how to resolve conflicts with the fn/Globe key and other apps.",
    "lede": "Fourteen keys to choose from, one held at a time. The default is fn — here is how to change it and what to do when macOS wants that key for itself.",
    "body": """
        <h2 id="available">Available keys</h2>
        <table>
          <thead><tr><th scope="col">Key</th><th scope="col">Notes</th></tr></thead>
          <tbody>
            <tr><td><kbd>fn</kbd> / 🌐 Globe</td><td>The default. Reachable by the left hand, unused by most apps — but macOS may claim it (see below).</td></tr>
            <tr><td><kbd>Right ⌘</kbd> / <kbd>Left ⌘</kbd></td><td>Comfortable and rarely held alone. A popular alternative to fn.</td></tr>
            <tr><td><kbd>Right ⌥</kbd> / <kbd>Left ⌥</kbd></td><td>Also rarely held alone.</td></tr>
            <tr><td><kbd>Right ⌃</kbd></td><td>Control on the right side only.</td></tr>
            <tr><td><kbd>F5</kbd> – <kbd>F12</kbd></td><td>Eight function keys. Useful on external keyboards without a Globe key.</td></tr>
          </tbody>
        </table>
        <p>Only modifier and function keys are offered, deliberately: the key you hold to talk should never be a key you also need to type.</p>

        <h2 id="changing">Changing the key</h2>
        <p>Either from the <strong>menu-bar menu ▸ Hotkey</strong>, or in <strong>Dashboard ▸ Settings ▸ Dictation ▸ Hotkey</strong>. The change takes effect immediately — there is nothing to restart.</p>
        <p>For the first week after a change the HUD shows a small reminder chip naming the key, then stops. Changing the key restarts that week, because a new key has to be learned all over again.</p>

        <h2 id="fn">The fn / Globe conflict</h2>
        <p>By default, macOS assigns its own behaviour to <kbd>fn</kbd> — usually opening the emoji picker or starting Apple's own dictation. If pressing it does something unexpected:</p>
        <ol>
          <li>Open <strong>System Settings ▸ Keyboard</strong>.</li>
          <li>Set <strong>Press 🌐 to</strong> → <strong>Do Nothing</strong>.</li>
        </ol>
        <p>Onboarding offers a direct button to that settings pane when <kbd>fn</kbd> is your chosen key. Alternatively, just pick a different hotkey — <kbd>Right ⌘</kbd> is the most common second choice.</p>

        <div class="callout warn">
          <span class="callout-label">If the key does nothing at all</span>
          <p>A hotkey that never fires is almost always missing <strong>Input Monitoring</strong> permission rather than a key conflict. Check <a href="permissions.html">Permissions</a> first, then look for another app holding the same key globally (Raycast, Alfred, Karabiner and similar tools can claim modifiers).</p>
        </div>

        <h2 id="other">Other shortcuts</h2>
        <p>Inside the dashboard, <kbd>⌘⇧D</kbd> opens the dashboard window from anywhere in the app. Dictation itself has no other shortcuts — the design goal is one key that behaves identically in every app.</p>
""",
}

PAGES["text-insertion"] = {
    "head_title": "How OpenVoiceFlow Inserts Text — Auto-Paste and Clipboard Safety",
    "title": "How text is inserted",
    "description": "How OpenVoiceFlow gets dictated text into your app: synthesized Command-V, clipboard save-and-restore, what happens when pasting is blocked, and how to turn auto-paste off.",
    "lede": "The last step of every dictation is putting the text where your cursor is. It is worth understanding, because it is the step that touches your clipboard.",
    "body": """
        <h2 id="how">What happens on release</h2>
        <p>Once the text is ready, OpenVoiceFlow:</p>
        <ol>
          <li><strong>Saves your clipboard</strong> — every item and every format currently on it, not just plain text.</li>
          <li><strong>Puts the dictated text on the clipboard</strong> and synthesizes a <kbd>⌘V</kbd> keystroke into the frontmost app.</li>
          <li><strong>Restores your original clipboard</strong> a fraction of a second later.</li>
        </ol>
        <p>The net effect is that text appears at your cursor and whatever you had copied before is still there afterward. That restore step is the reason dictating does not quietly destroy the URL or image you were about to paste.</p>

        <div class="callout">
          <span class="callout-label">Why paste rather than type</span>
          <p>Synthesizing a paste inserts the whole passage at once, correctly, in any app. Synthesizing individual keystrokes would be slower, would break on non-ASCII characters, and would interleave badly with autocomplete. The trade-off is that this route needs Accessibility permission and briefly uses the clipboard.</p>
        </div>

        <h2 id="blocked">When pasting is blocked</h2>
        <p>If Accessibility permission is missing or has been revoked, the app cannot press <kbd>⌘V</kbd> for you. Rather than losing your words, it deliberately <strong>leaves the dictated text on your clipboard</strong> and the HUD says <strong>Copied instead — press ⌘V</strong>, with a button that takes you to the permission.</p>
        <p>So a failed paste is never a lost dictation: your text is one manual paste away. Fix the permission and the next take inserts normally.</p>

        <h2 id="autopaste">Turning auto-paste off</h2>
        <p><strong>Dashboard ▸ Settings ▸ Dictation ▸ Paste automatically</strong> controls this. With it off, OpenVoiceFlow transcribes and shows you the result but does not press <kbd>⌘V</kbd> and does not touch your clipboard at all.</p>
        <p>People turn this off when they want to review before inserting, or when working in an app where an unexpected paste would be disruptive.</p>

        <h2 id="echo">What the HUD shows afterward</h2>
        <p>By default the HUD briefly echoes the tail of what was inserted, so you can confirm it landed correctly without switching windows. If you dictate sensitive material — passwords, medical notes — turn off <strong>Show what was typed in the HUD</strong> in Settings and the HUD shows a word count instead.</p>

        <h2 id="apps">App compatibility</h2>
        <p>Anywhere with a text cursor works: Mail, Slack, Safari, Chrome, Notes, Word, Notion, VS Code, Xcode, Terminal, iTerm. If a particular app refuses pasted text, that app is usually intercepting <kbd>⌘V</kbd> itself; turning off auto-paste and pasting manually is the reliable workaround.</p>
""",
}

PAGES["dashboard"] = {
    "head_title": "OpenVoiceFlow Dashboard — History, Stats, and Settings",
    "title": "Dashboard & history",
    "description": "A tour of the OpenVoiceFlow dashboard: the time-back stats, dictation history, and the panes for dictionary, snippets, styles, profile, and settings.",
    "lede": "The dashboard is where the app keeps your history, your personalization, and every setting. Open it from the Dock icon, the menu bar, or ⌘⇧D.",
    "body": """
        <h2 id="home">Home</h2>
        <p>The headline number is <strong>time back</strong> — an estimate of how long the same text would have taken to type, computed at 40 words per minute against your actual dictated word count. Below it: total words, number of takes, and a running streak of days used.</p>
        <p>The rest of the pane holds a &ldquo;this week&rdquo; chart of minutes returned per day, a breakdown of which apps you dictate into most (shown once you have used at least two), your three most recent takes, and — kept permanently — the very first thing you ever dictated.</p>
        <div class="callout">
          <span class="callout-label">About that estimate</span>
          <p>40 wpm is a reasonable average typing speed, not a measurement of you. Treat the number as an order of magnitude, not a stopwatch.</p>
        </div>

        <h2 id="history">History</h2>
        <p>Every take, with its timestamp, the app you dictated into, the text, and a word count. Each row has a <strong>Copy</strong> button.</p>
        <p>History holds the most recent <strong>500 entries</strong> and rolls over after that. It lives on your Mac in <code>~/Library/Application Support/OpenVoiceFlow/</code> and is never uploaded. Audio is not kept at all — only the resulting text.</p>
        <p>To clear it: <strong>Settings ▸ Privacy ▸ Delete history…</strong>, which offers <strong>Delete, keep my first words</strong> or <strong>Delete everything</strong>. The first option exists because people tend to want the memento even when clearing the log.</p>

        <h2 id="panes">The other panes</h2>
        <p><strong>Personalize</strong> is one pane with three tabs — everything that teaches the app something once so it stops needing to be told again:</p>
        <table>
          <thead><tr><th scope="col">Tab</th><th scope="col">What it is for</th></tr></thead>
          <tbody>
            <tr><td><a href="dictionary.html">Dictionary</a></td><td>Words it keeps getting wrong. Fix them once.</td></tr>
            <tr><td><a href="snippets.html">Snippets</a></td><td>Say the short thing, get the long thing.</td></tr>
            <tr><td><a href="styles.html">Styles</a></td><td>How you sound, per app.</td></tr>
          </tbody>
        </table>
        <table>
          <thead><tr><th scope="col">Pane</th><th scope="col">What it is for</th></tr></thead>
          <tbody>
            <tr><td><a href="profile.html">Know-Me</a></td><td>A short profile that helps cleanup spell your world correctly.</td></tr>
            <tr><td><a href="settings.html">Settings</a></td><td>Permissions, dictation, transcription, cleanup, privacy, and updates.</td></tr>
          </tbody>
        </table>

        <h2 id="feedback-leaderboard">Feedback and Leaderboard</h2>
        <p>Two more rows sit below Settings in the sidebar:</p>
        <table>
          <thead><tr><th scope="col">Pane</th><th scope="col">What it is for</th></tr></thead>
          <tbody>
            <tr><td>Feedback</td><td>A short form (bug, idea, praise, or other, plus an optional reply email) that opens a <code>mailto:</code> on Send with a small aggregate usage snapshot attached — never dictation text.</td></tr>
            <tr><td>Leaderboard</td><td>Your rank by <strong>time back</strong> against other installations sharing usage, with a display name you can change. Sharing is on by default since 0.5.7 — see <a href="privacy-architecture.html#analytics">Analytics &amp; leaderboard</a> for exactly what that sends and how to turn it off.</td></tr>
          </tbody>
        </table>

        <h2 id="menubar">The menu-bar menu</h2>
        <p>The waveform icon at the top right gives you the fast controls without opening the dashboard: pause listening for an hour, change the hotkey, change the cleanup backend, open permission settings, and check for updates.</p>
        <div class="callout tip">
          <span class="callout-label">Changing the speech model</span>
          <p>Change your Whisper model from <strong>Dashboard ▸ Settings ▸ Transcription</strong>. That path loads the new model immediately. Selecting a model elsewhere may not take effect until the app is relaunched.</p>
        </div>
""",
}

# ── Transcription ──────────────────────────────────────────────────────

PAGES["how-transcription-works"] = {
    "head_title": "How OpenVoiceFlow Transcription Works — On-Device Whisper Pipeline",
    "title": "How transcription works",
    "description": "The OpenVoiceFlow pipeline end to end: 16 kHz audio capture, on-device Whisper via WhisperKit, live partial transcripts, optional cleanup, and insertion at your cursor.",
    "lede": "Five stages between holding a key and seeing text. Four of them never touch a network, and the fifth only does if you have explicitly turned cleanup on.",
    "body": """
        <h2 id="pipeline">The pipeline</h2>
        <ol>
          <li><strong>Capture.</strong> While the key is held, audio is recorded at 16 kHz mono directly into memory. Nothing is written to disk.</li>
          <li><strong>Transcribe.</strong> On release, the buffer is passed to Whisper running locally through <a href="models.html">WhisperKit</a>, which uses your Mac's Neural Engine and GPU. The audio is discarded once text exists.</li>
          <li><strong>Expand snippets.</strong> If what you said matches a <a href="snippets.html">snippet trigger</a> exactly, the expansion is inserted immediately and the remaining steps are skipped.</li>
          <li><strong>Clean up (optional).</strong> Only if you have enabled <a href="ai-cleanup.html">AI cleanup</a>. This is the one stage that can involve a network, and only the <em>text</em> is ever sent.</li>
          <li><strong>Insert.</strong> The result is placed at your cursor — see <a href="text-insertion.html">How text is inserted</a>.</li>
        </ol>

        <h2 id="live">Live partial transcripts</h2>
        <p>While you hold the key, the app re-transcribes the growing buffer roughly three times a second so words appear in the HUD as you speak. This is a preview, not the final answer: the real pass runs on the complete recording after you release, and it is the one that gets inserted. Seeing partials that later change slightly is normal and expected — the full recording gives Whisper more context to work with.</p>
        <p>Partials cost a little extra compute. If you are on an older Mac and want maximum battery life, turn off <strong>Show words as you speak</strong> in Settings.</p>

        <h2 id="offline">What needs a network</h2>
        <table>
          <thead><tr><th scope="col">Stage</th><th scope="col">Network</th></tr></thead>
          <tbody>
            <tr><td>Capturing audio</td><td>Never</td></tr>
            <tr><td>Transcribing</td><td>Never — after the one-time model download</td></tr>
            <tr><td>Snippet expansion</td><td>Never</td></tr>
            <tr><td>AI cleanup</td><td>Only if enabled <em>and</em> pointed at a cloud provider. Local Ollama and &ldquo;off&rdquo; stay on your Mac.</td></tr>
            <tr><td>Inserting text</td><td>Never</td></tr>
          </tbody>
        </table>
        <p>With cleanup off — the default — dictation works in airplane mode indefinitely.</p>

        <h2 id="quality">Why results vary</h2>
        <p>Whisper predicts the most likely word sequence given the audio and its training. That explains most of what you will observe: it is excellent on ordinary prose, good with accents on larger models, and unreliable on proper nouns it has never seen. The fix for names is not a bigger model but the <a href="dictionary.html">personal dictionary</a>.</p>
        <div class="callout">
          <span class="callout-label">A known Whisper quirk</span>
          <p>On near-silent or very short audio, Whisper models occasionally emit a stock phrase such as &ldquo;Thank you&rdquo; or &ldquo;Thanks for watching&rdquo; — an artifact of the subtitled video in their training data. Push-to-talk avoids most of it, since you hold the key only while speaking. If you see it, that is the model, not a fault in your setup.</p>
        </div>
""",
}

PAGES["models"] = {
    "head_title": "Whisper Models in OpenVoiceFlow — Tiny, Small, Medium, Large Turbo",
    "title": "Whisper models",
    "description": "The four on-device Whisper models OpenVoiceFlow offers, how to choose one for your Mac, how downloads and storage work, and how to recover from a failed model download.",
    "lede": "Four engines, all running on your Mac, all free. Bigger models hear more and cost more time and disk — this page helps you pick once and stop thinking about it.",
    "faq": [
        ("Which Whisper model should I use?",
         "On an Apple Silicon Mac with a few gigabytes free, use Large turbo — it is the most accurate option that still feels immediate. On an Intel Mac or a machine short on disk or memory, use Small. Tiny is for quick notes where speed matters more than precision."),
        ("Where does OpenVoiceFlow store downloaded models?",
         "In the WhisperKit cache under your Documents folder, at ~/Documents/huggingface/models/argmaxinc/whisperkit-coreml/. Deleting that folder frees the space; the app re-downloads the model you select next time."),
        ("Why does the progress bar pause near the end of a model download?",
         "The transfer finishes around ninety percent, then macOS compiles the model for your specific Mac. That compile step happens only on the first run of a given model and is why the app shows 'Downloaded — now optimizing for your Mac'."),
    ],
    "body": """
        <h2 id="choose">Choosing a model</h2>
        <table>
          <thead><tr><th scope="col">Engine</th><th scope="col">Download</th><th scope="col">Character</th></tr></thead>
          <tbody>
            <tr><td>Tiny</td><td>39 MB</td><td>Fastest. Fine for quick notes; struggles with accents, noise, and jargon.</td></tr>
            <tr><td>Small</td><td>466 MB</td><td>Everyday dictation on any Mac. The safe default on Intel.</td></tr>
            <tr><td>Medium</td><td>1.5 GB</td><td>Hears more, asks more of your Mac.</td></tr>
            <tr><td>Large turbo</td><td>1.6 GB</td><td>Hears the most. Best on Apple Silicon, and fast enough for live dictation.</td></tr>
          </tbody>
        </table>
        <p>During onboarding one option carries a <strong>RECOMMENDED</strong> chip, picked from your actual hardware: Large turbo if you are on Apple Silicon with more than about 5 GB free, otherwise Small. That heuristic is a good default — the sections below cover when to override it.</p>

        <h3>When to go bigger</h3>
        <ul>
          <li>You dictate in a <a href="languages.html">language other than English</a> — model size matters most here.</li>
          <li>You have an accent the smaller models handle poorly.</li>
          <li>You dictate in rooms with background noise or at a distance from the mic.</li>
          <li>Your work is full of technical vocabulary.</li>
        </ul>

        <h3>When to go smaller</h3>
        <ul>
          <li>You are on an Intel Mac, where there is no Neural Engine to lean on.</li>
          <li>Your Mac has 8 GB of memory and is already under pressure.</li>
          <li>You want the shortest possible delay between releasing the key and seeing text.</li>
          <li>Disk space is tight.</li>
        </ul>

        <div class="callout tip">
          <span class="callout-label">The thirty-second test</span>
          <p>Dictate one real paragraph of your actual work — your jargon, your names, your speaking pace — on the recommended model. Then switch one size and dictate it again. Keep whichever you would forgive being slower. Accuracy you cannot feel is not worth latency you can.</p>
        </div>

        <h2 id="changing">Changing your model</h2>
        <p>Go to <strong>Dashboard ▸ Settings ▸ Transcription — on this Mac ▸ Whisper model</strong> and pick one. If it has not been downloaded before, the download begins immediately; models you have used before are already on disk and switch instantly.</p>

        <h2 id="downloads">Downloads and storage</h2>
        <p>Models download once and are cached at <code>~/Documents/huggingface/models/argmaxinc/whisperkit-coreml/</code>. The progress display shows transferred size, current speed, and a time estimate.</p>
        <p>Two behaviours worth knowing:</p>
        <ul>
          <li>The bar reaching the top does <strong>not</strong> mean it is done. The transfer occupies most of the bar, then macOS compiles the model for your Mac — labelled &ldquo;now optimizing for your Mac. First run only.&rdquo;</li>
          <li>Switching engines mid-download cancels the transfer in progress rather than running two at once.</li>
        </ul>

        <h2 id="failures">If a download fails</h2>
        <p>The app retries once automatically, deleting the partial files first — a truncated download is the usual cause of a model that will not load. If the second attempt also fails, the screen shows <strong>Try again</strong> plus a <strong>Details</strong> disclosure with the underlying error.</p>
        <p>The app deliberately does not guess at causes. If Details mentions the network, check your connection or VPN; if it mentions disk space, free some and retry. Manual recovery: quit the app, delete the model folder above, relaunch, and select the model again.</p>

        <div class="callout warn">
          <span class="callout-label">If you upgraded from 0.5.2</span>
          <p>Version 0.5.2 briefly offered a model id that did not exist, leaving affected installs unable to download anything. Current versions rewrite that stored value automatically on launch — you do not need to do anything, but if you were stuck on 0.5.2, updating is the fix.</p>
        </div>
""",
}

PAGES["languages"] = {
    "head_title": "Dictation Languages in OpenVoiceFlow — Whisper Multilingual Support",
    "title": "Languages",
    "description": "The languages OpenVoiceFlow supports for dictation, how to change the language, and why model choice matters more outside English.",
    "lede": "Whisper is multilingual, and OpenVoiceFlow exposes its full 99-language picker. Which model you run matters more here than anywhere else in the app.",
    "body": """
        <h2 id="supported">Languages in the picker</h2>
        <p><strong>Dashboard ▸ Settings ▸ Transcription — on this Mac ▸ Language</strong> offers every language Whisper's multilingual models are trained on:</p>
        <table>
          <thead><tr><th scope="col">Language</th><th scope="col">Code</th><th scope="col">Language</th><th scope="col">Code</th></tr></thead>
          <tbody>
            <tr><td>English</td><td><code>en</code></td><td>Afrikaans</td><td><code>af</code></td></tr>
            <tr><td>Albanian</td><td><code>sq</code></td><td>Amharic</td><td><code>am</code></td></tr>
            <tr><td>Arabic</td><td><code>ar</code></td><td>Armenian</td><td><code>hy</code></td></tr>
            <tr><td>Assamese</td><td><code>as</code></td><td>Azerbaijani</td><td><code>az</code></td></tr>
            <tr><td>Bashkir</td><td><code>ba</code></td><td>Basque</td><td><code>eu</code></td></tr>
            <tr><td>Belarusian</td><td><code>be</code></td><td>Bengali</td><td><code>bn</code></td></tr>
            <tr><td>Bosnian</td><td><code>bs</code></td><td>Breton</td><td><code>br</code></td></tr>
            <tr><td>Bulgarian</td><td><code>bg</code></td><td>Burmese</td><td><code>my</code></td></tr>
            <tr><td>Catalan</td><td><code>ca</code></td><td>Chinese</td><td><code>zh</code></td></tr>
            <tr><td>Croatian</td><td><code>hr</code></td><td>Czech</td><td><code>cs</code></td></tr>
            <tr><td>Danish</td><td><code>da</code></td><td>Dutch</td><td><code>nl</code></td></tr>
            <tr><td>Estonian</td><td><code>et</code></td><td>Faroese</td><td><code>fo</code></td></tr>
            <tr><td>Finnish</td><td><code>fi</code></td><td>French</td><td><code>fr</code></td></tr>
            <tr><td>Galician</td><td><code>gl</code></td><td>Georgian</td><td><code>ka</code></td></tr>
            <tr><td>German</td><td><code>de</code></td><td>Greek</td><td><code>el</code></td></tr>
            <tr><td>Gujarati</td><td><code>gu</code></td><td>Haitian Creole</td><td><code>ht</code></td></tr>
            <tr><td>Hausa</td><td><code>ha</code></td><td>Hawaiian</td><td><code>haw</code></td></tr>
            <tr><td>Hebrew</td><td><code>he</code></td><td>Hindi</td><td><code>hi</code></td></tr>
            <tr><td>Hungarian</td><td><code>hu</code></td><td>Icelandic</td><td><code>is</code></td></tr>
            <tr><td>Indonesian</td><td><code>id</code></td><td>Italian</td><td><code>it</code></td></tr>
            <tr><td>Japanese</td><td><code>ja</code></td><td>Javanese</td><td><code>jw</code></td></tr>
            <tr><td>Kannada</td><td><code>kn</code></td><td>Kazakh</td><td><code>kk</code></td></tr>
            <tr><td>Khmer</td><td><code>km</code></td><td>Korean</td><td><code>ko</code></td></tr>
            <tr><td>Lao</td><td><code>lo</code></td><td>Latin</td><td><code>la</code></td></tr>
            <tr><td>Latvian</td><td><code>lv</code></td><td>Lingala</td><td><code>ln</code></td></tr>
            <tr><td>Lithuanian</td><td><code>lt</code></td><td>Luxembourgish</td><td><code>lb</code></td></tr>
            <tr><td>Macedonian</td><td><code>mk</code></td><td>Malagasy</td><td><code>mg</code></td></tr>
            <tr><td>Malay</td><td><code>ms</code></td><td>Malayalam</td><td><code>ml</code></td></tr>
            <tr><td>Maltese</td><td><code>mt</code></td><td>Maori</td><td><code>mi</code></td></tr>
            <tr><td>Marathi</td><td><code>mr</code></td><td>Mongolian</td><td><code>mn</code></td></tr>
            <tr><td>Nepali</td><td><code>ne</code></td><td>Norwegian</td><td><code>no</code></td></tr>
            <tr><td>Norwegian Nynorsk</td><td><code>nn</code></td><td>Occitan</td><td><code>oc</code></td></tr>
            <tr><td>Pashto</td><td><code>ps</code></td><td>Persian</td><td><code>fa</code></td></tr>
            <tr><td>Polish</td><td><code>pl</code></td><td>Portuguese</td><td><code>pt</code></td></tr>
            <tr><td>Punjabi</td><td><code>pa</code></td><td>Romanian</td><td><code>ro</code></td></tr>
            <tr><td>Russian</td><td><code>ru</code></td><td>Sanskrit</td><td><code>sa</code></td></tr>
            <tr><td>Serbian</td><td><code>sr</code></td><td>Shona</td><td><code>sn</code></td></tr>
            <tr><td>Sindhi</td><td><code>sd</code></td><td>Sinhala</td><td><code>si</code></td></tr>
            <tr><td>Slovak</td><td><code>sk</code></td><td>Slovenian</td><td><code>sl</code></td></tr>
            <tr><td>Somali</td><td><code>so</code></td><td>Spanish</td><td><code>es</code></td></tr>
            <tr><td>Sundanese</td><td><code>su</code></td><td>Swahili</td><td><code>sw</code></td></tr>
            <tr><td>Swedish</td><td><code>sv</code></td><td>Tagalog</td><td><code>tl</code></td></tr>
            <tr><td>Tajik</td><td><code>tg</code></td><td>Tamil</td><td><code>ta</code></td></tr>
            <tr><td>Tatar</td><td><code>tt</code></td><td>Telugu</td><td><code>te</code></td></tr>
            <tr><td>Thai</td><td><code>th</code></td><td>Tibetan</td><td><code>bo</code></td></tr>
            <tr><td>Turkish</td><td><code>tr</code></td><td>Turkmen</td><td><code>tk</code></td></tr>
            <tr><td>Ukrainian</td><td><code>uk</code></td><td>Urdu</td><td><code>ur</code></td></tr>
            <tr><td>Uzbek</td><td><code>uz</code></td><td>Vietnamese</td><td><code>vi</code></td></tr>
            <tr><td>Welsh</td><td><code>cy</code></td><td>Yiddish</td><td><code>yi</code></td></tr>
            <tr><td>Yoruba</td><td><code>yo</code></td><td></td><td></td></tr>
          </tbody>
        </table>
        <p>That's every language in Whisper's standard 99-language set. (Large turbo also recognizes Cantonese under the hood, but that language token doesn't exist in Tiny, Small, or Medium's vocabulary, so it's left out of the shared picker above.)</p>

        <div class="callout warn">
          <span class="callout-label">Pair the language with a multilingual model</span>
          <p>Whisper ships both multilingual models and English-only variants (their ids end in <code>.en</code>). The four engines in the onboarding picker — Tiny, Small, Medium, and Large turbo — are multilingual and work with every language above. If your model setting shows an id ending in <code>.en</code>, it will not transcribe other languages properly. Re-pick an engine in <a href="models.html">Settings ▸ Transcription</a> and the pairing takes care of itself.</p>
        </div>

        <h2 id="quality">Accuracy outside English</h2>
        <p>Whisper's quality varies by language, and the gap between model sizes widens considerably away from English. As models get smaller they effectively become English specialists. Practical guidance:</p>
        <ul>
          <li>For non-English dictation, run the <strong>largest model your Mac handles comfortably</strong> before tuning anything else.</li>
          <li>Widely represented languages (Spanish, French, German, Portuguese, Italian) do well. Languages with less training data are more variable.</li>
          <li>The <a href="dictionary.html">personal dictionary</a> works in any language and is the fix for names regardless.</li>
        </ul>

        <h2 id="switching">Switching languages</h2>
        <p>The language setting is a single global choice, not per-app or automatic. Change it in Settings when you switch languages. There is no mixed-language mode: dictate one language per take for best results.</p>

        <h2 id="cleanup">Cleanup and language</h2>
        <p>If you use <a href="ai-cleanup.html">AI cleanup</a>, the model you point it at also needs to handle your language well. Cleanup is instructed to preserve meaning and return only the cleaned text, so a model weak in your language may do more harm than good. When in doubt in a non-English language, leaving cleanup off and taking the raw Whisper transcript is often the better result.</p>
""",
}

PAGES["accuracy"] = {
    "head_title": "Improving Dictation Accuracy in OpenVoiceFlow",
    "title": "Improving accuracy",
    "description": "Practical steps to make OpenVoiceFlow more accurate, ordered by how much difference each one makes: microphone, speaking style, model size, and the personal dictionary.",
    "lede": "Ordered by effect, largest first. Most accuracy complaints are solved by the first two items, and neither of them involves changing a setting.",
    "body": """
        <h2 id="mic">1. Fix the microphone situation</h2>
        <p>This is the biggest single factor and the most overlooked. A MacBook's built-in microphone is decent at conversational distance and poor across a room. If you are leaning back from an open laptop, the mic is largely hearing your ceiling.</p>
        <ul>
          <li>Sit at a normal working distance, or use a headset — AirPods or any wired headset mic beat a built-in array at distance.</li>
          <li>Reduce steady background noise where you can: fans, air conditioning, a nearby TV.</li>
          <li>Check that macOS is using the input you think it is, in <strong>System Settings ▸ Sound ▸ Input</strong>. Bluetooth headsets sometimes select a low-quality input profile.</li>
        </ul>

        <h2 id="speak">2. Speak in phrases</h2>
        <p>Whisper resolves ambiguity from surrounding words. Delivering a complete clause at a natural pace gives it that context; word-by-word delivery removes it and makes the model <em>less</em> accurate, not more.</p>
        <ul>
          <li>Speak as if to a colleague, not as if to a machine.</li>
          <li>Do not over-enunciate — unnatural stress patterns hurt.</li>
          <li>Hold the key a beat before you start and a beat after you finish, so the first and last words are not clipped.</li>
        </ul>

        <h2 id="dictionary">3. Teach it your vocabulary</h2>
        <p>Proper nouns are not a model-size problem — a name absent from training data stays absent at every size. The <a href="dictionary.html">personal dictionary</a> is the durable fix for colleagues' names, product names, and internal jargon.</p>
        <div class="callout warn">
          <span class="callout-label">Important caveat</span>
          <p>The dictionary and the <a href="profile.html">Know-Me profile</a> are applied during <a href="ai-cleanup.html">AI cleanup</a>. With cleanup set to <strong>None</strong>, they have no effect on your output. If you rely on them, cleanup needs to be on.</p>
        </div>

        <h2 id="model">4. Move up a model size</h2>
        <p>If the first three did not get you there, try the next model up in <a href="models.html">Settings ▸ Transcription</a>. The jump matters most for accented speech, noisy rooms, and non-English languages. On Apple Silicon, Large turbo is usually worth it.</p>

        <h2 id="cleanup">5. Turn on cleanup for prose</h2>
        <p>Raw transcripts contain your filler words and false starts because that is what you said. If you are dictating email or documents rather than notes, <a href="ai-cleanup.html">AI cleanup</a> removes the &ldquo;um&rdquo;s, fixes grammar, and handles spoken corrections like &ldquo;no wait, I mean&rdquo;. It also activates your dictionary and profile.</p>

        <h2 id="expectations">What accuracy to expect</h2>
        <p>We do not publish a benchmark, because word error rate depends on your microphone, accent, vocabulary, and room far more than on anything we could measure in a lab. The honest test is the one you can run in a minute: dictate a real paragraph of your own work and judge the result. If it disappoints, work down this page in order — the fix is nearly always here.</p>
""",
}

# ── Personalization ────────────────────────────────────────────────────

PAGES["dictionary"] = {
    "head_title": "Personal Dictionary in OpenVoiceFlow — Fix Names and Jargon",
    "title": "Personal dictionary",
    "description": "How the OpenVoiceFlow personal dictionary works: adding words, how entries are applied during cleanup, why it requires AI cleanup, and where entries are stored.",
    "lede": "Teach it the words it keeps getting wrong — names, products, internal jargon — and it stops getting them wrong. One important condition applies.",
    "body": """
        <div class="callout warn">
          <span class="callout-label">Read this first</span>
          <p>The dictionary is applied during <a href="ai-cleanup.html">AI cleanup</a>. With cleanup set to <strong>None</strong> — the shipping default — your entries have <strong>no effect</strong>, because there is no stage in which to apply them. If the dictionary is why you want the feature, turn cleanup on.</p>
        </div>

        <h2 id="adding">Adding words</h2>
        <p>Open <strong>Dashboard ▸ Personalize</strong> and type the word as it should be spelled, then press add. Entries are stored immediately.</p>
        <p>Good candidates:</p>
        <ul>
          <li>Colleagues' and clients' names, especially non-English spellings.</li>
          <li>Product and project names — yours and your customers'.</li>
          <li>Technical terms and command names: <code>kubectl</code>, <code>WhisperKit</code>, <code>TestFlight</code>.</li>
          <li>Anything you have corrected by hand more than twice.</li>
        </ul>
        <p>There is no cap on entries, but a focused list works better than an exhaustive one — every entry is context the cleanup model has to weigh.</p>

        <h2 id="how">How entries are applied</h2>
        <p>The dictionary is not a find-and-replace pass. Your words are supplied to the cleanup model as explicit instructions — roughly &ldquo;always use these exact spellings&rdquo; followed by your list — so the model corrects a misheard variant in context rather than blindly substituting text. That is why an entry can fix a name even when Whisper produced something only loosely similar.</p>
        <p>Entries may also carry <strong>aliases</strong>: known mishearings of the word, which are passed along as &ldquo;may be misheard as…&rdquo;. Aliases are shown in the dictionary list when present. The Know-Me interview seeds some entries automatically from the names and jargon you provide.</p>

        <h2 id="duplicates">Duplicates and editing</h2>
        <p>Adding a word that already exists (ignoring case) merges into the existing entry rather than creating a second one. To remove an entry, use the delete control on its row.</p>

        <h2 id="storage">Where it is stored</h2>
        <p><code>~/Library/Application Support/OpenVoiceFlow/dictionary.json</code>, written with file protection on every change. It never leaves your Mac except as part of the cleanup prompt, and then only to the provider you chose. See <a href="privacy-architecture.html">Privacy architecture</a>.</p>

        <h2 id="seeding">Seeding from your profile</h2>
        <p>Running the <a href="profile.html">Know-Me interview</a> adds the names and technical terms you list into the dictionary automatically, without overwriting entries you added yourself. It is the fastest way to populate a useful starting set.</p>
""",
}

PAGES["snippets"] = {
    "head_title": "Voice Snippets in OpenVoiceFlow — Say a Trigger, Get the Text",
    "title": "Snippets",
    "description": "How OpenVoiceFlow voice snippets work: creating triggers, how matching happens, why snippets bypass AI cleanup entirely, and where they are stored.",
    "lede": "Say a short phrase, get a long block of text. Unlike the dictionary, snippets work whether or not AI cleanup is on — they run before it.",
    "body": """
        <h2 id="what">What a snippet is</h2>
        <p>A snippet pairs a spoken <strong>trigger</strong> with an <strong>expansion</strong>. Say the trigger and nothing else, and the expansion is inserted verbatim.</p>
        <p>Common uses: your email signature, your address, a standup preamble, a bug-report template, a legal disclaimer, a support reply you send daily.</p>

        <h2 id="creating">Creating one</h2>
        <p>The Snippets tab in <strong>Dashboard ▸ Personalize</strong> has two fields — trigger and expansion. Keep triggers short and distinctive: <code>my address</code>, <code>signature</code>, <code>standup intro</code>. Triggers are stored lowercase and matched case-insensitively, so you do not need to worry about how you capitalize them.</p>
        <p>Adding a trigger that already exists replaces its expansion, which makes editing a snippet as simple as re-adding it.</p>

        <h2 id="matching">How matching works</h2>
        <p>After transcription, the app compares what you said against your triggers:</p>
        <ul>
          <li>An <strong>exact match</strong> of the whole transcript expands.</li>
          <li>A <strong>prefix match</strong> also expands, provided the trigger ends at a word boundary — so &ldquo;signature&rdquo; matches but &ldquo;signatures&rdquo; does not accidentally fire it.</li>
          <li>When several triggers could match, the longest one wins.</li>
        </ul>
        <p>Say a trigger in the middle of a longer sentence and it will <em>not</em> expand — snippets are deliberately an all-or-nothing gesture, so ordinary dictation never mutates unexpectedly.</p>

        <div class="callout tip">
          <span class="callout-label">Snippets skip cleanup entirely</span>
          <p>When a trigger matches, the expansion is inserted immediately and no cleanup call is made — not even when cleanup is enabled. Your expansion arrives exactly as you wrote it, with no model rewriting it, and with no network request. It is the fastest path through the app.</p>
        </div>

        <h2 id="storage">Where they are stored</h2>
        <p><code>~/Library/Application Support/OpenVoiceFlow/snippets.json</code>. There is no cap on how many you can have, and they are never uploaded.</p>

        <h2 id="tips">Choosing good triggers</h2>
        <ul>
          <li>Two or three words beats one — single common words risk firing when you meant to dictate them.</li>
          <li>Avoid triggers that are also natural sentence openings.</li>
          <li>Say the trigger cleanly and stop. Trailing &ldquo;um&rdquo; can prevent a match.</li>
          <li>If a snippet is not firing, check <a href="dashboard.html">History</a> to see exactly what was transcribed — usually the transcript differs slightly from the trigger you registered.</li>
        </ul>
""",
}

PAGES["styles"] = {
    "head_title": "Per-App Styles in OpenVoiceFlow — Casual in Slack, Formal in Mail",
    "title": "Per-app styles",
    "description": "How OpenVoiceFlow adjusts tone per application: the five styles, which apps map to which style by default, and how style interacts with AI cleanup.",
    "lede": "The same sentence should not read the same way in Slack and in a client email. Styles adjust how cleanup rewrites you, based on the app you are dictating into.",
    "body": """
        <div class="callout warn">
          <span class="callout-label">Requires AI cleanup</span>
          <p>Styles work by adjusting the instructions given to the cleanup model. With cleanup set to <strong>None</strong>, you get the raw transcript and styles have no effect.</p>
        </div>

        <h2 id="styles">The five styles</h2>
        <table>
          <thead><tr><th scope="col">Style</th><th scope="col">What it asks for</th></tr></thead>
          <tbody>
            <tr><td>Neutral</td><td>No tone instruction — plain cleanup only.</td></tr>
            <tr><td>Casual</td><td>A casual, friendly tone.</td></tr>
            <tr><td>Formal</td><td>Formal language; avoids contractions.</td></tr>
            <tr><td>Code</td><td>Preserves technical terms and code references exactly.</td></tr>
            <tr><td>Email</td><td>Formats the result as professional email text.</td></tr>
          </tbody>
        </table>

        <h2 id="mapping">Which app gets which style</h2>
        <p>OpenVoiceFlow checks which app is frontmost when you dictate and applies that app's style automatically. The shipping map:</p>
        <table>
          <thead><tr><th scope="col">Style</th><th scope="col">Apps</th></tr></thead>
          <tbody>
            <tr><td>Code</td><td>Visual Studio Code, Xcode, PyCharm, Zed, Terminal, iTerm2, Sublime Text, Nova</td></tr>
            <tr><td>Email</td><td>Mail, Gmail, Outlook, Superhuman</td></tr>
            <tr><td>Casual</td><td>Slack, Discord, Messages, WhatsApp, Telegram, Signal</td></tr>
            <tr><td>Neutral</td><td>Microsoft Word, Pages, Notion, Safari, Google Chrome</td></tr>
          </tbody>
        </table>
        <p>Dictate into an app that is not on this list and the fallback style applies. You can change the style assigned to any app already in the list from the Styles tab in <strong>Dashboard ▸ Personalize</strong>.</p>

        <div class="callout">
          <span class="callout-label">In this version</span>
          <p>The Styles tab edits the mapping for apps already listed; there is no control for adding an app that is not on the list, so unlisted apps use the fallback. If per-app tone in a specific app matters to you, tell us at <a href="mailto:shimoverse@gmail.com">shimoverse@gmail.com</a> — that feedback is how the list grows.</p>
        </div>

        <h2 id="storage">Where it is stored</h2>
        <p><code>~/Library/Application Support/OpenVoiceFlow/styles.json</code>. The app name recorded with each dictation in <a href="dashboard.html">History</a> is the same name used for this lookup, which makes it easy to see what the app thought you were dictating into.</p>
""",
}

PAGES["profile"] = {
    "head_title": "Know-Me Profile in OpenVoiceFlow — Personal Context for Cleanup",
    "title": "Know-Me profile",
    "description": "The OpenVoiceFlow Know-Me profile: the five questions it asks, how the answers improve cleanup accuracy, and how to review, re-run, or clear it.",
    "lede": "A two-minute interview that tells cleanup who you are, who you talk about, and how you like to sound. It is optional, and it only matters when cleanup is on.",
    "body": """
        <h2 id="what">What it collects</h2>
        <p><strong>Dashboard ▸ Know-Me ▸ Run interview</strong> asks five questions, one per screen. Every one is skippable.</p>
        <table>
          <thead><tr><th scope="col">Question</th><th scope="col">Example answer</th><th scope="col">What it fixes</th></tr></thead>
          <tbody>
            <tr><td>What should we call you?</td><td>Alex Chen</td><td>Your own name being misspelled in your own writing.</td></tr>
            <tr><td>What do you do?</td><td>iOS engineer at a small startup</td><td>Gives cleanup domain context for ambiguous words.</td></tr>
            <tr><td>Who do you mention most?</td><td>Priya, Sam, Dr. Okafor</td><td>Colleagues' names, the single most common complaint.</td></tr>
            <tr><td>Any words it keeps getting wrong?</td><td>WhisperKit, TestFlight, Kubernetes</td><td>Your jargon.</td></tr>
            <tr><td>How do you like to sound?</td><td>concise, no exclamation marks, Oxford comma</td><td>Stops cleanup from making you sound like someone else.</td></tr>
          </tbody>
        </table>
        <p>Onboarding asks only for your name; the rest live in the dashboard interview so first-run setup stays short.</p>

        <h2 id="how">How it is used</h2>
        <p>Your answers become a short personal-context block supplied to the cleanup model alongside your <a href="dictionary.html">dictionary</a> — who you are, who you mention, which terms to spell correctly, and how you like to sound. It is why cleanup can pick the right spelling of a colleague's name from an ambiguous transcript.</p>
        <p>Running the interview also <strong>seeds your dictionary</strong> with the names and technical terms you list, without disturbing entries you added yourself.</p>

        <div class="callout warn">
          <span class="callout-label">Requires AI cleanup</span>
          <p>Like the dictionary, the profile is applied during cleanup. With cleanup set to <strong>None</strong> it has no effect on your output.</p>
        </div>

        <h2 id="managing">Reviewing, re-running, clearing</h2>
        <p>The Know-Me pane shows what is currently stored. <strong>Re-run interview</strong> walks the five questions again; <strong>Clear</strong> empties the profile entirely. Both take effect on your next dictation.</p>

        <h2 id="privacy">Where it lives</h2>
        <p><code>~/Library/Application Support/OpenVoiceFlow/profile.json</code> on your Mac. If you enable <strong>cloud</strong> cleanup, this context is sent with each cleanup request to the provider you chose, under your own API key — that is what makes it work. If that trade is not one you want, use <a href="backends.html">local Ollama cleanup</a>, which keeps the same behaviour entirely on your machine, or leave cleanup off and skip the interview.</p>
""",
}

# ── AI cleanup ─────────────────────────────────────────────────────────

PAGES["ai-cleanup"] = {
    "head_title": "AI Cleanup in OpenVoiceFlow — Optional, Bring Your Own Key",
    "title": "AI cleanup overview",
    "description": "What OpenVoiceFlow AI cleanup does, exactly what is sent and to whom, how to turn it on or off, and what happens when a cleanup request fails.",
    "lede": "Cleanup turns a raw transcript into finished prose — filler words gone, grammar fixed, spoken corrections applied. It ships off, and off is a legitimate place to stay.",
    "faq": [
        ("Does OpenVoiceFlow send my audio to the cloud?",
         "Never. Audio is transcribed on your Mac and discarded. Only if you enable cloud cleanup does the resulting text leave your machine, and then only to the provider you selected, under your own API key."),
        ("Is AI cleanup on by default?",
         "No. Cleanup ships set to None, which means you get the raw on-device transcript and no network request is made at any point in the pipeline."),
        ("What happens if the cleanup service is down?",
         "You get your raw transcript. Cleanup is designed to fail open: on a missing key, an HTTP error, a timeout, or an unparseable response, the app inserts the original on-device transcription rather than showing an error or losing your words."),
    ],
    "body": """
        <h2 id="what">What cleanup does</h2>
        <p>Cleanup takes the raw transcript and returns a tidied version. The instruction it operates under is narrow and specific: fix grammar, remove filler words (&ldquo;um&rdquo;, &ldquo;uh&rdquo;, &ldquo;like&rdquo;, &ldquo;you know&rdquo;), apply spoken corrections (&ldquo;no wait&rdquo;, &ldquo;I mean&rdquo;, &ldquo;actually&rdquo;), preserve the original meaning and tone, and return only the cleaned text. If the input is already clean, it comes back unchanged.</p>
        <p>It is a copy-editor, not a co-author. It is not asked to expand, summarize, or answer anything.</p>

        <h3>Before and after</h3>
        <table>
          <thead><tr><th scope="col">Raw transcript</th><th scope="col">After cleanup</th></tr></thead>
          <tbody>
            <tr><td>so um I think we should uh ship the beta tonight no wait tomorrow morning would be better</td><td>I think we should ship the beta tomorrow morning — that would be better.</td></tr>
          </tbody>
        </table>

        <h2 id="onoff">Turning it on and off</h2>
        <p><strong>Dashboard ▸ Settings ▸ AI cleanup</strong>, or the <strong>Cleanup</strong> submenu in the menu bar. Off is called <strong>None — raw transcript</strong>.</p>
        <p>With cleanup off, the pipeline makes no network request at all and OpenVoiceFlow works entirely offline. With it on, you also activate your <a href="dictionary.html">dictionary</a>, <a href="profile.html">profile</a>, and <a href="styles.html">per-app styles</a>, all of which are applied at this stage.</p>

        <h2 id="sent">Exactly what is sent</h2>
        <p>When cloud cleanup runs, the request contains:</p>
        <ul>
          <li>The <strong>raw transcript</strong> of what you just said.</li>
          <li>The <strong>cleanup instruction</strong> above, plus your <a href="styles.html">style</a> instruction.</li>
          <li>Your <strong>personal context</strong> — <a href="profile.html">Know-Me profile</a>, <a href="dictionary.html">dictionary</a>, and snippet triggers.</li>
        </ul>
        <p>What is never sent: <strong>audio</strong>, your history, your settings, or any identifier for you or your Mac beyond what your own API key implies to your provider. Choose <a href="backends.html">Ollama</a> and none of it leaves your machine at all.</p>

        <h2 id="failure">When it fails</h2>
        <p>Cleanup fails open, always. If the API key is missing, the provider returns an error, the request times out (10 seconds for cloud providers, 120 for local Ollama), or the response cannot be parsed, OpenVoiceFlow inserts your <strong>raw on-device transcript</strong> instead.</p>
        <p>The practical consequence is that a cleanup outage costs you polish, never words. It also means that if cleanup silently seems to stop working, the thing to check is your <a href="api-keys.html">API key and credit balance</a> — the app will keep quietly giving you raw transcripts.</p>

        <h2 id="should">Should you turn it on?</h2>
        <ul>
          <li><strong>Leave it off</strong> if you dictate notes and search queries, want zero network involvement, or prefer your exact words preserved.</li>
          <li><strong>Turn it on</strong> if you dictate email, documents, and messages, or if you want your <a href="dictionary.html">dictionary</a> and <a href="profile.html">profile</a> to take effect.</li>
          <li><strong>Use Ollama</strong> if you want cleanup's benefits with no network at all — see <a href="backends.html">Choosing a backend</a>.</li>
        </ul>
""",
}

PAGES["backends"] = {
    "head_title": "Cleanup Backends in OpenVoiceFlow — OpenRouter, OpenAI, Anthropic, Groq, Ollama",
    "title": "Choosing a backend",
    "description": "Compare the cleanup backends OpenVoiceFlow supports — OpenRouter, OpenAI, Anthropic, Groq, and local Ollama — on privacy, speed, cost, and setup effort.",
    "lede": "Five providers plus off. The only decision that really matters is whether cleanup runs on your Mac or in someone's cloud.",
    "body": """
        <h2 id="compare">The options</h2>
        <table>
          <thead><tr><th scope="col">Backend</th><th scope="col">Runs</th><th scope="col">Needs</th><th scope="col">Best for</th></tr></thead>
          <tbody>
            <tr><td>None</td><td>—</td><td>Nothing</td><td>The default. Raw transcript, zero network.</td></tr>
            <tr><td>Ollama</td><td>Your Mac</td><td>Ollama installed locally</td><td>Cleanup with no network at all.</td></tr>
            <tr><td>OpenRouter</td><td>Cloud</td><td>OpenRouter key</td><td>One key that reaches many models.</td></tr>
            <tr><td>Anthropic</td><td>Cloud</td><td>Anthropic key</td><td>Claude models directly.</td></tr>
            <tr><td>OpenAI</td><td>Cloud</td><td>OpenAI key</td><td>GPT models directly.</td></tr>
            <tr><td>Groq</td><td>Cloud</td><td>Groq key</td><td>Very low latency.</td></tr>
          </tbody>
        </table>
        <p>All cloud options are bring-your-own-key: you contract directly with the provider and pay them for tokens. OpenVoiceFlow takes no cut and has no server in the path.</p>

        <h2 id="ollama">Local cleanup with Ollama</h2>
        <p>Ollama runs a language model on your own Mac, so cleanup keeps the entire pipeline offline.</p>
        <ol>
          <li>Install <a href="https://ollama.com">Ollama</a>.</li>
          <li>Pull a small instruct model — a 3B-class model is plenty for tidying text.</li>
          <li>In <strong>Settings ▸ AI cleanup</strong>, choose <strong>Ollama</strong>.</li>
        </ol>
        <p>OpenVoiceFlow talks to Ollama at <code>localhost:11434</code>, and allows a longer timeout (120 seconds) than for cloud providers, since local generation on a busy machine can be slower. If Ollama is not running, cleanup fails open and you get the raw transcript.</p>
        <div class="callout tip">
          <span class="callout-label">The best of both</span>
          <p>Cleanup is a dropdown, not a commitment. Plenty of people run Ollama on the road and a cloud provider at their desk.</p>
        </div>

        <h2 id="cloud">Cloud providers</h2>
        <p>Each backend uses that provider's standard API endpoint with a sensible default model. You can override the model per backend with the <strong>model override</strong> field in Settings if you prefer a specific one — leave it empty to use the default.</p>
        <p>Since cleanup is a short, simple rewriting task, the cheapest small model from any provider generally does it well. Reaching for a frontier model here mostly buys you latency.</p>

        <h2 id="latency">What to expect on speed</h2>
        <p>Cleanup adds a step between releasing the key and seeing text. Cloud providers are typically fast enough to feel immediate, with Groq marketed specifically on latency. Local Ollama depends entirely on your Mac and chosen model — a small model on Apple Silicon is comfortable; a large one on a busy Intel Mac is not.</p>
        <p>If cleanup ever feels slow, remember the 10-second cloud timeout: past that, the app gives you the raw transcript rather than making you wait.</p>

        <h2 id="switching">Switching backends</h2>
        <p>Change it any time from <strong>Settings ▸ AI cleanup</strong> or the menu-bar <strong>Cleanup</strong> submenu. Each backend keeps its own key in the Keychain, so switching back and forth does not require re-entering anything. Next steps: <a href="api-keys.html">API keys &amp; costs</a>.</p>
""",
}

PAGES["api-keys"] = {
    "head_title": "API Keys and Costs for OpenVoiceFlow Cleanup",
    "title": "API keys & costs",
    "description": "How to add an API key for OpenVoiceFlow cleanup, where keys are stored on macOS, what cleanup typically costs, and how to revoke access.",
    "lede": "Cloud cleanup is bring-your-own-key. Here is where to get one, where OpenVoiceFlow keeps it, and what you should expect to pay.",
    "body": """
        <h2 id="adding">Adding a key</h2>
        <ol>
          <li>Create an API key in your provider's console (OpenRouter, Anthropic, OpenAI, or Groq).</li>
          <li>In OpenVoiceFlow, open <strong>Dashboard ▸ Settings ▸ AI cleanup</strong>.</li>
          <li>Select the provider and paste the key into its field.</li>
        </ol>
        <p>The key is saved to your Keychain as soon as you enter it. Each backend stores its own key, so you can configure several and switch freely.</p>

        <h2 id="storage">Where keys are stored</h2>
        <p>In the <strong>macOS Keychain</strong>, as generic passwords under the service <code>app.openvoiceflow.apikeys</code>, marked accessible only after the first unlock of your Mac. They are never written to the settings file or any plain-text file on disk, and never included in history or logs.</p>
        <p>You can inspect or delete them yourself in <strong>Keychain Access</strong> by searching for that service name.</p>

        <h2 id="cost">What it costs</h2>
        <p>A cleanup request is small: your transcript plus a short instruction and your personal context, returning about the same length of text. In practical terms this is one of the cheapest possible API workloads — most people dictating all day land in the range of cents per month on a small model, not dollars.</p>
        <p>We deliberately do not print per-token prices here, because providers change them and a stale number in documentation is worse than none. Check your provider's current pricing page, and note that:</p>
        <ul>
          <li>Small and &ldquo;mini&rdquo;-class models are entirely adequate for this task.</li>
          <li>Longer dictations cost proportionally more, but they are still short by API standards.</li>
          <li>A large <a href="dictionary.html">dictionary</a> and <a href="profile.html">profile</a> add context to every request — another reason to keep them focused.</li>
          <li><a href="backends.html">Ollama</a> costs nothing at all.</li>
        </ul>

        <h2 id="revoking">Revoking and rotating</h2>
        <p>To stop using a key, clear the field in Settings, or delete the entry in Keychain Access, or revoke it in your provider's console — any of the three works, and revoking at the provider is the one that is definitive if you believe a key was exposed.</p>
        <p>Switching cleanup to <strong>None</strong> stops all outbound cleanup requests immediately, whether or not a key is still stored.</p>

        <div class="callout warn">
          <span class="callout-label">If cleanup quietly stops improving your text</span>
          <p>Because cleanup <a href="ai-cleanup.html">fails open</a>, an expired key, an exhausted balance, or a rate limit shows up as raw transcripts rather than an error message. If your output suddenly reads like exactly what you said, check your provider's dashboard first.</p>
        </div>
""",
}

# ── Reference ──────────────────────────────────────────────────────────

PAGES["settings"] = {
    "head_title": "OpenVoiceFlow Settings Reference — Every Option Explained",
    "title": "Settings reference",
    "description": "Every OpenVoiceFlow setting, its default, and what it changes: hotkey, take length, auto-paste, live words, login item, Dock icon, model, language, cleanup, and updates.",
    "lede": "Every setting in the app, what it defaults to, and what it actually changes. Grouped as they appear in Dashboard ▸ Settings.",
    "body": """
        <h2 id="dictation">Dictation</h2>
        <table>
          <thead><tr><th scope="col">Setting</th><th scope="col">Default</th><th scope="col">What it does</th></tr></thead>
          <tbody>
            <tr><td>Hotkey</td><td>fn / 🌐 Globe</td><td>The key you hold to talk. Fourteen options — see <a href="hotkeys.html">Hotkeys</a>.</td></tr>
            <tr><td>Max take length</td><td>5 minutes</td><td>Safety cap per dictation (1, 2, 5, or 10 minutes). On reaching it the take is finished and inserted, never discarded.</td></tr>
            <tr><td>Paste automatically</td><td>On</td><td>Inserts text at your cursor. Off means the app transcribes but leaves insertion to you — see <a href="text-insertion.html">How text is inserted</a>.</td></tr>
            <tr><td>Show words as you speak</td><td>On</td><td>Live partial transcript in the HUD. Costs a little compute; turn off to save battery.</td></tr>
            <tr><td>Start when you log in</td><td>On</td><td>Registers OpenVoiceFlow as a login item. A menu-bar utility that vanishes on reboot reads as broken, so this defaults on.</td></tr>
            <tr><td>Show in Dock</td><td>On</td><td>Off makes the app menu-bar only. The dashboard is still reachable from the menu bar.</td></tr>
          </tbody>
        </table>

        <h2 id="transcription">Transcription — on this Mac</h2>
        <table>
          <thead><tr><th scope="col">Setting</th><th scope="col">Default</th><th scope="col">What it does</th></tr></thead>
          <tbody>
            <tr><td>Whisper model</td><td>Chosen during onboarding</td><td>Which engine transcribes your speech. Changing it here loads the new model immediately — see <a href="models.html">Whisper models</a>.</td></tr>
            <tr><td>Language</td><td>English</td><td>The language you dictate in. All 99 languages in Whisper's multilingual set, including Ukrainian — see <a href="languages.html">Languages</a>.</td></tr>
          </tbody>
        </table>

        <h2 id="cleanup">AI cleanup</h2>
        <table>
          <thead><tr><th scope="col">Setting</th><th scope="col">Default</th><th scope="col">What it does</th></tr></thead>
          <tbody>
            <tr><td>Clean up my dictation</td><td>Off</td><td>Master switch. Off means raw on-device transcript and no network request at all.</td></tr>
            <tr><td>Provider</td><td>—</td><td>Which backend performs cleanup — see <a href="backends.html">Choosing a backend</a>.</td></tr>
            <tr><td>API key</td><td>Empty</td><td>Stored in the macOS Keychain, per provider — see <a href="api-keys.html">API keys</a>.</td></tr>
            <tr><td>Model override</td><td>Empty</td><td>Use a specific model instead of the provider default. Empty means the default.</td></tr>
          </tbody>
        </table>

        <h2 id="privacy">Privacy &amp; updates</h2>
        <table>
          <thead><tr><th scope="col">Setting</th><th scope="col">Default</th><th scope="col">What it does</th></tr></thead>
          <tbody>
            <tr><td>Reveal in Finder</td><td>—</td><td>Opens the folder holding your settings, history, and personalization files.</td></tr>
            <tr><td>Delete history…</td><td>—</td><td>Clears dictation history, with the option to keep your first-ever transcript.</td></tr>
            <tr><td>Show what was typed in the HUD</td><td>On</td><td>Echoes the tail of inserted text. Turn off when dictating sensitive material — the HUD shows a word count instead.</td></tr>
            <tr><td>Share anonymous usage &amp; leaderboard rank</td><td>On</td><td>Powers the in-app Leaderboard. On by default since 0.5.7 — full detail in <a href="privacy-architecture.html#analytics">Analytics &amp; leaderboard</a>.</td></tr>
            <tr><td>Delete my leaderboard data</td><td>—</td><td>Removes a past leaderboard submission outright; does not itself turn off future sharing.</td></tr>
            <tr><td>Automatic updates</td><td>On</td><td>Checks for signed updates in the background daily and installs them on next launch — see <a href="updates.html">Updates</a>.</td></tr>
          </tbody>
        </table>

        <h2 id="permissions">Permissions</h2>
        <p>The top card shows the state of each of the three macOS permissions with a button to grant or open System Settings. Full detail in <a href="permissions.html">Permissions</a>.</p>

        <h2 id="where">Where settings are stored</h2>
        <p><code>~/Library/Application Support/OpenVoiceFlow/settings.json</code>, excluding API keys, which live in the Keychain. The file is written atomically, and an unrecognized or missing field falls back to its default rather than resetting everything — so a settings file from an older version keeps working after an update.</p>
""",
}

PAGES["privacy-architecture"] = {
    "head_title": "OpenVoiceFlow Privacy Architecture — What Leaves Your Mac",
    "title": "Privacy architecture",
    "description": "A precise account of OpenVoiceFlow data handling: what is captured, what is written to disk, what can leave your Mac and under which setting, and what is never collected.",
    "lede": "Not a policy summary — an architecture. This page states exactly what exists on your Mac, what can leave it, and under which setting that happens.",
    "body": """
        <h2 id="audio">Audio</h2>
        <ul>
          <li>Captured only while your hotkey is held, at 16 kHz mono, <strong>into memory</strong>.</li>
          <li>Never written to disk — there is no audio file to find, recover, or leak.</li>
          <li>Discarded as soon as text exists.</li>
          <li><strong>Never transmitted.</strong> There is no setting that causes audio to leave your Mac, because no code path exists to send it.</li>
        </ul>

        <h2 id="disk">What is written to disk</h2>
        <p>Everything lives under your own user account, in <code>~/Library/Application Support/OpenVoiceFlow/</code>:</p>
        <table>
          <thead><tr><th scope="col">File</th><th scope="col">Contents</th></tr></thead>
          <tbody>
            <tr><td><code>settings.json</code></td><td>Your preferences. No secrets.</td></tr>
            <tr><td><code>dictionary.json</code></td><td>Your <a href="dictionary.html">personal dictionary</a>.</td></tr>
            <tr><td><code>snippets.json</code></td><td>Your <a href="snippets.html">snippets</a>.</td></tr>
            <tr><td><code>styles.json</code></td><td>Your <a href="styles.html">per-app style</a> map.</td></tr>
            <tr><td><code>profile.json</code></td><td>Your <a href="profile.html">Know-Me profile</a>.</td></tr>
            <tr><td>History and stats files</td><td>Recent transcripts (most recent 500), word counts, per-app and per-day totals, and your first-ever transcript.</td></tr>
          </tbody>
        </table>
        <p>Speech models are cached separately at <code>~/Documents/huggingface/models/argmaxinc/whisperkit-coreml/</code>. API keys are in the <strong>macOS Keychain</strong>, service <code>app.openvoiceflow.apikeys</code> — never in any file above.</p>

        <h2 id="network">Every outbound connection</h2>
        <p>The app makes exactly four kinds of network request, and you can reason about all of them:</p>
        <table>
          <thead><tr><th scope="col">Request</th><th scope="col">When</th><th scope="col">Contains</th></tr></thead>
          <tbody>
            <tr><td>Model download</td><td>The first time you select a given Whisper model</td><td>Nothing about you — it is a public model file fetch.</td></tr>
            <tr><td>Update check</td><td>Daily, and at launch, if automatic updates are on</td><td>A request for the signed appcast at openvoiceflow.com. No account, no identifier.</td></tr>
            <tr><td>Cleanup request</td><td>Per dictation, <strong>only</strong> if you enabled a cloud backend</td><td>Transcript text, cleanup instruction, style, and your dictionary/profile context. Never audio.</td></tr>
            <tr><td>Usage sync</td><td>Roughly every few minutes of active dictation, <strong>only</strong> if &ldquo;Share anonymous usage &amp; leaderboard rank&rdquo; is on (Settings ▸ Privacy — on by default since 0.5.7)</td><td>See <a href="#analytics">Analytics &amp; leaderboard</a> below. Never audio, never dictated text.</td></tr>
          </tbody>
        </table>
        <p>Set cleanup to <strong>None</strong> (the default) or <strong>Ollama</strong>, and the cleanup row never happens. Turn off automatic updates and the update-check row stops too. Turn off usage sharing and the fourth row stops immediately — nothing queues up and sends later.</p>

        <h2 id="analytics">Analytics &amp; leaderboard</h2>
        <p>Since <strong>0.5.7</strong>, the app can share an anonymous usage summary to power an in-app leaderboard ranked by time back (typing time avoided, not a net saving — see the dashboard manual). This is a real change from earlier versions, which sent nothing — it's on by default, and this section says exactly what that means.</p>
        <p><strong>Turning it off:</strong> Settings ▸ Privacy ▸ <em>&ldquo;Share anonymous usage &amp; leaderboard rank&rdquo;</em>. Off stops every request in the row above; nothing is cached to send later. The screen and feature counters keep counting locally &mdash; that is how Home shows your own totals &mdash; they simply stop leaving your Mac. <em>&ldquo;Delete my leaderboard data&rdquo;</em> clears the local counters too, so nothing you deleted can be re-uploaded by the next sync.</p>
        <p><strong>What's sent, when it's on:</strong></p>
        <ul>
          <li>A random device ID generated for this installation (not tied to your Apple ID, email, or any account — there is no account) and a display name you can change, shown to other users on the leaderboard. Installations remain separate even when they use the same nickname, so three computers produce three independent rows.</li>
          <li>Aggregate counters already shown on your Home pane: total words dictated, total time back, your streak, and which features are on (cleanup enabled, snippet/dictionary counts, whether you've run Know-Me) — counts only, never contents.</li>
          <li><strong>Which parts of the app you use (since 0.5.22).</strong> A running count per screen (Home, History, Personalize and its tabs, Settings, Leaderboard) and per feature you press (finished a dictation, added a dictionary word or a snippet, started the Know-Me interview, changed the cleanup backend, checked for updates, opened Feedback, and similar). Each one is a fixed name and a number &mdash; <code>pane.history</code>, 12 &mdash; with <strong>no timestamps and no ordering</strong>, so it can show that a feature gets used and never when you used it or what you did around it. The list of names is compiled into the app and the server discards anything not already on its matching list, which is what keeps text you type or dictate out of it entirely.</li>
          <li>Your country, derived server-side from the request at the moment it arrives. Your IP address itself is never logged or stored.</li>
        </ul>
        <p>Aggregate totals sync periodically during active dictation. Opening Leaderboard sends the same aggregate snapshot before fetching standings, so saved local totals can restore that installation's row. Changing a nickname also sends the snapshot once when you press Return or leave the field; individual keystrokes are not uploaded.</p>
        <p><strong>What's never sent, whether or not this is on:</strong> dictated text, snippets, dictionary entries, Know-Me profile content, or anything from the cleanup path. Those stay exactly as described in the rest of this page.</p>
        <p>The leaderboard itself never discloses how many people use OpenVoiceFlow in total — only ranks and time-saved figures for the people shown. Two things keep it that way: the API names only the leaders past a usage bar and caps how many rows it will return, and the app draws a fixed number of rows whatever comes back, masking the ones it has no name for. So neither the response nor the height of the board is a headcount. Masked rows stand for withheld names; they are never invented people.</p>

        <h2 id="never">What is never collected</h2>
        <ul>
          <li><strong>No dictation content, ever.</strong> Not your words, not your audio — the usage summary above is aggregate counts only.</li>
          <li><strong>No account.</strong> Nothing to sign up for. The device ID above identifies one app installation, not a person; installations are never merged by nickname.</li>
          <li><strong>No precise location.</strong> Country-level only, derived at request time; no IP address is stored.</li>
          <li><strong>No screen reading.</strong> Accessibility permission is used only to send a paste keystroke.</li>
          <li><strong>No keystroke logging.</strong> Input Monitoring watches for one key; everything else passes straight through.</li>
        </ul>
        <div class="callout">
          <span class="callout-label">About this website</span>
          <p>openvoiceflow.com uses privacy-friendly Vercel Analytics for anonymous page views and Speed Insights for performance — website measurement only, with no advertising cookies and no cross-site profile. That's separate from the app-level usage summary described above, which is documented in full in this section rather than folded into the website's own analytics. Details on the <a href="../privacy.html">privacy page</a>.</p>
        </div>

        <h2 id="verify">Verifying this yourself</h2>
        <p>Two checks anyone can run:</p>
        <ul>
          <li><strong>Airplane mode.</strong> Turn off Wi-Fi with cleanup set to None and dictate. It works, because dictation itself never needs a network — the usage sync above is fire-and-forget and never blocks it.</li>
          <li><strong>Network monitor.</strong> Run Little Snitch or similar and watch. With cleanup off and usage sharing off, dictation generates no connections at all. With usage sharing on (the default), you'll see the occasional request described in the table above, and nothing else.</li>
        </ul>
        <p>OpenVoiceFlow's source is public, so every claim here is checkable in the code itself rather than taken on trust. If anything on this page does not match what the app does, that is a bug — tell us at <a href="mailto:shimoverse@gmail.com">shimoverse@gmail.com</a>.</p>
""",
}

PAGES["updates"] = {
    "head_title": "OpenVoiceFlow Updates — Automatic Signed Updates on macOS",
    "title": "Updates & versions",
    "description": "How OpenVoiceFlow updates itself: signed Sparkle updates, the daily check, how to update manually, how to turn automatic updates off, and how to check your version.",
    "lede": "Updates are signed, verified, and quiet. Here is what runs on your behalf and how to take manual control of it.",
    "body": """
        <h2 id="how">How updating works</h2>
        <p>OpenVoiceFlow uses <strong>Sparkle</strong>, the standard update framework for Mac apps distributed outside the App Store. With automatic updates on, it checks a signed feed hosted on openvoiceflow.com at launch and roughly once a day, downloads any newer version in the background, and installs it the next time you launch the app.</p>

        <h2 id="security">How updates are verified</h2>
        <p>Two independent checks must pass before anything installs:</p>
        <ul>
          <li><strong>EdDSA signature.</strong> Every update is signed with a private key held by the maintainers, and each shipped app pins the matching public key. An update that is not signed with that exact key is rejected.</li>
          <li><strong>Apple notarization.</strong> The downloaded build must carry a valid Developer-ID signature and Apple notarization.</li>
        </ul>
        <p>This is why the update path is safe to leave on: an attacker who compromised the download would still need the signing key, which never leaves the maintainers' control.</p>

        <h2 id="manual">Updating manually</h2>
        <p>Choose <strong>Check for Updates…</strong> from the menu-bar menu, or use <strong>Check for updates now</strong> in <strong>Dashboard ▸ Settings</strong>. If a newer version exists you will be shown what changed before anything installs.</p>

        <h2 id="turnoff">Turning automatic updates off</h2>
        <p><strong>Dashboard ▸ Settings ▸ Automatic updates</strong>. With it off, no background checks are made and no update downloads — you can still check manually at any time.</p>
        <div class="callout tip">
          <span class="callout-label">A reason to leave it on</span>
          <p>Even with usage sharing on, the anonymous summary doesn't tell us who's on an old build in any actionable way — there's no way to reach a specific device. Automatic updates are how a fix for something like a broken model download actually reaches you.</p>
        </div>

        <h2 id="version">Checking your version</h2>
        <p>The dashboard sidebar footer shows your version and whether it is current: <em>Up to date</em> when the latest release is the one you are running, or an <em>Update</em> link that installs the new version when there is one. <strong>Settings</strong> shows the version too, alongside the manual check button. This documentation describes <strong>0.5.24</strong>.</p>

        <h2 id="downgrade">Reinstalling or going back</h2>
        <p>To reinstall, download the current DMG from the <a href="%s">download page</a> and replace the copy in Applications; your settings, history, and personalization are stored separately and survive. There is no supported downgrade path — older builds are not hosted, and installing one would disable the fixes that came after it.</p>
""" % DL,
}

PAGES["uninstall"] = {
    "head_title": "Uninstalling OpenVoiceFlow — Remove Every Trace",
    "title": "Uninstalling",
    "description": "How to completely remove OpenVoiceFlow from your Mac, including settings, history, downloaded speech models, Keychain entries, and permission grants.",
    "lede": "No uninstaller and no leftovers to hunt down — the app is a single bundle plus one folder. Here is the complete list, in order.",
    "body": """
        <h2 id="steps">Complete removal</h2>
        <ol>
          <li><strong>Quit the app</strong> from the menu-bar menu.</li>
          <li><strong>Delete the app:</strong> drag <code>/Applications/OpenVoiceFlow.app</code> to the Trash. This also removes the login item.</li>
          <li><strong>Delete your data:</strong> remove <code>~/Library/Application Support/OpenVoiceFlow/</code> — settings, history, dictionary, snippets, styles, and profile.</li>
          <li><strong>Delete the speech models</strong> (the big one): remove <code>~/Documents/huggingface/models/argmaxinc/whisperkit-coreml/</code>. Models are up to 1.6 GB each.</li>
          <li><strong>Remove API keys</strong> (only if you used cloud cleanup): open <strong>Keychain Access</strong>, search for <code>app.openvoiceflow.apikeys</code>, and delete the entries.</li>
          <li><strong>Revoke permissions</strong> (optional): in <strong>System Settings ▸ Privacy &amp; Security</strong>, remove OpenVoiceFlow from Microphone, Accessibility, and Input Monitoring.</li>
        </ol>
        <p>That is everything. No background daemons, kernel extensions, or system-level files are installed at any point, so there is nothing else to clean up.</p>

        <div class="callout tip">
          <span class="callout-label">Just want the disk space back?</span>
          <p>Step 4 alone recovers nearly all of it. If you switch models occasionally, that folder may hold several — deleting it is safe, and the app re-downloads whichever model you select next.</p>
        </div>

        <h2 id="keep">Clearing your data but keeping the app</h2>
        <p>You do not have to uninstall to reset. <strong>Dashboard ▸ Settings ▸ Delete history…</strong> clears your transcripts, with an option to keep your first-ever dictation. <strong>Know-Me ▸ Clear</strong> empties your profile. Dictionary and snippet entries can be deleted individually from the Personalize pane.</p>

        <h2 id="reinstall">Reinstalling later</h2>
        <p>If you leave the Application Support folder in place, reinstalling picks up exactly where you left off — same settings, same history, same dictionary. Remove that folder first if you want a genuinely clean start.</p>

        <h2 id="feedback">Before you go</h2>
        <p>If something drove you to uninstall, we would genuinely like to know which thing it was — <a href="mailto:shimoverse@gmail.com">shimoverse@gmail.com</a>. The project has no individual retention analytics, so an email is the only way that detailed signal reaches anyone.</p>
""",
}

# ── Help ───────────────────────────────────────────────────────────────

PAGES["troubleshooting"] = {
    "head_title": "OpenVoiceFlow Troubleshooting — Common Problems and Fixes",
    "title": "Troubleshooting",
    "description": "Fixes for common OpenVoiceFlow problems: the hotkey not working, no text appearing, poor accuracy, model download failures, cleanup not applying, and high memory use.",
    "lede": "Symptoms, causes, and fixes for the problems people actually report. Start with the one that matches what you are seeing.",
    "body": """
        <div class="issue">
          <h3 id="hotkey-nothing">Holding the key does nothing</h3>
          <dl>
            <dt>Symptoms</dt>
            <dd>No HUD appears, no waveform, nothing happens when you hold your hotkey.</dd>
            <dt>Most likely cause</dt>
            <dd>Missing <strong>Input Monitoring</strong> permission. This is the single most common cause by a wide margin.</dd>
            <dt>Fixes</dt>
            <dd>
              <ol>
                <li>Check <strong>Dashboard ▸ Settings ▸ Permissions</strong>. Grant anything not showing as granted.</li>
                <li>If macOS shows the prompt but nothing changes, open <strong>System Settings ▸ Privacy &amp; Security ▸ Input Monitoring</strong>, click <strong>+</strong>, and add OpenVoiceFlow from Applications.</li>
                <li>Check the app is not <strong>paused</strong> — the menu-bar menu shows this, and pausing lasts an hour.</li>
                <li>Check another app has not claimed the key globally (Raycast, Alfred, Karabiner). Try a different hotkey to confirm.</li>
                <li>If you moved the app after granting permissions, macOS may have invalidated the grant. Put it back in <code>/Applications</code> and re-grant.</li>
              </ol>
            </dd>
          </dl>
        </div>

        <div class="issue">
          <h3 id="fn-emoji">Pressing fn opens emoji or Apple's dictation</h3>
          <dl>
            <dt>Cause</dt>
            <dd>macOS has its own assignment for the 🌐 Globe key, and it takes priority.</dd>
            <dt>Fix</dt>
            <dd>Open <strong>System Settings ▸ Keyboard</strong> and set <strong>Press 🌐 to</strong> → <strong>Do Nothing</strong>. Or pick a different key in <a href="hotkeys.html">Hotkeys</a> — <kbd>Right ⌘</kbd> is the usual choice.</dd>
          </dl>
        </div>

        <div class="issue">
          <h3 id="no-text">It hears me, but no text appears</h3>
          <dl>
            <dt>Symptoms</dt>
            <dd>The waveform moves and the HUD shows words, but nothing is inserted — or the HUD says <strong>Copied instead — press ⌘V</strong>.</dd>
            <dt>Cause</dt>
            <dd>Missing <strong>Accessibility</strong> permission, so the app cannot press <kbd>⌘V</kbd> for you.</dd>
            <dt>Fixes</dt>
            <dd>
              <ol>
                <li>Your text is not lost — it is on the clipboard. Press <kbd>⌘V</kbd> to place it now.</li>
                <li>Grant Accessibility in <strong>System Settings ▸ Privacy &amp; Security ▸ Accessibility</strong>, adding the app with <strong>+</strong> if it is absent.</li>
                <li>Check <strong>Paste automatically</strong> is on in <strong>Settings ▸ Dictation</strong>.</li>
                <li>Confirm your cursor is in a text field that accepts a paste — some apps intercept <kbd>⌘V</kbd> themselves.</li>
              </ol>
            </dd>
          </dl>
        </div>

        <div class="issue">
          <h3 id="flat-wave">The waveform stays flat</h3>
          <dl>
            <dt>Cause</dt>
            <dd>The app is not receiving audio — a microphone permission, input selection, or hardware issue.</dd>
            <dt>Fixes</dt>
            <dd>
              <ol>
                <li>Check Microphone permission in <strong>Settings ▸ Permissions</strong>.</li>
                <li>Check <strong>System Settings ▸ Sound ▸ Input</strong> — the right device selected, and its level moving when you speak.</li>
                <li>Disconnect and reconnect a Bluetooth headset; they occasionally attach with a broken input profile.</li>
                <li>Quit other apps that may be holding the microphone exclusively.</li>
              </ol>
            </dd>
          </dl>
        </div>

        <div class="issue">
          <h3 id="accuracy">Accuracy is poor</h3>
          <dl>
            <dt>Fixes, in order of effect</dt>
            <dd>
              <ol>
                <li><strong>Microphone position.</strong> Sit at normal working distance or use a headset. This fixes most cases.</li>
                <li><strong>Speak in phrases</strong>, not word by word — Whisper needs context to disambiguate.</li>
                <li><strong>Add problem words</strong> to your <a href="dictionary.html">dictionary</a> (requires cleanup on).</li>
                <li><strong>Move up a model size</strong> in <a href="models.html">Settings ▸ Transcription</a>.</li>
                <li>For non-English, make sure you are on a large enough model — see <a href="languages.html">Languages</a>.</li>
              </ol>
              <p>Full detail: <a href="accuracy.html">Improving accuracy</a>.</p>
            </dd>
          </dl>
        </div>

        <div class="issue">
          <h3 id="dictionary-ignored">My dictionary or profile is being ignored</h3>
          <dl>
            <dt>Cause</dt>
            <dd>Almost always that <a href="ai-cleanup.html">AI cleanup</a> is set to <strong>None</strong>. The dictionary, Know-Me profile, and per-app styles are all applied during cleanup — with it off, they cannot do anything.</dd>
            <dt>Fixes</dt>
            <dd>
              <ol>
                <li>Turn on cleanup in <strong>Settings ▸ AI cleanup</strong> and pick a backend.</li>
                <li>If cleanup is already on, verify your API key and provider balance — cleanup <a href="ai-cleanup.html">fails open</a>, so an expired key looks exactly like raw transcripts.</li>
                <li>Want the dictionary without sending text anywhere? Use <a href="backends.html">local Ollama</a>.</li>
              </ol>
            </dd>
          </dl>
        </div>

        <div class="issue">
          <h3 id="model-fail">A model download fails or gets stuck</h3>
          <dl>
            <dt>Fixes</dt>
            <dd>
              <ol>
                <li>Use <strong>Try again</strong> — the app clears the partial download first, which resolves most cases.</li>
                <li>Open <strong>Details</strong> on the error for the actual reason rather than guessing.</li>
                <li>Check free disk space: Large turbo needs about 1.6 GB plus room to compile.</li>
                <li>A corporate VPN or proxy can block the model host. Try another network.</li>
                <li>Manual reset: quit the app, delete <code>~/Documents/huggingface/models/argmaxinc/whisperkit-coreml/</code>, relaunch, re-select the model.</li>
              </ol>
            </dd>
            <dt>Tip</dt>
            <dd>The progress bar reaching the top and then pausing is not a hang — that is macOS compiling the model, and it happens once per model.</dd>
          </dl>
        </div>

        <div class="issue">
          <h3 id="cleanup-slow">Cleanup is slow, or output is unchanged</h3>
          <dl>
            <dt>Causes and fixes</dt>
            <dd>
              <ul>
                <li><strong>Unchanged output:</strong> cleanup fails open. A missing/expired key, no balance, or a provider outage all yield the raw transcript. Check your provider dashboard.</li>
                <li><strong>Slow with a cloud provider:</strong> requests time out at 10 seconds and fall back to raw text, so this shows up as inconsistency rather than a hang. Try a smaller model or a faster provider.</li>
                <li><strong>Slow with Ollama:</strong> local generation is bounded by your Mac. Use a smaller model — a 3B-class instruct model is plenty for cleanup.</li>
                <li><strong>Ollama not responding:</strong> make sure Ollama is actually running and listening on <code>localhost:11434</code>.</li>
              </ul>
            </dd>
          </dl>
        </div>

        <div class="issue">
          <h3 id="thankyou">Output says &ldquo;Thank you&rdquo; or &ldquo;Thanks for watching&rdquo;</h3>
          <dl>
            <dt>Cause</dt>
            <dd>A known Whisper family behaviour: on near-silent or very short audio, the model can emit a stock phrase learned from subtitled video.</dd>
            <dt>Fixes</dt>
            <dd>
              <ul>
                <li>Hold the key only while actually speaking, and start speaking promptly.</li>
                <li>Check your microphone is picking you up — a flat waveform makes this far more likely.</li>
                <li>A larger model reduces but does not eliminate it.</li>
              </ul>
            </dd>
          </dl>
        </div>

        <div class="issue">
          <h3 id="memory">High memory or CPU use</h3>
          <dl>
            <dt>Cause</dt>
            <dd>Larger Whisper models are genuinely large — Medium and Large turbo hold well over a gigabyte in memory while loaded. This is expected, not a leak.</dd>
            <dt>Fixes</dt>
            <dd>
              <ul>
                <li>Drop to <strong>Small</strong> in <a href="models.html">Settings ▸ Transcription</a>, especially on 8 GB Macs.</li>
                <li>Turn off <strong>Show words as you speak</strong>, which re-transcribes while you hold the key.</li>
                <li>On Intel Macs, prefer Small or Tiny — there is no Neural Engine to offload to.</li>
              </ul>
            </dd>
          </dl>
        </div>

        <div class="issue">
          <h3 id="icon-missing">The menu-bar icon is missing</h3>
          <dl>
            <dt>Cause</dt>
            <dd>A full menu bar — common on laptops with a notch — silently hides overflow icons.</dd>
            <dt>Fixes</dt>
            <dd>
              <ul>
                <li>Quit another menu-bar app to make room, or use a menu-bar manager.</li>
                <li>Open the dashboard from the Dock icon instead, or turn <strong>Show in Dock</strong> back on in Settings.</li>
              </ul>
            </dd>
          </dl>
        </div>

        <h2 id="still">Still stuck?</h2>
        <p>Use the <strong>Feedback</strong> item in the dashboard sidebar, or email <a href="mailto:shimoverse@gmail.com">shimoverse@gmail.com</a> with your macOS version, your Mac's chip, your OpenVoiceFlow version (Settings shows it), the model you are using, and what you saw versus what you expected. The anonymous usage summary (see <a href="privacy-architecture.html#analytics">Privacy architecture</a>) is aggregate counts, not diagnostics — it can't tell us what went wrong on your machine, so a real description is still what gets bugs fixed.</p>
""",
}

PAGES["faq"] = {
    "head_title": "OpenVoiceFlow FAQ — Free Voice Dictation for macOS",
    "title": "FAQ",
    "description": "Frequently asked questions about OpenVoiceFlow: whether it is really free, how private it is, offline use, accuracy, supported Macs, languages, and how it compares to alternatives.",
    "lede": "Short answers to what we get asked most. Longer versions link through to the relevant page.",
    "faq": [
        ("Is OpenVoiceFlow really free?",
         "Personal and qualifying noncommercial use is free, with no account or trial period. Business use, resale, bundling, paid products or services, and other commercial use require a separate license from Shimoverse Studios; contact shimoverse@gmail.com. If you enable optional cloud cleanup you pay your chosen AI provider directly for tokens."),
        ("Does my voice leave my Mac?",
         "No. Audio is transcribed on-device by Whisper and discarded once text exists. There is no code path that uploads audio. If you turn on cloud AI cleanup, the resulting text is sent to the provider you chose under your own key; choosing Ollama or leaving cleanup off keeps everything local."),
        ("Does it work offline?",
         "Yes. After the one-time model download, dictation works in airplane mode — the usage-sharing sync (if you've left it on) is fire-and-forget and never blocks it. With cleanup and usage sharing both off, no network request is made at any point."),
        ("Which Macs are supported?",
         "macOS 14 Sonoma or newer, on both Apple Silicon and Intel. One universal build covers both. For macOS 12 to 13 a retained 0.3.6 Apple Silicon build is available, but it is end-of-life."),
        ("Is there a Windows, Linux, iPhone, or Android version?",
         "Not today. OpenVoiceFlow is macOS-only. iOS and Android versions are in development but cannot be downloaded yet."),
        ("How accurate is it?",
         "That depends on your microphone, accent, vocabulary, and model choice far more than on anything we could benchmark. Whisper's larger models are widely regarded as excellent. The honest test takes a minute: dictate a real paragraph of your own work and judge the result."),
        ("Can I say punctuation out loud?",
         "Not in version 0.5.24 — saying 'comma' produces the word 'comma'. Whisper punctuates from sentence structure automatically, and optional AI cleanup fixes grammar and removes filler words if you want more."),
        ("Why is my dictionary not working?",
         "The personal dictionary, Know-Me profile, and per-app styles are all applied during AI cleanup. With cleanup set to None, which is the default, they have no effect. Turn cleanup on, or use local Ollama if you want that behaviour without sending text to a cloud."),
        ("Which languages does it support?",
         "All 99 languages in Whisper's multilingual set, including Ukrainian, Arabic, Hindi, and Chinese — see the full list on the <a href=\"languages.html\">Languages</a> page. Accuracy outside English depends heavily on model size, so use the largest model your Mac handles comfortably."),
        ("What happens if the AI cleanup service fails?",
         "You get your raw transcript. Cleanup is designed to fail open: on a missing key, an error, a timeout, or an unparseable response, the app inserts the on-device transcription rather than losing your words."),
        ("Does it collect any analytics?",
         "As of 0.5.7, yes, and it's on by default: an anonymous usage summary (word/time totals, which features you use, your country, and a display name you choose) powers an in-app leaderboard. Never audio, never dictated text, never anything from your dictionary, snippets, or Know-Me profile. Turn it off in Settings ▸ Privacy ▸ \"Share anonymous usage & leaderboard rank\" — full detail in Privacy architecture's Analytics & leaderboard section. The website separately uses privacy-friendly anonymous page-view analytics — page views plus counts of which links and buttons get clicked — unrelated to the app and tied to no identifier."),
        ("How do I get support?",
         "Use the Feedback item in the dashboard sidebar, or email shimoverse@gmail.com. Include your macOS version, your Mac's chip, your OpenVoiceFlow version, and what you saw versus what you expected — the usage summary is aggregate counts, not diagnostics, so your description is still what gets things fixed."),
        ("Can I use OpenVoiceFlow at work with confidential material?",
         "The architecture supports that case: audio never leaves the machine, and with cleanup off or pointed at local Ollama, neither does text. Your organization's own policy still applies, and the public source lets your security team verify the claims. Workplace or other business use requires a commercial license from Shimoverse Studios."),
        ("Can I use the code in my own project?",
         "For personal and qualifying noncommercial purposes, yes, under the OpenVoiceFlow Personal and Reciprocal Source License 1.0. If you distribute a derivative or let others use a modified version over a network, publish its complete corresponding source under the same license, keep the required notices, and rebrand the derivative. Business use, paid products or services, bundling, resale, and other commercial use require a separate license even when source is published; contact shimoverse@gmail.com."),
    ],
    "body": """
        <p>If your question is not here, the <a href="troubleshooting.html">troubleshooting guide</a> covers specific symptoms, and <a href="privacy-architecture.html">privacy architecture</a> answers data questions in far more depth. Anything still unanswered: <a href="mailto:shimoverse@gmail.com">shimoverse@gmail.com</a>.</p>
""",
}
