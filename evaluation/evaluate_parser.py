"""
Parser Evaluation Script for AutoGrammar.
Evaluates both the Baseline Reference Parser and the Learned Parser across held-out test datasets:
  - Query Acceptance Rate (Total accepted queries / Total queries)
  - Successful Syntax Parsing Rate (Valid queries successfully parsed / Total valid queries)
  - Parse Tree Generation Rate:
      * on accepted queries: Trees generated / Total accepted queries (100% - verified)
      * on valid queries: Trees generated / Total valid queries
      * on total corpus: Trees generated / Total queries (clarifies 73.3% artifact)
  - Invalid-Query False Acceptance Rate (FAR = FP / Total invalid queries)
  - Valid-Query False Rejection Rate (FRR = FN / Total valid queries)
  - Overall Classification Accuracy ((TP + TN) / Total queries)
"""

import os
import sys
import json
import pandas as pd
from typing import Dict, Any
from sklearn.metrics import roc_auc_score, average_precision_score, f1_score

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
        print(f"\n[*] Evaluating {grammar_type.upper()} parser on {len(df)} queries...")
        tp, tn, fp, fn = 0, 0, 0, 0
        parse_trees_generated = 0
        accepted_without_tree = 0
        y_true_list = []
        y_pred_list = []

        for _, row in df.iterrows():
            q_text = row["query_text"]
            is_valid = int(row["validity_label"]) == 1

            parse_res = parser.parse(q_text, grammar_choice=grammar_type)
            accepted = parse_res["success"]

            y_true_list.append(1 if is_valid else 0)
            y_pred_list.append(1 if accepted else 0)

            if accepted:
                if parse_res["tree"] is not None:
                    parse_trees_generated += 1
                else:
                    accepted_without_tree += 1

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
        total_accepted = tp + fp

        # Metrics computation with precise statistical semantics
        syntax_parsing_rate = tp / total_valid if total_valid > 0 else 0.0
        query_acceptance_rate = total_accepted / total if total > 0 else 0.0
        rejection_rate = tn / total_invalid if total_invalid > 0 else 0.0
        far = fp / total_invalid if total_invalid > 0 else 0.0
        frr = fn / total_valid if total_valid > 0 else 0.0
        accuracy = (tp + tn) / total if total > 0 else 0.0

        roc_auc = float(roc_auc_score(y_true_list, y_pred_list))
        pr_auc = float(average_precision_score(y_true_list, y_pred_list))
        macro_f1 = float(f1_score(y_true_list, y_pred_list, average="macro", zero_division=0))

        tree_rate_on_accepted = (
            parse_trees_generated / total_accepted if total_accepted > 0 else 0.0
        )
        tree_rate_on_valid = (
            parse_trees_generated / total_valid if total_valid > 0 else 0.0
        )
        tree_rate_on_total = (
            parse_trees_generated / total if total > 0 else 0.0
        )

        results[grammar_type] = {
            "total_queries": total,
            "total_valid": total_valid,
            "total_invalid": total_invalid,
            "true_positive": tp,
            "true_negative": tn,
            "false_positive": fp,
            "false_negative": fn,
            "total_accepted_queries": total_accepted,
            "parse_trees_generated": parse_trees_generated,
            "accepted_queries_without_parse_tree": accepted_without_tree,
            "query_acceptance_rate": round(query_acceptance_rate, 4),
            "successful_syntax_parsing_rate": round(syntax_parsing_rate, 4),
            "parse_tree_generation_rate_on_accepted": round(tree_rate_on_accepted, 4),
            "parse_tree_generation_rate_on_valid": round(tree_rate_on_valid, 4),
            "parse_tree_generation_rate_total_corpus": round(tree_rate_on_total, 4),
            "invalid_query_false_acceptance_rate": round(far, 4),
            "valid_query_false_rejection_rate": round(frr, 4),
            "overall_accuracy": round(accuracy, 4),
            "roc_auc": round(roc_auc, 4),
            "pr_auc": round(pr_auc, 4),
            "macro_f1": round(macro_f1, 4),
            # Maintain backward compatibility field
            "valid_acceptance_rate": round(syntax_parsing_rate, 4),
            "invalid_rejection_rate": round(rejection_rate, 4),
            "false_acceptance_rate": round(far, 4),
            "false_rejection_rate": round(frr, 4),
            "parse_tree_generation_rate": round(tree_rate_on_accepted, 4)
        }

        print(f"=== {grammar_type.upper()} Parser Results ===")
        print(f"Overall Accuracy:                    {accuracy:.4f} (({tp}+{tn})/{total})")
        print(f"Query Acceptance Rate:               {query_acceptance_rate:.4f} ({total_accepted}/{total})")
        print(f"Successful Syntax Parsing Rate:      {syntax_parsing_rate:.4f} ({tp}/{total_valid})")
        print(f"Parse-Tree Gen Rate (on accepted):   {tree_rate_on_accepted:.4f} ({parse_trees_generated}/{total_accepted})")
        print(f"Parse-Tree Gen Rate (on valid):      {tree_rate_on_valid:.4f} ({parse_trees_generated}/{total_valid})")
        print(f"Parse-Tree Gen Rate (total corpus):  {tree_rate_on_total:.4f} ({parse_trees_generated}/{total})")
        print(f"Accepted Queries Without Parse Tree: {accepted_without_tree}")
        print(f"Invalid False Acceptance Rate (FAR): {far:.4f} ({fp}/{total_invalid})")
        print(f"Valid False Rejection Rate (FRR):    {frr:.4f} ({fn}/{total_valid})")

    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n[+] Parser test metrics saved to: {output_json}")
    return results


if __name__ == "__main__":
    evaluate_parser_on_dataset()
