"""
Comparative Evaluation and Benchmarking Script for AutoGrammar.
Compares:
  1. Fixed Baseline Grammar Parser
  2. Automatically Inferred Grammar Parser
  3. TF-IDF + Logistic Regression ML Classifier
Outputs:
  - evaluation/results/model_comparison.csv
  - evaluation/results/model_comparison.json
  - Visual charts in evaluation/results/ and report/figures/
"""

import os
import sys
import json
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from evaluation.evaluate_grammar import evaluate_grammar_rules
from evaluation.evaluate_parser import evaluate_parser_on_dataset
from ml.evaluate_classifier import evaluate_classifier_on_test


def run_comparative_evaluation():
    os.makedirs("evaluation/results", exist_ok=True)
    os.makedirs("report/figures", exist_ok=True)

    print("[1/3] Running Grammar Structural Rule Evaluation...")
    grammar_metrics = evaluate_grammar_rules()

    print("\n[2/3] Running Parser Evaluation on Held-Out Test Set...")
    parser_metrics = evaluate_parser_on_dataset("data/test.csv")

    print("\n[3/3] Running ML Baseline Classifier Evaluation on Held-Out Test Set...")
    ml_metrics = evaluate_classifier_on_test()

    comparison_data = [
        {
            "System / Paradigm": "Fixed Baseline Grammar (Compiler Reference)",
            "Technique": "Manually Authored EBNF + Earley/LALR Parser",
            "Accuracy": parser_metrics["baseline"]["overall_accuracy"],
            "Valid Acceptance (Recall)": parser_metrics["baseline"]["valid_acceptance_rate"],
            "Invalid Rejection (Specificity)": parser_metrics["baseline"]["invalid_rejection_rate"],
            "False Acceptance (FAR)": parser_metrics["baseline"]["false_acceptance_rate"],
            "False Rejection (FRR)": parser_metrics["baseline"]["false_rejection_rate"],
            "Grammar Rule Precision": 1.0000,
            "Grammar Rule Recall": 1.0000,
            "Generates Parse Tree": "Yes (Deterministic)"
        },
        {
            "System / Paradigm": "AutoGrammar Learned Grammar (Induction)",
            "Technique": "Structural Pattern Mining + Dynamic EBNF Synthesis",
            "Accuracy": parser_metrics["learned"]["overall_accuracy"],
            "Valid Acceptance (Recall)": parser_metrics["learned"]["valid_acceptance_rate"],
            "Invalid Rejection (Specificity)": parser_metrics["learned"]["invalid_rejection_rate"],
            "False Acceptance (FAR)": parser_metrics["learned"]["false_acceptance_rate"],
            "False Rejection (FRR)": parser_metrics["learned"]["false_rejection_rate"],
            "Grammar Rule Precision": grammar_metrics["production_precision"],
            "Grammar Rule Recall": grammar_metrics["production_recall"],
            "Generates Parse Tree": "Yes (Deterministic)"
        },
        {
            "System / Paradigm": "ML Statistical Baseline Classifier",
            "Technique": "TF-IDF (1-3 n-grams) + Logistic Regression",
            "Accuracy": ml_metrics["accuracy"],
            "Valid Acceptance (Recall)": ml_metrics["recall"],
            "Invalid Rejection (Specificity)": round(ml_metrics["confusion_matrix"]["true_negative"] / ml_metrics["invalid_count"], 4),
            "False Acceptance (FAR)": round(ml_metrics["confusion_matrix"]["false_positive"] / ml_metrics["invalid_count"], 4),
            "False Rejection (FRR)": round(ml_metrics["confusion_matrix"]["false_negative"] / ml_metrics["valid_count"], 4),
            "Grammar Rule Precision": "N/A (Black-box)",
            "Grammar Rule Recall": "N/A (Black-box)",
            "Generates Parse Tree": "No"
        }
    ]

    comp_df = pd.DataFrame(comparison_data)
    csv_path = "evaluation/results/model_comparison.csv"
    comp_df.to_csv(csv_path, index=False)
    print(f"\n[+] Saved comparative summary table to: {csv_path}")

    json_path = "evaluation/results/model_comparison.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(comparison_data, f, indent=2)

    # Generate Performance Bar Chart
    fig, ax = plt.subplots(figsize=(10, 5))
    systems = ["Baseline Grammar", "Learned Grammar", "ML Classifier"]
    accuracies = [
        parser_metrics["baseline"]["overall_accuracy"] * 100,
        parser_metrics["learned"]["overall_accuracy"] * 100,
        ml_metrics["accuracy"] * 100
    ]
    recalls = [
        parser_metrics["baseline"]["valid_acceptance_rate"] * 100,
        parser_metrics["learned"]["valid_acceptance_rate"] * 100,
        ml_metrics["recall"] * 100
    ]

    x = range(len(systems))
    width = 0.35

    ax.bar([p - width/2 for p in x], accuracies, width, label='Overall Accuracy (%)', color='#2563eb')
    ax.bar([p + width/2 for p in x], recalls, width, label='Valid Acceptance / Recall (%)', color='#10b981')

    ax.set_ylabel('Percentage (%)')
    ax.set_title('AutoGrammar Experimental Comparison: Baseline vs. Learned vs. ML')
    ax.set_xticks(list(x))
    ax.set_xticklabels(systems)
    ax.set_ylim(0, 110)
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    for i in x:
        ax.annotate(f"{accuracies[i]:.1f}%", (i - width/2, accuracies[i] + 2), ha='center', fontsize=9, fontweight='bold')
        ax.annotate(f"{recalls[i]:.1f}%", (i + width/2, recalls[i] + 2), ha='center', fontsize=9, fontweight='bold')

    plt.tight_layout()
    chart_path1 = "evaluation/results/metrics_comparison.png"
    chart_path2 = "report/figures/metrics_comparison.png"
    plt.savefig(chart_path1, dpi=300)
    plt.savefig(chart_path2, dpi=300)
    plt.close()
    print(f"[+] Saved evaluation comparison charts to: {chart_path1} and {chart_path2}")

    return comp_df


if __name__ == "__main__":
    run_comparative_evaluation()
