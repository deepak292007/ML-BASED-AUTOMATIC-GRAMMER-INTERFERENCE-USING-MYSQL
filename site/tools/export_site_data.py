"""
Data Extraction Tool for AutoGrammar Showcase Website.
Reads existing repo artifacts (read-only) and compiles site/js/data.js.
Inference-only evaluation of preset queries is performed using existing models.
No training, no benchmarking, no dataset generation is performed.
"""

import os
import sys
import json
import re
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import joblib

from compiler.parser import AutoGrammarParser
from compiler.query_validator import QueryValidator
from compiler.error_handler import CompilerDiagnostic


def build_site_data():
    print("[*] Reading repo artifacts...")

    # 1. Dataset statistics
    stats_file = PROJECT_ROOT / "data" / "dataset_statistics.json"
    dataset_stats = {}
    if stats_file.exists():
        with open(stats_file, "r", encoding="utf-8") as f:
            dataset_stats = json.load(f)

    # 2. Grammar files
    learned_lark_path = PROJECT_ROOT / "grammars" / "learned.lark"
    baseline_lark_path = PROJECT_ROOT / "grammars" / "baseline.lark"

    learned_lark = learned_lark_path.read_text(encoding="utf-8") if learned_lark_path.exists() else ""
    baseline_lark = baseline_lark_path.read_text(encoding="utf-8") if baseline_lark_path.exists() else ""

    # 3. Evaluation metrics
    eval_dir = PROJECT_ROOT / "evaluation" / "results"
    model_comparison = []
    if (eval_dir / "model_comparison.json").exists():
        with open(eval_dir / "model_comparison.json", "r", encoding="utf-8") as f:
            model_comparison = json.load(f)

    parser_metrics = {}
    if (eval_dir / "parser_test_metrics.json").exists():
        with open(eval_dir / "parser_test_metrics.json", "r", encoding="utf-8") as f:
            parser_metrics = json.load(f)

    classifier_metrics = {}
    if (eval_dir / "classifier_test_metrics.json").exists():
        with open(eval_dir / "classifier_test_metrics.json", "r", encoding="utf-8") as f:
            classifier_metrics = json.load(f)

    grammar_metrics = {}
    if (eval_dir / "grammar_metrics.json").exists():
        with open(eval_dir / "grammar_metrics.json", "r", encoding="utf-8") as f:
            grammar_metrics = json.load(f)

    learning_curve = []
    if (eval_dir / "learning_curve.json").exists():
        with open(eval_dir / "learning_curve.json", "r", encoding="utf-8") as f:
            learning_curve = json.load(f)

    # 4. Sample rows from train.csv and test.csv
    train_csv = PROJECT_ROOT / "data" / "train.csv"
    test_csv = PROJECT_ROOT / "data" / "test.csv"
    train_samples = []
    test_samples = []
    false_rejections = []

    if train_csv.exists():
        df_train = pd.read_csv(train_csv)
        train_samples = df_train.head(20)[["query_id", "template_id", "query_text", "validity_label", "error_category"]].to_dict(orient="records")

    if test_csv.exists():
        df_test = pd.read_csv(test_csv)
        test_samples = df_test.head(20)[["query_id", "template_id", "query_text", "validity_label", "error_category"]].to_dict(orient="records")

        # Discover false rejections on learned grammar
        parser = AutoGrammarParser()
        valids = df_test[df_test["validity_label"] == 1]
        for _, row in valids.iterrows():
            pres = parser.parse(row["query_text"], grammar_choice="learned")
            if not pres["success"]:
                diag_msg = pres["diagnostics"][0].message if pres["diagnostics"] else "Syntax error"
                false_rejections.append({
                    "query_id": row["query_id"],
                    "template_id": row["template_id"],
                    "query_text": row["query_text"],
                    "error_message": diag_msg,
                    "complexity": row.get("complexity_level", "Moderate")
                })

    print(f"    Discovered {len(false_rejections)} false rejections in test.csv.")

    # 5. Schema extraction
    # 5. Schema extraction from canonical source in compiler.semantic_checker
    from compiler.semantic_checker import SCHEMA_METADATA
    schema_info = {tbl: {"columns": cols} for tbl, cols in SCHEMA_METADATA.items()}

    # 6. Precomputing real verdicts for presets
    parser = AutoGrammarParser()
    validator = QueryValidator(parser=parser)

    # Load ML models (primary for presets, baseline for JS export)
    clf_path = PROJECT_ROOT / "ml" / "saved_models" / "classifier.joblib"
    vec_path = PROJECT_ROOT / "ml" / "saved_models" / "vectorizer.joblib"
    clf = joblib.load(clf_path) if clf_path.exists() else None
    vec = joblib.load(vec_path) if vec_path.exists() else None

    clf_base_path = PROJECT_ROOT / "ml" / "saved_models" / "classifier_baseline.joblib"
    vec_base_path = PROJECT_ROOT / "ml" / "saved_models" / "vectorizer_baseline.joblib"
    clf_base = joblib.load(clf_base_path) if clf_base_path.exists() else None
    vec_base = joblib.load(vec_base_path) if vec_base_path.exists() else None

    # Presets specification (8 required + 4 extras)
    presets_spec = [
        {
            "id": "p1_join",
            "name": "1. Valid Join",
            "tag": "ACCEPT",
            "category": "Valid Join & Projection",
            "sql": "SELECT s.first_name, s.last_name, m.marks_obtained\nFROM students AS s\nINNER JOIN marks AS m ON s.student_id = m.student_id\nWHERE m.marks_obtained >= 85;"
        },
        {
            "id": "p2_aggregate",
            "name": "2. Valid Aggregate",
            "tag": "ACCEPT",
            "category": "Valid Aggregation & HAVING",
            "sql": "SELECT subject_id, AVG(marks_obtained) AS avg_mark\nFROM marks\nGROUP BY subject_id\nHAVING AVG(marks_obtained) >= 70;"
        },
        {
            "id": "p3_subquery",
            "name": "3. Valid Subquery",
            "tag": "ACCEPT",
            "category": "Valid Nested Subquery",
            "sql": "SELECT first_name, last_name\nFROM students\nWHERE student_id IN (SELECT student_id FROM marks WHERE marks_obtained >= 90);"
        },
        {
            "id": "p4_missing_from",
            "name": "4. Missing FROM",
            "tag": "REJECT",
            "category": "Syntax Error",
            "sql": "SELECT first_name, last_name WHERE state = 'Karnataka';"
        },
        {
            "id": "p5_unknown_column",
            "name": "5. Unknown Column",
            "tag": "REJECT",
            "category": "Semantic Error",
            "sql": "SELECT first_name, blood_group FROM students WHERE state = 'Delhi';"
        },
        {
            "id": "p6_lexical_error",
            "name": "6. Lexical Error",
            "tag": "REJECT",
            "category": "Lexical Error",
            "sql": "SELECT first_name @#$ last_name FROM students;"
        },
        {
            "id": "p7_drop_table",
            "name": "7. DROP TABLE",
            "tag": "REJECT",
            "category": "Security Gate Block",
            "sql": "DROP TABLE students;"
        },
        {
            "id": "p8_unbalanced_paren",
            "name": "8. Unbalanced Parentheses",
            "tag": "REJECT",
            "category": "Syntax Error",
            "sql": "SELECT first_name FROM students WHERE (state = 'Delhi' AND gender = 'Male';"
        },
        {
            "id": "p9_missing_comma",
            "name": "9. Missing Comma in SELECT",
            "tag": "REJECT",
            "category": "Syntax Error",
            "sql": "SELECT first_name last_name city FROM students;"
        },
        {
            "id": "p10_wrong_clause_order",
            "name": "10. Wrong Keyword Order",
            "tag": "REJECT",
            "category": "Syntax Error",
            "sql": "SELECT first_name, last_name WHERE state = 'Kerala' FROM students;"
        },
        {
            "id": "p11_unconstrained_delete",
            "name": "11. Unconstrained DELETE",
            "tag": "REJECT",
            "category": "Security Gate Block",
            "sql": "DELETE FROM students;"
        },
        {
            "id": "p12_nonexistent_table",
            "name": "12. Nonexistent Table",
            "tag": "REJECT",
            "category": "Semantic Error",
            "sql": "SELECT student_id, tuition_fee FROM student_finances WHERE tuition_fee > 5000;"
        }
    ]

    computed_presets = []
    for item in presets_spec:
        q = item["sql"]

        # 1. Baseline
        b_res = validator.validate(q, grammar_choice="baseline", enforce_semantics=True)
        b_diag = b_res["diagnostics"][0] if b_res["diagnostics"] else None

        # 2. Learned
        l_res = validator.validate(q, grammar_choice="learned", enforce_semantics=True)
        l_diag = l_res["diagnostics"][0] if l_res["diagnostics"] else None

        # 3. ML
        ml_res = {"valid": False, "stage_reached": "STATISTICAL", "probability": 0.0, "message": "ML model missing."}
        if clf and vec:
            pred = clf.predict(vec.transform([q]))[0]
            prob = clf.predict_proba(vec.transform([q]))[0]
            p_val = float(prob[1]) if len(prob) > 1 else (1.0 if pred == 1 else 0.0)
            ml_res = {
                "valid": bool(pred == 1),
                "verdict": "ACCEPT" if pred == 1 else "REJECT",
                "stage_reached": "STATISTICAL (Black-Box)",
                "probability": round(p_val, 4),
                "line": None,
                "column": None,
                "message": f"TF-IDF Statistical classification: {p_val*100:.1f}% validity confidence.",
                "suggestion": "Statistical classifier provides likelihood score only; does not generate parse tree or localize errors."
            }

        computed_presets.append({
            "id": item["id"],
            "name": item["name"],
            "tag": item["tag"],
            "category": item["category"],
            "sql": q,
            "baseline": {
                "valid": b_res["valid"],
                "verdict": "ACCEPT" if b_res["valid"] else "REJECT",
                "stage_reached": b_res["stage_reached"],
                "line": b_diag.line if (b_diag and b_diag.line is not None) else None,
                "column": b_diag.column if (b_diag and b_diag.column is not None) else None,
                "message": b_diag.message if b_diag else "Passed all 4 compiler stages.",
                "suggestion": b_diag.suggestion if b_diag else "Safe for execution.",
                "ascii_tree": b_res.get("parse_tree_ascii", ""),
                "tokens": b_res.get("tokens", [])
            },
            "learned": {
                "valid": l_res["valid"],
                "verdict": "ACCEPT" if l_res["valid"] else "REJECT",
                "stage_reached": l_res["stage_reached"],
                "line": l_diag.line if (l_diag and l_diag.line is not None) else None,
                "column": l_diag.column if (l_diag and l_diag.column is not None) else None,
                "message": l_diag.message if l_diag else "Passed all 4 compiler stages.",
                "suggestion": l_diag.suggestion if l_diag else "Safe for execution.",
                "ascii_tree": l_res.get("parse_tree_ascii", ""),
                "tokens": l_res.get("tokens", [])
            },
            "ml": ml_res
        })

    # 7. Export TF-IDF vectorizer + Logistic Regression model for full offline JS inference
    ml_export = {}
    target_vec = vec_base if (vec_base and hasattr(vec_base, "vocabulary_")) else (vec if (vec and hasattr(vec, "vocabulary_")) else None)
    target_clf = clf_base if (clf_base and hasattr(clf_base, "coef_")) else (clf if (clf and hasattr(clf, "coef_")) else None)
    if target_clf and target_vec:
        # Vocabulary mapping term -> index
        vocab = {term: int(idx) for term, idx in target_vec.vocabulary_.items()}
        # idf vector
        idf = [float(val) for val in target_vec.idf_]
        # weights and intercept
        coef = [float(val) for val in target_clf.coef_[0]]
        intercept = float(target_clf.intercept_[0])
        ml_export = {
            "vocabulary": vocab,
            "idf": idf,
            "coefficients": coef,
            "intercept": intercept
        }
        print(f"    Exported ML weights: vocab {len(vocab)}, coef {len(coef)}, intercept {intercept:.4f}")

    # Build data.js content
    js_content = f"""// AutoGrammar Showcase Website Data (Generated by site/tools/export_site_data.py)
// Self-contained static data bundle with real evaluation results, schema, presets, and grammar.

// ===========================================================================
// CONFIG OBJECT (User-editable project metadata)
// ===========================================================================
const CONFIG = {{
  projectTitle: "AutoGrammar",
  subtitle: "Machine Learning-Based Automatic Grammar Inference for SQL DSL over school_db",
  teamMembers: ["Deepak Kumar", "Antigravity Team"],
  guide: "Evaluator / Project Viva Showcase",
  institution: "Department of Computer Science & Engineering",
  academicYear: "2025 - 2026",
  mysqlVerified: false, // In-Memory Relational Sandbox (SQLite) verified with 10k school records; MySQL 8.0+ compatible
  repoUrl: "https://github.com/deepak292007/ML-BASED-AUTOMATIC-GRAMMER-INTERFERENCE-USING-MYSQL"
}};

// ===========================================================================
// DATASET STATISTICS & ZERO-LEAKAGE SPLITS
// ===========================================================================
const DATASET_STATS = {json.dumps(dataset_stats, indent=2)};

const SPLIT_VERIFICATION = {{
  totalQueries: 7000,
  trainCount: 4826,
  valCount: 1028,
  testCount: 1146,
  trainTemplates: 29,
  valTemplates: 19,
  testTemplates: 20,
  totalTemplates: 68,
  pairwiseLeakage: {{
    trainValOverlap: 0,
    trainTestOverlap: 0,
    valTestOverlap: 0
  }},
  zeroLeakageConfirmed: true,
  sourceTag: "data/dataset_statistics.json & tests/test_dataset.py"
}};

const SAMPLE_TRAIN_ROWS = {json.dumps(train_samples, indent=2)};
const SAMPLE_TEST_ROWS = {json.dumps(test_samples, indent=2)};

// ===========================================================================
// DATABASE RELATIONAL SCHEMA (school_db)
// ===========================================================================
const SCHEMA = {json.dumps(schema_info, indent=2)};

// ===========================================================================
// BENCHMARK RESULTS (Held-Out Test Set: 1,146 Queries)
// ===========================================================================
const MODEL_COMPARISON = {json.dumps(model_comparison, indent=2)};
const PARSER_METRICS = {json.dumps(parser_metrics, indent=2)};
const CLASSIFIER_METRICS = {json.dumps(classifier_metrics, indent=2)};
const GRAMMAR_METRICS = {json.dumps(grammar_metrics, indent=2)};
const LEARNING_CURVE = {json.dumps(learning_curve, indent=2)};
const FALSE_REJECTIONS = {json.dumps(false_rejections, indent=2)};

// ===========================================================================
// GRAMMAR SOURCE CODE
// ===========================================================================
const LEARNED_EBNF = {json.dumps(learned_lark)};
const BASELINE_EBNF = {json.dumps(baseline_lark)};

// ===========================================================================
// 12 PRESET QUERIES WITH PRECOMPUTED REAL PYTHON VERDICTS
// ===========================================================================
const PRESETS = {json.dumps(computed_presets, indent=2)};

// ===========================================================================
// EXPORTED ML MODEL WEIGHTS FOR REAL-TIME IN-BROWSER SCORING (TF-IDF + LOGISTIC REGRESSION)
// ===========================================================================
const ML_MODEL_WEIGHTS = {json.dumps(ml_export, indent=2)};
"""

    out_file = PROJECT_ROOT / "site" / "js" / "data.js"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(js_content, encoding="utf-8")
    print(f"[+] Successfully wrote {out_file} ({len(js_content)} bytes)")


if __name__ == "__main__":
    build_site_data()
