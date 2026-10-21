"""
Feature Preprocessing and Vectorization Pipeline for AutoGrammar ML Baseline.
Converts SQL query strings into token and character n-gram TF-IDF representations.
"""

from typing import Tuple, Any
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd


def get_vectorizer(
    ngram_range: Tuple[int, int] = (1, 3),
    max_features: int = 5000
) -> TfidfVectorizer:
    """Creates a configured TF-IDF vectorizer suitable for SQL code tokens."""
    return TfidfVectorizer(
        ngram_range=ngram_range,
        max_features=max_features,
        token_pattern=r"(?u)\b\w+\b|[<>=!]+|[,;()]",
        lowercase=True,
        sublinear_tf=True
    )


def extract_features_and_labels(
    df: pd.DataFrame
) -> Tuple[pd.Series, pd.Series]:
    """Extracts raw query text and validity labels from dataset."""
    X = df["query_text"]
    y = df["validity_label"].astype(int)
    return X, y
