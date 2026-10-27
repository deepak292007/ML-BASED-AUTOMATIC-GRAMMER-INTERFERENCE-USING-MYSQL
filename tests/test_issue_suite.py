"""
Regression and Verification Suite for AutoGrammar Issues 1-8.
Validates:
  Issue 1: Aggregate functions and COUNT(*) parsing in both Baseline and Learned grammars.
  Issue 2: Agreement/disagreement measurement between Baseline and Learned grammars over validation dataset.
  Issue 3: Aliased JOIN query support in compiler and ML Linear SVM.
  Issue 4: ML model separation from compiler authority (disagreement message without overriding compiler).
  Issue 5: Error classification (SECURITY, LEXICAL, SYNTAX, SEMANTIC, BACKEND).
  Issue 6: Real Python Lark Earley compiler integration.
  Issue 7: Test Suites A through G with full structured reporting.
  Issue 8: Canonical schema validation (subjects, teachers, classes, students, marks, attendance).
"""

import os
import joblib
import pandas as pd
import pytest
from starlette.testclient import TestClient

from compiler.lexer import SqlLexer, TokenType
from compiler.parser import AutoGrammarParser
from compiler.semantic_checker import SemanticChecker, SCHOOL_DB_SCHEMA
from compiler.query_validator import QueryValidator
from server import app


@pytest.fixture(scope="module")
def validator():
    return QueryValidator()


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def ml_model():
    clf_path = "ml/saved_models/classifier.joblib"
    vec_path = "ml/saved_models/vectorizer.joblib"
    if os.path.exists(clf_path) and os.path.exists(vec_path):
        clf = joblib.load(clf_path)
        vec = joblib.load(vec_path)
        return clf, vec
    return None, None


def evaluate_query_pipeline(validator, ml_model, query: str):
    """Evaluates query across baseline, learned, semantics, security, and ML."""
    tokens = validator.lexer.tokenize(query)

    # Baseline grammar parse
    try:
        t_base = validator.parser.parse(query, grammar_choice="baseline")
        base_syntax_ok = True
    except Exception:
        base_syntax_ok = False

    # Learned grammar parse
    try:
        t_learn = validator.parser.parse(query, grammar_choice="learned")
        learn_syntax_ok = True
    except Exception:
        learn_syntax_ok = False

    # Validation (Baseline pipeline)
    val_base = validator.validate(query, grammar_choice="baseline")
    # Validation (Learned pipeline)
    val_learn = validator.validate(query, grammar_choice="learned")

    # Security check
    sec_diags = validator.check_security(query, tokens, {})
    sec_ok = len(sec_diags) == 0

    # Semantic check (if semantics extracted)
    sem_ok = False
    if val_base.get("semantics"):
        sem_diags = validator.semantic_checker.validate_semantics(val_base["semantics"])
        sem_ok = len(sem_diags) == 0

    # ML prediction
    ml_pred = "N/A"
    ml_score = 0.0
    ml_prob = 0.0
    clf, vec = ml_model
    if clf is not None and vec is not None:
        feat = vec.transform([query])
        pred_int = int(clf.predict(feat)[0])
        ml_pred = "ACCEPT" if pred_int == 1 else "REJECT"
        if hasattr(clf, "predict_proba"):
            ml_prob = float(clf.predict_proba(feat)[0][1])
        if hasattr(clf, "decision_function"):
            ml_score = float(clf.decision_function(feat)[0])

    return {
        "query": query,
        "base_syntax": "ACCEPT" if base_syntax_ok else "REJECT",
        "learn_syntax": "ACCEPT" if learn_syntax_ok else "REJECT",
        "val_base_valid": val_base["valid"],
        "val_learn_valid": val_learn["valid"],
        "stage_reached": val_base["stage_reached"],
        "semantic_result": "ACCEPT" if sem_ok else "REJECT",
        "security_result": "ACCEPT" if sec_ok else "REJECT",
        "ml_pred": ml_pred,
        "ml_prob": round(ml_prob, 4),
        "ml_score": round(ml_score, 4),
        "diagnostics": [d.message for d in val_base["diagnostics"]]
    }


# ===========================================================================
# ISSUE 7: TESTS A THROUGH G
# ===========================================================================

