"""
Parser Evaluation Script for AutoGrammar.
Evaluates both the Baseline Parser and the Learned Parser across held-out test datasets:
  - Valid Query Acceptance Rate (Recall on valid queries)
  - Invalid Query Rejection Rate (Specificity on invalid queries)
  - False Acceptance Rate (FAR) and False Rejection Rate (FRR)
  - Parse tree generation success rate
"""

import os
import sys
import json
import pandas as pd
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from compiler.parser import AutoGrammarParser


def evaluate_parser_on_dataset(
    dataset_path: str = "data/test.csv",
    output_json: str = "evaluation/results/parser_test_metrics.json"
) -> Dict[str, Any]:
    print(f"[*] Loading evaluation dataset from {dataset_path}...")
    df = pd.read_csv(dataset_path)

    parser = AutoGrammarParser()
    results = {}

    for grammar_type in ["baseline", "learned"]:
        print(f"[*] Evaluating {grammar_type.upper()} parser on {len(df)} queries...")
        tp, tn, fp, fn = 0, 0, 0, 0
        parse_trees_generated = 0

        for _, row in df.iterrows():
            q_text = row["query_text"]
            is_valid = int(row["validity_label"]) == 1

            parse_res = parser.parse(q_text, grammar_choice=grammar_type)
            accepted = parse_res["success"]

            if accepted and parse_res["tree"] is not None:
                parse_trees_generated += 1

            if is_valid and accepted:
                tp += 1
            elif not is_valid and not accepted:
                tn += 1
            elif not is_valid and accepted:
                fp += 1
            elif is_valid and not accepted:
                fn += 1

        total_valid = tp + fn
        total_invalid = tn + fp
        total = len(df)

        acceptance_rate = tp / total_valid if total_valid > 0 else 0.0
        rejection_rate = tn / total_invalid if total_invalid > 0 else 0.0
        far = fp / total_invalid if total_invalid > 0 else 0.0
        frr = fn / total_valid if total_valid > 0 else 0.0
        accuracy = (tp + tn) / total if total > 0 else 0.0

        results[grammar_type] = {
            "total_queries": total,
            "total_valid": total_valid,
            "total_invalid": total_invalid,
            "true_positive": tp,
            "true_negative": tn,
            "false_positive": fp,
            "false_negative": fn,
            "valid_acceptance_rate": round(acceptance_rate, 4),
            "invalid_rejection_rate": round(rejection_rate, 4),
            "false_acceptance_rate": round(far, 4),
            "false_rejection_rate": round(frr, 4),
            "overall_accuracy": round(accuracy, 4),
            "parse_tree_generation_rate": round(parse_trees_generated / total, 4)
        }

        print(f"\n=== {grammar_type.upper()} Parser Results ===")
        print(f"Accuracy:                {accuracy:.4f}")
        print(f"Valid Acceptance (TPR):  {acceptance_rate:.4f} ({tp}/{total_valid})")
        print(f"Invalid Rejection (TNR): {rejection_rate:.4f} ({tn}/{total_invalid})")
        print(f"False Acceptance (FAR):  {far:.4f} ({fp}/{total_invalid})")
        print(f"False Rejection (FRR):   {frr:.4f} ({fn}/{total_valid})")

    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n[+] Parser test metrics saved to: {output_json}")
    return results


if __name__ == "__main__":
    evaluate_parser_on_dataset()
