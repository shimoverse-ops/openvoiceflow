"""Prevent repo moves from leaving broken links in public Markdown documentation."""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINK_TARGET = re.compile(r"\]\(([^)]+)\)")
FENCE_START = re.compile(r"^[ ]{0,3}(`{3,}|~{3,})")
URI_SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*:", re.IGNORECASE)
SKIPPED_DIRECTORIES = {".git", ".venv", "node_modules"}


def tracked_markdown_files():
    """Return Markdown paths that Git includes in the repository."""
    output = subprocess.run(
        ["git", "ls-files", "--", "*.md"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [
        ROOT / path
        for path in output.splitlines()
        if not SKIPPED_DIRECTORIES.intersection(Path(path).parts)
    ]


def markdown_targets(contents):
    """Yield link destinations from inline Markdown links."""
    fence = None
    for line in contents.splitlines():
        stripped = line.lstrip()
        if fence is not None:
            marker, minimum_length = fence
            candidate = stripped.rstrip()
            if candidate and set(candidate) == {marker} and len(candidate) >= minimum_length:
                fence = None
            continue

        fence_start = FENCE_START.match(line)
        if fence_start:
            opening = fence_start.group(1)
            fence = (opening[0], len(opening))
            continue

        for match in LINK_TARGET.finditer(line):
            target = match.group(1).strip()
            if target.startswith("<") and ">" in target:
                target = target[1 : target.index(">")]
            else:
                target = target.split(maxsplit=1)[0]
            yield target


def test_all_relative_markdown_links_resolve():
    broken = []

    for markdown_file in tracked_markdown_files():
        contents = markdown_file.read_text(encoding="utf-8")
        for target in markdown_targets(contents):
            if target.startswith(("#", "//")) or URI_SCHEME.match(target):
                continue

            path_without_fragment = target.split("#", 1)[0]
            resolved = (markdown_file.parent / path_without_fragment).resolve()
            source = markdown_file.relative_to(ROOT)
            try:
                repo_path = resolved.relative_to(ROOT)
            except ValueError:
                broken.append(
                    f"{source}: relative Markdown target {target!r} points outside the repository; "
                    "update it to a repo-root-relative destination"
                )
                continue

            if not resolved.exists():
                broken.append(
                    f"{source}: relative Markdown target {target!r} resolves to missing path {repo_path}; "
                    "update the link or restore the target"
                )

    assert not broken, "Broken relative Markdown links:\n- " + "\n- ".join(broken)