class TestRegressionSuitesAThroughG:

    def test_suite_a_basic_valid_queries(self, validator, ml_model):
        """Test A: Basic valid queries."""
        queries = [
            "SELECT * FROM students;",
            "SELECT first_name, last_name FROM students;",
            "SELECT * FROM subjects;",
            "SELECT COUNT(*) FROM subjects;"
        ]
        results = []
        for q in queries:
            eval_res = evaluate_query_pipeline(validator, ml_model, q)
            passed = (eval_res["val_base_valid"] is True and eval_res["val_learn_valid"] is True)
            eval_res["expected"] = "ACCEPT"
            eval_res["passed"] = passed
            results.append(eval_res)
            print(f"\n[Test A] Query: {q}")
            print(f"  Expected: ACCEPT | Baseline: {eval_res['base_syntax']} | Learned: {eval_res['learn_syntax']} | Semantic: {eval_res['semantic_result']} | Security: {eval_res['security_result']} | ML: {eval_res['ml_pred']} | Passed: {passed}")
            assert passed, f"Failed on query: {q}"

    def test_suite_b_aggregate_functions(self, validator, ml_model):
        """Test B: Aggregate functions."""
        queries = [
            "SELECT COUNT(subject_id) FROM subjects;",
            "SELECT AVG(marks_obtained) FROM marks;",
            "SELECT SUM(marks_obtained) FROM marks;",
            "SELECT MIN(marks_obtained) FROM marks;",
            "SELECT MAX(marks_obtained) FROM marks;"
        ]
        for q in queries:
            eval_res = evaluate_query_pipeline(validator, ml_model, q)
            passed = (eval_res["val_base_valid"] is True and eval_res["val_learn_valid"] is True)
            print(f"\n[Test B] Query: {q}")
            print(f"  Expected: ACCEPT | Baseline: {eval_res['base_syntax']} | Learned: {eval_res['learn_syntax']} | Semantic: {eval_res['semantic_result']} | Security: {eval_res['security_result']} | ML: {eval_res['ml_pred']} | Passed: {passed}")
            assert passed, f"Failed on aggregate query: {q}"

    def test_suite_c_aliases_and_join(self, validator, ml_model):
        """Test C: Aliases and JOIN."""
        queries = [
            "SELECT s.first_name FROM students AS s;",
            "SELECT s.first_name, m.marks_obtained FROM students AS s JOIN marks AS m ON s.student_id = m.student_id;",
            "SELECT students.first_name, marks.marks_obtained FROM students JOIN marks ON students.student_id = marks.student_id;"
        ]
        for q in queries:
            eval_res = evaluate_query_pipeline(validator, ml_model, q)
            passed = (eval_res["val_base_valid"] is True and eval_res["val_learn_valid"] is True)
            print(f"\n[Test C] Query: {q}")
            print(f"  Expected: ACCEPT | Baseline: {eval_res['base_syntax']} | Learned: {eval_res['learn_syntax']} | Semantic: {eval_res['semantic_result']} | Security: {eval_res['security_result']} | ML: {eval_res['ml_pred']} | Passed: {passed}")
            assert passed, f"Failed on aliased/join query: {q}"
            # Specific verification for Issue 3
            if "students AS s JOIN marks AS m" in q:
                assert eval_res["ml_pred"] == "ACCEPT", f"Issue 3 query rejected by ML: {eval_res}"

    def test_suite_d_aggregate_with_conditions(self, validator, ml_model):
        """Test D: Aggregate with conditions."""
        queries = [
            "SELECT COUNT(*) FROM students WHERE city = 'Guntur';",
            "SELECT exam_name, AVG(marks_obtained) FROM marks GROUP BY exam_name;"
        ]
        for q in queries:
            eval_res = evaluate_query_pipeline(validator, ml_model, q)
            passed = (eval_res["val_base_valid"] is True and eval_res["val_learn_valid"] is True)
            print(f"\n[Test D] Query: {q}")
            print(f"  Expected: ACCEPT | Baseline: {eval_res['base_syntax']} | Learned: {eval_res['learn_syntax']} | Semantic: {eval_res['semantic_result']} | Security: {eval_res['security_result']} | ML: {eval_res['ml_pred']} | Passed: {passed}")
            assert passed, f"Failed on conditional aggregate: {q}"

    def test_suite_e_invalid_syntax(self, validator, ml_model):
        """Test E: Invalid syntax."""
        queries = [
            "SELECT COUNT( FROM subjects;",
            "SELECT * FROM students WHERE city =;",
            "SELECT FROM students;",
            "SELECT COUNT(*) subjects;"
        ]
        for q in queries:
            eval_res = evaluate_query_pipeline(validator, ml_model, q)
            passed = (eval_res["val_base_valid"] is False and eval_res["val_learn_valid"] is False)
            print(f"\n[Test E] Query: {q}")
            print(f"  Expected: REJECT | Baseline: {eval_res['base_syntax']} | Learned: {eval_res['learn_syntax']} | Semantic: {eval_res['semantic_result']} | Security: {eval_res['security_result']} | ML: {eval_res['ml_pred']} | Passed: {passed}")
            assert passed, f"Expected syntax rejection for query: {q}"
            assert eval_res["stage_reached"] == "SYNTAX"

    def test_suite_f_semantic_errors(self, validator, ml_model):
        """Test F: Semantic errors."""
        queries = [
            "SELECT unknown_column FROM students;",
            "SELECT * FROM unknown_table;",
            "SELECT AVG(unknown_column) FROM marks;",
            "SELECT s.unknown_column FROM students AS s;"
        ]
        for q in queries:
            eval_res = evaluate_query_pipeline(validator, ml_model, q)
            # Syntax should accept (it's syntactically SQL), but semantic check must REJECT
            passed = (eval_res["base_syntax"] == "ACCEPT" and eval_res["val_base_valid"] is False and eval_res["stage_reached"] == "SEMANTIC")
            print(f"\n[Test F] Query: {q}")
            print(f"  Expected: REJECT (SEMANTIC) | Baseline: {eval_res['base_syntax']} | Learned: {eval_res['learn_syntax']} | Semantic: {eval_res['semantic_result']} | Security: {eval_res['security_result']} | ML: {eval_res['ml_pred']} | Passed: {passed}")
            assert passed, f"Expected semantic rejection for query: {q}"

    def test_suite_g_security(self, validator, ml_model):
        """Test G: Security violations."""
        queries = [
            "DROP TABLE students;",
            "DELETE FROM students;",
            "UPDATE students SET status = 'Inactive';",
            "SELECT * FROM students; DROP TABLE students;"
        ]
        for q in queries:
            eval_res = evaluate_query_pipeline(validator, ml_model, q)
            passed = (eval_res["val_base_valid"] is False and eval_res["stage_reached"] == "SECURITY")
            print(f"\n[Test G] Query: {q}")
            print(f"  Expected: REJECT (SECURITY) | Baseline: {eval_res['base_syntax']} | Learned: {eval_res['learn_syntax']} | Semantic: {eval_res['semantic_result']} | Security: {eval_res['security_result']} | ML: {eval_res['ml_pred']} | Passed: {passed}")
            assert passed, f"Expected security rejection for query: {q}"


