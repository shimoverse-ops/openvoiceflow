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


def test_root_license_is_personal_reciprocal_and_names_commercial_path():
    license_text = read(ROOT / "LICENSE")
    assert "# OpenVoiceFlow Personal and Reciprocal Source License 1.0" in license_text
    assert "## 4. Commercial use is not granted" in license_text
    assert "## 5. Source-sharing conditions" in license_text
    assert "### 5.1 Distribution" in license_text
    assert "### 5.2 Network use" in license_text
    assert "license the entire Covered Work" in license_text
    assert "complete Corresponding Source" in license_text
    assert "shimoverse@gmail.com" in license_text


def test_plain_language_licensing_guide_covers_boundaries():
    guide = one_line(read(ROOT / "LICENSING.md"))
    for phrase in [
        "not an open-source license",
        "Commercial use requires a separate license",
        "Closed-source derivatives are not permitted",
        "modified version over a network",
        "sole proprietorship",
        "paid product",
        "Earlier releases",
        "remain available under the MIT terms",
        "LEGACY_MIT_PORTIONS.md",
        "THIRD_PARTY_NOTICES.md",
        "TRADEMARKS.md",
    ]:
        assert phrase in guide


def test_primary_policy_surfaces_name_noncommercial_and_commercial_paths():
    for rel in ["README.md", "PRIVACY.md", "SECURITY.md", "SUPPORT.md"]:
        text = one_line(read(ROOT / rel))
        assert "OpenVoiceFlow Personal and Reciprocal Source License 1.0" in text, rel
        assert "commercial" in text.lower(), rel
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


def test_current_product_copy_uses_qualifying_noncommercial_scope():
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
        *DOCS.glob("*.html"),
        *(DOCS / "blog").glob("*.html"),
        *(DOCS / "docs").glob("*.html"),
    ]
    broad_phrases = [
        "personal and noncommercial use",
        "personal and other noncommercial use",
        "personal/noncommercial",
        "free for noncommercial use",
    ]
    for surface in current_copy:
        text = read(surface).casefold()
        for phrase in broad_phrases:
            assert phrase not in text, f"{surface}: broad license phrase {phrase!r}"
        assert "free forever" not in text, f"{surface}: unqualified forever claim"
        assert re.search(r"\$0\s*[/,]?\s*forever", text) is None, (
            f"{surface}: unqualified forever-cost claim"
        )


def test_package_and_cli_metadata_qualify_free_use():
    pyproject = read(ROOT / "pyproject.toml")
    cli = read(ROOT / "voiceflow" / "__main__.py")

    assert "free for personal and qualifying noncommercial use" in pyproject.lower()
    assert "free for personal and qualifying noncommercial use" in cli.lower()
    assert 'description = "Free voice dictation' not in pyproject
    assert "— Free voice dictation" not in cli


def test_homepage_and_faq_state_the_commercial_boundary():
    home = read(DOCS / "index.html")
    faq = read(DOCS / "docs" / "faq.html")
    assert "FREE FOR PERSONAL USE" in home
    assert "commercial use require a separate license" in home
    assert "OpenVoiceFlow Personal and Reciprocal Source License 1.0" in faq
    assert "Workplace or other business use requires a commercial license" in faq
