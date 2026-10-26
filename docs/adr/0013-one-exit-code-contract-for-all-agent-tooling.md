---
date: 2026-10-25
status: current
---

# One exit-code contract for all agent-tooling software, modelled on HTTP status classes

**Context:** Every Wrapper family and the Installer report outcomes through exit codes that callers, unattended agents especially, branch on, but the codes grew family by family: codes 3 to 6 were carved out of 1 when fjw arrived, the Installer kept its own set, and `bdw` passes bd's codes through. So the same situation exits differently across families, and each new Verb re-decides edge cases; three rival rules separated 2 from 4, and a wrong-kind number was 3 in fjw's code and 4 in its design. The contract itself is specified in [the Exit-code contract](../index.md#exit-code-contract).

**Decision:** All agent-tooling software exits with one six-code contract: 0 done; 1 broken on our side, not the caller's fault; 2 the caller must change the call or the state it acts on; 3 the named resource does not exist; 4 policy forbids this caller this action; 5 partial completion, with caller work to do as the output directs.

**Rationale:** One contract, uniform across all agent-tooling software, keyed to what the caller must do next, and independent of the tools underneath, gives callers a clear signal that stays stable when those tools change.

## Consequences

- Every family's shipped codes change, so callers and Skills that branch on the old codes break until each family migrates.
- No code says "retry": a Wrapper retries internally where a retry is worth it, and a caller applies its own threshold to a 1.
- An underlying tool's exit code never reaches the caller; `bdw` must translate bd's codes rather than pass them through.
- A repo the caller cannot see and a repo that does not exist both exit 3, since a forge answers 404 for both and the Wrapper cannot tell them apart.

## Alternatives Considered

### Keep the seven-code taxonomy (0 to 6) and settle its edge cases

**Description:** Keep 1 unclassified, 2 usage, 3 not found, 4 refused, 5 deployment, 6 network, and record a rule for each disputed boundary.
**Rejection rationale:** Its 2-versus-4 boundary rested on when a check runs (parse time, or the first network call) rather than on whose fault the failure is, which is what produced three rival rules; and it split failures inside the abstraction (1, 5, 6) that a caller handles the same way, by stopping and reporting.

### A retryable code

**Description:** Keep a code (6, or a split of 1 into "broken, do not retry" and "transient, try again") that tells the caller a retry may succeed.
**Rejection rationale:** What is worth retrying is the caller's judgement, which the contract does not claim to know; and a Wrapper that can tell a retry is worthwhile and safe retries internally instead.

### Partial completion on 1

**Description:** Give 1 the meaning "partial completion, caller work required", as for a rebase conflict stop.
**Rejection rationale:** 1 is the industry's generic failure code and Python's exit on an uncaught exception, so a crash would tell the caller to act on the output and carry on; on 1 a crash instead reads correctly, as broken on our side.

### A rebase conflict stop as a refusal

**Description:** Report a conflict stop as a refusal, with `"action": "conflict"` in the JSON telling it apart from a caller bug.
**Rejection rationale:** A conflict stop is deliberate, resumable state, not a refusal, and a code whose advice is "never retry unchanged" misdirects a caller whose next step is to resolve and continue.

### Codes per family

**Description:** Let each family, and the Installer, keep the codes that suit its own domain.
**Rejection rationale:** Callers, agents especially, cross families in one session, and per-family codes are what let each family drift.

### Pass the underlying tool's code through

**Description:** Exit with the code of the tool a Wrapper runs (git, gh, bd) when that tool fails.
**Rejection rationale:** The caller then needs each tool's own conventions, which differ and change between versions, so the Wrapper's signal would move whenever the tool's did.
