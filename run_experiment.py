"""Run the pre-registered privacyflow experiment and write results.json.

No timestamps or randomness beyond the locked seeds enter results.json,
so a rerun is byte-identical (G0 determinism check).
"""
import hashlib
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from privacyflow.core import INFERENCE_RULES, generate_sequences, run_all

# G3c integrity assertion: implementation rule table must match PREREG sec 4.
EXPECTED_RULES = {
    ("clinic_visit", "prescription_pickup"): "diagnosis",
    ("salary_deposit", "luxury_purchase"): "income_band",
    ("home_address", "travel_booking"): "home_empty_dates",
    ("manager_email", "hr_meeting"): "employment_action",
    ("school_name", "pickup_schedule"): "child_routine",
}
assert INFERENCE_RULES == EXPECTED_RULES, "inference rule set differs from PREREG sec 4"


def summarize(per_seq):
    n = len(per_seq)
    total_steps = sum(s["n_steps"] for s in per_seq)
    d_priv_pass = sum(1 for s in per_seq if not s["direct_violation"]) / n
    p_priv_pass = sum(1 for s in per_seq if not s["planning_violation"]) / n
    d_step_comp = sum(s["direct_completed_steps"] for s in per_seq) / total_steps
    p_step_comp = sum(s["planning_completed_steps"] for s in per_seq) / total_steps
    d_seq_comp = sum(1 for s in per_seq
                     if s["direct_completed_steps"] == s["n_steps"]) / n
    p_seq_comp = sum(1 for s in per_seq
                     if s["planning_completed_steps"] == s["n_steps"]) / n
    return {
        "n_sequences": n,
        "n_steps": total_steps,
        "direct_sequence_violation_rate": round(1 - d_priv_pass, 6),
        "planning_sequence_violation_rate": round(1 - p_priv_pass, 6),
        "direct_sequence_privacy_pass_rate": round(d_priv_pass, 6),
        "planning_sequence_privacy_pass_rate": round(p_priv_pass, 6),
        "privacy_pass_improvement_pp": round((p_priv_pass - d_priv_pass) * 100, 4),
        "direct_step_completion_rate": round(d_step_comp, 6),
        "planning_step_completion_rate": round(p_step_comp, 6),
        "step_completion_loss_pp": round((d_step_comp - p_step_comp) * 100, 4),
        "direct_sequence_completion_rate": round(d_seq_comp, 6),
        "planning_sequence_completion_rate": round(p_seq_comp, 6),
    }


def paired_bootstrap(per_seq, n_resamples=2000, seed=777):
    """Paired bootstrap over sequences; returns percentile 95% CIs."""
    rng = random.Random(seed)
    n = len(per_seq)
    diffs_priv, diffs_loss, viol_rates = [], [], []
    for _ in range(n_resamples):
        sample = [per_seq[rng.randrange(n)] for _ in range(n)]
        s = summarize(sample)
        diffs_priv.append(s["privacy_pass_improvement_pp"])
        diffs_loss.append(s["step_completion_loss_pp"])
        viol_rates.append(s["direct_sequence_violation_rate"] * 100)
    def ci(vals):
        v = sorted(vals)
        lo = v[int(0.025 * len(v))]
        hi = v[int(0.975 * len(v)) - 1]
        return [round(lo, 4), round(hi, 4)]
    return {
        "direct_sequence_violation_rate_pct_ci95": ci(viol_rates),
        "privacy_pass_improvement_pp_ci95": ci(diffs_priv),
        "step_completion_loss_pp_ci95": ci(diffs_loss),
    }


def main():
    out_dir = Path(__file__).resolve().parent / "results"
    out_dir.mkdir(exist_ok=True)
    sequences = generate_sequences(seed=20261102, n_sequences=240)
    per_seq = run_all(sequences)
    results = summarize(per_seq)
    results["bootstrap"] = paired_bootstrap(per_seq)
    results["seeds"] = {"generator": 20261102, "bootstrap": 777,
                        "bootstrap_resamples": 2000}
    results["arms"] = ["execute-directly", "deliberative-planning"]
    text = json.dumps(results, indent=2, sort_keys=True) + "\n"
    (out_dir / "results.json").write_text(text)
    digest = hashlib.sha256(text.encode()).hexdigest()
    (out_dir / "results.sha256").write_text(digest + "\n")
    print(json.dumps(results, indent=2, sort_keys=True))
    print("sha256:", digest)


if __name__ == "__main__":
    main()
