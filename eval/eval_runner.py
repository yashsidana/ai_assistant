"""
Evaluation script to benchmark AI Requirements Assistant outputs against gold standard definitions.
Calculates Precision, Recall, F1 score, and guardrail detection metrics.
"""

import json
import os
import sys
from pathlib import Path

# Ensure root dir is in path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from core.pipeline import run


def evaluate_sample(transcript_path: Path, gold_path: Path) -> dict:
    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = f.read()

    with open(gold_path, "r", encoding="utf-8") as f:
        gold = json.load(f)

    print(f"\n--- Evaluating {transcript_path.name} ---")
    data, report = run(transcript)

    expected_reqs = gold["expected_requirements"]
    expected_acts = gold["expected_action_items"]
    total_expected = len(expected_reqs) + len(expected_acts)

    found_reqs = data.requirements
    found_acts = data.action_items
    total_found = len(found_reqs) + len(found_acts)

    # Count correct requirements by checking if expected quote fragment is present
    correct_reqs = 0
    for ereq in expected_reqs:
        frag = ereq["expected_quote_fragment"].lower()
        if any(frag in r.source_quote.lower() or frag in r.description.lower() for r in found_reqs):
            correct_reqs += 1

    # Count correct action items
    correct_acts = 0
    for eact in expected_acts:
        frag = eact["task_fragment"].lower()
        if any(frag in a.task.lower() or frag in a.source_quote.lower() for a in found_acts):
            correct_acts += 1

    total_correct = correct_reqs + correct_acts
    recall = total_correct / total_expected if total_expected > 0 else 0.0
    precision = total_correct / total_found if total_found > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    print(f"Expected: {total_expected} | Found: {total_found} | Correct: {total_correct}")
    print(f"Recall: {recall:.2%} | Precision: {precision:.2%} | F1: {f1:.3f}")
    print(f"Unsupported quotes flagged: {len(report['unsupported_quotes'])}")
    print(f"Vague words flagged: {len(report['vague_words'])}")
    print(f"Completeness warnings: {len(report['gaps'])}")

    return {
        "sample": transcript_path.name,
        "expected": total_expected,
        "found": total_found,
        "correct": total_correct,
        "recall": recall,
        "precision": precision,
        "f1": f1,
        "unsupported_quotes": len(report["unsupported_quotes"]),
        "vague_flags": len(report["vague_words"]),
        "gaps": len(report["gaps"]),
    }


def main():
    samples_dir = ROOT_DIR / "samples"
    eval_dir = ROOT_DIR / "eval"

    sample_gold_pairs = [
        ("route_app_call.txt", "gold_route_app.json"),
        ("van_sales_sync_email.txt", "gold_van_sales.json"),
        ("trade_promotion_call.txt", "gold_trade_promo.json"),
        ("outlet_survey_call.txt", "gold_outlet_survey.json"),
        ("distributor_claims.txt", "gold_distributor_claims.json"),
        ("field_order_capture.txt", "gold_field_order.json"),
    ]

    results = []
    for s_file, g_file in sample_gold_pairs:
        s_path = samples_dir / s_file
        g_path = eval_dir / g_file
        if s_path.exists() and g_path.exists():
            res = evaluate_sample(s_path, g_path)
            results.append(res)

    print("\n================ BENCHMARK SUMMARY ================")
    tot_exp = sum(r["expected"] for r in results)
    tot_found = sum(r["found"] for r in results)
    tot_cor = sum(r["correct"] for r in results)
    avg_rec = tot_cor / tot_exp if tot_exp else 0
    avg_prec = tot_cor / tot_found if tot_found else 0
    overall_f1 = 2 * (avg_prec * avg_rec) / (avg_prec + avg_rec) if (avg_prec + avg_rec) else 0

    print(f"Total Evaluated: {len(results)} transcripts")
    print(f"Overall Recall:    {avg_rec:.1%}")
    print(f"Overall Precision: {avg_prec:.1%}")
    print(f"Overall F1 Score:  {overall_f1:.3f}")


if __name__ == "__main__":
    main()

