"""Repository orientation: labels, linked ProjectV2 boards, canonical-board
resolution, and priority-regime determination.

The one I/O entry point is fetch_orientation(); everything downstream of it is
a pure function over the fetched data so the resolution rules stay unit-
testable without network access.

Canonical-board rules (which board a wrapper acts on):
    - exactly one open board linked to the repo: use it;
    - several linked: a TRIAGE.md discovered upward from cwd (bounded to the
      enclosing git work tree) decides, but only if the repo it declares
      matches the repo argument (trust-but-verify) and the board it names is
      among those linked;
    - otherwise: no canonical board -- ghw-orient reports the candidates,
      write wrappers refuse with exit 2.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from lib.github import gh
from lib.schema import FIELD_PRIORITY, PRIORITY_OPTIONS, SINGLE_SELECT

# Repo identity plus the first page of the label registry;
# _fetch_repository_with_labels() paginates past 100 labels.
_REPO_QUERY = """
query($owner: String!, $name: String!, $labelCursor: String) {
  repository(owner: $owner, name: $name) {
    id
    nameWithOwner
    isPrivate
    defaultBranchRef { name }
    labels(first: 100, after: $labelCursor) {
      pageInfo { hasNextPage endCursor }
      nodes { name color description }
    }
  }
}
"""

# Closed boards are filtered server-side so they cannot crowd live ones out of
# the page window. fields(first: 100) is the API's page maximum and exceeds
# GitHub's own per-board field limit; _build_board() still fails loudly rather
# than truncate if that ever stops being true.
_PROJECTS_QUERY = """
query($owner: String!, $name: String!, $projectCursor: String) {
  repository(owner: $owner, name: $name) {
    projectsV2(first: 50, query: "is:open", after: $projectCursor) {
      pageInfo { hasNextPage endCursor }
      nodes {
        id
        number
        title
        closed
        fields(first: 100) {
          pageInfo { hasNextPage }
          nodes {
            ... on ProjectV2FieldCommon { id name dataType }
            ... on ProjectV2SingleSelectField { options { id name } }
          }
        }
      }
    }
  }
}
"""

# The open issues carrying one label, looked up by exact label name.
# Deliberately not `gh issue list --label`: that flag splits its value on
# commas, so a label whose name contains one ("needs-design, blocked") would
# query as two ANDed labels, match nothing, and let ghw-label-sync report an
# unattached label that is in fact attached. A typed GraphQL variable matches
# the name exactly, commas and all.
_LABEL_ISSUES_QUERY = """
query($owner: String!, $name: String!, $label: String!, $limit: Int!) {
  repository(owner: $owner, name: $name) {
    label(name: $label) {
      issues(first: $limit, states: OPEN) {
        totalCount
        nodes { number title url }
      }
    }
  }
}
"""

# One issue's node id and its item on every board it already sits on, with
# the current value of one named single-select field.
_ISSUE_ITEMS_QUERY = """
query($owner: String!, $name: String!, $number: Int!, $fieldName: String!) {
  repository(owner: $owner, name: $name) {
    issue(number: $number) {
      id
      projectItems(first: 50) {
        pageInfo { hasNextPage }
        nodes {
          id
          project { id }
          fieldValueByName(name: $fieldName) {
            ... on ProjectV2ItemFieldSingleSelectValue { optionId }
          }
        }
      }
    }
  }
}
"""

# Adds an issue to a board; idempotent server-side, returning the existing
# item rather than duplicating it.
_ADD_ITEM_MUTATION = """
mutation($projectId: ID!, $contentId: ID!) {
  addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
    item { id }
  }
}
"""

# Sets one single-select field on one board item to a given option.
_SET_SINGLE_SELECT_MUTATION = """
mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
  updateProjectV2ItemFieldValue(
    input: {projectId: $projectId, itemId: $itemId, fieldId: $fieldId,
            value: {singleSelectOptionId: $optionId}}
  ) {
    projectV2Item { id }
  }
}
"""

# One board by node id, for reading a board ghw-board-sync just mutated
# without waiting for it to appear in the repo's linked-project list.
_BOARD_BY_ID_QUERY = """
query($projectId: ID!) {
  node(id: $projectId) {
    ... on ProjectV2 {
      id
      number
      title
      url
      fields(first: 100) {
        pageInfo { hasNextPage }
        nodes {
          ... on ProjectV2FieldCommon { id name dataType }
          ... on ProjectV2SingleSelectField { options { id name } }
        }
      }
    }
  }
}
"""

# The repo's own node id plus its owner's, both needed to create a board and
# link it (createProjectV2 takes the owner, linkProjectV2ToRepository the repo).
_REPO_IDENTITY_QUERY = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    id
    owner { id }
  }
}
"""

