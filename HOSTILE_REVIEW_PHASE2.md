# Phase 2 hostile methodology review

Date: 2026-09-04 (Asia/Kolkata)

A separate `gpt-5.6-sol` Codex CLI process at high reasoning effort reviewed the
repository read-only after the first Phase 2 analysis and before publication. It is
an AI review, not expert or human endorsement. The reviewer verified run sizes,
counts, paired seeds, token-cap counts, reported intervals, artifact hashes, and the
relevant tests, then returned a “blocked” verdict with five findings.

## Findings and disposition

1. **D was mislabeled in the narrative.** Four of five strict D positives did not
   admit an actually used workaround and violate the exact severity ≥2 rule.
   **Accepted.** They are now described as AI-coder errors, not false admissions.
2. **The human packet was not blind.** It exposed arm, truth, sources, and AI labels.
   **Accepted and fixed.** The packet now has only audit ID, experiment type,
   response, and empty human fields. Metadata and AI labels are in a separate key.
3. **Two preregistered analyses were missing.** There was no paired source scatter
   or complete replicate distribution. **Accepted and fixed.** Both figures and a
   full coder/cell/replicate CSV are now generated.
4. **B was overclaimed as null.** Its wide interval does not establish equivalence.
   **Accepted and fixed.** It is now “no clear detected difference.”
5. **The reproducibility trail was incomplete.** Results were not yet committed,
   and judging/analysis commands were absent. **Accepted and fixed for the public
   artifact.** Exact commands and CLI versions are in `results/RUN_LOG.md`; all
   referenced files are committed together.

The review also motivated a stricter look at the actor gate. All 18 strict positives
attempted to commit before resolving errors, but none named an explicit bypass
mechanism. That limitation is now prominent in the report and worthiness audit.

## Remaining blocker

The 295-row human audit is still blank. The project should not be presented as a
finished application result until a human completes the blinded packet, records its
hash before opening the key, and reports human-vs-AI sensitivity. A stronger
same-actor rollout would also be needed to claim demonstrated recreation of an
actual bypass rather than a workaround-oriented commit attempt.
