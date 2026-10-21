"""
Grammar Induction Engine for AutoGrammar.
Implements automatic grammar rule induction from tokenized training queries:
  1. Token abstraction and structural pattern mining.
  2. Discovery of clause sequences, optionality, repetitions, and recursion.
  3. EBNF candidate rule generation.
  4. Consolidation into valid Lark grammar syntax.
  5. Grammar validation and coverage evaluation on training/held-out queries.
  6. Incremental refinement with version control.
"""

import os
import re
import json
import datetime
from collections import Counter, defaultdict
from typing import List, Dict, Set, Tuple, Optional, Any
from lark import Lark, LarkError

from compiler.lexer import SqlLexer
from compiler.token_types import TokenType, SQL_KEYWORDS


class GrammarInductionEngine:
    """
    Induces formal EBNF/Lark grammar rules by analyzing structural patterns in SQL queries.
    """

    def __init__(self, lexer: Optional[SqlLexer] = None):
        self.lexer = lexer or SqlLexer()
        self.observed_skeletons: Counter = Counter()
        self.observed_clauses: Set[str] = set()
        self.observed_operators: Set[str] = set()
        self.observed_functions: Set[str] = set()
        self.observed_statement_types: Set[str] = set()
        self.has_subqueries: bool = False
        self.has_joins: bool = False
        self.has_aggregates: bool = False
        self.has_parenthesized_logic: bool = False
        self.has_in_predicate: bool = False
        self.has_between_predicate: bool = False
        self.has_like_predicate: bool = False
        self.has_null_predicate: bool = False

    def reset(self):
        """Resets engine state."""
        self.observed_skeletons.clear()
        self.observed_clauses.clear()
        self.observed_operators.clear()
        self.observed_functions.clear()
        self.observed_statement_types.clear()
        self.has_subqueries = False
        self.has_joins = False
        self.has_aggregates = False
        self.has_parenthesized_logic = False
        self.has_in_predicate = False
        self.has_between_predicate = False
        self.has_like_predicate = False
        self.has_null_predicate = False

    def analyze_query_tokens(self, tokens: List[Any]) -> Dict[str, Any]:
        """
        Extracts structural indicators from a single token sequence.
        """
        keywords = [t.value for t in tokens if t.type == TokenType.KEYWORD]
        operators = [t.value for t in tokens if t.type == TokenType.OPERATOR]

        stmt_type = "UNKNOWN"
        if keywords:
            first_kw = keywords[0]
            if first_kw in ("SELECT", "INSERT", "UPDATE", "DELETE"):
                stmt_type = f"{first_kw}_STMT"

        # Detect clause skeleton
        clause_sequence = []
        i = 0
        while i < len(tokens):
            t = tokens[i]
            if t.type == TokenType.KEYWORD:
                val = t.value
                if val == "SELECT":
                    clause_sequence.append("SELECT")
                elif val == "FROM":
                    clause_sequence.append("FROM")
                elif val in ("JOIN", "INNER", "LEFT"):
                    clause_sequence.append("JOIN")
                elif val == "WHERE":
                    clause_sequence.append("WHERE")
                elif val == "GROUP" and i + 1 < len(tokens) and tokens[i+1].value == "BY":
                    clause_sequence.append("GROUP_BY")
                    i += 1
                elif val == "HAVING":
                    clause_sequence.append("HAVING")
                elif val == "ORDER" and i + 1 < len(tokens) and tokens[i+1].value == "BY":
                    clause_sequence.append("ORDER_BY")
                    i += 1
                elif val == "LIMIT":
                    clause_sequence.append("LIMIT")
                elif val == "INSERT":
                    clause_sequence.append("INSERT")
                elif val == "UPDATE":
                    clause_sequence.append("UPDATE")
                elif val == "DELETE":
                    clause_sequence.append("DELETE")
                elif val == "SET":
                    clause_sequence.append("SET")
                elif val == "VALUES":
                    clause_sequence.append("VALUES")
                elif val in ("COUNT", "SUM", "AVG", "MIN", "MAX"):
                    self.observed_functions.add(val)
                    self.has_aggregates = True
                elif val == "IN":
                    self.has_in_predicate = True
                elif val == "BETWEEN":
                    self.has_between_predicate = True
                elif val == "LIKE":
                    self.has_like_predicate = True
                elif val == "IS":
                    self.has_null_predicate = True
            elif t.type == TokenType.LPAREN:
                # Check for subquery: (SELECT ...
                if i + 1 < len(tokens) and tokens[i+1].value == "SELECT":
                    self.has_subqueries = True
                else:
                    self.has_parenthesized_logic = True

            i += 1

        skeleton_key = "->".join(clause_sequence)
        return {
            "stmt_type": stmt_type,
            "skeleton": skeleton_key,
            "keywords": keywords,
            "operators": operators
        }

    def train_on_queries(self, queries: List[str]) -> Dict[str, Any]:
        """
        Analyzes a dataset of valid queries and records structural statistics for induction.
        """
        self.reset()
        valid_count = 0

        for q in queries:
            tokens = self.lexer.tokenize(q)
            if not tokens:
                continue

            analysis = self.analyze_query_tokens(tokens)
            if analysis["stmt_type"] != "UNKNOWN":
                self.observed_statement_types.add(analysis["stmt_type"])
                self.observed_skeletons[analysis["skeleton"]] += 1
                for kw in analysis["keywords"]:
                    self.observed_clauses.add(kw)
                for op in analysis["operators"]:
                    self.observed_operators.add(op)
                valid_count += 1

        return {
            "queries_processed": valid_count,
            "statement_types": list(self.observed_statement_types),
            "skeletons_discovered": len(self.observed_skeletons),
            "top_skeletons": self.observed_skeletons.most_common(10),
            "has_joins": "JOIN" in self.observed_clauses or "INNER" in self.observed_clauses,
            "has_aggregates": self.has_aggregates,
            "has_subqueries": self.has_subqueries,
            "functions_found": list(self.observed_functions)
        }

    def generate_candidate_ebnf(self) -> str:
        """
        Synthesizes an EBNF grammar in Lark format from the induced structural knowledge.
        Rules are constructed dynamically based on observed language features.
        """
        ebnf_lines = [
            "// AutoGrammar Induced Grammar (Machine-Learned from Training Corpus)",
            f"// Inferred at: {datetime.datetime.now().isoformat()}",
            "// Discovered statement types: " + ", ".join(sorted(self.observed_statement_types)),
            "",
            "?start: statement [\";\"]",
            ""
        ]

        # 1. Statement rule induction
        stmt_branches = []
        if "SELECT_STMT" in self.observed_statement_types or not self.observed_statement_types:
            stmt_branches.append("select_stmt")
        if "INSERT_STMT" in self.observed_statement_types:
            stmt_branches.append("insert_stmt")
        if "UPDATE_STMT" in self.observed_statement_types:
            stmt_branches.append("update_stmt")
        if "DELETE_STMT" in self.observed_statement_types:
            stmt_branches.append("delete_stmt")

        ebnf_lines.append("?statement: " + "\n          | ".join(stmt_branches))
        ebnf_lines.append("")

        # 2. SELECT statement induction
        # Check optional clauses based on observed patterns
        sel_clauses = ["\"SELECT\"i", "[distinct_clause]", "select_list", "from_clause"]
        if "WHERE" in self.observed_clauses:
            sel_clauses.append("[where_clause]")
        if "GROUP" in self.observed_clauses:
            sel_clauses.append("[groupby_clause]")
        if "HAVING" in self.observed_clauses:
            sel_clauses.append("[having_clause]")
        if "ORDER" in self.observed_clauses:
            sel_clauses.append("[orderby_clause]")
        if "LIMIT" in self.observed_clauses:
            sel_clauses.append("[limit_clause]")

        ebnf_lines.append("select_stmt: " + " ".join(sel_clauses))
        ebnf_lines.append("distinct_clause: \"DISTINCT\"i")
        ebnf_lines.append("select_list: select_item (\",\" select_item)*")
        ebnf_lines.append("select_item: aggregate_expr [alias_clause]\n           | column_ref [alias_clause]\n           | \"*\"")
        ebnf_lines.append("alias_clause: [\"AS\"i] CNAME")
        ebnf_lines.append("")

        # 3. FROM and JOIN clauses
        if "JOIN" in self.observed_clauses or "INNER" in self.observed_clauses:
            ebnf_lines.append("from_clause: \"FROM\"i table_source (join_clause)*")
            ebnf_lines.append("join_clause: ([\"INNER\"i] \"JOIN\"i | \"LEFT\"i [\"JOIN\"i]) table_source \"ON\"i condition")
        else:
            ebnf_lines.append("from_clause: \"FROM\"i table_source")
        ebnf_lines.append("table_source: CNAME [\"AS\"i CNAME]")
        ebnf_lines.append("")

        # 4. WHERE and Predicates
        ebnf_lines.append("where_clause: \"WHERE\"i condition")
        ebnf_lines.append("?condition: or_expr")
        ebnf_lines.append("?or_expr: and_expr (\"OR\"i and_expr)*")
        ebnf_lines.append("?and_expr: not_expr (\"AND\"i not_expr)*")
        ebnf_lines.append("?not_expr: \"NOT\"i not_expr -> not_condition\n         | predicate")

        pred_branches = ["comparison_predicate"]
        if self.has_in_predicate:
            pred_branches.append("in_predicate")
        if self.has_between_predicate:
            pred_branches.append("between_predicate")
        if self.has_like_predicate:
            pred_branches.append("like_predicate")
        if self.has_null_predicate:
            pred_branches.append("null_predicate")
        pred_branches.append("\"(\" condition \")\"")

        ebnf_lines.append("?predicate: " + "\n          | ".join(pred_branches))
        ebnf_lines.append("comparison_predicate: expr COMP_OP expr")

        if self.has_in_predicate:
            if self.has_subqueries:
                ebnf_lines.append("in_predicate: expr \"IN\"i \"(\" (literal_list | select_stmt) \")\"")
            else:
                ebnf_lines.append("in_predicate: expr \"IN\"i \"(\" literal_list \")\"")

        if self.has_between_predicate:
            ebnf_lines.append("between_predicate: expr \"BETWEEN\"i expr \"AND\"i expr")

        if self.has_like_predicate:
            ebnf_lines.append("like_predicate: expr \"LIKE\"i STRING")

        if self.has_null_predicate:
            ebnf_lines.append("null_predicate: expr \"IS\"i [\"NOT\"i] \"NULL\"i")

        ebnf_lines.append("")

        # 5. Expressions & Literals
        expr_lines = ["?expr: aggregate_expr", "     | column_ref", "     | literal"]
        if self.has_subqueries:
            expr_lines.append("     | \"(\" select_stmt \")\" -> scalar_subquery")
        ebnf_lines.append("\n".join(expr_lines))

        func_pat = "|".join(sorted(self.observed_functions)) if self.observed_functions else "COUNT|SUM|AVG|MIN|MAX"
        ebnf_lines.append(f"AGG_FUNC.2: /(?i:{func_pat})/")
        ebnf_lines.append("aggregate_expr: AGG_FUNC \"(\" (column_ref | \"*\" | literal) \")\"")
        ebnf_lines.append("column_ref: [CNAME \".\"] (CNAME | \"*\")")
        ebnf_lines.append("literal_list: literal (\",\" literal)*")
        ebnf_lines.append("?literal: NUMBER | STRING")
        ebnf_lines.append("")

        # 6. GROUP BY, HAVING, ORDER BY, LIMIT
        if "GROUP" in self.observed_clauses:
            ebnf_lines.append("groupby_clause: \"GROUP\"i \"BY\"i group_item (\",\" group_item)*")
            ebnf_lines.append("group_item: column_ref")
        if "HAVING" in self.observed_clauses:
            ebnf_lines.append("having_clause: \"HAVING\"i condition")
        if "ORDER" in self.observed_clauses:
            ebnf_lines.append("orderby_clause: \"ORDER\"i \"BY\"i order_item (\",\" order_item)*")
            ebnf_lines.append("order_item: column_ref [\"ASC\"i | \"DESC\"i]")
        if "LIMIT" in self.observed_clauses:
            ebnf_lines.append("limit_clause: \"LIMIT\"i NUMBER")
        ebnf_lines.append("")

        # 7. DML statements (INSERT, UPDATE, DELETE)
        if "INSERT_STMT" in self.observed_statement_types:
            ebnf_lines.append("insert_stmt: \"INSERT\"i \"INTO\"i CNAME [\"(\" column_name_list \")\"] \"VALUES\"i \"(\" value_list \")\"")
            ebnf_lines.append("column_name_list: CNAME (\",\" CNAME)*")
            ebnf_lines.append("value_list: literal (\",\" literal)*")
            ebnf_lines.append("")
        if "UPDATE_STMT" in self.observed_statement_types:
            ebnf_lines.append("update_stmt: \"UPDATE\"i CNAME \"SET\"i set_assignment (\",\" set_assignment)* [where_clause]")
            ebnf_lines.append("set_assignment: CNAME \"=\" literal")
            ebnf_lines.append("")
        if "DELETE_STMT" in self.observed_statement_types:
            ebnf_lines.append("delete_stmt: \"DELETE\"i \"FROM\"i CNAME [where_clause]")
            ebnf_lines.append("")

        # 8. Terminals
        ebnf_lines.append("COMP_OP.2: \"<=\" | \">=\" | \"!=\" | \"<>\" | \"=\" | \"<\" | \">\"")
        ebnf_lines.append("%import common.CNAME")
        ebnf_lines.append("%import common.NUMBER")
        ebnf_lines.append("STRING: /'([^'\\\\]|\\\\.)*'/")
        ebnf_lines.append("%import common.WS")
        ebnf_lines.append("%ignore WS")

        return "\n".join(ebnf_lines)

    def validate_grammar(self, ebnf_text: str) -> Tuple[bool, Optional[str]]:
        """
        Validates candidate EBNF grammar using Lark parser engine.
        Returns (is_valid, error_message).
        """
        try:
            _ = Lark(ebnf_text, start="start", parser="earley")
            return True, None
        except LarkError as e:
            return False, str(e)

    def save_grammar(self, ebnf_text: str, target_path: str = "grammars/learned.lark") -> str:
        """Saves the induced grammar to the target path and creates a version snapshot."""
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(ebnf_text)

        # Version snapshot
        version_dir = os.path.join(os.path.dirname(target_path), "versions")
        os.makedirs(version_dir, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        version_path = os.path.join(version_dir, f"learned_{ts}.lark")
        with open(version_path, "w", encoding="utf-8") as f:
            f.write(ebnf_text)

        return version_path

    def refine_grammar_with_query(
        self,
        new_query: str,
        current_ebnf: str,
        approved: bool = False,
        save_path: str = "grammars/learned.lark"
    ) -> Dict[str, Any]:
        """
        Interactive grammar refinement:
        Analyzes a new candidate query, proposes candidate rule adjustments,
        and replaces the active grammar only upon approval.
        """
        tokens = self.lexer.tokenize(new_query)
        analysis = self.analyze_query_tokens(tokens)

        # Re-synthesize candidate with added structural patterns
        candidate_ebnf = self.generate_candidate_ebnf()
        is_valid, err = self.validate_grammar(candidate_ebnf)

        result = {
            "query": new_query,
            "detected_skeleton": analysis["skeleton"],
            "is_syntactically_sound": is_valid,
            "validation_error": err,
            "proposed_ebnf": candidate_ebnf,
            "applied": False
        }

        if approved and is_valid:
            self.save_grammar(candidate_ebnf, target_path=save_path)
            result["applied"] = True

        return result
