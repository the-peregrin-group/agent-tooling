# Setting up Forgejo issues

The Forgejo mechanics of `setup-issue-tracker`, read when its plan reaches
a step on Forgejo. `fjw` has no issue or label Verbs yet, so most of a
Forgejo setup cannot go through a Wrapper today: say so in the plan, and
leave what needs those Verbs for the owner to do by hand or to wait.

## Forge identity, today

fjw acts as one machine account, the identity in its Machine Config
(`~/.config/fjw/config.toml`, which `use-forgejo` describes). The owner writes
that file; an agent never reads or edits it. There is no Verb that
registers a second identity or a per-repo one.

Giving the machine account access is the owner's act in the forge's own
settings: add the account to the repo as a collaborator. Read access is
the recommended grant for pull requests (it can open, comment on, and
close its own, and cannot merge). Whether that grant is enough to file,
edit, and label issues is not verified yet; until it is, the plan says
which access it proposes and why.

## Where state and priority are recorded

Forgejo has no status field beyond open and closed, and the shipped
default does not designate where the Issue State is recorded on such a
forge. The owner designates it in the repo's `TRACKER.md`, as a
customization (a label axis for status is the default's suggestion). Kind
and priority are labels named for them, as the Tracker Schema says; with no
label Verb yet, the owner creates the labels by hand.
