"""Group commits into Added / Changed / Fixed and word them as plain sentences.

Rules of the road (honesty first):
- group from the actual message, nothing invented;
- plain sentences built from the subject only; bodies never hidden in – beyond
  their normal `--raw` mode – unless asked for;
- breaking changes tagged when the message declares them.
"""

import re
from typing import Dict, List

from .git_ops import CommitInfo

GROUPS = ["Added", "Changed", "Fixed"]

CONVENTIONAL = re.compile(
    r"^(feat|fix|perf|refactor|docs|chore|test|build|ci|style|revert|improv)"
    r"(?:\(([^)]*)\))?(!?):\s*(.*)$",
    re.IGNORECASE,
)

ADDED_STEMS = {
    "add", "adds", "added", "adding", "new", "introduce", "introduces",
    "introduced", "support", "supports", "supported", "implement",
    "implements", "implemented", "create", "creates", "created",
    "enable", "enables", "enabled", "initial", "init",
}
FIXED_STEMS = {
    "fix", "fixes", "fixed", "fixing", "bugfix", "repair", "repaired",
    "correct", "corrected", "resolve", "resolved", "resolves", "issue",
    "prevent", "prevented", "avoid", "regression",
}
CHANGED_STEMS = {
    "change", "changes", "changed", "update", "updates", "updated",
    "improve", "improves", "improved", "refactor", "refactored",
    "refactors", "clean", "cleanup", "tidy", "tweak", "tweaked",
    "bump", "bumped", "rename", "renamed", "move", "moved", "remove",
    "removed", "drop", "dropped", "replace", "replaced", "switch",
    "switched", "migrate", "rework", "perf", "speed", "deps",
}

GROUP_STEMS = {
    "Added": ADDED_STEMS,
    "Fixed": FIXED_STEMS,
    "Changed": CHANGED_STEMS,
}


def classify(subject: str) -> str:
    """Which section does this subject belong to? (Added / Changed / Fixed)"""
    m = CONVENTIONAL.match(subject)
    if m:
        kind = m.group(1).lower()
        if kind == "feat":
            return "Added"
        if kind == "fix":
            return "Fixed"
        return "Changed"
    first = subject.split(None, 1)[0].lower().strip(",.:;") if subject else ""
    if first in GROUP_STEMS["Added"]:
        return "Added"
    if first in GROUP_STEMS["Fixed"]:
        return "Fixed"
    return "Changed"


def _strip_leading_verb(text: str, group: str, stems) -> str:
    """Drop a redundant leading verb ("add ...") under the same group heading.

    Returns "" when nothing was stripped (caller keeps whole text).
    """
    words = text.split(None, 1)
    if not words:
        return ""
    first = words[0].lower()
    if first in stems and len(words) > 1:
        return words[1].strip()
    if first in {"added", "changed", "fixed"} and len(words) > 1:
        return words[1].strip()
    return ""


def word_sentence(subject: str, breaking: bool = False) -> str:
    """One-line human sentence for a commit subject, e.g.
    "fix(parser): crash on empty input" -> "Fixed parser crash on empty input."
    """
    m = CONVENTIONAL.match(subject)
    scope = ""
    if m:
        kind, scope, m_breaking, text = (
            m.group(1).lower(),
            m.group(2) or "",
            bool(m.group(3)),
            m.group(4).strip(),
        )
        breaking = breaking or m_breaking
        if kind == "feat":
            group = "Added"
        elif kind == "fix":
            group = "Fixed"
        else:
            group = "Changed"
        stripped = _strip_leading_verb(text, group, GROUP_STEMS[group])
        if stripped:
            text = stripped
            prefix = group
        else:
            prefix = group
    else:
        group = classify(subject)
        words = subject.split(None, 1)
        first = words[0].lower().strip(",.:;") if words else ""
        if first in GROUP_STEMS.get(group, set()) and len(words) > 1:
            text = words[1].strip()
            prefix = group
        elif first in {"added", "changed", "fixed"} and len(words) > 1:
            text = words[1].strip()
            prefix = ""
        else:
            text = subject.strip()
            prefix = ""  # heading carries the grouping; bullet stays honest

    # already starts with the group word from the raw subject, dedupe
    words2 = text.split(None, 1)
    if words2 and words2[0].lower().strip(",.:;") in {"added", "changed", "fixed"}:
        text = words2[1].strip()

    text = text.strip().rstrip(".").strip()
    if not text:
        return f"{group}"
    sentence = (prefix + " " if prefix else "") + text
    sentence = sentence[0].upper() + sentence[1:] if sentence else sentence
    if scope:
        sentence += f" ({scope})"
    sentence += "."
    if breaking:
        sentence += " Includes breaking changes."
    return re.sub(r"\s+", " ", sentence).strip()


def draft_sections(commits: List[CommitInfo], raw_mode: bool = False) -> Dict[str, List[str]]:
    """Group commits into section bullets; raw mode uses hash + subject verbatim."""
    if raw_mode:
        return {"Raw commits": [f"{c.hash} {c.subject}" for c in commits]}
    sections: Dict[str, List[str]] = {g: [] for g in GROUPS}
    for c in commits:
        if not c.subject:
            continue
        break_now = "BREAKING CHANGE" in c.body or re.search(r"^BREAKING\s+CHANGE", c.body, re.MULTILINE)
        group = classify(c.subject)
        sections[group].append(word_sentence(c.subject, breaking=break_now))
    return sections
