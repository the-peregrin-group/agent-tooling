"""Git-specific library for the gitw-* wrappers.

Thin subprocess layer over the git CLI -- stdlib-only, non-interactive by
construction (no editor, no pager, no credential or ssh prompt can ever
block a wrapper). Repo identity is explicit: every verb resolves a leading
repo label against the machine-local roster (~/.config/gitw/repos.toml) and
trust-but-verifies the working copy at cwd against the registered checkout
before touching anything.

Modules:
  arguments -- leaf validators for the gitw positional grammar (repo
               labels, branch prefixes, branch names)
  policy    -- the local-only file patterns mutating verbs refuse to
               sweep into history (settings.local.json, .env*)
  roster    -- the roster file: label -> {remote URL, primary checkout,
               authoritative remote/default branch, operable_from paths}
  run       -- subprocess substrate: non-interactive environment, remote
               failure classification into the shared exit-code taxonomy
  repo      -- working-copy verification (cwd vs. roster entry) and the
               read primitives verbs share (branch/dirty state,
               ahead/behind, worktree occupancy)
"""
