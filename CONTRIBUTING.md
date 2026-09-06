# Contributing to OpenVoiceFlow

Thanks for thinking about contributing. If anything in this file is wrong or
out of date, that itself is a bug — please open an issue.

## What this project is, briefly

OpenVoiceFlow is a macOS-only voice-dictation app, free for personal use only:
hold a hotkey, speak, and text appears at your
cursor. The **shipping app is native Swift** and lives in
`native/`. The repo also carries the legacy Python app (`voiceflow/`, ≤ 0.3.6)
it replaced — end-of-life, no security fixes, kept for reference and the
macOS 12–13 fallback build. New work belongs in `native/` unless you're fixing
something in the website or docs.

This is a **single-maintainer source-available project**. Issues and PRs get
best-effort responses on a human schedule. There is no SLA. If you build on
this code in your own project, follow the reciprocal-source and rebranding
requirements in [LICENSE](LICENSE). You are welcome to tell us about it at
shimoverse@gmail.com — we like knowing where the work travels.

## Working on the native app (the usual case)

You need a Mac on macOS 14+, Xcode 16.4+ (WhisperKit 0.18 needs Swift tools
6.1), and XcodeGen:

```bash
brew install xcodegen
git clone https://github.com/shimoverse/openvoiceflow.git
cd openvoiceflow
bash native/scripts/run-local.sh   # generate project, build, launch
```

The Xcode project is **generated** from `native/project.yml` — edit that, not
the `.xcodeproj`. The build signs ad-hoc so the permission-bound features
(hotkey, paste) actually work on your machine.

What CI checks on every PR (`.github/workflows/ci.yml`):

- **`native-build`** — compiles the Swift app on macos-15 with Xcode 16.4.
  If your PR touches `native/`, this must pass.
- **`test`** — pytest on Python 3.9/3.10/3.11. This covers the website
  distribution tests (`tests/test_docs_distribution.py`) and the legacy app.
- **ruff** — lint for the Python tree.

There is **no Swift test target yet**; the app is verified by CI compile plus
on-device passes. Adding an XCTest target for the pure-logic pieces
(`Settings`, `CleanupProvider` prompt assembly, hotkey flag decoding) would be
one of the most valuable first contributions.

### Conventions in the Swift tree

- Match the file you're in: comment density, naming, SwiftUI idioms.
- Comments explain *why*, or a constraint the code can't show — not what the
  next line does.
- One feature per PR. Screenshots or a short screen recording in the PR body
  for anything visual.
- Version bumps are release work, not feature work — leave
  `project.yml`/`Info.plist` versions alone unless you're cutting a release
  (all four fields must move together; CI enforces it at release time).

## Working on the website (`docs/`)

The site is static HTML/CSS/JS served by Vercel from `docs/`. It has real
tests:

```bash
python3 -m pytest tests/test_docs_distribution.py -q
```

They pin download filenames, checksums, appcast integrity, and the
Gatekeeper-warning cards. If your change breaks one, read the test — each one
documents the support question or invariant it protects.

## Maintainer analytics dashboard

Repository traffic, aggregate website analytics, and the app's own aggregate
install and usage counters can be combined into a private local dashboard:

```bash
gh auth status
vercel whoami
export OVF_ANALYTICS_STATS_TOKEN=…        # matches ANALYTICS_STATS_TOKEN on the deployment
python3 scripts/analytics_dashboard.py --open
```

`OVF_ANALYTICS_STATS_TOKEN` authenticates against `api/analytics/stats.js`, the
aggregate install/usage endpoint. It is deliberately private: the public
leaderboard hides the population size on purpose (`api/leaderboard.js`), and an
open install counter would give that away. Set `ANALYTICS_STATS_TOKEN` in the
Vercel project to a long random value and use the same value here; without it
the endpoint answers 404 and the dashboard's app sections report themselves
unavailable rather than claiming the app sends nothing.

The generated HTML and normalized snapshot live in `.analytics-dashboard/`,
use owner-only file permissions, and are ignored by Git. The dashboard never
copies GitHub or Vercel credentials into its output. It deliberately keeps
repository views, clone operations, CI checkouts, release-asset requests,
website visitors, and verified installs separate: none is a proxy for another.

The GitHub traffic window is short, so rebuild or archive the private snapshot
regularly if trend history matters. Website data comes from Vercel's documented
Web Analytics REST API. `--no-vercel` and `--no-app` each drop one source.

Verified installs count *devices that share anonymous usage* (opt-out, on by
default — `PRIVACY.md` §7). That makes it a floor, not a headcount: one person
with two Macs is two, and anyone who opted out is invisible. Say "opted-in
installs" when quoting it, never "users".

## Working on the legacy Python app

Only security-relevant or fallback-critical fixes are accepted; features
won't be. Setup, if you truly need it:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[all,dev]"
pytest -q
```

## Reporting bugs

Use the issue templates. The fields that make a report actionable: macOS
version (`sw_vers`), app version (menu bar → Open Dashboard → Settings shows
it), which speech engine you chose, and what the HUD showed when it went
wrong. For dictation-accuracy issues, the exact spoken phrase vs. what landed.

Security issues: **don't** open a public issue — see [SECURITY.md](SECURITY.md).

## Pull-request checklist

- [ ] CI green (`native-build` for Swift changes, pytest for website/Python)
- [ ] For UI changes: screenshot or recording in the PR body
- [ ] For behavior changes: the PR body says what changed *for the user*
- [ ] No version bumps, no new dependencies without discussion in an issue
- [ ] You agree to the contribution and licensing terms below

## License

The project is source-available under the [OpenVoiceFlow Personal and Reciprocal
Source License 1.0](LICENSE), with separate commercial and organizational licenses available from
Shimoverse Studios. Distributed derivatives and modified network versions must
publish complete corresponding source under the same license. See
[LICENSING.md](LICENSING.md).

By submitting a contribution, you represent that you have the right to do so
and grant Shimoverse Studios a perpetual, worldwide, non-exclusive,
royalty-free, irrevocable copyright and patent license to use, reproduce,
modify, distribute, sublicense, and relicense that contribution, including as
part of commercial and organizational licenses. You also agree that the contribution may be
distributed under the project's current or future public license. This grant
does not transfer your copyright ownership.
