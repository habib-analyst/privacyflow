"""privacyflow — scripted, deterministic analog of CI-grounded privacy planning.

Scope: synthetic multi-step tasks, scripted arms, zero LLM, CPU only.
This is NOT the authors' implementation and NOT a reproduction of
arXiv 2610.40714. See PREREG.md for the locked design.
"""
from __future__ import annotations

import random

# --- Fixed inference-attack rule set (PREREG section 4, frozen) ---
# pair of item categories -> inferred target attribute
INFERENCE_RULES = {
    ("clinic_visit", "prescription_pickup"): "diagnosis",
    ("salary_deposit", "luxury_purchase"): "income_band",
    ("home_address", "travel_booking"): "home_empty_dates",
    ("manager_email", "hr_meeting"): "employment_action",
    ("school_name", "pickup_schedule"): "child_routine",
}

ROLES = ["vendor", "colleague", "family", "manager", "clinician", "service"]
CONTEXTS = ["home", "work", "clinic", "bank", "family"]
TOPICS = ["health", "finance", "family", "work"]
# Normal (non-pair) item categories. Pair categories above never appear
# as normal required/distractor items, so inference can only fire on
# planted inference-pair steps (or via background + required pair element).
NORMAL_CATEGORIES = [
    "email_address", "phone_number", "project_note", "meeting_time",
    "budget_figure", "dietary_note", "travel_preference", "work_schedule",
    "bank_account_hint", "medical_note", "family_event", "salary_hint",
]


class Item:
    def __init__(self, category, sensitivity, subject, origin_context,
                 original_purpose, authorized_roles, consent=True):
        self.category = category
        self.sensitivity = sensitivity
        self.subject = subject  # "first" or "third"
        self.origin_context = origin_context
        self.original_purpose = original_purpose
        self.authorized_roles = list(authorized_roles)
        self.consent = consent

    def to_dict(self):
        return {
            "category": self.category, "sensitivity": self.sensitivity,
            "subject": self.subject, "origin_context": self.origin_context,
            "original_purpose": self.original_purpose,
            "authorized_roles": self.authorized_roles, "consent": self.consent,
        }


class Step:
    def __init__(self, topic, recipient_role, recipient_context, purpose,
                 task_type, required, distractor, background_categories,
                 inference_target_disallowed=False, ambiguous=False):
        self.topic = topic
        self.recipient_role = recipient_role
        self.recipient_context = recipient_context
        self.purpose = purpose
        self.task_type = task_type  # "scheduling" (generalization-accepting) or "other"
        self.required = required
        self.distractor = distractor
        self.background_categories = set(background_categories)
        self.inference_target_disallowed = inference_target_disallowed
        self.ambiguous = ambiguous

    @property
    def generalization_accepting(self):
        return self.task_type == "scheduling"


def allow_set_ok(item, recipient_role, purpose, recipient_context):
    """Ground-truth CI allow-set check, PREREG section 1 (a)-(d)."""
    if recipient_role not in item.authorized_roles:
        return False
    if purpose != item.original_purpose:
        return False
    if item.subject == "third" and not item.consent:
        return False
    if item.origin_context != recipient_context and item.sensitivity >= 3:
        return False
    return True


def planner_inferred_ok(item, recipient_role, purpose, recipient_context):
    """Planner's inferred allow-set: observable features only.

    Consent is unobservable, so the planner does NOT check it. This is
    exactly what produces hidden-consent violations (PREREG section 2).
    """
    if recipient_role not in item.authorized_roles:
        return False
    if purpose != item.original_purpose:
        return False
    if item.origin_context != recipient_context and item.sensitivity >= 3:
        return False
    return True


def inference_violation(sent_categories, background_categories, target_disallowed):
    """Fixed attacker (PREREG section 4). Returns inferred target or None."""
    if not target_disallowed:
        return None
    present = set(sent_categories) | set(background_categories)
    for (a, b), target in INFERENCE_RULES.items():
        if a in present and b in present:
            return target
    return None


def step_violation(sent_items, step):
    """True iff any sent item fails the ground-truth allow-set, or the
    fixed inference attacker derives a disallowed target."""
    for it in sent_items:
        if not allow_set_ok(it, step.recipient_role, step.purpose, step.recipient_context):
            return True
    sent_cats = [it.category for it in sent_items]
    return inference_violation(sent_cats, step.background_categories,
                                 step.inference_target_disallowed) is not None


# The distractor needs a topic tag; wrap it in a small holder below.
class Distractor:
    def __init__(self, item, topic):
        self.item = item
        self.topic = topic


def run_direct_arm(step):
    sent = list(step.required)
    if step.distractor.topic == step.topic:
        sent.append(step.distractor.item)
    violation = step_violation(sent, step)
    completed = True  # direct never blocks; required items always sent exact
    return {"sent_categories": [it.category for it in sent],
            "violation": violation, "completed": completed}


