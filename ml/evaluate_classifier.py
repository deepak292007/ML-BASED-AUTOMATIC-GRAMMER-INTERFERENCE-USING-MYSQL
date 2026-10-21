"""
Model Evaluation Script for AutoGrammar Baseline Classifier.
Evaluates the trained TF-IDF + Logistic Regression model on the held-out test set.
Saves metrics to JSON and CSV files.
"""

import os
import sys
import json
import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, roc_auc_score, classification_report
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml.preprocess import extract_features_and_labels


def evaluate_classifier_on_test(
    test_path: str = "data/test.csv",
    model_dir: str = "ml/saved_models",
    output_json: str = "evaluation/results/classifier_test_metrics.json"
):
    model_path = os.path.join(model_dir, "classifier.joblib")
    vec_path = os.path.join(model_dir, "vectorizer.joblib")

    if not os.path.exists(model_path) or not os.path.exists(vec_path):
        raise FileNotFoundError(f"Model or vectorizer missing in {model_dir}. Train classifier first.")

    clf = joblib.load(model_path)
    vec = joblib.load(vec_path)

    test_df = pd.read_csv(test_path)
    X_test_raw, y_test = extract_features_and_labels(test_df)

    X_test = vec.transform(X_test_raw)
    y_pred = clf.predict(X_test)
    y_proba = clf.predict_proba(X_test)[:, 1]

    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    roc_auc = float(roc_auc_score(y_test, y_proba))
    cm = confusion_matrix(y_test, y_pred).tolist()

    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

    results = {
        "model_type": "TF-IDF (1-3 ngrams) + Logistic Regression",
        "test_sample_size": len(y_test),
        "valid_count": int((y_test == 1).sum()),
        "invalid_count": int((y_test == 0).sum()),
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "roc_auc": roc_auc,
        "confusion_matrix": {
            "true_negative": cm[0][0],
            "false_positive": cm[0][1],
            "false_negative": cm[1][0],
            "true_positive": cm[1][1]
        },
        "classification_report": report
    }

    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n=== Classifier Held-Out Test Evaluation ===")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1-Score:  {f1:.4f}")
    print(f"ROC-AUC:   {roc_auc:.4f}")
    print(f"Confusion Matrix: TN={cm[0][0]}, FP={cm[0][1]}, FN={cm[1][0]}, TP={cm[1][1]}")
    print(f"[+] Saved evaluation metrics to: {output_json}")

    return results


if __name__ == "__main__":
    evaluate_classifier_on_test()