# ===========================================================================
# ISSUE 2: MEASURE AGREEMENT AND DISAGREEMENT OVER VALIDATION DATASET
# ===========================================================================

def test_issue_2_agreement_measurement(validator):
    """Measures actual empirical agreement and disagreement over data/validation.csv."""
    val_path = "data/validation.csv"
    assert os.path.exists(val_path), "Validation dataset data/validation.csv not found."
    df = pd.read_csv(val_path)

    total = len(df)
    both_accept = 0
    both_reject = 0
    baseline_accept_learned_reject = 0
    baseline_reject_learned_accept = 0

    for _, row in df.iterrows():
        q = row["query_text"]
        res_b = validator.validate(q, grammar_choice="baseline")
        res_l = validator.validate(q, grammar_choice="learned")

        b_ok = res_b["valid"]
        l_ok = res_l["valid"]

        if b_ok and l_ok:
            both_accept += 1
        elif not b_ok and not l_ok:
            both_reject += 1
        elif b_ok and not l_ok:
            baseline_accept_learned_reject += 1
        elif not b_ok and l_ok:
            baseline_reject_learned_accept += 1

    total_agreement = both_accept + both_reject
    total_disagreement = baseline_accept_learned_reject + baseline_reject_learned_accept
    agreement_pct = (total_agreement / total) * 100.0

    print(f"\n=== Validation Dataset Agreement Metrics (N={total}) ===")
    print(f"  Both Accept:                      {both_accept} ({both_accept/total*100:.2f}%)")
    print(f"  Both Reject:                      {both_reject} ({both_reject/total*100:.2f}%)")
    print(f"  Baseline Accept, Learned Reject:  {baseline_accept_learned_reject} ({baseline_accept_learned_reject/total*100:.2f}%)")
    print(f"  Baseline Reject, Learned Accept:  {baseline_reject_learned_accept} ({baseline_reject_learned_accept/total*100:.2f}%)")
    print(f"  Overall Agreement Rate:           {agreement_pct:.2f}%")
    print(f"  Total Disagreements:              {total_disagreement} ({total_disagreement/total*100:.2f}%)")

    # Both grammars should have high agreement on the representative validation dataset
    assert agreement_pct >= 95.0, f"Agreement rate {agreement_pct:.2f}% is lower than 95% threshold"


