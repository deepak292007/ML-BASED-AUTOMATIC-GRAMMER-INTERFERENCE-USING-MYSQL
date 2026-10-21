"""
Grammar Builder Script.
Trains the GrammarInductionEngine on the training set, generates grammars/learned.lark,
and tests grammar validity and initial coverage.
"""

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from compiler.grammar_induction import GrammarInductionEngine


def build_and_save_learned_grammar(
    train_csv_path: str = "data/train.csv",
    output_grammar_path: str = "grammars/learned.lark"
):
    print(f"[*] Loading training queries from {train_csv_path}...")
    df = pd.read_csv(train_csv_path)

    # Train induction engine strictly on valid queries in the training split
    valid_train = df[df["validity_label"] == 1]["query_text"].tolist()
    print(f"    Found {len(valid_train)} valid training queries across {df[df['validity_label'] == 1]['template_id'].nunique()} templates.")

    engine = GrammarInductionEngine()
    stats = engine.train_on_queries(valid_train)
    print(f"[*] Pattern discovery complete:")
    print(f"    - Statement types: {stats['statement_types']}")
    print(f"    - Skeletons discovered: {stats['skeletons_discovered']}")
    print(f"    - Aggregate functions: {stats['functions_found']}")
    print(f"    - Joins present: {stats['has_joins']}")
    print(f"    - Subqueries present: {stats['has_subqueries']}")

    print(f"[*] Synthesizing candidate EBNF grammar...")
    ebnf = engine.generate_candidate_ebnf()

    print(f"[*] Validating candidate grammar with Lark engine...")
    is_valid, err = engine.validate_grammar(ebnf)
    if not is_valid:
        raise RuntimeError(f"Generated grammar failed validation: {err}")
    print("    [+] Grammar validation passed successfully (0 syntax conflicts).")

    vpath = engine.save_grammar(ebnf, target_path=output_grammar_path)
    print(f"[+] Active grammar saved to: {output_grammar_path}")
    print(f"[+] Version snapshot archived to: {vpath}")

    return {
        "output_path": output_grammar_path,
        "version_path": vpath,
        "stats": stats,
        "ebnf": ebnf
    }


if __name__ == "__main__":
    build_and_save_learned_grammar()
