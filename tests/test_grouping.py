from changelog_drafter.grouping import classify, draft_sections, word_sentence
from changelog_drafter.git_ops import CommitInfo


def test_conventional_types_map_to_sections():
    assert classify("feat: add export button") == "Added"
    assert classify("fix(parser): crash") == "Fixed"
    assert classify("chore: bump deps") == "Changed"
    assert classify("refactor: tidy code") == "Changed"


def test_plain_english_heuristics():
    assert classify("add export button") == "Added"
    assert classify("new support page") == "Added"
    assert classify("fix crash on empty input") == "Fixed"
    assert classify("update readme") == "Changed"


def test_word_sentence_from_conventional_commit():
    assert (
        word_sentence("fix(parser): crash on empty input")
        == "Fixed crash on empty input (parser)."
    )


def test_word_sentence_strips_redundant_verb():
    assert word_sentence("feat: add export button") == "Added export button."
    assert word_sentence("add export button") == "Added export button."
    assert word_sentence("fix crash when input empty") == "Fixed crash when input empty."


def test_word_sentence_keeps_unrecognized_subject_honest():
    assert word_sentence("Prepare release 0.2.0") == "Prepare release 0.2.0."


def test_breaking_flag_surfaced():
    assert (
        word_sentence("feat!: rework config file", breaking=True)
        .endswith("Includes breaking changes.")
    )


def test_draft_sections_groups_each_bucket():
    commits = [
        CommitInfo("a1b2c3d", "feat: add dark mode", ""),
        CommitInfo("b2c3d4e", "fix crash at startup", ""),
        CommitInfo("c3d4e5f", "update the manual", ""),
    ]
    sections = draft_sections(commits)
    assert sections["Added"] == ["Added dark mode."]
    assert sections["Fixed"] == ["Fixed crash at startup."]
    assert sections["Changed"] == ["Changed the manual."]


def test_draft_sections_raw_mode():
    commits = [CommitInfo("a1b2c3d", "feat: add dark mode", "body text")]
    sections = draft_sections(commits, raw_mode=True)
    assert sections == {"Raw commits": ["a1b2c3d feat: add dark mode"]}
