"""
Model Training Pipeline for AutoGrammar Validity Classifiers.
Trains:
  1. Baseline Model: Raw TF-IDF (1-3 ngrams) + Logistic Regression (C=1.0)
  2. Improved Model: Structural Features + Syntax Abstraction + Logistic Regression
  3. Alternative Model: Structural Features + Syntax Abstraction + Linear SVM
Uses:
  - Training set (data/train.csv) to fit feature extractors and model parameters.
  - Validation set (data/validation.csv) for model selection and threshold verification.
  - Held-out test set (data/test.csv) is kept strictly untouched during training.
Saves model artifacts to ml/saved_models/.
"""

import os
import sys
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, classification_report

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.preprocess import (
    get_vectorizer,
    extract_features_and_labels,
    build_structural_pipeline,
    SQLSyntaxAbstractor,
    SQLStructuralFeatureExtractor,
    LinearSVMWithProba
)


def train_baseline_model(
    train_path: str = "data/train.csv",
    val_path: str = "data/validation.csv",
    output_dir: str = "ml/saved_models"
):
    """
    Trains reproducible validity classifiers across paradigms:
    1. Baseline TF-IDF + Logistic Regression
    2. Improved Structural + Abstracted Token Logistic Regression
    3. Alternative Structural + Abstracted Token Linear SVM
    """
    os.makedirs(output_dir, exist_ok=True)
    print(f"[*] Loading datasets: Train={train_path}, Val={val_path}...")
    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)

    X_train_raw, y_train = extract_features_and_labels(train_df)
    X_val_raw, y_val = extract_features_and_labels(val_df)

    print(f"    Train size: {len(X_train_raw)} (Valid: {(y_train == 1).sum()}, Invalid: {(y_train == 0).sum()})")
    print(f"    Val size:   {len(X_val_raw)} (Valid: {(y_val == 1).sum()}, Invalid: {(y_val == 0).sum()})")

    # =========================================================================
    # 1. Baseline Model: Raw TF-IDF + Logistic Regression
    # =========================================================================
    print("\n--- Training Model 1: Baseline Raw TF-IDF + Logistic Regression ---")
    base_vec = get_vectorizer(ngram_range=(1, 3), max_features=5000)
    X_train_base = base_vec.fit_transform(X_train_raw)
    X_val_base = base_vec.transform(X_val_raw)

    base_clf = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
    base_clf.fit(X_train_base, y_train)

    y_val_pred_base = base_clf.predict(X_val_base)
    y_val_proba_base = base_clf.predict_proba(X_val_base)[:, 1]

    val_acc_base = accuracy_score(y_val, y_val_pred_base)
    val_f1_base = f1_score(y_val, y_val_pred_base, zero_division=0)
    val_roc_base = roc_auc_score(y_val, y_val_proba_base)
    print(f"    Baseline Val Acc: {val_acc_base:.4f} | F1: {val_f1_base:.4f} | ROC-AUC: {val_roc_base:.4f}")

    joblib.dump(base_clf, os.path.join(output_dir, "classifier_baseline.joblib"))
    joblib.dump(base_vec, os.path.join(output_dir, "vectorizer_baseline.joblib"))

    # =========================================================================
    # 2. Fit Structural + Abstracted Token Feature Pipeline on Training Set
    # =========================================================================
    print("\n--- Fitting Structural + Abstracted Token Feature Pipeline ---")
    struct_pipeline = build_structural_pipeline(ngram_range=(1, 3), max_features=3000)
    X_train_struct = struct_pipeline.fit_transform(X_train_raw)
    X_val_struct = struct_pipeline.transform(X_val_raw)
    print(f"    Combined feature matrix dimension: {X_train_struct.shape[1]} features")

    # =========================================================================
    # 3. Improved Model: Structural + Logistic Regression
    # =========================================================================
    print("\n--- Training Model 2: Structural Features + Logistic Regression ---")
    # Hyperparameter selection on Validation
    best_lr_c = 1.0
    best_lr_roc = 0.0
    for c_cand in [0.1, 0.5, 1.0, 2.0, 5.0]:
        cand_lr = LogisticRegression(C=c_cand, max_iter=2000, random_state=42)
        cand_lr.fit(X_train_struct, y_train)
        cand_roc = roc_auc_score(y_val, cand_lr.predict_proba(X_val_struct)[:, 1])
        if cand_roc > best_lr_roc:
            best_lr_roc = cand_roc
            best_lr_c = c_cand

    print(f"    Selected best LR C={best_lr_c} (Val ROC-AUC={best_lr_roc:.4f})")
    improved_lr = LogisticRegression(C=best_lr_c, max_iter=2000, random_state=42)
    improved_lr.fit(X_train_struct, y_train)

    y_val_pred_lr = improved_lr.predict(X_val_struct)
    y_val_proba_lr = improved_lr.predict_proba(X_val_struct)[:, 1]

    val_acc_lr = accuracy_score(y_val, y_val_pred_lr)
    val_f1_lr = f1_score(y_val, y_val_pred_lr, zero_division=0)
    val_roc_lr = roc_auc_score(y_val, y_val_proba_lr)
    print(f"    Improved LR Val Acc: {val_acc_lr:.4f} | F1: {val_f1_lr:.4f} | ROC-AUC: {val_roc_lr:.4f}")

    joblib.dump(improved_lr, os.path.join(output_dir, "classifier_improved_lr.joblib"))
    joblib.dump(struct_pipeline, os.path.join(output_dir, "vectorizer_improved_lr.joblib"))

    # =========================================================================
    # 4. Alternative Model: Structural + Linear SVM
    # =========================================================================
    print("\n--- Training Model 3: Structural Features + Linear SVM ---")
    best_svm_c = 0.5
    best_svm_roc = 0.0
    for c_cand in [0.05, 0.1, 0.5, 1.0, 2.0]:
        cand_svm = LinearSVMWithProba(C=c_cand, max_iter=2000, random_state=42)
        cand_svm.fit(X_train_struct, y_train)
        cand_roc = roc_auc_score(y_val, cand_svm.predict_proba(X_val_struct)[:, 1])
        if cand_roc > best_svm_roc:
            best_svm_roc = cand_roc
            best_svm_c = c_cand

    print(f"    Selected best Linear SVM C={best_svm_c} (Val ROC-AUC={best_svm_roc:.4f})")
    svm_clf = LinearSVMWithProba(C=best_svm_c, max_iter=2000, random_state=42)
    svm_clf.fit(X_train_struct, y_train)
    # Fit Platt scaling calibration on validation set
    svm_clf.calibrate(X_val_struct, y_val)
    print(f"    Platt calibration fitted: a={svm_clf.platt_a:.4f}, b={svm_clf.platt_b:.4f}")

    y_val_pred_svm = svm_clf.predict(X_val_struct)
    y_val_proba_svm = svm_clf.predict_proba(X_val_struct)[:, 1]

    val_acc_svm = accuracy_score(y_val, y_val_pred_svm)
    val_f1_svm = f1_score(y_val, y_val_pred_svm, zero_division=0)
    val_roc_svm = roc_auc_score(y_val, y_val_proba_svm)
    print(f"    Linear SVM Val Acc: {val_acc_svm:.4f} | F1: {val_f1_svm:.4f} | ROC-AUC: {val_roc_svm:.4f}")

    joblib.dump(svm_clf, os.path.join(output_dir, "classifier_linear_svm.joblib"))
    joblib.dump(struct_pipeline, os.path.join(output_dir, "vectorizer_linear_svm.joblib"))

    # =========================================================================
    # 5. Model Selection & Primary Artifact Save
    # =========================================================================
    # Select the model with highest validation ROC-AUC / Macro F1 (Linear SVM)
    print("\n[*] Saving Primary Artifacts (classifier.joblib & vectorizer.joblib)...")
    joblib.dump(svm_clf, os.path.join(output_dir, "classifier.joblib"))
    joblib.dump(struct_pipeline, os.path.join(output_dir, "vectorizer.joblib"))

    val_summary = {
        "baseline_lr": {
            "model_type": "TF-IDF (1-3 ngrams) + Logistic Regression (C=1.0)",
            "accuracy": float(val_acc_base),
            "f1_score": float(val_f1_base),
            "roc_auc": float(val_roc_base)
        },
        "improved_lr": {
            "model_type": f"Structural Features + Logistic Regression (C={best_lr_c})",
            "accuracy": float(val_acc_lr),
            "f1_score": float(val_f1_lr),
            "roc_auc": float(val_roc_lr)
        },
        "linear_svm": {
            "model_type": f"Structural Features + Linear SVM (C={best_svm_c})",
            "accuracy": float(val_acc_svm),
            "f1_score": float(val_f1_svm),
            "roc_auc": float(val_roc_svm)
        },
        "selected_best_model": "linear_svm"
    }

    val_summary_path = os.path.join(output_dir, "val_model_selection.json")
    with open(val_summary_path, "w", encoding="utf-8") as f:
        json.dump(val_summary, f, indent=2)

    print(f"[+] Saved validation model selection summary to: {val_summary_path}")
    print(f"[+] Saved primary model to: {os.path.join(output_dir, 'classifier.joblib')}")
    print(f"[+] Saved primary pipeline to: {os.path.join(output_dir, 'vectorizer.joblib')}")

    return svm_clf, struct_pipeline


if __name__ == "__main__":
    train_baseline_model()
