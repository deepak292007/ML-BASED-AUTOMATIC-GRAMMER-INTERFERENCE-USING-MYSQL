"""
Feature Preprocessing and Vectorization Pipeline for AutoGrammar ML.
Supports:
1. Baseline Raw TF-IDF Vectorizer (for baseline comparison).
2. Syntax Token Abstraction (abstracts identifiers, literals, aggregates to prevent lexical overfitting).
3. Structural Feature Extraction (parentheses balance, quotes, syntax boundaries, clause ordering).
4. Unified Scikit-Learn Feature Pipeline for reproducible ML training and evaluation.
"""

import re
from typing import Tuple, List, Any, Union
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.preprocessing import StandardScaler

from compiler.lexer import SqlLexer
from compiler.token_types import TokenType, AGGREGATE_FUNCS


def get_vectorizer(
    ngram_range: Tuple[int, int] = (1, 3),
    max_features: int = 5000
) -> TfidfVectorizer:
    """Creates a configured baseline TF-IDF vectorizer for raw SQL query strings."""
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


_GLOBAL_LEXER = SqlLexer()

DANGLING_PATTERNS = [
    re.compile(r"\bFROM\s*;", re.I),
    re.compile(r"\bWHERE\s*;", re.I),
    re.compile(r"\bSELECT\s*;", re.I),
    re.compile(r"\bJOIN\s*;", re.I),
    re.compile(r"\bSET\s*;", re.I),
    re.compile(r"\bAND\s*;", re.I),
    re.compile(r"\bOR\s*;", re.I),
    re.compile(r"\bBY\s*;", re.I),
    re.compile(r"\bIN\s*;", re.I),
    re.compile(r"\bON\s*;", re.I),
    re.compile(r",\s*FROM\b", re.I),
    re.compile(r",\s*WHERE\b", re.I),
    re.compile(r",\s*;", re.I),
    re.compile(r",\s*,", re.I),
    re.compile(r">\s*=", re.I),
    re.compile(r"<\s*=", re.I),
    re.compile(r"!\s*=", re.I),
    re.compile(r"\bSELECT\s+FROM\b", re.I),
    re.compile(r"\bUPDATE\s+WHERE\b", re.I),
    re.compile(r"\bUPDATE\s+[a-zA-Z_]\w*\s+[a-zA-Z_]\w*\s*=", re.I),
    re.compile(r"\bDELETE\s+[a-zA-Z_]\w*\b", re.I),
    re.compile(r"\bORDER\s+BY\b.*?\bWHERE\b", re.I),
]


def abstract_sql(query: str, lexer: SqlLexer = None) -> str:
    """
    Abstracts a SQL query string into a syntax-oriented token representation.
    - Preserves keywords, operators, and punctuation.
    - Normalizes aggregate functions to <AGG>.
    - Abstracts table/column identifiers to <ID>, numbers to <NUM>, strings to <STR>.
    - Flags illegal characters as <LEX_ERR>.
    - Normalizes core statement verbs with <DML> tag to facilitate out-of-distribution generalization.
    """
    if lexer is None:
        lexer = _GLOBAL_LEXER

    tokens = lexer.tokenize(query)
    abstracted = []
    for t in tokens:
        val = t.value.upper()
        if val in AGGREGATE_FUNCS:
            abstracted.append("<AGG>")
        elif val in ("SELECT", "INSERT", "UPDATE", "DELETE"):
            abstracted.append("<DML>")
            abstracted.append(val)
        elif t.type == TokenType.KEYWORD:
            abstracted.append(val)
        elif t.type == TokenType.IDENTIFIER:
            abstracted.append("<ID>")
        elif t.type == TokenType.NUMBER:
            abstracted.append("<NUM>")
        elif t.type == TokenType.STRING:
            abstracted.append("<STR>")
        elif t.type == TokenType.OPERATOR:
            abstracted.append(t.value)
        elif t.type in (TokenType.COMMA, TokenType.SEMICOLON, TokenType.DOT, TokenType.LPAREN, TokenType.RPAREN):
            abstracted.append(t.value)
        elif t.type == TokenType.UNKNOWN:
            abstracted.append("<LEX_ERR>")
        else:
            abstracted.append(t.value)
    return " ".join(abstracted)


