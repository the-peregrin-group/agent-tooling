"""Forgejo-specific library for the fjw-* wrappers.

Thin REST over the Python stdlib (urllib) -- no `tea`, no dependencies, raw
API objects end to end. All traffic goes to the single host named in
~/.config/fjw/config.toml; nothing here ever egresses anywhere else.

Modules:
  config -- the deployment-config file: API URL, machine-account token,
            git-over-SSH host/port (the hostname-reconciliation pair)
  api    -- HTTP layer: auth header, JSON codec, error classification into
            the shared exit-code taxonomy, swagger feature-probing
  pulls  -- PR operations: create/list/view/close/comment and the
            quad-state head-branch query
"""