# ===========================================================================
# ISSUE 4: ML CLASSIFIER MUST NOT OVERRIDE THE COMPILER
# ===========================================================================

def test_issue_4_ml_never_overrides_compiler(client):
    """
    Verifies that when the compiler rejects a query, safe_to_execute is False even if ML predicts ACCEPT.
    When compiler accepts and ML rejects, safe_to_execute is True and informative disagreement is displayed.
    """
    # 1. Compiler REJECTS (security violation), ML might predict ACCEPT or REJECT -> must remain safe_to_execute = False
    resp1 = client.post("/api/validate", json={"query": "DROP TABLE students;"})
    data1 = resp1.json()
    assert data1["baseline"]["valid"] is False
    assert data1["safe_to_execute"] is False

    # 2. Compiler REJECTS (semantic error: nonexistent table) -> safe_to_execute = False
    resp2 = client.post("/api/validate", json={"query": "SELECT * FROM nonexistent_table;"})
    data2 = resp2.json()
    assert data2["baseline"]["valid"] is False
    assert data2["safe_to_execute"] is False

    # 3. Compiler ACCEPTS a valid query -> safe_to_execute is True, and if ML disagrees, message is presented
    resp3 = client.post("/api/validate", json={"query": "SELECT COUNT(*) FROM subjects;"})
    data3 = resp3.json()
    assert data3["baseline"]["valid"] is True
    assert data3["safe_to_execute"] is True
    if data3.get("ml_disagreement"):
        assert "The compiler accepts this query. The experimental ML classifier disagrees and predicts REJECT" in data3["ml_override_message"]


# ===========================================================================
# ISSUE 8: CANONICAL SCHEMA VERIFICATION
# ===========================================================================

def test_issue_8_canonical_database_schema(validator):
    """
    Verifies canonical schema:
    subjects: subject_id, subject_name
    teachers: teacher_id, first_name, last_name, subject_id
    classes: class_id, class_name, academic_year, class_teacher_id
    students: student_id, admission_no, first_name, last_name, class_id, section, date_of_birth, gender, city, state, enrollment_date, status
    marks: mark_id, student_id, subject_id, exam_name, marks_obtained, maximum_marks, exam_date
    attendance: attendance_id, student_id, attendance_date, attendance_status
    """
    assert "subjects" in SCHOOL_DB_SCHEMA
    assert set(SCHOOL_DB_SCHEMA["subjects"]) == {"subject_id", "subject_name"}

    assert "teachers" in SCHOOL_DB_SCHEMA
    assert set(SCHOOL_DB_SCHEMA["teachers"]) == {"teacher_id", "first_name", "last_name", "subject_id"}

    assert "classes" in SCHOOL_DB_SCHEMA
    assert set(SCHOOL_DB_SCHEMA["classes"]) == {"class_id", "class_name", "academic_year", "class_teacher_id"}

    assert "students" in SCHOOL_DB_SCHEMA
    assert set(SCHOOL_DB_SCHEMA["students"]) == {
        "student_id", "admission_no", "first_name", "last_name", "class_id",
        "section", "date_of_birth", "gender", "city", "state", "enrollment_date", "status"
    }

    assert "marks" in SCHOOL_DB_SCHEMA
    assert set(SCHOOL_DB_SCHEMA["marks"]) == {
        "mark_id", "student_id", "subject_id", "exam_name", "marks_obtained", "maximum_marks", "exam_date"
    }

    assert "attendance" in SCHOOL_DB_SCHEMA
    assert set(SCHOOL_DB_SCHEMA["attendance"]) == {
        "attendance_id", "student_id", "attendance_date", "attendance_status"
    }

    # COUNT(*) should not be treated as a column reference
    res = validator.validate("SELECT COUNT(*) FROM subjects;", grammar_choice="baseline")
    assert res["valid"] is True
    # Verify no diagnostic for unknown column '*'
    assert not any("*" in d.message for d in res["diagnostics"])