def extract_structural_features(queries: List[str], lexer: SqlLexer = None) -> np.ndarray:
    """
    Computes dense, interpretable structural features:
    1. Parentheses balance and non-negative nesting depth.
    2. Quote balance and backtick presence.
    3. Semicolon placement and termination.
    4. Lexical anomaly detection (illegal chars, numeric-leading identifiers).
    5. Dangling keywords and malformed clause transitions.
    6. Statement starting token validity and clause sequencing.
    7. Unsupported features (CTE, window functions).
    8. Query length and token counts.
    """
    if lexer is None:
        lexer = _GLOBAL_LEXER

    features = []
    for q in queries:
        q_strip = q.strip()
        tokens = lexer.tokenize(q_strip)

        # Parentheses
        lparen = q.count("(")
        rparen = q.count(")")
        paren_diff = float(abs(lparen - rparen))
        paren_balanced = 1.0 if lparen == rparen else 0.0

        depth = 0
        min_depth = 0
        for ch in q:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth < min_depth:
                    min_depth = depth
        depth_non_negative = 1.0 if min_depth >= 0 else 0.0

        # Quotes and backticks
        single_quotes = q.count("'")
        quotes_balanced = 1.0 if single_quotes % 2 == 0 else 0.0
        backticks = q.count("`")
        has_backticks = 1.0 if backticks > 0 else 0.0

        # Semicolon
        ends_semicolon = 1.0 if q_strip.endswith(";") else 0.0
        semicolon_count = q.count(";")
        single_semicolon = 1.0 if semicolon_count == 1 else 0.0

        # Lexical anomalies
        has_lex_err = 1.0 if any(t.type == TokenType.UNKNOWN for t in tokens) else 0.0
        has_num_leading_ident = 1.0 if re.search(r"\b\d+[a-zA-Z_]\w*\b", q) else 0.0

        # Dangling patterns
        dangling_counts = [1.0 if p.search(q) else 0.0 for p in DANGLING_PATTERNS]

        # Valid statement start
        first_kw = next((t.value.upper() for t in tokens if t.type == TokenType.KEYWORD), "")
        valid_start = 1.0 if first_kw in ("SELECT", "INSERT", "UPDATE", "DELETE") else 0.0

        # Unsupported SQL DSL features
        is_unsupported = 1.0 if ("WITH " in q.upper() or "OVER (" in q.upper() or "ROW_NUMBER()" in q.upper()) else 0.0

        # Token count
        num_tokens = float(len(tokens))

        row = [
            paren_balanced,
            paren_diff,
            depth_non_negative,
            quotes_balanced,
            has_backticks,
            ends_semicolon,
            single_semicolon,
            has_lex_err,
            has_num_leading_ident,
            valid_start,
            is_unsupported,
            num_tokens
        ] + dangling_counts
        features.append(row)

    return np.array(features, dtype=np.float32)


class SQLSyntaxAbstractor(BaseEstimator, TransformerMixin):
    """Transformer that abstracts SQL queries into tokenized syntax skeletons."""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        queries = X.tolist() if isinstance(X, pd.Series) else list(X)
        return [abstract_sql(q) for q in queries]


class SQLStructuralFeatureExtractor(BaseEstimator, TransformerMixin):
    """Transformer that extracts dense numerical structural features from raw SQL queries."""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        queries = X.tolist() if isinstance(X, pd.Series) else list(X)
        return extract_structural_features(queries)


from sklearn.base import ClassifierMixin
from sklearn.svm import LinearSVC


class LinearSVMWithProba(BaseEstimator, ClassifierMixin):
    """
    Linear Support Vector Classifier with Platt-calibrated posterior probabilities.
    Converts hyperplane margin distances into calibrated posterior probabilities
    using empirical Platt scaling (logistic sigmoid fitted on validation decision scores).
    Also provides raw decision margin scores via decision_function().
    """
    def __init__(self, C: float = 0.5, max_iter: int = 2000, random_state: int = 42):
        self.C = C
        self.max_iter = max_iter
        self.random_state = random_state
        self.clf = LinearSVC(C=self.C, max_iter=self.max_iter, random_state=self.random_state)
        self.platt_a = 1.0
        self.platt_b = 0.0
        self.is_calibrated = False

    def fit(self, X, y):
        self.clf.fit(X, y)
        self.classes_ = self.clf.classes_
        return self

    def calibrate(self, X_val, y_val):
        """Fits Platt calibration parameters on validation decision function values."""
        df = self.clf.decision_function(X_val)
        from sklearn.linear_model import LogisticRegression
        lr = LogisticRegression(C=1.0, solver="lbfgs")
        lr.fit(df.reshape(-1, 1), y_val)
        self.platt_a = float(lr.coef_[0][0])
        self.platt_b = float(lr.intercept_[0])
        self.is_calibrated = True
        return self

    def predict(self, X):
        return self.clf.predict(X)

    def decision_function(self, X):
        return self.clf.decision_function(X)

    def predict_proba(self, X):
        df = self.clf.decision_function(X)
        if self.is_calibrated:
            z = -(self.platt_a * df + self.platt_b)
            proba_1 = 1.0 / (1.0 + np.exp(np.clip(z, -25.0, 25.0)))
        else:
            proba_1 = 1.0 / (1.0 + np.exp(-np.clip(df, -25.0, 25.0)))
        return np.vstack([1.0 - proba_1, proba_1]).T


def build_structural_pipeline(
    ngram_range: Tuple[int, int] = (1, 3),
    max_features: int = 3000
) -> FeatureUnion:
    """
    Constructs a FeatureUnion combining:
    1. Abstracted token TF-IDF n-grams (1-3 n-grams)
    2. Scaled dense structural features
    """
    return FeatureUnion([
        (
            "abstract_tfidf",
            Pipeline([
                ("abstractor", SQLSyntaxAbstractor()),
                ("tfidf", TfidfVectorizer(
                    ngram_range=ngram_range,
                    max_features=max_features,
                    sublinear_tf=True
                ))
            ])
        ),
        (
            "structural_dense",
            Pipeline([
                ("extractor", SQLStructuralFeatureExtractor()),
                ("scaler", StandardScaler())
            ])
        )
    ])

