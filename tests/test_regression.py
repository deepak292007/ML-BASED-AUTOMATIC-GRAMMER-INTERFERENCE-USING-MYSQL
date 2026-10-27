"""
Comprehensive Regression Test Suite for AutoGrammar.
Covers:
  Category A: Valid Queries (Projections, WHERE, LIKE, ORDER BY/LIMIT, Aggregates)
  Category B: Invalid Syntax (Missing select target, missing FROM, dangling operators)
  Category C: Semantic Errors (Unknown tables, nonexistent columns, ambiguous unqualified references)
  Category D: Security Verification (DROP, TRUNCATE, unconstrained DML, command batching, comment bypass)
  Category E: Aliases and Joins (Table aliases, qualified columns, join conditions, s.*)
  Category F: Regression Edge Cases (Case insensitivity, multiline queries, escaped quotes, comments, backend API)
"""

import pytest
from starlette.testclient import TestClient

from compiler.lexer import SqlLexer, TokenType
from compiler.parser import AutoGrammarParser
from compiler.semantic_checker import SemanticChecker, SCHOOL_DB_SCHEMA
from compiler.query_validator import QueryValidator
from database.connection import db_manager
from server import app


@pytest.fixture(scope="module")
def validator():
    return QueryValidator()


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# ===========================================================================
# CATEGORY A: VALID QUERIES
# ===========================================================================

def test_a1_select_star(validator):
    """SELECT * FROM students;"""
    sql = "SELECT * FROM students;"
    res = validator.validate(sql, grammar_choice="baseline")
    assert res["valid"] is True
    assert res["stage_reached"] == "PASSED_ALL"
    assert res["safe_to_execute"] is True


def test_a2_select_column(validator):
    """SELECT first_name FROM students;"""
    sql = "SELECT first_name FROM students;"
    res = validator.validate(sql, grammar_choice="baseline")
    assert res["valid"] is True
    assert res["stage_reached"] == "PASSED_ALL"


def test_a3_where_equality(validator):
    """SELECT * FROM students WHERE city = 'Guntur';"""
    sql = "SELECT * FROM students WHERE city = 'Guntur';"
    res = validator.validate(sql, grammar_choice="baseline")
    assert res["valid"] is True
    assert res["stage_reached"] == "PASSED_ALL"


def test_a4_where_like(validator):
    """SELECT * FROM students WHERE first_name LIKE 'A%';"""
    sql = "SELECT * FROM students WHERE first_name LIKE 'A%';"
    res = validator.validate(sql, grammar_choice="baseline")
    assert res["valid"] is True
    assert res["stage_reached"] == "PASSED_ALL"


def test_a5_order_by_limit(validator):
    """SELECT * FROM students ORDER BY student_id DESC LIMIT 5;"""
    sql = "SELECT * FROM students ORDER BY student_id DESC LIMIT 5;"
    res = validator.validate(sql, grammar_choice="baseline")
    assert res["valid"] is True
    assert res["stage_reached"] == "PASSED_ALL"


def test_a6_count_aggregate(validator):
    """
    SELECT COUNT(*) FROM students;
    Both baseline and learned grammar accept valid COUNT(*) aggregate expressions.
    """
    sql = "SELECT COUNT(*) FROM students;"
    res_base = validator.validate(sql, grammar_choice="baseline")
    assert res_base["valid"] is True
    assert res_base["stage_reached"] == "PASSED_ALL"

    res_learn = validator.validate(sql, grammar_choice="learned")
    assert res_learn["valid"] is True
    assert res_learn["stage_reached"] == "PASSED_ALL"


def test_a7_avg_aggregate(validator):
    """SELECT AVG(marks_obtained) FROM marks;"""
    sql = "SELECT AVG(marks_obtained) FROM marks;"
    res_base = validator.validate(sql, grammar_choice="baseline")
    assert res_base["valid"] is True
    res_learn = validator.validate(sql, grammar_choice="learned")
    assert res_learn["valid"] is True


