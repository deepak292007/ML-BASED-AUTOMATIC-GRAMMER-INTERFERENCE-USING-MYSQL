"""
Unit Tests for Parser and Parse Tree Generation.
"""

from compiler.parser import AutoGrammarParser


def test_parser_accepts_valid_queries():
    parser = AutoGrammarParser()
    valid_sql = "SELECT s.first_name, m.marks_obtained FROM students AS s INNER JOIN marks AS m ON s.student_id = m.student_id WHERE m.marks_obtained >= 75;"

    res_base = parser.parse(valid_sql, grammar_choice="baseline")
    assert res_base["success"] is True
    assert res_base["tree"] is not None
    assert len(res_base["ascii_tree"]) > 0

    res_learn = parser.parse(valid_sql, grammar_choice="learned")
    assert res_learn["success"] is True
    assert res_learn["tree"] is not None


def test_parser_rejects_missing_from():
    parser = AutoGrammarParser()
    bad_sql = "SELECT first_name, last_name WHERE state = 'Telangana';"

    res = parser.parse(bad_sql, grammar_choice="baseline")
    assert res["success"] is False
    assert len(res["diagnostics"]) > 0


def test_parser_rejects_unbalanced_parentheses():
    parser = AutoGrammarParser()
    bad_sql = "SELECT first_name FROM students WHERE (state = 'Delhi' AND gender = 'Male';"

    res = parser.parse(bad_sql, grammar_choice="baseline")
    assert res["success"] is False
