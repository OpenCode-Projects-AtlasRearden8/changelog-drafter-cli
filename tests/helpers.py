"""Shared fixture helpers: build throwaway git repos for tests."""

import subprocess
from pathlib import Path


def run(cmd, cwd, check=True, input_=None):
    proc = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, input=input_
    )
    if check and proc.returncode != 0:
        raise AssertionError(
            f"command failed: {cmd}\n{proc.stderr}"
        )
    return proc.stdout


def init_repo(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    run(["git", "init", "-q", "-b", "main"], str(path))
    run(["git", "config", "user.name", "Fixture Tester"], str(path))
    run(["git", "config", "user.email", "fixture@example.invalid"], str(path))
    return path


def commit(path: Path, message: str, filename: str = None, tag: str = None):
    """Commit (optionally a new file and tag) and return the short hash."""
    if filename:
        (path / filename).write_text(message + "\n")
        run(["git", "add", filename], str(path))
    run(["git", "commit", "-q", "--allow-empty", "-m", message], str(path))
    if tag:
        run(["git", "tag", tag], str(path))
    return run(["git", "rev-parse", "--short=7", "HEAD"], str(path)).strip()


def make_repo(tmp_path: Path, commits, tags=None):
    """commits: list of (message, filename|None); tags appended in order."""
    repo = init_repo(tmp_path)
    for i, (msg, fname) in enumerate(commits):
        commit(repo, msg, filename=fname, tag=tags[i] if tags and i < len(tags) else None)
    return repo
