"""
Unit Tests for Automatic Grammar Induction and Dynamic Refinement.
"""

from compiler.grammar_induction import GrammarInductionEngine


def test_grammar_induction_from_queries():
    queries = [
        "SELECT first_name, last_name FROM students WHERE state = 'Karnataka';",
        "SELECT admission_no FROM students WHERE city = 'Bengaluru';",
        "SELECT COUNT(*) AS total FROM students GROUP BY class_id;",
        "INSERT INTO subjects (subject_id, subject_name) VALUES (10, 'History');",
        "UPDATE students SET status = 'Active' WHERE student_id = 1;"
    ]

    engine = GrammarInductionEngine()
    stats = engine.train_on_queries(queries)

    assert stats["queries_processed"] == 5
    assert "SELECT_STMT" in stats["statement_types"]
    assert "INSERT_STMT" in stats["statement_types"]
    assert "UPDATE_STMT" in stats["statement_types"]

    ebnf = engine.generate_candidate_ebnf()
    assert "select_stmt" in ebnf
    assert "insert_stmt" in ebnf
    assert "update_stmt" in ebnf

    is_valid, err = engine.validate_grammar(ebnf)
    assert is_valid, f"Generated grammar had syntax errors: {err}"


def test_grammar_refinement_workflow(tmp_path):
    engine = GrammarInductionEngine()
    engine.train_on_queries(["SELECT first_name FROM students;"])
    ebnf_before = engine.generate_candidate_ebnf()

    # User proposes new query with DELETE
    new_query = "DELETE FROM attendance WHERE attendance_id = 99;"
    test_save = str(tmp_path / "test_learned.lark")
    refinement = engine.refine_grammar_with_query(new_query, ebnf_before, approved=False, save_path=test_save)

    assert refinement["is_syntactically_sound"] is True
    assert refinement["applied"] is False  # Not applied without explicit approval

    # Now approve
    refinement_approved = engine.refine_grammar_with_query(new_query, ebnf_before, approved=True, save_path=test_save)
    assert refinement_approved["applied"] is True
