"""
Unit Tests for the Lexical Analyzer (Lexer).
"""

from compiler.lexer import SqlLexer, LexicalError, tokenize
from compiler.token_types import TokenType


def test_lexer_tokenizes_basic_keywords():
    sql = "SELECT first_name, last_name FROM students WHERE class_id = 5;"
    tokens = tokenize(sql)
    types = [t.type for t in tokens]
    values = [t.value for t in tokens]

    assert tokens[0].type == TokenType.KEYWORD
    assert tokens[0].value == "SELECT"
    assert tokens[1].type == TokenType.IDENTIFIER
    assert tokens[1].value == "first_name"
    assert tokens[2].type == TokenType.COMMA
    assert tokens[3].type == TokenType.IDENTIFIER
    assert tokens[3].value == "last_name"
    assert tokens[4].type == TokenType.KEYWORD
    assert tokens[4].value == "FROM"
    assert tokens[5].type == TokenType.IDENTIFIER
    assert tokens[5].value == "students"


def test_lexer_tracks_lines_and_columns():
    sql = "SELECT *\nFROM students\nWHERE student_id = 10;"
    tokens = tokenize(sql)

    # First line
    assert tokens[0].value == "SELECT"
    assert tokens[0].line == 1
    assert tokens[0].column == 1

    # Second line
    from_tok = next(t for t in tokens if t.value == "FROM")
    assert from_tok.line == 2
    assert from_tok.column == 1

    # Third line
    where_tok = next(t for t in tokens if t.value == "WHERE")
    assert where_tok.line == 3
    assert where_tok.column == 1


def test_lexer_detects_unknown_illegal_tokens():
    sql = "SELECT first_name @#$ last_name FROM students;"
    tokens = tokenize(sql)
    unknowns = [t for t in tokens if t.type == TokenType.UNKNOWN]
    assert len(unknowns) == 3
    assert [u.value for u in unknowns] == ["@", "#", "$"]


def test_lexer_literal_strings_and_operators():
    sql = "WHERE state = 'Andhra Pradesh' AND marks >= 80;"
    tokens = tokenize(sql)
    str_tok = next(t for t in tokens if t.type == TokenType.STRING)
    assert str_tok.value == "'Andhra Pradesh'"

    ge_tok = next(t for t in tokens if t.value == ">=")
    assert ge_tok.type == TokenType.OPERATOR
