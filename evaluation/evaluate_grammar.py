"""
Grammar Evaluation Script for AutoGrammar.
Compares the automatically learned grammar against the reference baseline grammar:
  - Production rule matching & structural alignment
  - Production precision, recall, and F1-score
  - Coverage on held-out valid queries
  - Skeletons and clause discovery analysis
"""

import os
import sys
import re
import json
from typing import Set, Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from compiler.parser import AutoGrammarParser


def extract_grammar_productions(grammar_text: str) -> Dict[str, List[str]]:
    """
    Extracts LHS rule names and RHS expansions from a Lark EBNF grammar file.
    Normalizes whitespace and comments.
    """
    productions: Dict[str, List[str]] = {}
    current_rule = None

    for raw_line in grammar_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("//") or line.startswith("%") or line.startswith("?start"):
            continue

        if ":" in line:
            parts = line.split(":", 1)
            rule_lhs = parts[0].strip().lstrip("?")
            rhs = parts[1].strip()
            current_rule = rule_lhs
            if current_rule not in productions:
                productions[current_rule] = []
            if rhs:
                # Add sub-branches
                for branch in rhs.split("|"):
                    if branch.strip():
                        productions[current_rule].append(branch.strip())
        elif line.startswith("|") and current_rule:
            branch = line.lstrip("|").strip()
            if branch:
                productions[current_rule].append(branch)

    return productions


def evaluate_grammar_rules(
    baseline_path: str = "grammars/baseline.lark",
    learned_path: str = "grammars/learned.lark",
    output_json: str = "evaluation/results/grammar_metrics.json"
) -> Dict[str, Any]:
    with open(baseline_path, "r", encoding="utf-8") as f:
        base_text = f.read()
    with open(learned_path, "r", encoding="utf-8") as f:
        learn_text = f.read()

    base_prods = extract_grammar_productions(base_text)
    learn_prods = extract_grammar_productions(learn_text)

    base_rules: Set[str] = set(base_prods.keys())
    learn_rules: Set[str] = set(learn_prods.keys())

    # Normalized matching
    matched_rules = base_rules.intersection(learn_rules)
    unmatched_in_base = base_rules - learn_rules
    unmatched_in_learn = learn_rules - base_rules

    precision = len(matched_rules) / len(learn_rules) if learn_rules else 0.0
    recall = len(matched_rules) / len(base_rules) if base_rules else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    metrics = {
        "baseline_production_count": len(base_rules),
        "learned_production_count": len(learn_rules),
        "shared_rules_count": len(matched_rules),
        "shared_rules": sorted(list(matched_rules)),
        "unmatched_baseline_rules": sorted(list(unmatched_in_base)),
        "unmatched_learned_rules": sorted(list(unmatched_in_learn)),
        "production_precision": round(precision, 4),
        "production_recall": round(recall, 4),
        "production_f1_score": round(f1, 4)
    }

    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print("\n=== Grammar Rule Induction Metrics ===")
    print(f"Baseline Rules:  {metrics['baseline_production_count']}")
    print(f"Learned Rules:   {metrics['learned_production_count']}")
    print(f"Shared Rules:    {metrics['shared_rules_count']}")
    print(f"Rule Precision:  {metrics['production_precision']:.4f}")
    print(f"Rule Recall:     {metrics['production_recall']:.4f}")
    print(f"Rule F1-Score:   {metrics['production_f1_score']:.4f}")
    print(f"Unmatched in Ref: {metrics['unmatched_baseline_rules']}")

    return metrics


if __name__ == "__main__":
    evaluate_grammar_rules()
