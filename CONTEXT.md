# Context: agent-tooling vocabulary

The terms this repo's code, skills, and ADRs use, one or two lines each.

## Wrappers

- **Wrapper**: a small executable in `cli/` that performs one kind of git, GitHub,
  or Forgejo operation under enforced policy. Agents call wrappers instead of raw
  `git` or `gh` so that permission rules can grant them by literal prefix.
- **Verb**: one wrapper, named `<family>-<verb>`: `gitw-*` (git), `ghw-*`
  (GitHub), `fjw-*` (Forgejo). Agents invoke a verb by bare name on PATH, never by
  path or through `python3`.
- **Roster**: the machine-local file `~/.config/gitw/repos.toml` that pins, per
  repo, the one blessed checkout, its authoritative remote, and its default branch.
- **Roster label**: a repo's short name in the roster, and the first argument of
  every `gitw-*` verb. Repo identity comes from the label, never from the path or
  the cwd.
- **Branch prefix**: the `fix/`-style token (lowercase, one level, trailing slash)
  that scopes a mutating verb. It is also the token that allowlist rules pin.
- **Exit-code contract**: 0 success, 1 unclassified failure, 2 usage, 3 not found,
  4 refused by policy, 5 roster or auth failure, 6 network. Callers branch on it.

## Installing

- **Source repo**: a checkout with an `install.json` at its root, named by that
  file's `source_repo` field. This repo is one; others can ship into the same
  targets.
- **Cohort**: one named section of `install.json`: a set of source directories
  that installs into one target, with its own excludes. Here: `bin`, `skills`,
  `agents`.
- **Target**: the directory a cohort installs into, fixed by the cohort's kind
  (`~/.local/libexec/agent-tooling/`, `~/.claude/skills/`, `~/.claude/agents/`).
- **Unit**: one skill directory. Skills install and swap a whole unit at a time;
  `bin` and `agents` install file by file.
- **Receipt**: `install-receipt.json` in each target, recording per source repo
  the commit installed and a sha256 for every file or unit it owns.
- **Foreign / unowned**: a file in a target that another source repo's receipt
  claims is foreign. A file no receipt claims is unowned. Installs preserve both
  and report them.
- **diff / apply / adopt**: the installer's three commands. `diff` compares
  installed against source and changes nothing. `apply` installs, refusing to
  overwrite foreign content. `adopt` installs and takes over the files one named
  source repo owned.

## Claude Code

- **Skill**: a directory with a `SKILL.md` that Claude Code loads on demand; the
  instructions an agent follows for one kind of task.
- **Agent**: a subagent definition in `agents/`, a Markdown file with frontmatter
  that Claude Code can spawn for a delegated task.
