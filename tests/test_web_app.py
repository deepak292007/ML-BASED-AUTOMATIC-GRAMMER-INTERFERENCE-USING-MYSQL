"""
Unit and Integration Tests for Web Application Functions, Edge Cases, and Missing Files.
"""

import os
import pytest
import pandas as pd
from compiler.parser import AutoGrammarParser
from compiler.query_validator import QueryValidator
from database.connection import db_manager
from ml.evaluate_classifier import evaluate_classifier_on_test
from app import get_compiler_suite, SAMPLE_QUERIES, read_dataset_stats, count_learned_rules, check_model_trained


def test_compiler_suite_initialization():
    parser, validator = get_compiler_suite()
    assert parser is not None
    assert validator is not None


def test_missing_grammar_file_handling(tmp_path):
    missing_path = str(tmp_path / "non_existent.lark")
    parser = AutoGrammarParser(learned_path=missing_path)
    res = parser.parse("SELECT * FROM students;", grammar_choice="learned")
    assert res["success"] is False
    assert len(res["diagnostics"]) > 0
    assert any("not found" in d.message.lower() or "failed" in d.message.lower() for d in res["diagnostics"])


def test_missing_model_files_handling(tmp_path):
    empty_dir = str(tmp_path / "empty_models")
    os.makedirs(empty_dir, exist_ok=True)
    with pytest.raises(FileNotFoundError):
        evaluate_classifier_on_test(model_dir=empty_dir)


def test_database_table_preview_and_nonexistent_table():
    # Valid table preview
    res_valid = db_manager.preview_table("students", limit=5)
    assert res_valid["success"] is True
    assert len(res_valid["rows"]) == 5

    # Nonexistent table preview
    res_invalid = db_manager.preview_table("non_existent_table", limit=5)
    assert res_invalid["success"] is False
    assert "Invalid table" in res_invalid["error"]


def test_sample_queries_validation_suite():
    parser, validator = get_compiler_suite()
    for name, sql in SAMPLE_QUERIES.items():
        res = validator.validate(sql, grammar_choice="baseline")
        assert "valid" in res
        assert "stage_reached" in res
        if "Valid" in name:
            assert res["valid"] is True, f"Expected {name} to be valid, got errors: {[str(d) for d in res['diagnostics']]}"
        elif "Error" in name or "Block" in name:
            assert res["valid"] is False, f"Expected {name} to fail validation"


def test_dashboard_status_readers():
    stats = read_dataset_stats()
    assert stats is not None
    assert "database_records" in stats

    rule_cnt = count_learned_rules()
    assert rule_cnt is not None
    assert rule_cnt >= 30

    trained = check_model_trained()
    assert trained is True
