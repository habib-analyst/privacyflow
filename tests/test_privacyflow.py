"""Unit tests for privacyflow (G0). No LLM, no network, deterministic."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from privacyflow.core import (
    INFERENCE_RULES, Distractor, Item, Step, allow_set_ok, generate_sequences,
    inference_violation, planner_inferred_ok, run_all, run_direct_arm,
    run_planning_arm,
)


def mk_step(**kw):
    base = dict(topic="work", recipient_role="manager",
                recipient_context="work", purpose="work_task",
                task_type="other", required=[], distractor=None,
                background_categories=set())
    base.update(kw)
    if base["distractor"] is None:
        base["distractor"] = Distractor(
            Item("project_note", 1, "first", "work", "work_task", ["manager"]),
            "health")
    return Step(**base)


def req_item(**kw):
    d = dict(category="project_note", sensitivity=1, subject="first",
             origin_context="work", original_purpose="work_task",
             authorized_roles=["manager"], consent=True)
    d.update(kw)
    return Item(**d)


class TestAllowSet(unittest.TestCase):
    def test_allowed_passes(self):
        self.assertTrue(allow_set_ok(req_item(), "manager", "work_task", "work"))

    def test_each_failing_factor(self):
        self.assertFalse(allow_set_ok(req_item(authorized_roles=["vendor"]),
                                      "manager", "work_task", "work"))
        self.assertFalse(allow_set_ok(req_item(original_purpose="other"),
                                      "manager", "work_task", "work"))
        self.assertFalse(allow_set_ok(req_item(subject="third", consent=False),
                                      "manager", "work_task", "work"))
        self.assertFalse(allow_set_ok(req_item(sensitivity=3, origin_context="home"),
                                      "manager", "work_task", "work"))

    def test_planner_cannot_see_consent(self):
        # Hidden-consent item looks allowed to the planner but violates truth.
        it = req_item(subject="third", consent=False)
        self.assertTrue(planner_inferred_ok(it, "manager", "work_task", "work"))
        self.assertFalse(allow_set_ok(it, "manager", "work_task", "work"))


class TestInference(unittest.TestCase):
    def test_pair_fires_only_with_both(self):
        self.assertEqual(
            inference_violation(["clinic_visit"], set(), True), None)
        self.assertEqual(
            inference_violation(["clinic_visit", "prescription_pickup"], set(), True),
            "diagnosis")
        self.assertEqual(
            inference_violation(["prescription_pickup"], {"clinic_visit"}, True),
            "diagnosis")
        self.assertEqual(
            inference_violation(["clinic_visit", "prescription_pickup"], set(), False),
            None)

    def test_rule_table_matches_prereg(self):
        self.assertEqual(INFERENCE_RULES, {
            ("clinic_visit", "prescription_pickup"): "diagnosis",
            ("salary_deposit", "luxury_purchase"): "income_band",
            ("home_address", "travel_booking"): "home_empty_dates",
            ("manager_email", "hr_meeting"): "employment_action",
            ("school_name", "pickup_schedule"): "child_routine",
        })


class TestArms(unittest.TestCase):
    def test_direct_sends_topic_matching_distractor_only(self):
        st = mk_step(required=[req_item()],
                     distractor=Distractor(req_item(category="dietary_note"), "work"))
        self.assertEqual(len(run_direct_arm(st)["sent_categories"]), 2)
        st2 = mk_step(required=[req_item()],
                      distractor=Distractor(req_item(category="dietary_note"), "health"))
        self.assertEqual(len(run_direct_arm(st2)["sent_categories"]), 1)

    def test_planning_omits_distractor_and_blocks_conflict(self):
        st = mk_step(required=[req_item()])
        out = run_planning_arm(st)
        self.assertTrue(out["completed"] and not out["violation"])
        bad = req_item(original_purpose="unrelated_purpose")
        out2 = run_planning_arm(mk_step(required=[bad]))
        self.assertFalse(out2["completed"]) and self.assertFalse(out2["violation"])

    def test_planning_consult_declines_ambiguous(self):
        st = mk_step(required=[req_item(subject="third")], ambiguous=True)
        out = run_planning_arm(st)
        self.assertFalse(out["completed"])

    def test_planning_generalizes_scheduling_inference(self):
        req = req_item(category="prescription_pickup")
        st = mk_step(required=[req], task_type="scheduling",
                     background_categories={"clinic_visit"},
                     inference_target_disallowed=True)
        out = run_planning_arm(st)
        self.assertTrue(out["completed"] and not out["violation"])
        st2 = mk_step(required=[req], task_type="other",
                      background_categories={"clinic_visit"},
                      inference_target_disallowed=True)
        out2 = run_planning_arm(st2)
        self.assertFalse(out2["completed"] and not out2["violation"])

    def test_determinism_of_generation(self):
        a = run_all(generate_sequences())
        b = run_all(generate_sequences())
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
