# AGENTS.md — how to work in this repo

For AI agents and humans alike. If this file disagrees with the code, the code
wins — and fixing this file is part of the change.

## The lay of the land

- **`native/`** — the shipping macOS app (Swift/SwiftUI, v0.5.x). This is
  where product work happens. The Xcode project is generated from
  `native/project.yml`; edit the yml, never the `.xcodeproj`.
- **The website is not in this repo.** The marketing site, docs site, SEO
  surface and the analytics/leaderboard API live in the private
  [shimoverse/openvoiceflow-web](https://github.com/shimoverse/openvoiceflow-web)
  repo, which Vercel deploys. Site claims must still be true of the shipped
  app; the cross-repo contract tests there check the app half against a clone
  of this repo.
- **`voiceflow/` + `install.sh` + `build-dmg.sh`** — the legacy Python app
  (≤ 0.3.6, EOL). Only fallback-critical fixes. Its conventions (secure
  file writes via `voiceflow/_secure_io.py`, `from __future__ import
  annotations` for 3.9 compat) still apply to any touch there, and its tests
  still run in CI.
- **`.github/workflows/`** — CI compiles the Swift app and runs pytest on
  every PR. `release-native.yml` is the tag-driven release;
  `create-release-tag.yml` plants/moves tags for environments that can't
  push them. See `RELEASE.md` for the whole process.

## Ground rules

- Branch → PR → green CI → squash-merge. No direct pushes to `main`; never
  `git push --force` to shared branches.
- Versions are release work: the four version fields
  (`project.yml` ×2, `Info.plist` ×2) move together or not at all, and only
  when cutting a release.
- Privacy defaults are one-way: changes that make defaults *more* private are
  ordinary PRs; anything more permissive needs explicit maintainer sign-off
  in the PR description.
- Never regenerate the Sparkle keypair. Every shipped app pins the public
  key; a new pair breaks updates for every install, permanently.
- The website tests are contracts, not decoration — each one names the
  support question it prevents. Read the test before "fixing" it.
- Claims on the website must be true of the shipped app. When in doubt,
  understate.

## Verifying work

- Swift: CI's `native-build` compiles it; behavior needs a Mac
  (`bash native/scripts/run-local.sh`). Say plainly in the PR what was
  compile-verified vs. device-verified.
- Website: `python3 -m pytest tests/test_docs_distribution.py -q` locally,
  plus a look at the rendered page.
- Python (legacy): `pytest -q`.
