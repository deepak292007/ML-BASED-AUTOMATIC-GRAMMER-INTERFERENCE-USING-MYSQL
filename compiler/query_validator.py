"""
Query Validator Orchestrator for AutoGrammar.
Integrates Lexing, Syntax Parsing, Semantic Validation, and Security Analysis.
"""

from typing import Dict, Any, List, Optional
from compiler.lexer import SqlLexer
from compiler.token_types import TokenType
from compiler.parser import AutoGrammarParser
from compiler.semantic_checker import SemanticChecker
from compiler.error_handler import CompilerDiagnostic


class QueryValidator:
    """End-to-end compilation and safety verification pipeline."""

    def __init__(
        self,
        parser: Optional[AutoGrammarParser] = None,
        semantic_checker: Optional[SemanticChecker] = None,
        lexer: Optional[SqlLexer] = None
    ):
        self.lexer = lexer or SqlLexer()
        self.parser = parser or AutoGrammarParser()
        self.semantic_checker = semantic_checker or SemanticChecker()

    def check_security(self, query: str, tokens: List[Any], semantics: Dict[str, Any]) -> List[CompilerDiagnostic]:
        """
        Enforces safety guardrails:
          - Destructive statements (DROP, TRUNCATE, ALTER) are strictly rejected.
          - Multi-statement command chaining (';' followed by commands) is prohibited.
          - Unrestricted UPDATE / DELETE statements without WHERE clauses are flagged.
        """
        diagnostics: List[CompilerDiagnostic] = []
        upper_query = query.upper()

        # Check for forbidden destructive commands
        forbidden = ["DROP", "TRUNCATE", "ALTER", "GRANT", "REVOKE", "EXEC", "EXECUTE"]
        for cmd in forbidden:
            if f" {cmd} " in f" {upper_query} " or upper_query.startswith(cmd + " "):
                diagnostics.append(CompilerDiagnostic(
                    phase="SECURITY",
                    message=f"Dangerous SQL command '{cmd}' is prohibited in student DSL environment.",
                    suggestion="AutoGrammar permits only controlled SELECT and sandboxed student DML."
                ))

        # Check for multi-statement injection (semicolon followed by non-whitespace)
        if ";" in query:
            parts = [p.strip() for p in query.split(";") if p.strip()]
            if len(parts) > 1:
                diagnostics.append(CompilerDiagnostic(
                    phase="SECURITY",
                    message="Multiple SQL statements detected. Command batching is blocked to prevent injection attacks.",
                    suggestion="Execute one statement at a time."
                ))

        # Check unconstrained UPDATE / DELETE
        clauses = semantics.get("clauses", [])
        if "DELETE" in clauses and "WHERE" not in clauses:
            diagnostics.append(CompilerDiagnostic(
                phase="SECURITY",
                message="Unconstrained DELETE without WHERE clause is dangerous and prohibited.",
                suggestion="Add a specific WHERE condition (e.g. WHERE student_id = ...)."
            ))
        if "UPDATE" in clauses and "WHERE" not in clauses:
            diagnostics.append(CompilerDiagnostic(
                phase="SECURITY",
                message="Unconstrained UPDATE without WHERE clause is dangerous and prohibited.",
                suggestion="Add a specific WHERE condition (e.g. WHERE student_id = ...)."
            ))

        return diagnostics

    def validate(
        self,
        query: str,
        grammar_choice: str = "learned",
        enforce_semantics: bool = True
    ) -> Dict[str, Any]:
        """
        Executes the compilation and validation pipeline on the input query.
        Returns a rich status report.
        """
        cleaned_query = query.strip()
        all_diagnostics: List[CompilerDiagnostic] = []

        if not cleaned_query:
            return {
                "valid": False,
                "stage_reached": "INITIAL",
                "grammar_choice": grammar_choice,
                "tokens": [],
                "parse_tree_ascii": "",
                "diagnostics": [CompilerDiagnostic("VALIDATOR", "Query string is empty.")],
                "safe_to_execute": False,
                "semantics": {}
            }

        # Stage 0: Pre-Parse Security Check (Forbidden commands & multi-statements)
        pre_sec_errors = self.check_security(cleaned_query, [], {})
        if pre_sec_errors:
            all_diagnostics.extend(pre_sec_errors)
            return {
                "valid": False,
                "stage_reached": "SECURITY",
                "grammar_choice": grammar_choice,
                "tokens": [],
                "parse_tree_ascii": "",
                "diagnostics": all_diagnostics,
                "safe_to_execute": False,
                "semantics": {}
            }

        # Stage 1: Lexical Analysis
        tokens = self.lexer.tokenize(cleaned_query)
        lex_errors = [t for t in tokens if t.type == TokenType.UNKNOWN]
        if lex_errors:
            for err_tok in lex_errors:
                all_diagnostics.append(CompilerDiagnostic(
                    phase="LEXICAL",
                    message=f"Illegal or unrecognized token '{err_tok.value}' in input.",
                    line=err_tok.line,
                    column=err_tok.column,
                    unexpected_token=err_tok.value,
                    suggestion="Remove or fix unrecognized character."
                ))
            return {
                "valid": False,
                "stage_reached": "LEXICAL",
                "grammar_choice": grammar_choice,
                "tokens": [t.to_dict() for t in tokens],
                "parse_tree_ascii": "",
                "diagnostics": all_diagnostics,
                "safe_to_execute": False,
                "semantics": {}
            }

        # Stage 2: Syntax Parsing
        parse_res = self.parser.parse(cleaned_query, grammar_choice=grammar_choice)
        if not parse_res["success"]:
            all_diagnostics.extend(parse_res["diagnostics"])
            return {
                "valid": False,
                "stage_reached": "SYNTAX",
                "grammar_choice": grammar_choice,
                "tokens": [t.to_dict() for t in tokens],
                "parse_tree_ascii": "",
                "diagnostics": all_diagnostics,
                "safe_to_execute": False,
                "semantics": {}
            }

        semantics = parse_res["semantics"]

        # Stage 3: Semantic Validation
        if enforce_semantics:
            sem_errors = self.semantic_checker.validate_semantics(semantics)
            if sem_errors:
                all_diagnostics.extend(sem_errors)
                return {
                    "valid": False,
                    "stage_reached": "SEMANTIC",
                    "grammar_choice": grammar_choice,
                    "tokens": [t.to_dict() for t in tokens],
                    "parse_tree_ascii": parse_res["ascii_tree"],
                    "diagnostics": all_diagnostics,
                    "safe_to_execute": False,
                    "semantics": semantics
                }

        # Stage 4: Post-parse Semantic Security Checks (e.g. Unconstrained DML)
        post_sec_errors = self.check_security(cleaned_query, tokens, semantics)
        # Filter out anything already flagged
        new_sec_errors = [e for e in post_sec_errors if e.message not in [d.message for d in all_diagnostics]]
        if new_sec_errors:
            all_diagnostics.extend(new_sec_errors)
            return {
                "valid": False,
                "stage_reached": "SECURITY",
                "grammar_choice": grammar_choice,
                "tokens": [t.to_dict() for t in tokens],
                "parse_tree_ascii": parse_res["ascii_tree"],
                "diagnostics": all_diagnostics,
                "safe_to_execute": False,
                "semantics": semantics
            }

        # Approved Query
        is_read_only = "SELECT" in semantics.get("clauses", []) and "INSERT" not in semantics.get("clauses", []) and "UPDATE" not in semantics.get("clauses", []) and "DELETE" not in semantics.get("clauses", [])
        return {
            "valid": True,
            "stage_reached": "PASSED_ALL",
            "grammar_choice": grammar_choice,
            "tokens": [t.to_dict() for t in tokens],
            "parse_tree_ascii": parse_res["ascii_tree"],
            "diagnostics": [],
            "safe_to_execute": True,
            "is_read_only": is_read_only,
            "semantics": semantics
        }