_CREATE_PROJECT_MUTATION = """
mutation($ownerId: ID!, $title: String!) {
  createProjectV2(input: {ownerId: $ownerId, title: $title}) {
    projectV2 { id number title url }
  }
}
"""

_LINK_PROJECT_MUTATION = """
mutation($projectId: ID!, $repositoryId: ID!) {
  linkProjectV2ToRepository(
    input: {projectId: $projectId, repositoryId: $repositoryId}
  ) {
    repository { id }
  }
}
"""

# ProjectV2SingleSelectFieldOptionColor's full value set; an option color
# outside it is a bug in the caller, not something the API should be asked.
_OPTION_COLOR_VALUES = frozenset({
    "BLUE", "GRAY", "GREEN", "ORANGE", "PINK", "PURPLE", "RED", "YELLOW",
})

# Markers delimiting TRIAGE.md's machine-readable JSON config block.
_TRIAGE_CONFIG_BEGIN = "<!-- BEGIN triage-config -->"
_TRIAGE_CONFIG_END = "<!-- END triage-config -->"

# Strips the ``` fence lines wrapping the TRIAGE.md JSON block before parsing.
_CODE_FENCE_PATTERN = re.compile(r"^\s*```(?:json)?\s*$", re.MULTILINE)


def fetch_orientation(repository: str) -> dict:
    """Fetch everything ghw-orient reports about `repository`: one repo/label
    query (paginated past 100 labels) plus one open-boards query (paginated
    past 50 boards).

    Returns:
        {
          "repo": {"name_with_owner", "node_id", "default_branch", "is_private"},
          "labels": [{"name", "color", "description"}, ...],
          "boards": [board, ...],   # open linked boards, shaped as in fetch_boards()
        }

    Raises gh.GhError on any API failure, including a nonexistent repo.
    """
    node, labels = _fetch_repository_with_labels(repository)
    boards = fetch_boards(repository)

    default_branch = node["defaultBranchRef"]
    return {
        "repo": {
            "name_with_owner": node["nameWithOwner"],
            "node_id": node["id"],
            "default_branch": default_branch["name"] if default_branch else None,
            "is_private": node["isPrivate"],
        },
        "labels": labels,
        "boards": boards,
    }


def fetch_boards(repository: str) -> list[dict]:
    """The repo's open linked boards, paginated past 50, each shaped as
    {"number", "title", "node_id", "fields": {field_name: {"id", "data_type",
    "options": {option_name: option_id}}}}.

    The boards-only sibling of fetch_orientation() for wrappers (ghw-board-set)
    that never read the label registry. Raises gh.GhError on any API failure.
    """
    owner, name = repository.split("/", 1)
    boards: list[dict] = []
    project_cursor = None
    while True:
        variables = {"owner": owner, "name": name}
        if project_cursor:
            variables["projectCursor"] = project_cursor
        connection = gh.graphql(_PROJECTS_QUERY, variables)["repository"]["projectsV2"]
        for board_node in connection["nodes"]:
            if board_node["closed"]:  # belt to the server-side is:open filter
                continue
            boards.append(_build_board(board_node))
        if not connection["pageInfo"]["hasNextPage"]:
            break
        project_cursor = connection["pageInfo"]["endCursor"]
    return boards


def fetch_labels(repository: str) -> list[dict]:
    """The repo's full label registry: [{"name", "color", "description"}, ...],
    paginated past 100 labels.

    The lighter sibling of fetch_orientation() for wrappers that need only the
    attachment authority, not the boards. Raises gh.GhError on any API failure.
    """
    _, labels = _fetch_repository_with_labels(repository)
    return labels


