# PREREG — privacyflow scripted analog (LOCKED BEFORE ANY HEADLINE NUMBER)

Scope (binding): SCRIPTED ANALOG ONLY, CPU-only, $0, zero LLM, deterministic.
This is not a reproduction of arXiv 2610.40714, not the authors' PrivacyBench
(5,873 tasks / 986 sequences), and not the authors' PrivacyFlow system.
It tests the same *disease* and the same *mechanism class* on synthetic data:
does deliberative, CI-grounded planning before execution reduce disclosure
violations versus executing directly, at bounded utility cost?
The object is disclosure-risk management under Contextual Integrity (CI),
NOT access control and NOT authorization (cf. arXiv 2610.41401, which is a
different paper about privacy-preserving auditing — out of scope here).

## 1. Synthetic task sequences (generator, seed 20261102)
- N = 240 sequences. Steps per sequence drawn deterministically from {4,5,6}
  (seeded RNG). Expected total steps ≈ 1,200.
- Each step: a user task with (recipient role, purpose, origin context),
  1–2 REQUIRED data items, and exactly 1 sensitive DISTRACTOR item present
  in the agent's accumulated context but not needed for the task.
- Item fields: category, sensitivity tier 1–4, subject (first-/third-party),
  origin context, original purpose, authorized recipient roles, consent flag
  (third-party only), topic tag ∈ {health, finance, family, work}.
- Ground-truth CI allow-set (hidden from the planning arm's *inference* of
  consent, see §3): an item may flow to a recipient iff ALL hold:
  (a) recipient role ∈ item.authorized_roles;
  (b) step purpose == item.original_purpose;
  (c) NOT (item is third-party AND consent == False);
  (d) NOT (context crossing: item.origin_context != recipient context AND
      item.sensitivity >= 3).
  A step VIOLATES iff any item actually sent (or inferred, §4) fails the
  allow-set for that recipient/purpose/context.
- Required items are generated as allow-set-satisfying EXCEPT the planted
  trap categories below (rates are generator parameters, fixed here):
  * hidden-consent trap: 1.5% of steps — required item is third-party with
    consent == False, but its observable features (role, purpose) look
    allowed. The planner cannot observe consent, so it allows it → violation.
    This is the planner's honest imperfection; it is NOT tuned after results.
  * CI-conflict: 0.8% of steps — required item visibly fails (b) or (d).
    Planner blocks → step incomplete, no violation.
  * ambiguous-purpose: 0.8% of steps — required item is third-party with an
    ambiguous purpose tag. Planner consults; the simulated user declines for
    third-party ambiguous items (fixed rule) → step incomplete, no violation.
  * inference-pair background: 3% of steps — recipient background knowledge
    already contains one element of a §4 pair and the required item is the
    other element, with the inferred target disallowed for that recipient.
    Planner generalizes or blocks (see §3).
- Distractors are generated to fail at least one of (a)–(d) (i.e. they are
  never allow-set-satisfying for the step's recipient). Sending one is a
  violation by construction.

## 2. Arms (both deterministic, scripted, no LLM)
- EXECUTE-DIRECTLY (System-1-only analog): sends all required items PLUS
  the distractor iff distractor.topic == step.topic (a fixed "helpful
  context inclusion" heuristic — it forwards topically related context it
  has accumulated). Never blocks, never consults.
- DELIBERATIVE-PLANNING (System-2-then-System-1 analog): for each step,
  in order: (0) triage by sensitivity tier; (1) plan: annotate each planned
  item with subject, provenance (origin context, original purpose), and
  recipient background profile; (2) inference simulation with the FIXED
  rule set in §4 applied to planned set + recipient background;
  (3) flow analysis against the planner's *inferred* allow-set (observable
  features only: role, purpose, context crossing; consent unobservable —
  planner assumes consent for first-party items and for third-party items
  whose observable features pass, which is exactly what creates the
  hidden-consent violations); (4) verdict + mitigation hierarchy:
  omission (drop non-required items) → generalization (replace an exact
  value by its category, only where the step's task type is pre-registered
  as generalization-accepting: scheduling tasks accept generalized dates,
  all other task types do not) → redaction (not used for required items)
  → block / consult. Consult outcome is fixed: approve iff the item is
  first-party; decline iff third-party (above, ambiguous steps are
  third-party, so consult declines). Execution sends only the approved plan.

