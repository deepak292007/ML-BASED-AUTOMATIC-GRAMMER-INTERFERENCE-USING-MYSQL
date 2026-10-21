"""
Token types and Token definitions for the AutoGrammar SQL DSL Compiler.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Any


class TokenType(Enum):
    # Keywords
    KEYWORD = auto()
    
    # Literals
    NUMBER = auto()
    STRING = auto()
    
    # Identifiers (table names, column names, aliases)
    IDENTIFIER = auto()
    
    # Operators
    OPERATOR = auto()
    
    # Punctuation
    COMMA = auto()
    SEMICOLON = auto()
    LPAREN = auto()
    RPAREN = auto()
    DOT = auto()
    
    # Special / Error
    UNKNOWN = auto()
    EOF = auto()


# Canonical SQL keywords recognized in the School DSL
SQL_KEYWORDS = {
    "SELECT", "DISTINCT", "FROM", "WHERE", "AND", "OR", "NOT",
    "IN", "BETWEEN", "LIKE", "IS", "NULL", "ORDER", "BY",
    "LIMIT", "ASC", "DESC", "COUNT", "SUM", "AVG", "MIN", "MAX",
    "GROUP", "HAVING", "JOIN", "INNER", "LEFT", "RIGHT", "AS",
    "ON", "INSERT", "INTO", "VALUES", "UPDATE", "SET", "DELETE"
}

# Aggregate functions
AGGREGATE_FUNCS = {"COUNT", "SUM", "AVG", "MIN", "MAX"}

# Comparison operators
COMPARISON_OPS = {"=", "!=", "<>", "<=", ">=", "<", ">"}


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int
    category: str = ""

    def __post_init__(self):
        if not self.category:
            self.category = self.type.name

    def to_dict(self):
        return {
            "type": self.type.name,
            "value": self.value,
            "line": self.line,
            "column": self.column,
            "category": self.category
        }

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, line={self.line}, col={self.column})"
