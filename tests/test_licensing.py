"""Contracts that keep the source-available licensing change coherent."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def one_line(text: str) -> str:
    """Normalize prose so Markdown wrapping does not weaken the contract."""
    return " ".join(text.split())


def test_root_license_is_personal_only_reciprocal_and_names_permission_path():
    license_text = one_line(read(ROOT / "LICENSE"))
    assert "# OpenVoiceFlow Personal and Reciprocal Source License 1.0" in license_text
    assert "## 4. Commercial and organizational use are not granted" in license_text
    assert "## 5. Attribution and source-sharing conditions" in license_text
    assert "### 5.1 Distribution" in license_text
    assert "### 5.2 Network use" in license_text
    assert "license the entire Covered Work" in license_text
    assert "complete Corresponding Source" in license_text
    assert "Only personal use as defined in this section is permitted" in license_text
    assert '"Organization" means' in license_text
    assert '"Integration" means any software' in license_text
    assert "If you create a Covered Work or Integration" in license_text
    assert '"Based on OpenVoiceFlow by Shimoverse Studios"' in license_text
    assert "https://github.com/shimoverse/openvoiceflow" in license_text
    assert "or the Integration is a Covered" in license_text
    assert (
        "Commercial or organizational rights require separate written permission or a "
        "separate written license from Shimoverse Studios."
    ) in license_text
    assert (
        "It does not apply to independent works that are not Covered Works, except that "
        "every Integration remains subject to the attribution requirements in Section 5."
    ) in license_text
    assert "shimoverse@gmail.com" in license_text


def test_permission_path_uses_exact_binding_text_on_primary_license_surfaces():
    binding = "separate written permission or a separate written license"
    for rel in [
        "LICENSE",
        "LICENSING.md",
        "README.md",
        "PRIVACY.md",
        "SECURITY.md",
        "SUPPORT.md",
        "TRADEMARKS.md",
        "CHANGELOG.md",
        "docs/COMPLIANCE.md",
        "docs/legal/DPA-template.md",
        "docs/llms.txt",
        "scripts/docs_content.py",
        "docs/docs/faq.html",
        "native/Info.plist",
    ]:
        assert binding in one_line(read(ROOT / rel)), rel


def test_dpa_template_does_not_imply_personal_license_authorizes_organizations():
    template = one_line(read(DOCS / "legal" / "DPA-template.md"))
    assert (
        "the public personal-use-only license does not authorize organizational use"
        in template
    )


def test_plain_language_licensing_guide_covers_boundaries():
    guide = one_line(read(ROOT / "LICENSING.md"))
    for phrase in [
        "not an open-source license",
        "Commercial or organizational use requires separate written permission or a separate written license",
        "Closed-source derivatives are not permitted",
        "Covered Work is distributed or offered over a network",
        "sole proprietorship",
        "paid product",
        "Earlier releases",
        "remain available under the MIT terms",
        "LEGACY_MIT_PORTIONS.md",
        "THIRD_PARTY_NOTICES.md",
        "TRADEMARKS.md",
        "even if it stays private",
        "independent Integration must still carry the required OpenVoiceFlow credit",
    ]:
        assert phrase in guide


def test_primary_policy_surfaces_name_personal_and_permission_paths():
    for rel in ["README.md", "PRIVACY.md", "SECURITY.md", "SUPPORT.md"]:
        text = one_line(read(ROOT / rel))
        assert "OpenVoiceFlow Personal and Reciprocal Source License 1.0" in text, rel
        assert "personal use only" in text.lower(), rel
        assert "commercial" in text.lower(), rel
        assert "organizational" in text.lower(), rel
        assert "shimoverse@gmail.com" in text, rel


def test_primary_surfaces_explain_reciprocal_source_requirement():
    surfaces = [
        ROOT / "README.md",
        ROOT / "PRIVACY.md",
        ROOT / "SECURITY.md",
        ROOT / "SUPPORT.md",
        ROOT / "CONTRIBUTING.md",
    ]
    for surface in surfaces:
        text = one_line(read(surface)).lower()
        assert "modified" in text, surface
        assert "source" in text, surface
        assert "same license" in text, surface


def test_compliance_copy_matches_native_analytics_posture():
    compliance = one_line(read(DOCS / "COMPLIANCE.md")).casefold()
    for stale_claim in [
        "no vendor-side service exists",
        "we hold no personal data on a server",
        "there is no central server",
        "we don't sync, mirror, back up, or telemeter",
        "we do not retain anything centrally",
    ]:
        assert stale_claim not in compliance
    assert "analytics/leaderboard api" in compliance
    assert "never receives audio or dictated text" in compliance
    assert "anonymous usage sharing is enabled" in compliance


def test_current_public_pages_do_not_claim_mit_or_open_source():
    current_pages = [
        DOCS / "index.html",
        DOCS / "mission.html",
        DOCS / "download.html",
        DOCS / "install.html",
        DOCS / "privacy.html",
        DOCS / "blog" / "index.html",
        DOCS / "docs" / "index.html",
        DOCS / "docs" / "faq.html",
        DOCS / "docs" / "privacy-architecture.html",
    ]
    forbidden = ["MIT-licensed", "MIT open source", "free for any use", "free for everyone"]
    for page in current_pages:
        text = read(page)
        for phrase in forbidden:
            assert phrase.lower() not in text.lower(), f"{page}: stale {phrase!r}"


def test_current_product_copy_uses_personal_use_only_scope():
    current_copy = [
        ROOT / "README.md",
        ROOT / "PRD.md",
        ROOT / "LICENSING.md",
        ROOT / "PRIVACY.md",
        ROOT / "SECURITY.md",
        ROOT / "SUPPORT.md",
        ROOT / "TRADEMARKS.md",
        ROOT / "pyproject.toml",
        DOCS / "COMPLIANCE.md",
        DOCS / "llms.txt",
        ROOT / "scripts" / "docs_content.py",
        ROOT / "voiceflow" / "__init__.py",
        ROOT / "voiceflow" / "__main__.py",
        ROOT / "voiceflow" / "onboarding.py",
        *(page for page in DOCS.glob("*.html") if page.name != "index.html"),
        *(DOCS / "blog").glob("*.html"),
        *(DOCS / "docs").glob("*.html"),
    ]
    forbidden_phrases = [
        "personal and noncommercial use",
        "personal and other noncommercial use",
        "personal/noncommercial",
        "free for noncommercial use",
        "qualifying noncommercial",
        "business use requires",
        "commercial use requires",
        "commercial license required",
    ]
    for surface in current_copy:
        text = read(surface).casefold()
        for phrase in forbidden_phrases:
            assert phrase not in text, f"{surface}: stale license phrase {phrase!r}"
        assert "free forever" not in text, f"{surface}: unqualified forever claim"
        assert re.search(r"\$0\s*[/,]?\s*forever", text) is None, (
            f"{surface}: unqualified forever-cost claim"
        )
        for match in re.finditer(r"personal use", text):
            nearby = text[max(0, match.start() - 24) : match.end() + 24]
            assert "only" in nearby, (
                f"{surface}: personal use appears without the required only boundary"
            )


def test_package_and_cli_metadata_qualify_free_use():
    pyproject = read(ROOT / "pyproject.toml")
    cli = read(ROOT / "voiceflow" / "__main__.py")

    assert "free for personal use only" in pyproject.lower()
    assert "free for personal use only" in cli.lower()
    assert 'description = "Free voice dictation' not in pyproject
    assert "— Free voice dictation" not in cli


def test_homepage_uses_free_forever_message_while_faq_preserves_license_boundaries():
    home = read(DOCS / "index.html")
    faq = read(DOCS / "docs" / "faq.html")
    assert "FREE FOREVER" in home
    assert "personal use only" not in home.casefold()
    assert "personal purposes only" not in home.casefold()
    assert "commercial or organizational use requires" not in home.casefold()
    assert "The project license sets the terms for reuse and redistribution" in home
    assert "OpenVoiceFlow Personal and Reciprocal Source License 1.0" in faq
    assert (
        "Workplace or other organizational use requires separate written permission or a separate written license"
        in faq
    )
    assert "Based on OpenVoiceFlow by Shimoverse Studios" in faq
    assert "https://github.com/shimoverse/openvoiceflow" in faq
    assert "even if it stays private" in faq
    assert "merely connects through a documented interface" in faq


def test_primary_attribution_surfaces_require_visible_credit_and_original_link():
    for rel in ["LICENSE", "LICENSING.md", "README.md", "TRADEMARKS.md"]:
        text = one_line(read(ROOT / rel))
        assert "Based on OpenVoiceFlow by Shimoverse Studios" in text, rel
        assert "https://github.com/shimoverse/openvoiceflow" in text, rel
