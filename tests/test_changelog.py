import subprocess
from pathlib import Path

from helpers import make_repo
from changelog_drafter.changelog import new_changelog, prepend_entry, render_entry

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_render_entry_skips_empty_sections():
    text = render_entry("1.0.0", "2026-10-27", {"Added": ["Added thing."], "Changed": [], "Fixed": ["Fixed bug."]})
    assert "### Changed" not in text
    assert "### Added\n- Added thing." in text
    assert "### Fixed\n- Fixed bug." in text
    assert text.startswith("## 1.0.0 - 2026-10-27")


def test_prepend_entry_keeps_title_on_top():
    existing = "# Changelog\n\n## 0.1.0 - 2026-10-20\n\n### Added\n- Added home page.\n"
    out = prepend_entry(existing, "## 0.2.0 - 2026-10-27\n\n### Fixed\n- Fixed logo.")
    assert out.startswith("# Changelog\n\n## 0.2.0")
    assert out.index("0.2.0") < out.index("0.1.0")
    assert out.rstrip().endswith("- Added home page.")


def test_prepend_entry_without_title():
    out = prepend_entry("", "## 1.0.0 - 2026-10-27\n\n### Added\n- Added x.")
    assert out == "# Changelog\n\n## 1.0.0 - 2026-10-27\n\n### Added\n- Added x.\n"


def test_new_changelog_shape():
    text = new_changelog("v1.0.0", "2026-10-27", {"Added": ["Added thing."]})
    assert text.startswith("# Changelog\n\n## v1.0.0 - 2026-10-27")


def run_cli(args, cwd):
    import os

    return subprocess.run(
        ["python3", "-m", "changelog_drafter"] + args,
        cwd=str(cwd), capture_output=True, text=True,
        env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)},
    )


def test_cli_dry_run_full_history(tmp_path: Path):
    make_repo(tmp_path, [("feat: add dark mode", "a.txt"), ("fix: boot crash", "b.txt")])
    proc = run_cli(["--repo", ".", "--dry-run"], tmp_path)
    assert proc.returncode == 0
    assert "### Added" in proc.stdout
    assert "- Added dark mode." in proc.stdout
    assert "- Fixed boot crash." in proc.stdout
    assert "## Unreleased - " in proc.stdout


def test_cli_writes_and_prepends(tmp_path: Path):
    make_repo(
        tmp_path,
        [("feat: add dark mode", "a.txt"), ("feat: add tag", "b.txt")],
        tags=["v0.1.0", None],
    )
    proc = run_cli(["--repo", ".", "--yes"], tmp_path)
    assert proc.returncode == 0, proc.stderr
    text = (tmp_path / "CHANGELOG.md").read_text()
    assert "# Changelog" in text
    assert "## Unreleased - " in text
    assert "- Added tag." in text


def test_cli_respects_last_release_tag_range(tmp_path: Path):
    make_repo(
        tmp_path,
        [("feat: first", "a.txt"), ("feat: second", "b.txt"), ("feat: only this last one", "c.txt")],
        tags=["v1.0.0", "v1.1.0", None],
    )
    proc = run_cli(["--repo", ".", "--yes"], tmp_path)
    text = (tmp_path / "CHANGELOG.md").read_text()
    assert "Added only this last one." in text
    assert "Added first." not in text


def test_cli_raw_mode(tmp_path: Path):
    make_repo(tmp_path, [("feat: add dark mode", "a.txt"), ("fix: boot crash", "b.txt")])
    proc = run_cli(["--repo", ".", "--dry-run", "--raw"], tmp_path)
    assert proc.returncode == 0, proc.stderr
    assert "### Raw commits" in proc.stdout
    assert any("feat: add dark mode" in l for l in proc.stdout.splitlines())
    assert "- Added dark mode." not in proc.stdout


def test_cli_existing_changelog_gets_entry_on_top(tmp_path: Path):
    make_repo(
        tmp_path,
        [("feat: initial", "a.txt"), ("feat: add dark mode", "b.txt")],
        tags=["v1.0.0", None],
    )
    (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n## 0.9.0 - 2026-09-01\n\n### Added\n- Added search.\n"
    )
    proc = run_cli(["--repo", ".", "--yes"], tmp_path)
    text = (tmp_path / "CHANGELOG.md").read_text()
    assert text.index("Unreleased") < text.index("0.9.0")
    assert "- Added dark mode." in text


def test_cli_no_new_commits_means_no_write(tmp_path: Path):
    make_repo(tmp_path, [("feat: only one", "a.txt")], tags=["v1.0.0"])
    proc = run_cli(["--repo", ".", "--yes"], tmp_path)
    assert proc.returncode == 0
    assert "No commits found" in (proc.stdout + proc.stderr)
    assert not (tmp_path / "CHANGELOG.md").exists()


def test_cli_missing_repo_fails_cleanly(tmp_path: Path):
    proc = run_cli(["--repo", str(tmp_path / "nope"), "--yes"], tmp_path)
    assert proc.returncode == 2
    assert "error:" in proc.stderr
