"""Assemble and prepend changelog entries. Local files only."""

from typing import Dict, List

NEW_FILE_HEADER = "# Changelog"


def render_entry(version_label: str, date: str, sections: Dict[str, List[str]]) -> str:
    """Render one `## Version - Date` entry with its section bullets."""
    lines = [f"## {version_label} - {date}", ""]
    for title, bullets in sections.items():
        if not bullets:
            continue
        lines.append(f"### {title}")
        lines.extend(f"- {b}" for b in bullets)
        lines.append("")
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def prepend_entry(existing: str, entry: str) -> str:
    """Insert a new entry at the top of a changelog's body, keeping its title."""
    existing = existing.rstrip("\n")
    if not existing.strip():
        return f"{NEW_FILE_HEADER}\n\n{entry}\n"
    lines = existing.split("\n")
    if lines[0].lstrip().startswith("#"):
        head, rest = lines[0], "\n".join(lines[1:]).lstrip("\n")
        return f"{head}\n\n{entry}\n\n{rest}\n" if rest else f"{head}\n\n{entry}\n"
    return f"{entry}\n\n{existing}\n"


def new_changelog(version_label: str, date: str, sections: Dict[str, List[str]]) -> str:
    """Full text for a fresh CHANGELOG.md."""
    return f"{NEW_FILE_HEADER}\n\n{render_entry(version_label, date, sections)}\n"