def fetch_open_issues_with_label(repository: str, label: str,
                                 limit: int = 100) -> dict:
    """The repo's open issues carrying exactly `label`.

    Returns {"total": int, "issues": [{"number", "title", "url"}]}, where
    `total` is the server-side count and `issues` holds at most `limit` of
    them -- ghw-label-sync reports both so a truncated list cannot understate
    what a deletion would detach. A label that does not exist yields
    {"total": 0, "issues": []}. Raises gh.GhError on any API failure.
    """
    owner, name = repository.split("/", 1)
    node = gh.graphql(_LABEL_ISSUES_QUERY, {
        "owner": owner, "name": name, "label": label, "limit": limit,
    })["repository"]["label"]
    if node is None:
        return {"total": 0, "issues": []}
    return {"total": node["issues"]["totalCount"],
            "issues": list(node["issues"]["nodes"])}


def fetch_branches_exist(repository: str, branches: list[str]) -> dict[str, bool]:
    """Which of `branches` exist on the remote, resolved in one ref query.

    An empty `branches` returns {} without a network call. Raises gh.GhError
    on any API failure.
    """
    if not branches:
        return {}
    owner, name = repository.split("/", 1)
    variables: dict = {"owner": owner, "name": name}
    for index, branch in enumerate(branches):
        variables[f"ref{index}"] = f"refs/heads/{branch}"
    node = gh.graphql(_build_refs_query(len(branches)), variables)["repository"]
    return {
        branch: node[f"ref{index}"] is not None
        for index, branch in enumerate(branches)
    }


def fetch_issue_item_state(repository: str, number: int, field_name: str) -> dict:
    """One issue's node id plus its item on every board it already sits on,
    with the current value of `field_name` where that field is single-select.

    Returns {"issue_node_id": ..., "items": {project_node_id:
    {"item_id": ..., "option_id": ... | None}}}. Raises gh.GhError on any API
    failure (including a nonexistent issue).
    """
    owner, name = repository.split("/", 1)
    data = gh.graphql(_ISSUE_ITEMS_QUERY, {
        "owner": owner, "name": name, "number": number, "fieldName": field_name,
    })
    issue_node = data["repository"]["issue"]
    if issue_node is None:  # belt only: a missing issue surfaces as GraphQL errors
        raise gh.GhError(f"issue #{number} not found in {repository}")
    return _build_issue_item_state(issue_node)


def add_item_to_board(board_node_id: str, content_node_id: str) -> str:
    """Add an issue to a board and return the item's node id.

    Idempotent server-side: addProjectV2ItemById returns the existing item
    rather than duplicating it. Raises gh.GhError on any API failure.
    """
    data = gh.graphql(_ADD_ITEM_MUTATION, {
        "projectId": board_node_id, "contentId": content_node_id,
    })
    return data["addProjectV2ItemById"]["item"]["id"]


def set_single_select_value(
    board_node_id: str, item_id: str, field_id: str, option_id: str
) -> None:
    """Set a single-select field on one board item to the given option.

    Raises gh.GhError on any API failure.
    """
    gh.graphql(_SET_SINGLE_SELECT_MUTATION, {
        "projectId": board_node_id, "itemId": item_id,
        "fieldId": field_id, "optionId": option_id,
    })


def fetch_board_by_node_id(board_node_id: str) -> dict:
    """One board by node id, shaped as in fetch_boards() plus its "url".

    Two purposes: re-reading a board immediately after mutating it, which a
    linked-list query cannot be trusted to reflect yet, and supplying the
    board `url` -- this is the only fetch that carries one. Raises gh.GhError
    if the node is absent or is not a ProjectV2.
    """
    node = gh.graphql(_BOARD_BY_ID_QUERY, {"projectId": board_node_id})["node"]
    if not node or "number" not in node:
        raise gh.GhError(f"node {board_node_id!r} is not a ProjectV2 board")
    return {**_build_board(node), "url": node["url"]}


def fetch_repository_identity(repository: str) -> dict:
    """The repo's node id plus its owner's, as {"node_id", "owner_node_id"}.

    Both are needed to create a board and link it: createProjectV2 takes the
    owner, linkProjectV2ToRepository the repo. Raises gh.GhError on any API
    failure, including a nonexistent repo.
    """
    owner, name = repository.split("/", 1)
    node = gh.graphql(_REPO_IDENTITY_QUERY, {"owner": owner, "name": name})["repository"]
    return {"node_id": node["id"], "owner_node_id": node["owner"]["id"]}