def test_a8_filter_comparison(validator):
    """SELECT * FROM marks WHERE marks_obtained > 80;"""
    sql = "SELECT * FROM marks WHERE marks_obtained > 80;"
    res = validator.validate(sql, grammar_choice="baseline")
    assert res["valid"] is True


# ===========================================================================
# CATEGORY B: INVALID SYNTAX
# ===========================================================================

def test_b1_missing_select_list(validator):
    """SELECT FROM students;"""
    sql = "SELECT FROM students;"
    res = validator.validate(sql, grammar_choice="baseline")
    assert res["valid"] is False
    assert res["stage_reached"] == "SYNTAX"


def test_b2_missing_from_clause(validator):
    """SELECT name students;"""
    sql = "SELECT name students;"
    res = validator.validate(sql, grammar_choice="baseline")
    assert res["valid"] is False
    assert res["stage_reached"] == "SYNTAX"


def test_b3_where_before_from(validator):
    """SELECT * FROM WHERE students;"""
    sql = "SELECT * FROM WHERE students;"
    res = validator.validate(sql, grammar_choice="baseline")
    assert res["valid"] is False
    assert res["stage_reached"] == "SYNTAX"


def test_b4_dangling_comparison_operator(validator):
    """SELECT * FROM students WHERE marks_obtained >;"""
    sql = "SELECT * FROM students WHERE marks_obtained >;"
    res = validator.validate(sql, grammar_choice="baseline")
    assert res["valid"] is False
    assert res["stage_reached"] == "SYNTAX"


# ===========================================================================
# CATEGORY C: SEMANTIC ERRORS
# ===========================================================================

def test_c1_unknown_table(validator):
    """SELECT * FROM unknown_table;"""
    sql = "SELECT * FROM unknown_table;"
    res = validator.validate(sql, grammar_choice="baseline")
    assert res["valid"] is False
    assert res["stage_reached"] == "SEMANTIC"
    assert any("unknown_table" in d.message for d in res["diagnostics"])


def test_c2_nonexistent_column(validator):
    """SELECT nonexistent_column FROM students;"""
    sql = "SELECT nonexistent_column FROM students;"
    res = validator.validate(sql, grammar_choice="baseline")
    assert res["valid"] is False
    assert res["stage_reached"] == "SEMANTIC"
    assert any("nonexistent_column" in d.message for d in res["diagnostics"])


def test_c3_nonexistent_column_in_where(validator):
    """SELECT * FROM students WHERE nonexistent_column = 10;"""
    sql = "SELECT * FROM students WHERE nonexistent_column = 10;"
    res = validator.validate(sql, grammar_choice="baseline")
    assert res["valid"] is False
    assert res["stage_reached"] == "SEMANTIC"
    assert any("nonexistent_column" in d.message for d in res["diagnostics"])


def test_c4_ambiguous_column_in_join(validator):
    """
    SELECT student_id FROM students JOIN marks ON students.student_id = marks.student_id;
    student_id appears in both tables -> must be flagged as ambiguous when unqualified.
    """
    sql = "SELECT student_id FROM students JOIN marks ON students.student_id = marks.student_id;"
    res = validator.validate(sql, grammar_choice="baseline")
    assert res["valid"] is False
    assert res["stage_reached"] == "SEMANTIC"
    assert any("Ambiguous column reference" in d.message for d in res["diagnostics"])


def test_c5_unknown_column_in_aggregate(validator):
    """SELECT AVG(bogus_col) FROM marks;"""
    sql = "SELECT AVG(bogus_col) FROM marks;"
    res = validator.validate(sql, grammar_choice="baseline")
    assert res["valid"] is False
    assert res["stage_reached"] == "SEMANTIC"
    assert any("bogus_col" in d.message for d in res["diagnostics"])


# ===========================================================================
# CATEGORY D: SECURITY VERIFICATION
# ===========================================================================

