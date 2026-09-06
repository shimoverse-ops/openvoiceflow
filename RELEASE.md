# Releasing OpenVoiceFlow (native app)

The release pipeline is tag-driven and fully automatable — including from
environments that cannot push git tags. The legacy Python/PyPI process this
file used to describe is retired; `release.yml` refuses `v*` tags at 0.4.0+.

## The four version fields move together

`native/project.yml` → `MARKETING_VERSION` + `CURRENT_PROJECT_VERSION`
`native/Info.plist` → `CFBundleShortVersionString` + `CFBundleVersion`

The build number must strictly increase past the last published appcast build
— Sparkle orders updates by it and **silently offers nothing** if it stalls.
The release workflow's classify step hard-fails on any mismatch.

## Steps

1. **Bump** all four fields on a branch; PR; merge on green CI.
2. **Tag** — dispatch the **Create release tag** workflow with
   `tag: native-vX.Y.Z` and the full merge-commit SHA. (Exists because remote
   sessions can't push tags; it can also *move* a tag, but only one that has
   never had a published Release — shipped tags are immutable.)
3. **Build** — dispatch **Release (native app)** with
   `release_tag: native-vX.Y.Z`. It builds a universal DMG, signs the app
   *and the DMG*, notarizes, staples, generates the signed appcast, and
   attaches everything to a GitHub Release. Requires the Apple signing
   secrets and `SPARKLE_ED_PRIVATE_KEY`; fails loudly without them.
4. **Publish** — copy the Release's DMG + `appcast.xml` into
   `docs/downloads/` + `docs/appcast.xml`, sweep every version reference
   (`vercel.json`, `docs/*.html`, `site.js`, `llms.txt`, the tests), verify
   `pytest tests/test_docs_distribution.py`, PR, merge. **This merge is the
   moment users start updating** — the app polls the website's appcast, not
   GitHub.

   The same PR must add the CHANGELOG entry and regenerate the release pages
   with `python3 scripts/build_releases.py`. That writes `docs/releases.html`
   (what Sparkle's **Version History** button opens) and
   `docs/release-notes/<version>.html` (what its update sheet loads), and the
   appcast published in this PR links to both by URL — ship the appcast
   without them and every updating user gets a 404 where the notes should be.
   `test_appcast_release_notes_links_point_at_pages_that_exist` fails the PR
   if they are missing.
5. **Verify live**: the site serves the new appcast build number, the DMG
   sha256 matches the notarized artifact byte-for-byte, and
   `https://openvoiceflow.com/release-notes/<version>.html` resolves.
6. Prune the previous version's DMG from `docs/downloads/` and add its
   redirect in `vercel.json`.

Never regenerate the Sparkle keypair — every shipped app pins the public key,
and a new pair permanently breaks updates for every existing install.