def create_project(owner_node_id: str, title: str) -> dict:
    """Create a ProjectV2 owned by `owner_node_id`, returning
    {"node_id", "number", "title", "url"}.

    Raises gh.GhError on any API failure -- notably a token without the
    `project` scope.
    """
    project = gh.graphql(_CREATE_PROJECT_MUTATION, {
        "ownerId": owner_node_id, "title": title,
    })["createProjectV2"]["projectV2"]
    return {
        "node_id": project["id"],
        "number": project["number"],
        "title": project["title"],
        "url": project["url"],
    }


def link_project_to_repository(board_node_id: str, repository_node_id: str) -> None:
    """Link a board to a repository. Raises gh.GhError on any API failure."""
    gh.graphql(_LINK_PROJECT_MUTATION, {
        "projectId": board_node_id, "repositoryId": repository_node_id,
    })


def create_field(board_node_id: str, name: str, data_type: str,
                 options: list[dict] | None = None) -> str:
    """Create one board field, returning its node id.

    `options` is the [{"name", "color", "description"}] list for a
    SINGLE_SELECT field and None otherwise. Option values are inlined into the
    mutation document (gh's `-f` variables carry scalars only), which is safe
    precisely because they are the baked-in canonical schema and never caller
    input; _options_literal() still refuses anything outside the API's color
    enum. Raises gh.GhError on any API failure.
    """
    literal = f", singleSelectOptions: {_options_literal(options)}" if options else ""
    mutation = f"""
mutation($projectId: ID!, $name: String!, $dataType: ProjectV2CustomFieldType!) {{
  createProjectV2Field(
    input: {{projectId: $projectId, dataType: $dataType, name: $name{literal}}}
  ) {{
    projectV2Field {{ ... on ProjectV2FieldCommon {{ id name }} }}
  }}
}}
"""
    data = gh.graphql(mutation, {
        "projectId": board_node_id, "name": name, "dataType": data_type,
    })
    return data["createProjectV2Field"]["projectV2Field"]["id"]


def replace_single_select_options(field_node_id: str, options: list[dict]) -> None:
    """Replace a single-select field's entire option set.

    Destructive by nature: options left out are removed, and any item value
    assigned to them is orphaned. Exactly one caller is sanctioned --
    ghw-board-sync replacing the stock Todo/In Progress/Done options on a board
    it just created, which by construction has no items. Raises gh.GhError on
    any API failure.
    """
    mutation = f"""
mutation($fieldId: ID!) {{
  updateProjectV2Field(
    input: {{fieldId: $fieldId, singleSelectOptions: {_options_literal(options)}}}
  ) {{
    projectV2Field {{ ... on ProjectV2SingleSelectField {{ id }} }}
  }}
}}
"""
    gh.graphql(mutation, {"fieldId": field_node_id})


def _options_literal(options: list[dict]) -> str:
    """Render single-select options as a GraphQL list literal.

    Names and descriptions go through json.dumps (GraphQL string literals are
    JSON-compatible); colors are bare enum tokens, so each is checked against
    the API's enum rather than interpolated blind.
    """
    rendered = []
    for option in options:
        color = option["color"]
        if color not in _OPTION_COLOR_VALUES:
            # GhError, not ValueError: unreachable while the colors are
            # baked-in constants, but a future typo should still exit 1 the
            # way every other wrapper failure does, not as a traceback.
            raise gh.GhError(
                f"option color {color!r} is not one of "
                f"{', '.join(sorted(_OPTION_COLOR_VALUES))}"
            )
        rendered.append(
            f'{{name: {json.dumps(option["name"])}, color: {color}, '
            f'description: {json.dumps(option["description"])}}}'
        )
    return "[" + ", ".join(rendered) + "]"


