"""
Model Evaluation Script for AutoGrammar Validity Classifiers.
Evaluates trained models on the held-out test set (data/test.csv):
  1. Primary Model (Linear SVM with Structural Features)
  2. Baseline Model (Raw TF-IDF + Logistic Regression)
  3. Improved Logistic Regression (Structural Features)
  4. Majority-Class Baseline (Always predicts Valid / 1)
Reports comprehensive metrics:
  - Accuracy
  - Precision and Recall for both classes (Valid and Invalid)
  - Macro F1 and Weighted F1
  - ROC-AUC
  - PR-AUC (Average Precision)
  - Confusion Matrix (TN, FP, FN, TP)
  - False Acceptance Rate (FAR = FP / Invalid Count)
  - False Rejection Rate (FRR = FN / Valid Count)
Saves results to JSON in evaluation/results/.
"""

import os
import sys
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, roc_auc_score, average_precision_score,
    classification_report
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml.preprocess import (
    extract_features_and_labels,
    SQLSyntaxAbstractor,
    SQLStructuralFeatureExtractor
)
from ml.train_classifier import LinearSVMWithProba


def compute_comprehensive_metrics(y_true, y_pred, y_proba, model_name: str) -> dict:
    """Computes all required validation and diagnostic metrics for binary SQL classification."""
    total_samples = len(y_true)
    valid_count = int((y_true == 1).sum())
    invalid_count = int((y_true == 0).sum())

    acc = float(accuracy_score(y_true, y_pred))
    prec_1 = float(precision_score(y_true, y_pred, pos_label=1, zero_division=0))
    rec_1 = float(recall_score(y_true, y_pred, pos_label=1, zero_division=0))
    f1_1 = float(f1_score(y_true, y_pred, pos_label=1, zero_division=0))

    prec_0 = float(precision_score(y_true, y_pred, pos_label=0, zero_division=0))
    rec_0 = float(recall_score(y_true, y_pred, pos_label=0, zero_division=0))
    f1_0 = float(f1_score(y_true, y_pred, pos_label=0, zero_division=0))

    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))

    if y_proba is not None:
        try:
            roc_auc = float(roc_auc_score(y_true, y_proba))
        except Exception:
            roc_auc = 0.5
        try:
            pr_auc = float(average_precision_score(y_true, y_proba))
        except Exception:
            pr_auc = valid_count / total_samples
    else:
        roc_auc = 0.5
        pr_auc = valid_count / total_samples

    cm = confusion_matrix(y_true, y_pred).tolist()
    tn, fp = cm[0][0], cm[0][1]
    fn, tp = cm[1][0], cm[1][1]

    far = float(fp / invalid_count) if invalid_count > 0 else 0.0
    frr = float(fn / valid_count) if valid_count > 0 else 0.0

    report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)

    return {
        "model_type": model_name,
        "test_sample_size": total_samples,
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "accuracy": acc,
        "precision": prec_1,
        "recall": rec_1,
        "f1_score": f1_1,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "valid_class_metrics": {
            "precision": prec_1,
            "recall": rec_1,
            "f1_score": f1_1
        },
        "invalid_class_metrics": {
            "precision": prec_0,
            "recall": rec_0,
            "f1_score": f1_0
        },
        "false_acceptance_rate": far,
        "false_rejection_rate": frr,
        "confusion_matrix": {
            "true_negative": tn,
            "false_positive": fp,
            "false_negative": fn,
            "true_positive": tp
        },
        "classification_report": report
    }


