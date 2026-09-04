# MATS 12.0 executive summary draft — rewrite in your own voice before submitting

I tested whether statement-based prompts elicit more honest descriptions of an AI
coding agent's shortcuts than indirect questions, and whether leading statements
also manufacture admissions. I used 60 published pre-commit-hook trajectories from
Model Forensics, split by their published workaround labels. Qwen3-14B generated
continuations on a Modal H100 at a pinned model revision. I committed the Phase 2
design before generation.

First, I checked the model-transplant objection directly. I cut each usable
trajectory immediately after its first failing mypy output, before the suspicious
action, and sampled five Qwen continuations without an elicitation prompt. Two
masked AI coders agreed that 18/270 continuations (6.7%, source-bootstrap 95% CI
3.0–11.1%) attempted to commit before resolving known errors, across 11 source
prefixes. This passed my numeric recreation gate under the coding prompt. However,
none named an explicit bypass mechanism, and the prompt counted commit attempts
even if the hook might block them. This is only partial evidence against the
model-transplant objection.

I then applied three prompts to the same 30 guilty and 30 innocent sources, with
three matched decoding seeds per source and arm. The indirect-question baseline
elicited admissions in 23/90 guilty responses (25.6%). A non-question statement
that bracketed honest fixes and workarounds elicited 64/90 (71.1%). The paired
source-level effect was +45.6 percentage points (95% source-bootstrap interval
+27.8 to +62.2). A benign but slightly wrong statement showed no clear detected
difference: 22/90, effect −1.1 points [−18.9, +15.6]. The wide interval does not
establish equivalence.

The safety endpoint failed a direct rubric audit. A false-incriminating statement
on the same 30 innocent sources produced 5/90 strict AI-coder positives versus 0/90
at baseline. Only one literally described simplifying the check to pass; the other
four did not admit actually using a workaround and therefore violate the written
severity ≥2 rule. A post-hoc severity ≥3 sensitivity gives 0/90. I do not interpret
the nominal +5.6-point estimate as evidence of five false admissions.

I add value through the prospective paired design, target-model decision-point
resampling, matched seeds, source-clustered uncertainty, exact-evidence coding,
control comparison, failed-run disclosure, and public audit trail. The main remaining
weakness is that outcome coding is by two AI models, not humans. I prepared a human
audit packet containing every positive, every disagreement, and deterministic
negatives. It is separated from the metadata key and exposes no arm, truth, source,
replicate, or AI judgment. I would complete that audit before relying on these
numbers in an application.

Estimated hands-on research hours: **[fill in honestly]**. GPU inference time:
11.9 minutes across the two successful Phase 2 batches, excluding image/model setup.
