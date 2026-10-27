"""
Configurable Parser Component for AutoGrammar SQL DSL.
Loads and runs either the fixed baseline grammar or the automatically learned grammar.
"""

import os
from typing import Optional, Dict, Any, List
from lark import Lark, LarkError

from compiler.parse_tree import ParseTreeNode, extract_query_semantics
from compiler.error_handler import format_lark_syntax_error, CompilerDiagnostic


class AutoGrammarParser:
    """
    Parser capable of alternating between baseline and learned EBNF grammars.
    """

    def __init__(
        self,
        baseline_path: str = "grammars/baseline.lark",
        learned_path: str = "grammars/learned.lark",
        parser_type: str = "earley"
    ):
        self.baseline_path = baseline_path
        self.learned_path = learned_path
        self.parser_type = parser_type
        self._baseline_parser: Optional[Lark] = None
        self._learned_parser: Optional[Lark] = None

    def get_parser(self, grammar_choice: str = "learned") -> Lark:
        """Returns the requested parser instance, compiling it on demand."""
        grammar_choice = grammar_choice.lower()
        if grammar_choice == "baseline":
            if self._baseline_parser is None:
                if not os.path.exists(self.baseline_path):
                    raise FileNotFoundError(f"Baseline grammar not found at {self.baseline_path}")
                with open(self.baseline_path, "r", encoding="utf-8") as f:
                    self._baseline_parser = Lark(f.read(), start="start", parser=self.parser_type, ambiguity="resolve")
            return self._baseline_parser

        elif grammar_choice == "learned":
            if self._learned_parser is None:
                if not os.path.exists(self.learned_path):
                    raise FileNotFoundError(f"Learned grammar not found at {self.learned_path}. Run grammar induction first.")
                with open(self.learned_path, "r", encoding="utf-8") as f:
                    self._learned_parser = Lark(f.read(), start="start", parser=self.parser_type, ambiguity="resolve")
            return self._learned_parser

        else:
            raise ValueError(f"Unknown grammar choice '{grammar_choice}'. Choose 'baseline' or 'learned'.")

    def reload_learned_grammar(self):
        """Forces reloading of the learned grammar from disk (after refinement)."""
        self._learned_parser = None

    def parse(self, query: str, grammar_choice: str = "learned") -> Dict[str, Any]:
        """
        Parses a query string using the chosen grammar.
        Returns a comprehensive parse result dictionary.
        """
        try:
            parser = self.get_parser(grammar_choice)
        except Exception as e:
            return {
                "success": False,
                "grammar_choice": grammar_choice,
                "tree": None,
                "ascii_tree": "",
                "diagnostics": [CompilerDiagnostic("BACKEND", f"Failed to initialize {grammar_choice} parser: {str(e)}")],
                "semantics": {}
            }

        try:
            tree = parser.parse(query)
            pt_node = ParseTreeNode.from_lark_tree(tree)
            ascii_repr = pt_node.to_ascii_tree() if isinstance(pt_node, ParseTreeNode) else str(pt_node)
            semantics = extract_query_semantics(tree)

            return {
                "success": True,
                "grammar_choice": grammar_choice,
                "tree": tree,
                "ascii_tree": ascii_repr,
                "diagnostics": [],
                "semantics": semantics
            }
        except LarkError as e:
            diag = format_lark_syntax_error(e, query)
            return {
                "success": False,
                "grammar_choice": grammar_choice,
                "tree": None,
                "ascii_tree": "",
                "diagnostics": [diag],
                "semantics": {}
            }
        except Exception as e:
            diag = CompilerDiagnostic("BACKEND", f"Unexpected parsing error: {str(e)}")
            return {
                "success": False,
                "grammar_choice": grammar_choice,
                "tree": None,
                "ascii_tree": "",
                "diagnostics": [diag],
                "semantics": {}
            }
