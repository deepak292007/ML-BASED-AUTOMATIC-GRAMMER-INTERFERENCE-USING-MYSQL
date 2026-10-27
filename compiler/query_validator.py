"""
Query Validator Orchestrator for AutoGrammar.
Integrates Lexing, Syntax Parsing, Semantic Validation, and Security Analysis.
"""

import re
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
          - Destructive statements (DROP, TRUNCATE, ALTER, GRANT, REVOKE, EXEC) are strictly rejected.
          - Multi-statement command chaining (';' followed by commands outside string literals) is prohibited.
          - Unrestricted UPDATE / DELETE statements without WHERE clauses are flagged.
          - Comment-obfuscated bypass attempts are neutralized.
        """
        diagnostics: List[CompilerDiagnostic] = []

        # 1. Strip comments before security checks to prevent obfuscation bypass (e.g. DROP/*comment*/TABLE)
        stripped = re.sub(r'/\*[\s\S]*?\*/|--[^\r\n]*', ' ', query)

        # 2. Check for forbidden administrative / destructive commands using regex word boundaries
        forbidden_regex = r'\b(DROP|TRUNCATE|ALTER|GRANT|REVOKE|EXEC|EXECUTE)\b'
        forbidden_match = re.search(forbidden_regex, stripped, re.IGNORECASE)
        if forbidden_match:
            cmd = forbidden_match.group(1).upper()
            diagnostics.append(CompilerDiagnostic(
                phase="SECURITY",
                message=f"Dangerous SQL command '{cmd}' is prohibited in student DSL environment.",
                suggestion="AutoGrammar permits only controlled SELECT and sandboxed student DML."
            ))

        # 3. Check for multi-statement injection (ignoring semicolons inside quoted string literals)
        no_strings = re.sub(r"'([^'\\]|\\.|\'\')*'", "''", stripped)
        if ";" in no_strings:
            stmts = [p.strip() for p in no_strings.split(";") if p.strip()]
            if len(stmts) > 1:
                diagnostics.append(CompilerDiagnostic(
                    phase="SECURITY",
                    message="Multiple SQL statements detected. Command batching is blocked to prevent injection attacks.",
                    suggestion="Execute one statement at a time."
                ))

        # 4. Check unconstrained UPDATE / DELETE (both pre-parse pattern and post-parse semantics)
        clauses = semantics.get("clauses", [])
        is_unconstrained_del = (
            ("DELETE" in clauses and "WHERE" not in clauses) or
            (re.search(r'\bDELETE\s+FROM\b', no_strings, re.IGNORECASE) and not re.search(r'\bWHERE\b', no_strings, re.IGNORECASE))
        )
        if is_unconstrained_del and not any("Unconstrained DELETE" in d.message for d in diagnostics):
            diagnostics.append(CompilerDiagnostic(
                phase="SECURITY",
                message="Unconstrained DELETE without WHERE clause is dangerous and prohibited.",
                suggestion="Add a specific WHERE condition (e.g. WHERE student_id = ...)."
            ))

        is_unconstrained_upd = (
            ("UPDATE" in clauses and "WHERE" not in clauses) or
            (re.search(r'\bUPDATE\s+[a-zA-Z_][a-zA-Z0-9_]*\s+SET\b', no_strings, re.IGNORECASE) and not re.search(r'\bWHERE\b', no_strings, re.IGNORECASE))
        )
        if is_unconstrained_upd and not any("Unconstrained UPDATE" in d.message for d in diagnostics):
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
            first_phase = parse_res["diagnostics"][0].phase if parse_res["diagnostics"] else "SYNTAX"
            stage_reached = "BACKEND" if first_phase == "BACKEND" else ("LEXICAL" if first_phase == "LEXICAL" else "SYNTAX")
            return {
                "valid": False,
                "stage_reached": stage_reached,
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
