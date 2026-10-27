import subprocess
from pathlib import Path

import pytest

from helpers import init_repo, make_repo
from changelog_drafter import git_ops


def test_no_tags_returns_none(tmp_path: Path):
    make_repo(tmp_path, [("feat: start", "a.txt")])
    assert git_ops.last_release_tag(str(tmp_path)) is None


def test_last_release_tag_picks_highest_version(tmp_path: Path):
    make_repo(tmp_path, [("one", "a.txt"), ("two", "b.txt")], tags=["v1.2.0", "1.10.0"])
    assert git_ops.last_release_tag(str(tmp_path)) == "1.10.0"


def test_get_commits_full_history_when_no_range(tmp_path: Path):
    make_repo(
        tmp_path,
        [
            ("feat: first feature", "one.txt"),
            ("fix: an early fix", "two.txt"),
            ("docs: update readme", "three.txt"),
        ],
    )
    commits = git_ops.get_commits(str(tmp_path))
    subjects = [c.subject for c in commits]
    assert subjects == ["feat: first feature", "fix: an early fix", "docs: update readme"]


def test_get_commits_range_since_tag(tmp_path: Path):
    repo = make_repo(
        tmp_path,
        [
            ("feat: one", "one.txt"),
            ("feat: two", "two.txt"),
            ("feat: three", "three.txt"),
        ],
        tags=["v1.0.0", None, None],
    )
    commits = git_ops.get_commits(str(repo), from_ref="v1.0.0")
    subjects = [c.subject for c in commits]
    assert subjects == ["feat: two", "feat: three"]


def test_unknown_ref_raises(tmp_path: Path):
    make_repo(tmp_path, [("one", "a.txt")])
    with pytest.raises(git_ops.GitError):
        git_ops.get_commits(str(tmp_path), from_ref="v9.9.9")


def test_commit_body_captured(tmp_path: Path):
    repo = init_repo(tmp_path)
    subprocess.run(
        ["git", "commit", "-q", "--allow-empty", "-m", "feat: thing", "-m", "BREAKING CHANGE: API changed"],
        cwd=str(repo), check=True, capture_output=True,
    )
    (commits,) = git_ops.get_commits(str(repo))
    assert "BREAKING CHANGE" in commits.body
