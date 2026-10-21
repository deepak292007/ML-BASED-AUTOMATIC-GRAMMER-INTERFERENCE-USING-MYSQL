"""
Baseline Reference Grammar Loader and EBNF Specification.
Provides access to the manually authored reference grammar for comparison against the induced grammar.
"""

import os
from lark import Lark


BASELINE_GRAMMAR_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "grammars",
    "baseline.lark"
)


def get_baseline_ebnf_rules() -> str:
    """Reads the raw Lark EBNF text from the baseline grammar file."""
    with open(BASELINE_GRAMMAR_PATH, "r", encoding="utf-8") as f:
        return f.read()


def build_baseline_parser(parser_type: str = "earley") -> Lark:
    """Compiles the baseline Lark grammar into a Lark parser instance."""
    ebnf = get_baseline_ebnf_rules()
    return Lark(ebnf, start="start", parser=parser_type, ambiguity="resolve")
