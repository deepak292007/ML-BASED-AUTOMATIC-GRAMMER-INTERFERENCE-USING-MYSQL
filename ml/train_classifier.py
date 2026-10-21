"""
Model Training Pipeline for AutoGrammar Baseline Validity Classifier.
Trains a TF-IDF + Logistic Regression model to predict query validity.
Saves model artifacts to ml/saved_models/.
"""

import os
import sys
import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score, f1_score, roc_auc_score

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.preprocess import get_vectorizer, extract_features_and_labels


def train_baseline_model(
    train_path: str = "data/train.csv",
    val_path: str = "data/validation.csv",
    output_dir: str = "ml/saved_models"
):
    os.makedirs(output_dir, exist_ok=True)
    print(f"[*] Loading training data from {train_path}...")
    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)

    X_train_raw, y_train = extract_features_and_labels(train_df)
    X_val_raw, y_val = extract_features_and_labels(val_df)

    print(f"    Train size: {len(X_train_raw)} (Pos: {(y_train == 1).sum()}, Neg: {(y_train == 0).sum()})")
    print(f"    Val size:   {len(X_val_raw)} (Pos: {(y_val == 1).sum()}, Neg: {(y_val == 0).sum()})")

    print("[*] Vectorizing SQL tokens via TF-IDF (n-grams 1-3)...")
    vectorizer = get_vectorizer(ngram_range=(1, 3), max_features=5000)
    X_train = vectorizer.fit_transform(X_train_raw)
    X_val = vectorizer.transform(X_val_raw)

    print(f"    Vocabulary size: {len(vectorizer.vocabulary_)} features")

    print("[*] Training Logistic Regression classifier (C=1.0, max_iter=1000)...")
    clf = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
    clf.fit(X_train, y_train)

    y_val_pred = clf.predict(X_val)
    y_val_proba = clf.predict_proba(X_val)[:, 1]

    acc = accuracy_score(y_val, y_val_pred)
    f1 = f1_score(y_val, y_val_pred)
    roc_auc = roc_auc_score(y_val, y_val_proba)

    print("\n=== Validation Results ===")
    print(f"Accuracy:  {acc:.4f}")
    print(f"F1-Score:  {f1:.4f}")
    print(f"ROC-AUC:   {roc_auc:.4f}")
    print("\nClassification Report:\n", classification_report(y_val, y_val_pred, digits=4))

    # Save artifacts
    model_path = os.path.join(output_dir, "classifier.joblib")
    vec_path = os.path.join(output_dir, "vectorizer.joblib")

    joblib.dump(clf, model_path)
    joblib.dump(vectorizer, vec_path)
    print(f"[+] Model saved to: {model_path}")
    print(f"[+] Vectorizer saved to: {vec_path}")

    return clf, vectorizer


if __name__ == "__main__":
    train_baseline_model()
