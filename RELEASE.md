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
5. **Verify live**: the site serves the new appcast build number and the DMG
   sha256 matches the notarized artifact byte-for-byte.
6. Add a CHANGELOG entry; prune the previous version's DMG from
   `docs/downloads/` and add its redirect in `vercel.json`. Then regenerate
   `docs/releases.html` with `python3 scripts/build_releases.py` — it renders
   straight from CHANGELOG.md, so this is the only way the public Releases
   page picks up the new entry.

Never regenerate the Sparkle keypair — every shipped app pins the public key,
and a new pair permanently breaks updates for every existing install.
