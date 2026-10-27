"""Interactive terminal review of the draft, plus $EDITOR editing."""

import os
import subprocess
import sys
import tempfile


def edit_in_editor(text: str) -> str:
    """Let the user edit the draft in their favorite editor.

    Falls back quietly to the original text if anything goes wrong.
    """
    editor = os.environ.get("VISUAL") or os.environ.get("EDITOR") or ""
    if not editor:
        for cand in ("vi", "vim", "nano", "notepad"):
            from shutil import which
            if which(cand):
                editor = cand
                break
    try:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".md", delete=False, encoding="utf-8"
        ) as fh:
            fh.write(text)
            path = fh.name
        rc = subprocess.call([editor or "vi", path])
        if rc != 0:
            print(f"(editor exited with {rc}; keeping original draft)", file=sys.stderr)
            return text
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError as exc:
        print(f"(could not open editor: {exc}; keeping original draft)", file=sys.stderr)
        return text


def run_review(draft: str, assume_yes: bool = False, write: bool = True) -> str:
    """Show the draft and return the (possibly edited) text to write.

    Non-interactive calls must pass assume_yes=True; without a tty and without
    assume_yes an error is raised so scripts never hang on a prompt.
    """
    if assume_yes or not sys.stdin.isatty():
        if not assume_yes and not write:
            return draft
        if not assume_yes:
            raise SystemExit(
                "No interactive terminal detected; re-run with --yes to write "
                "without review, or --dry-run to preview only."
            )
        return draft
    print("--- draft ---")
    print(draft)
    print("-------------")
    while True:
        answer = input(
            "Write as-is [w], edit in $EDITOR [e], cancel [q] (default w): "
        ).strip().lower()
        if answer in ("", "w", "y"):
            return draft
        if answer in ("e", "edit"):
            edited = edit_in_editor(draft)
            print("--- final to write ---")
            print(edited)
            confirm = input("Save this [Enter/yes] or cancel [n]: ").strip().lower()
            if confirm in ("", "y", "yes"):
                return edited
            continue
        if answer in ("q", "n", "cancel"):
            print("Cancelled; nothing written.")
            raise SystemExit(1)
        print("Please answer w, e, or q.")
