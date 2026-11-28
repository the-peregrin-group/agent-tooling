"""GitHub-specific library for the ghw-* wrappers.

Modules:
  gh           -- thin subprocess layer over the `gh` CLI (GraphQL/REST, die())
  boards       -- repo/label/board orientation, canonical-board resolution,
                  and board/item mutations
  repo_schema  -- the repo's Tracker Schema, read from TRACKER.md on its
                  default branch, with its warnings
  labels       -- the label attachment contract
  label_schema -- ghw-label-sync's desired labels, from the Tracker Schema,
                  and their diff against the live ones
  board_schema -- the canonical board schema: conformance and provisioning
  pulls        -- pure PR-merge gate checks
"""
