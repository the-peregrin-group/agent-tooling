"""GitHub-specific library for the ghw-* wrappers.

Modules:
  gh           -- thin subprocess layer over the `gh` CLI (GraphQL/REST, die())
  boards       -- repo/label/board orientation, canonical-board resolution,
                  and board/item mutations
  labels       -- the label attachment contract
  label_schema -- ghw-label-sync's schema file and desired-state diff
  board_schema -- the canonical board schema: conformance and provisioning
  pulls        -- pure PR-merge gate checks
"""
