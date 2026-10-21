"""
Unit and Integration Tests for Synthetic Dataset and Data Leakage Prevention.
"""

import os
import json
import pandas as pd
import pytest


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def test_synthetic_student_records_exist():
    stu_path = os.path.join(DATA_DIR, "synthetic_students.csv")
    assert os.path.exists(stu_path), "synthetic_students.csv is missing"
    df = pd.read_csv(stu_path)
    assert len(df) == 10000, f"Expected 10,000 students, found {len(df)}"
    required_cols = {"student_id", "admission_no", "first_name", "last_name", "class_id", "section", "city", "state", "status"}
    assert required_cols.issubset(set(df.columns)), f"Missing required columns in students: {required_cols - set(df.columns)}"


def test_relational_entity_tables_exist():
    for table_name in ["synthetic_teachers", "synthetic_classes", "synthetic_subjects", "synthetic_marks", "synthetic_attendance"]:
        p = os.path.join(DATA_DIR, f"{table_name}.csv")
        assert os.path.exists(p), f"{table_name}.csv is missing"
        df = pd.read_csv(p)
        assert len(df) > 0, f"{table_name}.csv is empty"


def test_query_dataset_counts():
    q_path = os.path.join(DATA_DIR, "query_dataset.csv")
    assert os.path.exists(q_path), "query_dataset.csv is missing"
    df = pd.read_csv(q_path)
    assert len(df) >= 7000, f"Expected at least 7000 queries, got {len(df)}"
    assert (df["validity_label"] == 1).sum() >= 5000, "Expected at least 5000 valid queries"
    assert (df["validity_label"] == 0).sum() >= 2000, "Expected at least 2000 invalid queries"


def test_zero_data_leakage_between_splits():
    """Verifies that templates in train, validation, and test splits are strictly disjoint."""
    train_df = pd.read_csv(os.path.join(DATA_DIR, "train.csv"))
    val_df = pd.read_csv(os.path.join(DATA_DIR, "validation.csv"))
    test_df = pd.read_csv(os.path.join(DATA_DIR, "test.csv"))

    train_tpls = set(train_df["template_id"].unique())
    val_tpls = set(val_df["template_id"].unique())
    test_tpls = set(test_df["template_id"].unique())

    # Disjointness assertions
    train_val_overlap = train_tpls.intersection(val_tpls)
    train_test_overlap = train_tpls.intersection(test_tpls)
    val_test_overlap = val_tpls.intersection(test_tpls)

    assert len(train_val_overlap) == 0, f"Data leakage between Train and Val: {train_val_overlap}"
    assert len(train_test_overlap) == 0, f"Data leakage between Train and Test: {train_test_overlap}"
    assert len(val_test_overlap) == 0, f"Data leakage between Val and Test: {val_test_overlap}"