def evaluate_classifier_on_test(
    test_path: str = "data/test.csv",
    model_dir: str = "ml/saved_models",
    output_json: str = "evaluation/results/classifier_test_metrics.json"
):
    """
    Evaluates saved models on the held-out test set.
    Saves primary metrics to output_json and multi-model metrics to all_classifiers_test_metrics.json.
    """
    model_path = os.path.join(model_dir, "classifier.joblib")
    vec_path = os.path.join(model_dir, "vectorizer.joblib")

    if not os.path.exists(model_path) or not os.path.exists(vec_path):
        raise FileNotFoundError(f"Model or vectorizer missing in {model_dir}. Train classifier first.")

    primary_clf = joblib.load(model_path)
    primary_vec = joblib.load(vec_path)

    test_df = pd.read_csv(test_path)
    X_test_raw, y_test = extract_features_and_labels(test_df)
    y_test_arr = y_test.values

    # Primary Model Evaluation
    X_test_primary = primary_vec.transform(X_test_raw)
    y_pred_primary = primary_clf.predict(X_test_primary)
    if hasattr(primary_clf, "predict_proba"):
        y_proba_primary = primary_clf.predict_proba(X_test_primary)[:, 1]
    elif hasattr(primary_clf, "decision_function"):
        df = primary_clf.decision_function(X_test_primary)
        y_proba_primary = 1.0 / (1.0 + np.exp(-np.clip(df, -25.0, 25.0)))
    else:
        y_proba_primary = None

    primary_name = type(primary_clf).__name__
    if hasattr(primary_clf, "model_type"):
        primary_name = getattr(primary_clf, "model_type")
    elif isinstance(primary_clf, LinearSVMWithProba):
        primary_name = f"Structural Features + Linear SVM (C={primary_clf.C})"

    primary_metrics = compute_comprehensive_metrics(
        y_test_arr, y_pred_primary, y_proba_primary, primary_name
    )

    all_models_results = {
        "primary_model": primary_metrics
    }

    # Also evaluate Baseline if saved
    base_m_path = os.path.join(model_dir, "classifier_baseline.joblib")
    base_v_path = os.path.join(model_dir, "vectorizer_baseline.joblib")
    if os.path.exists(base_m_path) and os.path.exists(base_v_path):
        base_clf = joblib.load(base_m_path)
        base_vec = joblib.load(base_v_path)
        X_test_base = base_vec.transform(X_test_raw)
        y_pred_base = base_clf.predict(X_test_base)
        y_proba_base = base_clf.predict_proba(X_test_base)[:, 1]
        all_models_results["baseline_lr"] = compute_comprehensive_metrics(
            y_test_arr, y_pred_base, y_proba_base, "TF-IDF (1-3 n-grams) + Logistic Regression (C=1.0)"
        )

    # Also evaluate Improved LR if saved
    lr_m_path = os.path.join(model_dir, "classifier_improved_lr.joblib")
    lr_v_path = os.path.join(model_dir, "vectorizer_improved_lr.joblib")
    if os.path.exists(lr_m_path) and os.path.exists(lr_v_path):
        lr_clf = joblib.load(lr_m_path)
        lr_vec = joblib.load(lr_v_path)
        X_test_lr = lr_vec.transform(X_test_raw)
        y_pred_lr = lr_clf.predict(X_test_lr)
        y_proba_lr = lr_clf.predict_proba(X_test_lr)[:, 1]
        all_models_results["improved_lr"] = compute_comprehensive_metrics(
            y_test_arr, y_pred_lr, y_proba_lr, f"Structural Features + Logistic Regression (C={lr_clf.C})"
        )

    # Majority Baseline (predict all 1)
    y_pred_maj = np.ones_like(y_test_arr)
    y_proba_maj = np.full_like(y_test_arr, float((y_test_arr == 1).mean()), dtype=float)
    all_models_results["majority_baseline"] = compute_comprehensive_metrics(
        y_test_arr, y_pred_maj, y_proba_maj, "Majority-Class Baseline (All Valid / 1)"
    )

    # Save primary metrics to expected JSON path
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(primary_metrics, f, indent=2)

    # Save comprehensive comparison
    all_json_path = os.path.join(os.path.dirname(output_json), "all_classifiers_test_metrics.json")
    with open(all_json_path, "w", encoding="utf-8") as f:
        json.dump(all_models_results, f, indent=2)

    cm = primary_metrics["confusion_matrix"]
    print(f"\n=== Classifier Held-Out Test Evaluation ({primary_name}) ===")
    print(f"Accuracy:        {primary_metrics['accuracy']:.4f}")
    print(f"Valid Precision: {primary_metrics['precision']:.4f} | Recall: {primary_metrics['recall']:.4f} | F1: {primary_metrics['f1_score']:.4f}")
    print(f"Invalid Precision: {primary_metrics['invalid_class_metrics']['precision']:.4f} | Recall: {primary_metrics['invalid_class_metrics']['recall']:.4f} | F1: {primary_metrics['invalid_class_metrics']['f1_score']:.4f}")
    print(f"Macro F1:        {primary_metrics['macro_f1']:.4f} | Weighted F1: {primary_metrics['weighted_f1']:.4f}")
    print(f"ROC-AUC:         {primary_metrics['roc_auc']:.4f} | PR-AUC: {primary_metrics['pr_auc']:.4f}")
    print(f"Confusion Matrix: TN={cm['true_negative']}, FP={cm['false_positive']}, FN={cm['false_negative']}, TP={cm['true_positive']}")
    print(f"False Acceptance Rate (FAR): {primary_metrics['false_acceptance_rate']:.4f}")
    print(f"False Rejection Rate (FRR):  {primary_metrics['false_rejection_rate']:.4f}")
    print(f"[+] Saved evaluation metrics to: {output_json} and {all_json_path}")

    return primary_metrics


if __name__ == "__main__":
    evaluate_classifier_on_test()
