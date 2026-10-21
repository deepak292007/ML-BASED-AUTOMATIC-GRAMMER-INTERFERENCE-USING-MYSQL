"""
Unit Tests for Semantic Checker (Schema-Aware Validation).
"""

from compiler.semantic_checker import SemanticChecker
from compiler.parse_tree import extract_query_semantics
from compiler.parser import AutoGrammarParser


def test_semantic_checker_detects_unknown_table():
    parser = AutoGrammarParser()
    checker = SemanticChecker()

    sql = "SELECT student_id, fee_amount FROM student_fees WHERE fee_amount > 1000;"
    parse_res = parser.parse(sql, grammar_choice="baseline")
    assert parse_res["success"] is True  # Syntactically fine SQL!

    sem_errors = checker.validate_semantics(parse_res["semantics"])
    assert len(sem_errors) > 0
    assert any("student_fees" in d.message for d in sem_errors)


def test_semantic_checker_detects_unknown_column():
    parser = AutoGrammarParser()
    checker = SemanticChecker()

    sql = "SELECT first_name, blood_group FROM students WHERE state = 'Delhi';"
    parse_res = parser.parse(sql, grammar_choice="baseline")
    assert parse_res["success"] is True

    sem_errors = checker.validate_semantics(parse_res["semantics"])
    assert len(sem_errors) > 0
    assert any("blood_group" in d.message for d in sem_errors)


def test_semantic_checker_accepts_valid_schema_query():
    parser = AutoGrammarParser()
    checker = SemanticChecker()

    sql = "SELECT first_name, last_name, city, state FROM students WHERE status = 'Active';"
    parse_res = parser.parse(sql, grammar_choice="baseline")
    assert parse_res["success"] is True

    sem_errors = checker.validate_semantics(parse_res["semantics"])
    assert len(sem_errors) == 0
