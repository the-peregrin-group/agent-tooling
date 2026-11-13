# agent-tooling

Shared tooling for Claude Code agents:

- **A wrapper CLI** (`cli/`): the `gitw-*` verbs for git, `ghw-*` for GitHub, and
  `fjw-*` for Forgejo. Every mutating operation an agent performs goes through a
  wrapper, so permission rules can grant narrow, literal command prefixes instead
  of raw `git` or `gh`. `gitw-commit` appends an `Executed-By:` trailer naming
  the session actor to every commit.
- **The Beads wrapper** (`cli/bdw`): runs the real `bd` as a child process
  with `BD_ACTOR` and `BEADS_ACTOR` set to the session actor, refusing the
  calls that would falsify the actor or point bd at another database, and
  writes on bd versions it has not been verified against. See
  [bdw](docs/projects/bdw/index.md).
- **Ten skills** (`skills/`): `use-git`, `use-github`, `use-forgejo`,
  `setup-github-issues`, `triage-issues`, `refine-state-doc`, `use-lexicon`,
  `use-adrs`, `home-in`, `handoff`.
- **One agent** (`agents/`): `code-reviewer`.
- **The installer** (`cli/tooling-install`), which ships all of the above.

## The install model

Nothing runs from a checkout. The checkout is source; `tooling-install` copies it
into fixed Install Targets, and agents only ever use the installed copies:

| Cohort | Source | Installed to |
|---|---|---|
| `bin` | `cli/` | `~/.local/libexec/agent-tooling/` |
| `skills` | `skills/` | `~/.claude/skills/` |
| `agents` | `agents/` | `~/.claude/agents/` |

`install.json` at the repo root declares the Cohorts and what each excludes
(tests, bytecode, OS droppings). Each Install Target gets an
`install-receipt.json` recording which Source repo installed which file, from
which commit, with a sha256 per file. Several Source repos can install into
the same Install Target; each one's Receipt record covers only its own files.

```sh
/usr/bin/python3 cli/tooling-install diff  <checkout>   # read-only: installed vs. source
/usr/bin/python3 cli/tooling-install apply <checkout>   # install; refuses a dirty source
```

`diff` reports each Cohort's status (`in-sync`, `drift`, or `not-installed`)
in its JSON. `apply` refuses a dirty source tree
unless given `--force`, and it never overwrites a file another Source repo's
Receipt claims unless the bytes are identical. `adopt <checkout> <other-repo>` is
the explicit takeover of files that the named repo installed earlier. Run `diff`
first and read its `conflicting`, `unowned_replaced`, and `foreign_replaced`
lists. `--cohort <name>` restricts any command to one Cohort. The full contract
is in the docstring of `cli/lib/install.py`.

## Bootstrap on a fresh machine

Prerequisites: `git`; a system `/usr/bin/python3` of 3.9 or later, which every
executable's shebang pins; `gh`, authenticated, if you use the `ghw-*`
wrappers; and Beads' `bd` on PATH if you use `bdw`. On macOS,
`/usr/bin/python3` comes with the Xcode Command Line Tools
(`xcode-select --install`). The interpreter is the system one, not your usual
Homebrew, pyenv, or conda one: macOS grants OS-level permissions (privacy
prompts such as Local Network access) to the Apple-signed `/usr/bin/python3`,
and silently denies them to other interpreters when a wrapper runs from an
unattended or background session. The board wrappers (`ghw-board-*`,
`ghw-orient`) need the `project` scope on the `gh` token:
`gh auth refresh -s project`.

1. Clone this repo wherever you keep checkouts.
2. Install everything from it:

    ```sh
    /usr/bin/python3 <checkout>/cli/tooling-install apply <checkout>
    ```

3. Put the wrapper directory on PATH, for example in `~/.zshrc`:

    ```sh
    export PATH="$PATH:$HOME/.local/libexec/agent-tooling"
    ```

    Open a new shell and check with `which gitw-orient tooling-install`.
4. Register each repo you want agents to work in with the gitw roster
   (`~/.config/gitw/repos.toml`). The bare form prints the entry it would add,
   and the trailing `apply` writes it:

    ```sh
    gitw-repo-register <label> <checkout-path>
    gitw-repo-register <label> <checkout-path> apply
    ```