def test_d1_drop_table(validator):
    """DROP TABLE students;"""
    sql = "DROP TABLE students;"
    res = validator.validate(sql)
    assert res["valid"] is False
    assert res["stage_reached"] == "SECURITY"
    assert res["safe_to_execute"] is False
    assert any("DROP" in d.message for d in res["diagnostics"])


def test_d2_truncate_table(validator):
    """TRUNCATE TABLE students;"""
    sql = "TRUNCATE TABLE students;"
    res = validator.validate(sql)
    assert res["valid"] is False
    assert res["stage_reached"] == "SECURITY"
    assert any("TRUNCATE" in d.message for d in res["diagnostics"])


def test_d3_unconstrained_delete(validator):
    """DELETE FROM students;"""
    sql = "DELETE FROM students;"
    res = validator.validate(sql, grammar_choice="baseline")
    assert res["valid"] is False
    assert res["stage_reached"] == "SECURITY"
    assert any("Unconstrained DELETE" in d.message for d in res["diagnostics"])


def test_d4_unconstrained_update(validator):
    """UPDATE students SET city = 'Guntur';"""
    sql = "UPDATE students SET city = 'Guntur';"
    res = validator.validate(sql, grammar_choice="baseline")
    assert res["valid"] is False
    assert res["stage_reached"] == "SECURITY"
    assert any("Unconstrained UPDATE" in d.message for d in res["diagnostics"])


def test_d5_multiple_statements(validator):
    """SELECT * FROM students; DROP TABLE students;"""
    sql = "SELECT * FROM students; DROP TABLE students;"
    res = validator.validate(sql)
    assert res["valid"] is False
    assert res["stage_reached"] == "SECURITY"
    assert res["safe_to_execute"] is False


def test_d6_comment_obfuscated_injection(validator):
    """DROP/*bypass*/TABLE students;"""
    sql = "DROP/*bypass*/TABLE students;"
    res = validator.validate(sql)
    assert res["valid"] is False
    assert res["stage_reached"] == "SECURITY"
    assert any("DROP" in d.message for d in res["diagnostics"])


# ===========================================================================
# CATEGORY E: ALIASES AND JOINS
# ===========================================================================

def test_e1_table_alias_projection(validator):
    """SELECT s.first_name FROM students AS s;"""
    sql = "SELECT s.first_name FROM students AS s;"
    res = validator.validate(sql, grammar_choice="baseline")
    assert res["valid"] is True
    assert res["stage_reached"] == "PASSED_ALL"


def test_e2_table_alias_in_where(validator):
    """SELECT s.first_name FROM students AS s WHERE s.student_id > 10;"""
    sql = "SELECT s.first_name FROM students AS s WHERE s.student_id > 10;"
    res = validator.validate(sql, grammar_choice="baseline")
    assert res["valid"] is True
    assert res["stage_reached"] == "PASSED_ALL"


def test_e3_multi_table_join(validator):
    """SELECT s.first_name, m.marks_obtained FROM students AS s JOIN marks AS m ON s.student_id = m.student_id;"""
    sql = "SELECT s.first_name, m.marks_obtained FROM students AS s JOIN marks AS m ON s.student_id = m.student_id;"
    res = validator.validate(sql, grammar_choice="baseline")
    assert res["valid"] is True
    assert res["stage_reached"] == "PASSED_ALL"


def test_e4_table_wildcard_alias(validator):
    """SELECT s.* FROM students AS s;"""
    sql = "SELECT s.* FROM students AS s;"
    res = validator.validate(sql, grammar_choice="baseline")
    assert res["valid"] is True
    assert res["stage_reached"] == "PASSED_ALL"


def test_e5_unknown_qualifier(validator):
    """SELECT x.first_name FROM students AS s;"""
    sql = "SELECT x.first_name FROM students AS s;"
    res = validator.validate(sql, grammar_choice="baseline")
    assert res["valid"] is False
    assert res["stage_reached"] == "SEMANTIC"
    assert any("Unknown table alias or qualifier 'x'" in d.message for d in res["diagnostics"])


