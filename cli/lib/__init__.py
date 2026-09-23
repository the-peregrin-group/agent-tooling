"""Forge-neutral shared library for the installable wrapper CLIs (ghw-*,
fjw-*, gitw-*; eventually the rebased triage-* wrappers).

Modules:
  schema       -- the single home for the shared ecosystem schema constants
  staging      -- staged-file path validation (staging directories only)
  plan         -- JSON-plan output and exit-code conventions
  arguments    -- leaf validators for the hand-rolled positional parsing

Subpackages:
  github       -- everything that talks to GitHub (the `gh` CLI substrate)
  forgejo      -- everything that talks to the configured Forgejo host (REST)
  git          -- everything that drives the git CLI for the gitw verbs
"""
