"""
Error Handling and Diagnostic Reporting for AutoGrammar.
Formats human-readable and machine-actionable compiler diagnostics.
"""

from typing import Optional, List, Dict, Any


class CompilerDiagnostic:
    def __init__(
        self,
        phase: str,  # 'LEXICAL', 'SYNTAX', 'SEMANTIC', 'SECURITY'
        message: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
        unexpected_token: Optional[str] = None,
        expected_tokens: Optional[List[str]] = None,
        suggestion: Optional[str] = None
    ):
        self.phase = phase
        self.message = message
        self.line = line
        self.column = column
        self.unexpected_token = unexpected_token
        self.expected_tokens = expected_tokens or []
        self.suggestion = suggestion

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase,
            "message": self.message,
            "line": self.line,
            "column": self.column,
            "unexpected_token": self.unexpected_token,
            "expected_tokens": self.expected_tokens,
            "suggestion": self.suggestion
        }

    def __str__(self) -> str:
        loc = f"Line {self.line}, Col {self.column}" if self.line is not None else "Position unknown"
        res = f"[{self.phase} ERROR] {loc}: {self.message}"
        if self.unexpected_token:
            res += f" (Unexpected: {self.unexpected_token!r})"
        if self.expected_tokens:
            res += f" | Expected one of: {', '.join(self.expected_tokens[:5])}"
        if self.suggestion:
            res += f"\n  -> Suggestion: {self.suggestion}"
        return res


def format_lark_syntax_error(error: Exception, query_text: str) -> CompilerDiagnostic:
    """Extracts line, column, and expected tokens from Lark parser errors."""
    line = getattr(error, "line", None)
    column = getattr(error, "column", None)
    token = getattr(error, "token", None)
    unexpected = str(token.value) if token else getattr(error, "char", None)
    expected = list(getattr(error, "expected", []))

    # Construct contextual suggestion
    suggestion = None
    err_str = str(error)
    if "Unexpected end of input" in err_str:
        suggestion = "Query ended prematurely. Check for missing closing parenthesis, table name, or condition."
    elif unexpected == ";":
        suggestion = "Premature semicolon. Semicolons should only appear at the very end of the statement."
    elif unexpected == ",":
        suggestion = "Unexpected comma. Check for trailing commas in SELECT list or column definitions."
    elif expected:
        suggestion = f"Expected construct: {', '.join(expected[:3])}"

    return CompilerDiagnostic(
        phase="SYNTAX",
        message=f"Syntax analysis failed: {err_str.splitlines()[0] if err_str else 'Unknown error'}",
        line=line,
        column=column,
        unexpected_token=unexpected,
        expected_tokens=expected,
        suggestion=suggestion
    )
