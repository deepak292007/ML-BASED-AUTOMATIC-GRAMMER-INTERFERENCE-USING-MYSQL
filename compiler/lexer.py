"""
Lexical Analyzer (Lexer) for AutoGrammar SQL DSL.
Performs tokenization, lexical error identification, and token category labeling.
"""

import re
from typing import List, Tuple
from compiler.token_types import Token, TokenType, SQL_KEYWORDS


class LexicalError(Exception):
    def __init__(self, message: str, line: int, column: int, character: str):
        super().__init__(f"Lexical error at line {line}, col {column}: {message} (found: {character!r})")
        self.message = message
        self.line = line
        self.column = column
        self.character = character


class SqlLexer:
    """
    Regex-based lexical analyzer with line/col tracking and exact token categorization.
    """

    # Token specification ordered by precedence
    TOKEN_SPEC = [
        # Whitespace (skipped)
        ("WHITESPACE", r"[ \t\r\n]+"),
        # Single-quoted string literals
        ("STRING", r"'([^'\\]|\\.)*'"),
        # Numbers (integers and floats)
        ("NUMBER", r"\b\d+(\.\d+)?\b"),
        # Multi-char operators
        ("OPERATOR_MULTI", r"(<=|>=|!=|<>)"),
        # Single-char operators
        ("OPERATOR_SINGLE", r"[=<>+\-*/%]"),
        # Punctuation
        ("DOT", r"\."),
        ("COMMA", r","),
        ("SEMICOLON", r";"),
        ("LPAREN", r"\("),
        ("RPAREN", r"\)"),
        ("ASTERISK", r"\*"),
        # Identifiers and keywords
        ("IDENTIFIER", r"\b[a-zA-Z_][a-zA-Z0-9_]*\b"),
        # Unknown / Illegal characters
        ("MISMATCH", r"."),
    ]

    def __init__(self):
        self.regex = re.compile(
            "|".join(f"(?P<{pair[0]}>{pair[1]})" for pair in self.TOKEN_SPEC),
            re.DOTALL
        )

    def tokenize(self, text: str, raise_errors: bool = False) -> List[Token]:
        """
        Tokenizes the input text into a list of Token objects.
        If raise_errors is False, invalid characters are recorded as UNKNOWN tokens.
        """
        tokens: List[Token] = []
        line_num = 1
        line_start = 0

        for match in self.regex.finditer(text):
            kind = match.lastgroup
            val = match.group()
            col = match.start() - line_start + 1

            if kind == "WHITESPACE":
                # Track line numbering
                if "\n" in val:
                    line_num += val.count("\n")
                    line_start = match.end() - (len(val) - val.rfind("\n") - 1)
                continue

            elif kind == "STRING":
                # Strip outer quotes for clean string token
                tokens.append(Token(TokenType.STRING, val, line_num, col, category="LITERAL_STRING"))

            elif kind == "NUMBER":
                tokens.append(Token(TokenType.NUMBER, val, line_num, col, category="LITERAL_NUMBER"))

            elif kind in ("OPERATOR_MULTI", "OPERATOR_SINGLE"):
                tokens.append(Token(TokenType.OPERATOR, val, line_num, col, category="OPERATOR"))

            elif kind == "ASTERISK":
                # Can be multiplication or wildcard
                tokens.append(Token(TokenType.OPERATOR, val, line_num, col, category="WILDCARD_OR_OP"))

            elif kind == "DOT":
                tokens.append(Token(TokenType.DOT, val, line_num, col, category="PUNCTUATION"))

            elif kind == "COMMA":
                tokens.append(Token(TokenType.COMMA, val, line_num, col, category="PUNCTUATION"))

            elif kind == "SEMICOLON":
                tokens.append(Token(TokenType.SEMICOLON, val, line_num, col, category="PUNCTUATION"))

            elif kind == "LPAREN":
                tokens.append(Token(TokenType.LPAREN, val, line_num, col, category="DELIMITER"))

            elif kind == "RPAREN":
                tokens.append(Token(TokenType.RPAREN, val, line_num, col, category="DELIMITER"))

            elif kind == "IDENTIFIER":
                upper_val = val.upper()
                if upper_val in SQL_KEYWORDS:
                    tokens.append(Token(TokenType.KEYWORD, upper_val, line_num, col, category=f"KEYWORD_{upper_val}"))
                else:
                    tokens.append(Token(TokenType.IDENTIFIER, val, line_num, col, category="IDENTIFIER"))

            elif kind == "MISMATCH":
                tok = Token(TokenType.UNKNOWN, val, line_num, col, category="LEXICAL_ERROR")
                tokens.append(tok)
                if raise_errors:
                    raise LexicalError("Illegal character encountered", line_num, col, val)

        return tokens


def tokenize(text: str, raise_errors: bool = False) -> List[Token]:
    """Helper functional wrapper for SqlLexer."""
    return SqlLexer().tokenize(text, raise_errors=raise_errors)