def run_planning_arm(step):
    """Deliberative-planning arm, PREREG section 2 phases 0-4."""
    # Phase 0 triage: sensitivity tiers are recorded, no separate effect
    # beyond the flow analysis below (deterministic scripted analog).
    # Phase 1 plan: required items only; distractor omitted by construction.
    # Ambiguous third-party purpose -> consult -> decline (fixed rule).
    if step.ambiguous:
        return {"sent_categories": [], "violation": False, "completed": False,
                "verdict": "consult-declined"}
    # Phase 3 flow analysis on the planner's inferred allow-set.
    for it in step.required:
        if not planner_inferred_ok(it, step.recipient_role, step.purpose,
                                   step.recipient_context):
            return {"sent_categories": [], "violation": False, "completed": False,
                    "verdict": "block"}
    planned_cats = [it.category for it in step.required]
    # Phase 2 inference simulation (same fixed rules as the attacker).
    inferred = inference_violation(planned_cats, step.background_categories,
                                     step.inference_target_disallowed)
    if inferred is not None:
        if step.generalization_accepting:
            return {"sent_categories": planned_cats, "violation": False,
                    "completed": True, "verdict": "execute-generalized"}
        return {"sent_categories": [], "violation": False, "completed": False,
                "verdict": "block-inference"}
    # Phase 4 verdict: execute the minimized plan.
    sent = list(step.required)
    violation = step_violation(sent, step)  # hidden-consent traps land here
    return {"sent_categories": planned_cats, "violation": violation,
            "completed": True, "verdict": "execute"}


def generate_sequences(seed=20261102, n_sequences=240):
    """Deterministic synthetic sequences, PREREG section 1."""
    rng = random.Random(seed)
    sequences = []
    for _ in range(n_sequences):
        n_steps = rng.choice([4, 5, 6])
        steps = []
        for _ in range(n_steps):
            topic = rng.choice(TOPICS)
            recipient_role = rng.choice(ROLES)
            recipient_context = rng.choice(CONTEXTS)
            purpose = topic + "_task"
            task_type = "scheduling" if rng.random() < 0.3 else "other"
            # Trap draw: single draw, disjoint intervals (PREREG rates).
            r = rng.random()
            if r < 0.015:
                trap = "hidden-consent"
            elif r < 0.023:
                trap = "conflict"
            elif r < 0.031:
                trap = "ambiguous"
            elif r < 0.061:
                trap = "inference-pair"
            else:
                trap = "none"
            if trap == "inference-pair":
                (a, b), _target = rng.choice(list(INFERENCE_RULES.items()))
                req = Item(b, sensitivity=2, subject="first",
                           origin_context=recipient_context,
                           original_purpose=purpose,
                           authorized_roles=[recipient_role])
                required = [req]
                background = {a}
                inf_dis = True
                ambiguous = False
            else:
                n_req = rng.choice([1, 2])
                required = []
                for _ in range(n_req):
                    cat = rng.choice(NORMAL_CATEGORIES)
                    sens = rng.choice([1, 2, 3])
                    subj = rng.choice(["first", "first", "third"])
                    item = Item(cat, sensitivity=sens, subject=subj,
                                origin_context=recipient_context,
                                original_purpose=purpose,
                                authorized_roles=[recipient_role],
                                consent=True)
                    if trap == "hidden-consent" and subj != "third":
                        item.subject = "third"
                    if trap == "hidden-consent":
                        item.consent = False
                    if trap == "conflict":
                        item.original_purpose = "unrelated_purpose"
                    required.append(item)
                background = set()
                inf_dis = False
                ambiguous = (trap == "ambiguous")
                if ambiguous:
                    # Ambiguous steps are third-party by construction.
                    for it in required:
                        it.subject = "third"
            # Distractor: topic uniform independent of step topic; forced
            # to fail at least one allow-set factor.
            d_topic = rng.choice(TOPICS)
            d_cat = rng.choice(NORMAL_CATEGORIES)
            mode = rng.choice(["role", "purpose", "consent", "crossing"])
            if mode == "role":
                d_roles = [x for x in ROLES if x != recipient_role]
                d_item = Item(d_cat, sensitivity=2, subject="first",
                              origin_context=recipient_context,
                              original_purpose=purpose,
                              authorized_roles=d_roles[:1], consent=True)
            elif mode == "purpose":
                d_item = Item(d_cat, sensitivity=2, subject="first",
                              origin_context=recipient_context,
                              original_purpose="unrelated_purpose",
                              authorized_roles=[recipient_role], consent=True)
            elif mode == "consent":
                d_item = Item(d_cat, sensitivity=2, subject="third",
                              origin_context=recipient_context,
                              original_purpose=purpose,
                              authorized_roles=[recipient_role], consent=False)
            else:  # crossing
                other_ctx = [c for c in CONTEXTS if c != recipient_context]
                d_item = Item(d_cat, sensitivity=3, subject="first",
                              origin_context=other_ctx[0],
                              original_purpose=purpose,
                              authorized_roles=[recipient_role], consent=True)
            steps.append(Step(topic, recipient_role, recipient_context, purpose,
                              task_type, required, Distractor(d_item, d_topic),
                              background, inf_dis, ambiguous))
        sequences.append(steps)
    return sequences


def run_all(sequences):
    """Returns per-sequence paired outcomes for both arms."""
    out = []
    for steps in sequences:
        d_viol = p_viol = False
        d_comp_steps = p_comp_steps = 0
        n_steps = len(steps)
        for st in steps:
            d = run_direct_arm(st)
            p = run_planning_arm(st)
            d_viol = d_viol or d["violation"]
            p_viol = p_viol or p["violation"]
            d_comp_steps += int(d["completed"])
            p_comp_steps += int(p["completed"])
        out.append({
            "n_steps": n_steps,
            "direct_violation": d_viol, "planning_violation": p_viol,
            "direct_completed_steps": d_comp_steps,
            "planning_completed_steps": p_comp_steps,
        })
    return out
