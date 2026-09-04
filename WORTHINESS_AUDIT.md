# “Neel Nanda worthy?” audit

## Verdict

**The main result is research-quality and worth sharing; the package is not yet
Neel-Nanda-worthy as a finished application artifact.** The Phase 2
result now has a prospective hypothesis, a causal paired comparison, a target-model
behavior-recreation gate, matched decoding seeds, uncertainty at the correct source
unit, a control comparison, an adversarial safety arm, exact prompts, raw outputs,
and failed-attempt disclosure. That is a serious model-forensics artifact rather
than a prompt demo.

The remaining hard blockers are human judgment and a stronger same-actor check.
Both outcome coders are OpenAI model aliases; four of five D positives violate their
own rubric; and all 18 actor-gate positives are commit attempts without an explicit
bypass mechanism. Submitting a false-confession or fully resolved model-transplant
claim would overstate the evidence.

## Evidence against the MATS bar

| Criterion | Status | Evidence |
|---|---|---|
| Direct model-forensics relevance | Pass | Tests elicitation of hidden/undesired agent behavior and susceptibility to a false premise. |
| Causal counterfactual | Pass | Same source transcripts and matched seeds across A/B/C; same innocent sources for D/A. |
| Model-transplant sanity check | Partial | Qwen attempted commits with unresolved errors in 18 cases, but named no explicit bypass and prefixes still came from Kimi. |
| Correct unit of analysis | Pass | Source-level paired means; 20,000 source bootstraps. |
| Baseline and control | Pass | Indirect-question A baseline; B shows no clear detected difference and its wide interval is reported. |
| Skeptical safety analysis | Pass | The report rejects four rubric-invalid D labels instead of presenting them as false admissions. |
| Reproducibility | Pass with caveat | Pinned Qwen/data revisions, seeds, H100 runtime, raw outputs; judge aliases are not immutable. |
| Human-added value | Partial | Design, checks, interpretation, and audit tooling are substantive; labels still need human review. |
| Clear ≤600-word summary | Draft ready | `MATS_EXECUTIVE_SUMMARY.md`; applicant must rewrite it and add honest hours. |

## Before submission

1. Follow `HUMAN_AUDIT_INSTRUCTIONS.md` and audit every row in
   `results/analysis/phase2/human_audit_packet.csv` without opening the separate key; then
   publish completed human labels plus an AI-vs-human sensitivity analysis.
2. Rewrite the executive summary in the applicant's own voice; do not present AI
   prose as personal authorship.
3. Add the applicant's actual hours and a short account of decisions they personally
   made.
4. Replicate on a second task family or run a stronger same-actor rollout that
   demonstrates an actual bypass rather than an attempted commit.