# ===========================================================================
# CATEGORY F: REGRESSION EDGE CASES
# ===========================================================================

def test_f1_lowercase_keywords(validator):
    """select * from students where city = 'Guntur';"""
    sql = "select * from students where city = 'Guntur';"
    res = validator.validate(sql, grammar_choice="baseline")
    assert res["valid"] is True
    assert res["stage_reached"] == "PASSED_ALL"


def test_f2_whitespace_and_newlines(validator):
    sql = "   SELECT   first_name,\n\n  last_name\n\nFROM   students   WHERE   student_id  =  1  ;   "
    res = validator.validate(sql, grammar_choice="baseline")
    assert res["valid"] is True
    assert res["stage_reached"] == "PASSED_ALL"


def test_f3_optional_missing_semicolon(validator):
    sql = "SELECT first_name FROM students"
    res = validator.validate(sql, grammar_choice="baseline")
    assert res["valid"] is True


def test_f4_escaped_single_quotes(validator):
    """O'Connor escaped with standard SQL double single-quote: 'O''Connor'"""
    sql = "SELECT * FROM students WHERE last_name = 'O''Connor';"
    res = validator.validate(sql, grammar_choice="baseline")
    assert res["valid"] is True
    assert res["stage_reached"] == "PASSED_ALL"


def test_f5_sql_comments_ignored(validator):
    sql = "SELECT * FROM students -- inline comment\nWHERE city = 'Guntur' /* block comment */;"
    res = validator.validate(sql, grammar_choice="baseline")
    assert res["valid"] is True
    assert res["stage_reached"] == "PASSED_ALL"


def test_f6_semicolon_inside_string_not_multi_stmt(validator):
    sql = "SELECT * FROM students WHERE status = 'active;confirmed';"
    res = validator.validate(sql, grammar_choice="baseline")
    assert res["valid"] is True
    assert res["stage_reached"] == "PASSED_ALL"


def test_f7_unbalanced_parentheses(validator):
    sql = "SELECT first_name FROM students WHERE (student_id = 1;"
    res = validator.validate(sql, grammar_choice="baseline")
    assert res["valid"] is False
    assert res["stage_reached"] == "SYNTAX"


def test_f8_empty_query(validator):
    res = validator.validate("   ")
    assert res["valid"] is False
    assert res["stage_reached"] == "INITIAL"


# ===========================================================================
# CATEGORY G: FASTAPI BACKEND API ENDPOINTS
# ===========================================================================

def test_api_health_endpoint(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ONLINE"
    assert "compiler" in data
    assert "database" in data


def test_api_schema_endpoint(client):
    resp = client.get("/api/schema")
    assert resp.status_code == 200
    data = resp.json()
    assert "students" in data["schema"]
    assert "first_name" in data["schema"]["students"]
    assert "marks_obtained" in data["schema"]["marks"]
    assert "date_of_birth" in data["schema"]["students"]


def test_api_validate_valid_query(client):
    resp = client.post("/api/validate", json={"query": "SELECT first_name FROM students WHERE city = 'Guntur';"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_backend"] is True
    assert data["baseline"]["valid"] is True
    assert data["baseline"]["verdict"] == "ACCEPT"
    assert data["safe_to_execute"] is True
    assert "ml" in data
    assert "tokens" in data


def test_api_validate_security_rejection(client):
    resp = client.post("/api/validate", json={"query": "DROP TABLE students;"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["baseline"]["valid"] is False
    assert data["baseline"]["verdict"] == "REJECT"
    assert data["baseline"]["stage_reached"] == "Stage 0 (Security Gate)"
    assert data["safe_to_execute"] is False


def test_api_execute_safe_select(client):
    resp = client.post("/api/execute", json={"query": "SELECT first_name, last_name, city FROM students LIMIT 5;"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert len(data["rows"]) == 5
    assert "first_name" in data["columns"]


def test_api_execute_blocks_rejected_query(client):
    resp = client.post("/api/execute", json={"query": "DELETE FROM students;"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert data["blocked"] is True