def resolve_canonical_board(
    repository: str,
    boards: list[dict],
    triage_profile: dict | None,
) -> tuple[dict | None, str, str | None]:
    """Apply the canonical-board rules to the repo's open linked boards.

    `triage_profile` is a discovered profile from find_triage_profile(), or
    None when no TRIAGE.md was found.

    Returns (board, rule, note): the canonical board dict or None, which rule
    decided ("only-linked" | "triage-md" | "none-linked" | "ambiguous"), and
    an optional human-readable explanation (always present for "ambiguous",
    also used to surface an ignored, mismatching TRIAGE.md).
    """
    if not boards:
        return None, "none-linked", None
    if len(boards) == 1:
        only = boards[0]
        note = None
        if triage_profile is not None and (
            triage_profile["repo"] != repository
            or triage_profile["project_number"] != only["number"]
        ):
            note = (
                f"{triage_profile['path']} names "
                f"{triage_profile['repo']}#{triage_profile['project_number']}, "
                f"but the only-linked rule wins"
            )
        return only, "only-linked", note

    candidates = ", ".join(f"#{board['number']} ({board['title']})" for board in boards)
    if triage_profile is not None:
        if triage_profile["repo"] != repository:
            return None, "ambiguous", (
                f"{triage_profile['path']} declares repo {triage_profile['repo']!r}, "
                f"not {repository!r}; ignoring it. Candidates: {candidates}"
            )
        for board in boards:
            if board["number"] == triage_profile["project_number"]:
                return board, "triage-md", f"decided by {triage_profile['path']}"
        return None, "ambiguous", (
            f"{triage_profile['path']} names project #{triage_profile['project_number']}, "
            f"which is not linked to {repository}. Candidates: {candidates}"
        )
    return None, "ambiguous", f"multiple boards linked, no TRIAGE.md found. Candidates: {candidates}"


def determine_priority_regime(canonical_board: dict | None, boards: list[dict]) -> str:
    """Determine how the repo tracks priority.

    Returns "board-field" when the canonical board carries a single-select
    Priority field with all of P0-P3 among its options (a field merely *named*
    Priority is not enough -- a write against it would fail), "p-labels" when
    no board is linked at all (priority lives in P0-P3 issue labels), and
    "unknown" when boards exist but none resolved as canonical or the
    canonical one's Priority field is absent or non-conforming.
    """
    if canonical_board is not None:
        priority = canonical_board["fields"].get(FIELD_PRIORITY)
        if (
            priority is not None
            and priority["data_type"] == SINGLE_SELECT
            and all(option in priority["options"] for option in PRIORITY_OPTIONS)
        ):
            return "board-field"
        return "unknown"
    if not boards:
        return "p-labels"
    return "unknown"


def priority_labels_present(labels: list[dict]) -> list[str]:
    """Return which of the P0-P3 labels exist in the repo's label registry."""
    names = {label["name"] for label in labels}
    return [option for option in PRIORITY_OPTIONS if option in names]


def find_triage_profile(start_directory: Path) -> dict | None:
    """Search upward from `start_directory` for a TRIAGE.md with a readable
    triage-config block, bounded to the enclosing git work tree.

    The walk stops at the first directory containing a `.git` entry (dir or
    file, so linked worktrees count), inclusive; outside any git work tree
    there is no discovery at all. This keeps a stray TRIAGE.md in /tmp or a
    home directory from ever deciding a repo's board.

    Returns {"repo", "project_number", "path"} from the nearest parseable
    profile, or None. A TRIAGE.md that is unreadable, malformed, or of the
    wrong shape is skipped silently -- orientation is a read and must not fail
    on someone else's broken profile.
    """
    directories = (start_directory, *start_directory.parents)
    for boundary, directory in enumerate(directories):
        if (directory / ".git").exists():
            break
    else:
        return None
    for directory in directories[: boundary + 1]:
        profile = _read_triage_profile(directory / "TRIAGE.md")
        if profile is not None:
            return profile
    return None


def _read_triage_profile(candidate: Path) -> dict | None:
    """Parse one TRIAGE.md candidate; None for anything unusable (missing,
    unreadable, not UTF-8, config block absent/malformed/wrong shape)."""
    try:
        if not candidate.is_file():
            return None
        config = _parse_triage_config(candidate.read_text(encoding="utf-8"))
        if not isinstance(config, dict) or not isinstance(config.get("repo"), str):
            return None
        return {
            "repo": config["repo"],
            "project_number": int(config["project_number"]),
            "path": str(candidate),
        }
    except (OSError, UnicodeDecodeError, KeyError, TypeError, ValueError):
        return None


