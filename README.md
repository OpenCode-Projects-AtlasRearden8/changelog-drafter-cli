# changelog-drafter-cli

Draft an honest `CHANGELOG.md` straight from your git history.

`changelog-drafter` reads the commits and tags since your last release, groups
them into **Added / Changed / Fixed** in plain human sentences, lets you review
and edit the draft before anything is written, and prepends it to your
changelog. It never invents anything, never pushes anywhere, and only shows raw
commit messages if you ask. An optional polish pass can tidy the sentences
through any OpenAI-compatible endpoint — by default a local Ollama server —
with a configurable `base_url` and model, and **never** sends an API key.

Built for beginners and busy people: one command, plain English, everything
local.

## What it does

1. Finds your last release tag (loose semver tags like `v1.2.0` or `1.2.0`),
   or uses your entire history if there are none. Override with `--from TAG`.
2. Reads every commit between there and `--to` (default `HEAD`).
3. Groups commits by classic conventional-commit types (`feat`, `fix`, ...)
   plus plain-English heuristics ("add X", "fix crash", "bump deps").
4. Rewrites each commit subject as a one-line human sentence, e.g.
   `fix(parser): crash on empty input` → `- Fixed parser crash on empty input.`
5. If a terminal is attached, shows the draft and offers to write it as-is,
   edit it in your `$EDITOR`, or abort. Use `--yes` to skip review (scripts).
6. Prepends the finished entry to `CHANGELOG.md` (creating it if missing).

Everything happens in your local repo. Nothing is ever pushed, uploaded, or
sent anywhere unless you explicitly turn on the polish pass.

## Quick start

```bash
# from inside any git repository
python -m changelog_drafter --dry-run      # just preview the draft
python -m changelog_drafter                # preview + interactive review + write
changelog-drafter --yes                    # non-interactive (CI-friendly)
```

If you cloned this folder without installing, run the module from the folder
that contains `changelog_drafter/`:

```bash
python3 -m changelog_drafter --dry-run
```

## Options

| Flag | Meaning |
| --- | --- |
| `--repo PATH` | Repository to read (default: current directory) |
| `--from REF` | Start point (default: last release tag, else first commit) |
| `--to REF` | End point (default: `HEAD`) |
| `--changelog-path PATH` | Changelog file (default: `CHANGELOG.md`) |
| `--raw` | Draft uses the raw commit lines (hash + subject) verbatim |
| `--dry-run` | Print the draft and exit without touching files |
| `--yes` | Skip the interactive review; write as-is |
| `--polish` | Send the humanized bullets to a local LLM for a polish pass |
| `--base-url URL` | Polish endpoint (default `http://localhost:11434/v1`, Ollama) |
| `--model NAME` | Polish model (default configured in `changelog.toml`) |
| `--timeout SECONDS` | Polish request timeout (default 30) |

Options without a key: the polish endpoint is a plain OpenAI-compatible
`/chat/completions` call with **no auth header at all** — no key, no token,
nothing. If the endpoint is unreachable, the tool prints a one-line warning and
keeps the locally generated draft. The default points at Ollama's local server
(`http://localhost:11434/v1`); point `--base-url` anywhere OpenAI-compatible
you like (LM Studio, llama.cpp server, vLLM, ...).

## Config file (optional)

Drop a `changelog.toml` next to your repo root (or in the current directory) to
skip flags:

```toml
[polish]
base_url = "http://localhost:11434/v1"  # any OpenAI-compatible endpoint
model = "qwen2.5"
timeout = 30
```

`base_url`/`model`/`timeout` may be overridden by the flags above. The request
never includes credentials — the model field is just a model name.

## Honest outcomes

- Commits are grouped from their actual messages; nothing is inferred that
  isn't there.
- Sentence-style entries are generated only from subjects; bodies and full raw
  messages are shown only with `--raw`.
- If the changelog is missing, one is created with a simple `# Changelog`
  title; otherwise the new entry is inserted right after the existing title so
  newest is always on top.
- Date tags on entries reflect today's date, and the version label comes from
  the `--to` tag (or `Unreleased` when there isn't one).

## Example entry

```markdown
## 0.2.0 - 2026-10-27

### Added
- Added export button to parser sidebar.
- Added support for UTF-8 input files.

### Changed
- Changed internal logging to use structured JSON.

### Fixed
- Fixed crash when input file is empty.
```

## Tested

The test suite (`pytest`) builds throwaway fixture git repos in temp folders and
covers tag detection, commit range selection, grouping and sentence rewriting,
both draft formats, changelog prepending (fresh and existing), non-interactive
mode, and the polish fallback behavior.

```bash
pip install -e . && pytest
```

## Distinct from beta-feedback-collector-cli

This tool drafts release notes from git history. If instead you're gathering
user feedback from a beta build, that's a separate project. They share no code.

## Credits

Made with plain English for plain humans by **Asdale Dynamics, LLC** — part of
Dylan Asdale's beginner-friendly AI toolkit (dylanasdale.github.io).
MIT licensed; see `LICENSE`.