5. For Forgejo, write `~/.config/fjw/config.toml` with the API URL and a machine
   account token. The keys are documented in `cli/lib/forgejo/config.py`.
   If a Beads database here has a Dolt remote, list that remote's host in
   `bdw`'s push-host allowlist,
   `~/.config/agent-tooling/bdw/config.toml`, as
   `push_hosts = ["<host>"]` (the host alone): `bdw` pushes after every
   write only to listed hosts and refuses every other push. The format is
   in [docs/projects/bdw/index.md](docs/projects/bdw/index.md).
6. Wire permissions in `~/.claude/settings.json`. The wrappers and skills
   assume at least these rules:

    ```jsonc
    "deny":  ["Read(~/.config/fjw/**)", "Edit(~/.config/fjw/**)",
              "Bash(*.config/fjw*)",
              "Edit(~/.local/libexec/agent-tooling/**)",
              "Edit(~/.claude/skills/**)",
              "Edit(~/.claude/agents/**)"],
    "ask":   ["Bash(gitw-repo-register *)",
              "Bash(tooling-install apply *)",
              "Bash(tooling-install adopt *)"],
    "allow": ["Edit(//tmp/claude/**)", "Bash(tooling-install diff *)"]
    ```

    The first three deny rows keep the Forgejo token out of every agent's
    reach. The Bash row is needed because `Read()` denies do not cover shell
    tools: the Bash matcher checks redirect targets against file rules, not
    file arguments, so without it a plain `cat` could read the token.
    The Edit denies on the three Install Targets mean a change reaches
    installed tooling only through a committed source and an approved install
    (ADR 0007); some broad Bash grants can still write there, so keep those
    narrow. The ask rules keep roster registration and installs a human act.
    The `tooling-install diff` allow lets an agent report drift without being
    able to act on it (step 7 runs it). The `Edit(//tmp/claude/**)` allow is
    the staging root: every wrapper that reads a message or body file accepts it only from
    `/tmp/claude/` or `~/.claude/jobs/<job-id>/tmp/` and refuses any other
    path, so agents must be able to write there. Create it with
    `mkdir -p /tmp/claude` (and again after a reboot clears `/tmp`). Then grant
    the verbs each repo uses; `skills/use-git/SKILL.md` ("Allowlisting a
    Consumer") shows the rule shape. This repo also ships its own project
    `.claude/settings.json`, the permission rules for its Issue Tracker (see
    below); it applies only to sessions launched from a checkout whose
    checked-out branch contains it.
7. Check it all: `tooling-install diff <checkout>` reports every Cohort
   `in-sync`, and
   `gitw-orient <label>` reports the repo.

The skills tell agents to call the wrappers by bare name, which is the form the
permission rules match. The one exception is the `triage-issues` reference
wrappers, which are invoked as
`python3 ~/.claude/skills/triage-issues/reference/<wrapper>`; their allow rows
are in `skills/triage-issues/reference/DEPLOYMENT.md`.

## Working on this repo

Edit here, then install with `tooling-install apply`. Never edit the installed
copies. Run the tests from `cli/`:

```sh
cd cli && /usr/bin/python3 -m unittest discover -s . -p '*_test.py'
```

Tests never touch the real Install Targets or the network. Many write their
fixtures under `/tmp/claude/` (the staging root the wrappers accept). They
create it if it is missing, so `/tmp/claude/` must be creatable and writable
by you; the rest use a temporary directory.

`LEXICON.md` is the vocabulary. `docs/adr/` holds the design decisions.
`docs/index.md` is the documentation front door: per-project docs under
`docs/projects/`, the exit-code contract every wrapper shares, and the rest.

Work on this repo is tracked in Beads (`bd` 1.3.0), with GitHub Issues
kept but taking no work; `CLAUDE.md` has the rules and ADR 0011 the
reasons. You need `bd` to contribute, not to use the tooling. A fresh clone
gets the `.beads/` config but no issue data: the database is local to the
maintainer's machine, and nothing in it syncs to this repository. To set up Beads in
another repo, follow the onboarding checklist in
`skills/use-bd/onboarding.md`.

## Provenance

History in this repository begins fresh on 2026-09-22. The code was extracted
from a private configuration repository, whose history stays there; the
extracted tree was scrubbed of deployment-specific names and paths before its
first commit here.

## License

MIT; see [LICENSE](LICENSE).