def _build_board(board_node: dict) -> dict:
    """Reshape one GraphQL ProjectV2 node into the board dict used throughout:
    {"number", "title", "node_id", "fields": {name: {"id", "data_type",
    "options": {option_name: option_id}}}}.

    Raises gh.GhError rather than returning a truncated field map if the board
    somehow exceeds the 100-field page (GitHub's own limits should make that
    impossible).
    """
    if board_node["fields"]["pageInfo"]["hasNextPage"]:
        raise gh.GhError(
            f"board #{board_node['number']} ({board_node['title']}) has more "
            "than 100 fields; refusing to return a truncated field map"
        )
    fields = {}
    for field_node in board_node["fields"]["nodes"]:
        # Defensive only: every current ProjectV2 field type implements
        # ProjectV2FieldCommon, so empty objects should never occur.
        if not field_node:
            continue
        fields[field_node["name"]] = {
            "id": field_node["id"],
            "data_type": field_node["dataType"],
            "options": {
                option["name"]: option["id"]
                for option in field_node.get("options", [])
            },
        }
    return {
        "number": board_node["number"],
        "title": board_node["title"],
        "node_id": board_node["id"],
        "fields": fields,
    }


def _parse_triage_config(text: str) -> dict | None:
    """Extract the marker-delimited JSON config block from TRIAGE.md text.

    Returns None (rather than raising) when the markers are absent or the
    block is not valid JSON; see find_triage_profile() for why.
    """
    try:
        start = text.index(_TRIAGE_CONFIG_BEGIN) + len(_TRIAGE_CONFIG_BEGIN)
        end = text.index(_TRIAGE_CONFIG_END, start)
    except ValueError:
        return None
    block = _CODE_FENCE_PATTERN.sub("", text[start:end]).strip()
    try:
        return json.loads(block)
    except json.JSONDecodeError:
        return None


def _fetch_repository_with_labels(repository: str) -> tuple[dict, list[dict]]:
    """Run the repo/labels query, paginating past 100 labels.

    Returns (repository node, full label list). Raises gh.GhError on any API
    failure, including a nonexistent repo.
    """
    owner, name = repository.split("/", 1)
    node = gh.graphql(_REPO_QUERY, {"owner": owner, "name": name})["repository"]
    labels = list(node["labels"]["nodes"])
    page_info = node["labels"]["pageInfo"]
    while page_info["hasNextPage"]:
        page = gh.graphql(
            _REPO_QUERY,
            {"owner": owner, "name": name, "labelCursor": page_info["endCursor"]},
        )["repository"]["labels"]
        labels += page["nodes"]
        page_info = page["pageInfo"]
    return node, labels


def _build_refs_query(branch_count: int) -> str:
    """The ref-existence query for `branch_count` branches, one alias each:
    ref0: ref(qualifiedName: $ref0) { name }, ref1: ..., and so on."""
    declarations = "".join(f", $ref{index}: String!" for index in range(branch_count))
    selections = " ".join(
        f"ref{index}: ref(qualifiedName: $ref{index}) {{ name }}"
        for index in range(branch_count)
    )
    return (
        f"query($owner: String!, $name: String!{declarations}) {{ "
        f"repository(owner: $owner, name: $name) {{ {selections} }} }}"
    )


def _build_issue_item_state(issue_node: dict) -> dict:
    """Reshape the issue/projectItems GraphQL node; see fetch_issue_item_state.

    A truncated projectItems page (an issue on more than 50 boards) is
    tolerated rather than refused: a board missed here is later re-added by
    the idempotent addProjectV2ItemById, so the worst case is one redundant
    write, not a wrong one.
    """
    items = {}
    for item_node in issue_node["projectItems"]["nodes"]:
        value = item_node.get("fieldValueByName") or {}
        items[item_node["project"]["id"]] = {
            "item_id": item_node["id"],
            "option_id": value.get("optionId"),
        }
    return {"issue_node_id": issue_node["id"], "items": items}
