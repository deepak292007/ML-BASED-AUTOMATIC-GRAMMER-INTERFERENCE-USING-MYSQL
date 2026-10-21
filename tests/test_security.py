"""
Unit Tests for Compiler Security and Execution Guardrails.
"""

from compiler.query_validator import QueryValidator


def test_security_blocks_drop_table():
    validator = QueryValidator()
    sql = "DROP TABLE students;"
    res = validator.validate(sql)
    assert res["valid"] is False
    assert res["safe_to_execute"] is False
    assert any("prohibited" in str(d.message).lower() for d in res["diagnostics"])


def test_security_blocks_multiple_statements():
    validator = QueryValidator()
    sql = "SELECT * FROM students; DELETE FROM marks;"
    res = validator.validate(sql)
    assert res["valid"] is False
    assert res["safe_to_execute"] is False
    assert any("multiple sql statements" in str(d.message).lower() for d in res["diagnostics"])


def test_security_blocks_unconstrained_delete():
    validator = QueryValidator()
    sql = "DELETE FROM attendance;"
    res = validator.validate(sql, grammar_choice="baseline")
    assert res["valid"] is False
    assert any("unconstrained delete" in str(d.message).lower() for d in res["diagnostics"])