## 3. Utility (task completion)
- A step COMPLETES iff every required item is delivered to the correct
  recipient in exact form, or in generalized form for a
  generalization-accepting task type. A blocked/consult-declined step does
  not complete. A violating step can still complete (leak ≠ task failure),
  exactly as in the paper's pilot observation.
- Sequence completes iff all its steps complete.
- PRIMARY utility metric for G3b: STEP-level completion rate.
  Sequence-level completion is reported descriptively (it compounds
  per-step failures and is not the gate).

## 4. Inference-attack simulation — FIXED, pre-registered, never tuned
The attacker is a fixed set of 5 pair rules. Given sent items ∪ recipient
background knowledge, if both elements of a pair are present and the
inferred target attribute is not allow-set-satisfying for that recipient,
the step counts as an inference violation IN ADDITION to any direct
violation (a step counts once for the sequence-violation indicator).
  I1: {clinic_visit, prescription_pickup} → diagnosis (health)
  I2: {salary_deposit, luxury_purchase} → income_band (finance)
  I3: {home_address, travel_booking} → home_empty_dates (location)
  I4: {manager_email, hr_meeting} → employment_action (employment)
  I5: {school_name, pickup_schedule} → child_routine (family)
These rules are frozen here. If the planning win depends on changing them,
the result is a KILL, not a re-run. (For the record: the planner runs the
SAME fixed rules in its Phase-2 simulation, so it catches planned pairs;
hidden-consent violations are allow-set violations, not inference misses.)

## 5. Metrics, CIs, decision rule
- Sequence privacy-pass rate = share of sequences with NO violating step.
- Sequence violation rate = 1 − privacy-pass rate.
- All CIs: paired bootstrap over sequences (resample sequences, keep arms
  paired), 2,000 resamples, seeded RNG (seed 777), percentile 95% CI.
  Paired differences are computed per resample (planning − direct).
- Cost model: wall-clock CPU seconds on this VM, $0, zero LLM calls,
  zero network calls during the experiment. Cost is reported, not gated.

## 6. Locked gates (ANY locked bar fails → KILL, no bar-moving)
- G0: unit tests green AND seed rerun byte-identical results.json
  (SHA-256 recorded). Fail → KILL (or fix code, never the bars — a code
  bug fix before the first headline run is allowed only if PREREG is
  unchanged; after the first headline run, no code change that affects
  numbers is allowed without a KILL).
- G1: complete live author-code recheck (abs code link + GitHub search +
  full-text HTML scan incl. figure captions). Author code found → STAND
  DOWN, KILLED.md, no build. (Done 2026-11-02: PASS, see G1_CHECK.md.)
- G2 (disease): execute-directly sequence violation rate ≥ 25%
  (point estimate) AND its 95% bootstrap CI excludes 0. Fail → KILL.
- G3a (load-bearing): planning sequence privacy-pass rate − direct
  sequence privacy-pass rate ≥ 15 percentage points (point estimate)
  AND paired 95% CI lower bound > 0. Fail → KILL.
- G3b (utility bound): direct step-completion rate − planning
  step-completion rate ≤ 10 percentage points (point estimate) AND
  paired 95% CI upper bound < 10pp. Fail → KILL.
- G3c (attacker integrity): the §4 rule set is unchanged from this file
  (verified by diffing the implementation's rule table against §4 at run
  time; the run script asserts this). Any post-hoc rule change → KILL.

Decision rule: ANY of G0/G1/G2/G3a/G3b/G3c fails → KILL:
write KILLED.md + negative PAPER.md, no push payload, no LinkedIn draft,
no re-litigation, no second run with moved bars.
PASS on all gates → PAPER.md + LinkedIn draft (DRAFT ONLY) + staged push
payload, report REPO NEEDED: habib-analyst/privacyflow.

## 7. What is NOT claimed
- No claim about the authors' models, benchmark, or numbers (22–55pp in
  the paper is context only, never presented as reproduced).
- No claim of real-world privacy protection: synthetic items, scripted
  agents, a 5-rule attacker, and a planner that infers allow-sets from
  observable features only. Generalization to LLM agents is untested here.
