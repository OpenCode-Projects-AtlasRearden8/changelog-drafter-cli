"""Read commits and tags out of a git repository using only the git CLI."""

import subprocess
from dataclasses import dataclass
from typing import List, Optional

# loose semver tags: 1.2, v1.2.3, 1.0.0-rc1, 0.0.0b0 ...
VERSION_TAG_PATTERN = r"^v?[0-9]+\.[0-9]+(\.[0-9]+)?([+-][0-9A-Za-z.-]+)?$"

RECORD_SEP = "\x1e"
FIELD_SEP = "\x1f"


class GitError(RuntimeError):
    pass


@dataclass
class CommitInfo:
    hash: str
    subject: str
    body: str


def run_git(repo: str, *args: str) -> str:
    cmd = ["git", "-C", repo] + list(args)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        raise GitError("git executable not found on PATH")
    if proc.returncode != 0:
        raise GitError(proc.stderr.strip() or f"git {args} failed")
    return proc.stdout


def commit_count(repo: str, ref: str = "HEAD") -> int:
    out = run_git(repo, "rev-list", "--count", ref)
    return int(out.strip())


def get_commits(
    repo: str,
    from_ref: Optional[str] = None,
    to_ref: str = "HEAD",
) -> List[CommitInfo]:
    """Return commits in from_ref..to_ref (or the full history of to_ref)."""
    if from_ref:
        run_git(repo, "rev-parse", "--verify", from_ref + "^{commit}")
        run_git(repo, "rev-parse", "--verify", to_ref + "^{commit}")
        range_spec = f"{from_ref}..{to_ref}"
    else:
        range_spec = to_ref
    fmt = FIELD_SEP.join(["%h", "%s", "%b"]) + RECORD_SEP
    out = run_git(repo, "log", f"--format={fmt}", range_spec, "--reverse")
    commits = []
    # records end with the separator, so splitting on it yields a trailing ""
    for record in [r for r in out.split(RECORD_SEP) if r.strip()]:
        hash_, subject, body = (record.split(FIELD_SEP, 2) + ["", ""])[:3]
        commits.append(
            CommitInfo(hash=hash_.strip(), subject=subject.strip(), body=body.strip("\n"))
        )
    return commits

def get_tags(repo: str) -> List[str]:
    out = run_git(repo, "tag")
    return sorted(t.strip() for t in out.splitlines() if t.strip())


def parse_version(tag: str):
    """Return a sortable tuple for a version-like tag, else None."""
    import re

    m = re.match(r"^v?[0-9]+(\.[0-9]+)*([+-][0-9A-Za-z.-]+)?$", tag)
    if not m:
        return None
    nums = re.findall(r"[0-9]+", tag.split("+")[0].split("-")[0])
    return tuple(int(n) for n in nums)


def last_release_tag(repo: str) -> Optional[str]:
    """Most recent version-like tag, sorted by version numbers."""
    tags = [t for t in get_tags(repo) if parse_version(t) is not None]
    if not tags:
        return None
    tags.sort(key=parse_version)
    return tags[-1]
