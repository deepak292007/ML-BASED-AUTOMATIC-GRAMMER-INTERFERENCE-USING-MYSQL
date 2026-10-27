"""
Learning Curve Generation for AutoGrammar Induction Engine.
Measures the effect of training corpus diversity (template coverage) on generalization:
Evaluates grammar induction on 10%, 25%, 50%, 75%, and 100% of training templates.
Saves each induced grammar artifact for reproducible rule inspection and comparison.
Outputs:
  - evaluation/results/grammars/learning_curve_<pct>pct.lark
  - evaluation/results/learning_curve.json
  - evaluation/results/learning_curve.csv
  - evaluation/results/learning_curve.png
"""

import os
import sys
import json
import random
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import matplotlib.pyplot as plt
from lark import Lark

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from compiler.grammar_induction import GrammarInductionEngine


def compute_learning_curve(
    train_path: str = "data/train.csv",
    test_path: str = "data/test.csv",
    output_dir: str = "evaluation/results",
    fractions: List[float] = None,
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Computes accuracy, TPR, TNR, FAR, and FRR across subsets of training templates.
    Saves each induced candidate grammar artifact to allow structural comparison.
    """
    if fractions is None:
        fractions = [0.10, 0.25, 0.50, 0.75, 1.00]

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    grammars_dir = out_path / "grammars"
    grammars_dir.mkdir(parents=True, exist_ok=True)

    print(f"[*] Loading datasets: train={train_path}, test={test_path}")
    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)

    # Valid training templates
    valid_train_df = train_df[train_df["validity_label"] == 1]
    unique_templates = sorted(valid_train_df["template_id"].unique())
    total_templates = len(unique_templates)

    # Deterministic shuffle with seed
    rng = random.Random(seed)
    shuffled_templates = list(unique_templates)
    rng.shuffle(shuffled_templates)

    total_valid = int((test_df["validity_label"] == 1).sum())
    total_invalid = int((test_df["validity_label"] == 0).sum())
    total_test = len(test_df)

    curve_results = []
    previous_ebnf = None

    for frac in fractions:
        num_templates = max(1, int(round(total_templates * frac)))
        selected_templates = set(shuffled_templates[:num_templates])
        sub_train_queries = valid_train_df[valid_train_df["template_id"].isin(selected_templates)]["query_text"].tolist()

        pct_label = int(round(frac * 100))
        print(f"\n[*] Evaluating at {pct_label}% templates ({num_templates}/{total_templates} templates, {len(sub_train_queries)} valid queries)...")

        engine = GrammarInductionEngine()
        train_stats = engine.train_on_queries(sub_train_queries)
        candidate_ebnf = engine.generate_candidate_ebnf()

        # Save the exact induced grammar file for this fraction
        grammar_filename = f"learning_curve_{pct_label}pct.lark"
        grammar_file_path = grammars_dir / grammar_filename
        with open(grammar_file_path, "w", encoding="utf-8") as f:
            f.write(candidate_ebnf)

        # Count production rules in generated grammar
        rule_lines = [
            l.split(":")[0].strip().lstrip("?")
            for l in candidate_ebnf.splitlines()
            if ":" in l and not l.strip().startswith("//") and not l.strip().startswith("%")
        ]
        rule_count = len(set(rule_lines))

        # Check grammar equivalence with previous fraction
        is_same_as_prev = False
        if previous_ebnf is not None:
            # Compare ignoring dynamic timestamp comments
            lines_prev = [l for l in previous_ebnf.splitlines() if not l.startswith("// Inferred at:")]
            lines_curr = [l for l in candidate_ebnf.splitlines() if not l.startswith("// Inferred at:")]
            is_same_as_prev = (lines_prev == lines_curr)

        previous_ebnf = candidate_ebnf

        is_valid, err = engine.validate_grammar(candidate_ebnf)
        if not is_valid:
            print(f"    [!] Generated grammar has syntax error: {err}")
            continue

        lark_parser = Lark(candidate_ebnf, start="start", parser="earley", ambiguity="resolve")

        tp, tn, fp, fn = 0, 0, 0, 0

        for _, row in test_df.iterrows():
            q_text = row["query_text"]
            is_valid_gt = int(row["validity_label"]) == 1

            try:
                lark_parser.parse(q_text)
                accepted = True
            except Exception:
                accepted = False

            if is_valid_gt and accepted:
                tp += 1
            elif not is_valid_gt and not accepted:
                tn += 1
            elif not is_valid_gt and accepted:
                fp += 1
            elif is_valid_gt and not accepted:
                fn += 1

        accuracy = (tp + tn) / total_test if total_test > 0 else 0.0
        tpr = tp / total_valid if total_valid > 0 else 0.0
        tnr = tn / total_invalid if total_invalid > 0 else 0.0
        far = fp / total_invalid if total_invalid > 0 else 0.0
        frr = fn / total_valid if total_valid > 0 else 0.0

        pt_data = {
            "template_percentage": pct_label,
            "fraction": frac,
            "template_count": num_templates,
            "training_query_count": len(sub_train_queries),
            "grammar_file": str(grammar_file_path),
            "grammar_char_length": len(candidate_ebnf),
            "grammar_rule_count": rule_count,
            "discovered_statement_types": sorted(list(engine.observed_statement_types)),
            "observed_clauses": sorted(list(engine.observed_clauses)),
            "identical_to_previous_grammar": is_same_as_prev,
            "accuracy": round(accuracy, 4),
            "tpr": round(tpr, 4),
            "tnr": round(tnr, 4),
            "far": round(far, 4),
            "frr": round(frr, 4),
            "tp": tp,
            "tn": tn,
            "fp": fp,
            "fn": fn
        }
        curve_results.append(pt_data)
        print(f"    Rules: {rule_count} | GramChars: {len(candidate_ebnf)} | Identical to Prev: {is_same_as_prev}")
        print(f"    Accuracy: {accuracy:.4f} | TPR: {tpr:.4f} | FRR: {frr:.4f} | FAR: {far:.4f}")

    # Save JSON and CSV
    json_file = out_path / "learning_curve.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(curve_results, f, indent=2)
    print(f"\n[+] Saved learning curve JSON to: {json_file}")

    csv_file = out_path / "learning_curve.csv"
    pd.DataFrame(curve_results).to_csv(csv_file, index=False)
    print(f"[+] Saved learning curve CSV to: {csv_file}")

    # Generate Plot
    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=150)
    pcts = [d["template_percentage"] for d in curve_results]
    accs = [d["accuracy"] * 100 for d in curve_results]
    frrs = [d["frr"] * 100 for d in curve_results]

    ax.plot(pcts, accs, marker="o", linewidth=2.5, color="#0284c7", label="Overall Accuracy (%)")
    ax.plot(pcts, frrs, marker="s", linewidth=2.5, color="#ef4444", linestyle="--", label="False Rejection Rate (FRR %)")

    ax.set_title("Grammar Induction Learning Curve vs Training Diversity", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("% of Training Templates Included", fontsize=11, fontweight="semibold")
    ax.set_ylabel("Rate (%)", fontsize=11, fontweight="semibold")
    ax.set_xticks(pcts)
    ax.set_ylim(-2, 105)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(frameon=True, facecolor="#f8fafc", edgecolor="#cbd5e1", loc="center right")

    for x, y in zip(pcts, accs):
        ax.annotate(f"{y:.1f}%", (x, y), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=9, fontweight="bold", color="#0369a1")
    for x, y in zip(pcts, frrs):
        ax.annotate(f"{y:.1f}%", (x, y), textcoords="offset points", xytext=(0, -14), ha="center", fontsize=9, fontweight="bold", color="#b91c1c")

    plt.tight_layout()
    png_file = out_path / "learning_curve.png"
    plt.savefig(png_file)
    plt.close()
    print(f"[+] Saved learning curve plot to: {png_file}")

    return curve_results


if __name__ == "__main__":
    compute_learning_curve()
