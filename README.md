# privacyflow (scripted analog)

An open, deterministic, CPU-only, zero-LLM analog of the *mechanism class*
in arXiv 2610.40714 "PrivacyFlow" (Staab, Wollschläger, Mirrokni, Shokri):
deliberative, Contextual-Integrity-grounded privacy planning (System 2)
before task execution (System 1), versus executing directly.

**This is NOT the authors' code, NOT their PrivacyBench, and NOT a
reproduction of their results.** It is an independent from-scratch
implementation on synthetic multi-step tasks, built because a complete
live author-code recheck on 2026-11-02 (see `G1_CHECK.md`) found no author
repository: no code link on the arXiv abstract page, and a full-text HTML
scan (including all figure captions) whose only `github.com` hit is a
third-party OpenClaw reference. The paper's figures (5,873 tasks, 986
sequences, +22–55pp) are context only and are never presented as reproduced.

## What it does

Synthetic task sequences (240 sequences, 1,211 steps, seed 20261102). Each
step has required items and one sensitive distractor in the agent's context.
A CI-grounded allow-set (recipient role, purpose, third-party consent,
context crossing) judges every disclosure, plus a fixed 5-rule inference
attacker (see `PREREG.md` §4 — frozen before any number was generated).

- `execute-directly`: sends required items plus any distractor whose topic
  matches the task ("helpful context inclusion").
- `deliberative-planning`: triages, annotates provenance/purpose, simulates
  inference, checks flows against its inferred allow-set (consent is
  unobservable to it — the honest source of its residual violations), then
  omits, generalizes, blocks, or consults (fixed consult rule).

## Results (measured, paired bootstrap over sequences, 2,000 resamples)

| Metric | Execute-directly | Deliberative-planning |
|---|---|---|
| Sequence privacy-pass rate | 21.67% | 95.00% |
| Sequence violation rate | 78.33% [72.92, 83.33] | 5.00% |
| Step completion rate | 100% | 96.86% |
| Sequence completion rate | 100% | 85.00% |

Improvement in sequence privacy pass: **+73.33pp, 95% CI [67.92, 78.75]**.
Step-completion loss: **3.14pp, 95% CI [2.22, 4.16]** — inside the
pre-registered ≤10pp bound. Sequence completion falls further (85% vs 100%)
because a single blocked step fails a whole sequence; that compounding is
reported honestly and is why the pre-registered utility gate is step-level.

## Run it

```sh
python3 -m unittest discover -s tests -v   # 10 tests
python3 run_experiment.py                  # writes results/results.json
```

Determinism: rerunning produces byte-identical `results.json`
(SHA-256 `b919203bf9586505a44d1af11cc50719b28abb468c78c99be7004335414b720e`).
Cost: CPU seconds, $0, zero LLM calls, zero network calls during the run.

## Scope limits (read before citing)

Synthetic items, scripted agents, a 5-rule attacker, and a planner that
infers allow-sets from observable features only. Nothing here shows that
LLM agents in the wild would behave this way, and nothing here is a
privacy guarantee or legal/compliance verdict. The object is disclosure
risk under Contextual Integrity, not access control or authorization.
