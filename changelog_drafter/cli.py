"""Command-line entry point for changelog-drafter.

Draft an honest CHANGELOG.md straight from git history: commits since your
last release, grouped into Added/Changed/Fixed, reviewed before writing.
Everything stays local; nothing is ever pushed outside it.
"""

import argparse
import datetime
import os
import subprocess
import sys
from typing import List

from . import git_ops
from .changelog import prepend_entry, render_entry
from .config import load_config
from .grouping import GROUPS, draft_sections
from .polish import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    DEFAULT_TIMEOUT,
    polish_bullets,
)
from .review import run_review

PKG = "changelog_drafter"


def parse_args(argv: List[str] = None):
    parser = argparse.ArgumentParser(
        prog="changelog-drafter",
        description="Draft an honest CHANGELOG.md from git history (local only).",
    )
    parser.add_argument("--repo", default=".", help="Repository to read")
    parser.add_argument("--from", dest="from_ref", default=None,
                        help="Range start (default: last release tag)")
    parser.add_argument("--to", dest="to_ref", default="HEAD")
    parser.add_argument("--changelog-path", default="CHANGELOG.md")
    parser.add_argument("--raw", action="store_true",
                        help="Use raw hash + commit lines instead of sentences")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the draft and exit without writing")
    parser.add_argument("--yes", dest="assume_yes", action="store_true",
                        help="Skip the interactive review")
    parser.add_argument("--polish", action="store_true",
                        help="Optional polish pass via a local LLM endpoint")
    parser.add_argument("--base-url", default=None,
                        help="OpenAI-compatible base URL (default: Ollama local)")
    parser.add_argument("--model", default=None, help="Polish model name")
    parser.add_argument("--timeout", type=int, default=None,
                        help="Polish request timeout seconds")
    return parser.parse_args(argv)


def resolve_settings(args) -> dict:
    repo_root = os.path.abspath(args.repo)
    cfg = load_config(
        [
            os.path.join(repo_root, "changelog.toml"),
            os.path.join(os.getcwd(), "changelog.toml"),
        ]
    )
    return {
        "base_url": args.base_url or cfg.get("polish.base_url") or DEFAULT_BASE_URL,
        "model": args.model or cfg.get("polish.model") or DEFAULT_MODEL,
        "timeout": args.timeout
        or (int(cfg["polish.timeout"]) if cfg.get("polish.timeout") else DEFAULT_TIMEOUT),
    }


def maybe_polish(sections: dict, settings: dict) -> dict:
    """Apply the optional polish pass; on failure warn and keep local text."""
    polished = {}
    for title, bullets in sections.items():
        if title == "Raw commits" or not bullets:
            polished[title] = bullets
            continue
        result = polish_bullets(
            settings["base_url"], settings["model"], bullets, settings["timeout"]
        )
        if result is None:
            print(
                f"polish unavailable at {settings['base_url']} (model "
                f"{settings['model']}); keeping local draft",
                file=sys.stderr,
            )
            return sections
        polished[title] = result
    return polished


def draft_text(sections: dict, version_label: str, today: str) -> str:
    ordered = {g: sections.get(g, []) for g in GROUPS}
    for k in sections:
        if k not in ordered:
            ordered[k] = sections[k]
    return render_entry(version_label, today, ordered)


def main(argv: List[str] = None) -> int:
    args = parse_args(argv)
    settings = resolve_settings(args)
    repo = args.repo

    try:
        if not os.path.isdir(os.path.join(repo, ".git")):
            probe = subprocess.run(
                ["git", "-C", repo, "rev-parse", "--is-inside-work-tree"],
                capture_output=True, text=True,
            )
            if probe.returncode != 0:
                print(
                    f"error: {repo} is not a git repository "
                    "(or is a bare/unreadable one)",
                    file=sys.stderr,
                )
                return 2
        last_tag = git_ops.last_release_tag(repo)
        from_ref = args.from_ref or last_tag
        commits = git_ops.get_commits(repo, from_ref=from_ref, to_ref=args.to_ref)
    except git_ops.GitError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    version_label = (
        args.to_ref
        if args.to_ref and git_ops.parse_version(args.to_ref) is not None
        else "Unreleased"
    )

    sections = draft_sections(commits, raw_mode=args.raw)

    if args.polish:
        sections = maybe_polish(sections, settings)

    if not any(sections.values()):
        print("No commits found since your last release; nothing to add.")
        return 0

    today = datetime.date.today().isoformat()
    full_draft = draft_text(sections, version_label, today)

    if args.dry_run:
        print(full_draft)
        return 0

    reviewed = run_review(full_draft, assume_yes=args.assume_yes)

    path = os.path.abspath(args.changelog_path)
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as fh:
            text = prepend_entry(fh.read(), reviewed)
    else:
        text = f"# Changelog\n\n{reviewed.rstrip()}\n"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"Wrote entry to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
