# STATUS.md — changelog-drafter-cli

## What was built

A small, dependency-free Python CLI that drafts an honest `CHANGELOG.md`
straight from git history:

- Reads commits between your last release tag (loose semver `v?X.Y.Z` tags,
  newest by version) and HEAD — or the entire history when no tags exist;
  `--from` / `--to` override the range.
- Groups commits into **Added / Changed / Fixed** using conventional-commit
  types (`feat`, `fix`, `chore`, ...) plus plain-English heuristics, then
  rewrites each subject as a human sentence (e.g. `fix(parser): crash on
  empty input` → `- Fixed crash on empty input (parser).`). Breaking changes
  (`!` or `BREAKING CHANGE`) are noted. Nothing is invented; unrecognized
  subjects are kept verbatim, just capitalized.
- `--raw` swaps the sentence view for hash + subject lines verbatim (raw
  commit messages only when you ask).
- Interactive review at a terminal: write as-is, edit in `$EDITOR`, or
  cancel. Without a tty you must pass `--yes` (write) or `--dry-run`
  (preview) so scripts never hang.
- Prepends the reviewed entry to `CHANGELOG.md`, creating the file (with a
  `# Changelog` title) if missing, always newest-first.
- Optional polish pass (`--polish`) through any OpenAI-compatible endpoint.
  Default: local Ollama `http://localhost:11434/v1`, model `qwen2.5`;
  configurable via flags or `changelog.toml` (`[polish] base_url/model/
  timeout`). No API key, token, or auth header is ever sent — a mock server
  test asserts this. Endpoint failures degrade gracefully to the local draft.
- Everything is local: no git push, no remote creation, no publishing, no
  secrets or personal data in any file.

## Layout

```
changelog_drafter/   git_ops, grouping, changelog, review, polish, config, cli
tests/               pytest suite with throwaway fixture git repos
LICENSE              MIT, Copyright (c) 2026 Asdale Dynamics, LLC
README.md            usage, options, credits
pyproject.toml       setuptools packaging + `changelog-drafter` entry point
```

## How to run it

```bash
pip install -e .            # or use --break-system-packages on PEP 668 distros
changelog-drafter --dry-run # preview
changelog-drafter           # preview + interactive review + write
changelog-drafter --yes     # non-interactive write
python3 -m changelog_drafter --dry-run   # no-install mode
```

## Verification results

- `pytest`: **31 passed** (grouping/sentence rules, tag detection, commit
  ranges, changelog rendering/prepend, CLI dry-run/write/raw/tag-range/no-new
  commits/missing-repo paths, polish mock-server incl. no-auth-header check,
  unreachable-endpoint fallback, config loader, review flow incl. `$EDITOR`
  and no-tty guard).
- Install: `pip install -e . --break-system-packages` builds and installs;
  `changelog-drafter` entry point and `python3 -m changelog_drafter` both work.
- End-to-end on a demo repo: draft, raw mode, `--from` override, breaking
  changes notice, polish fallback warning to stderr with untouched output,
  prepend into existing CHANGELOG.md, clean `error: ... not a git repository`
  (exit 2) outside a repo — all verified.

## Known gaps

- Sentence wording is deterministic heuristics, not NLP: odd inflections are
  possible (e.g. scope shown as a parenthetical). Editor review or `--raw`
  is the honest escape hatch.
- Tag detection sorts version-like tags numerically; non-semver release tags
  or date-ordered duplicates need `--from`.
- Merge/revert commits are included verbatim rather than collapsed.
- Polish requires a running local endpoint; there is no auth support by
  design (key-free). No polish could subtly reword counts if an endpoint
  misbehaves, which is why mismatches fall back to the local draft.
- Not packaged for pip mirrors; local install only.

Made by Asdale Dynamics, LLC as part of Dylan Asdale's beginner-friendly AI
toolkit.
