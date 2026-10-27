"""
FastAPI Backend Server for AutoGrammar.
Exposes the actual Python compiler pipeline (Lark parser, Lexer, Semantic Checker, Security Gate)
and relational sandbox execution to the web showcase and external clients.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
import joblib

from compiler.lexer import SqlLexer, tokenize
from compiler.parser import AutoGrammarParser
from compiler.semantic_checker import SemanticChecker, SCHOOL_DB_SCHEMA, SCHEMA_METADATA
from compiler.query_validator import QueryValidator
from compiler.error_handler import CompilerDiagnostic
from database.connection import db_manager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("autogrammar_server")

app = FastAPI(
    title="AutoGrammar Compiler API",
    description="Backend API exposing the real Lark EBNF parser, compiler stages, ML models, and relational sandbox for AutoGrammar.",
    version="1.0.0"
)

# Enable CORS for local development and file:/// access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize compiler singletons
parser = AutoGrammarParser()
semantic_checker = SemanticChecker()
lexer = SqlLexer()
validator = QueryValidator(parser=parser, semantic_checker=semantic_checker, lexer=lexer)

# Load ML models safely
MODELS_DIR = PROJECT_ROOT / "ml" / "saved_models"
ml_primary_clf = None
ml_primary_vec = None
ml_baseline_clf = None
ml_baseline_vec = None

try:
    clf_p = MODELS_DIR / "classifier.joblib"
    vec_p = MODELS_DIR / "vectorizer.joblib"
    if clf_p.exists() and vec_p.exists():
        ml_primary_clf = joblib.load(clf_p)
        ml_primary_vec = joblib.load(vec_p)
        logger.info("[+] Loaded primary ML classifier (Linear SVM with Structural Pipeline)")
except Exception as e:
    logger.warning(f"[-] Could not load primary ML model: {e}")

try:
    clf_b = MODELS_DIR / "classifier_baseline.joblib"
    vec_b = MODELS_DIR / "vectorizer_baseline.joblib"
    if clf_b.exists() and vec_b.exists():
        ml_baseline_clf = joblib.load(clf_b)
        ml_baseline_vec = joblib.load(vec_b)
        logger.info("[+] Loaded baseline ML classifier (TF-IDF + Logistic Regression)")
except Exception as e:
    logger.warning(f"[-] Could not load baseline ML model: {e}")


# Request & Response Models
class QueryValidationRequest(BaseModel):
    query: str = Field(..., description="SQL DSL query string to validate")
    grammar_choice: Optional[str] = Field("both", description="'learned', 'baseline', or 'both'")
    session_refined: Optional[bool] = Field(False, description="Whether to test candidate refined rule session")


class QueryExecutionRequest(BaseModel):
    query: str = Field(..., description="SQL DSL query string to execute")
    max_rows: Optional[int] = Field(50, description="Maximum number of rows to return (default 50, max 200)")


@app.get("/api/health")
def get_health() -> Dict[str, Any]:
    """Returns compiler and database status."""
    db_status = db_manager.test_connection()
    return {
        "status": "ONLINE",
        "compiler": "Python 3.14 + Lark Earley Parser",
        "lark_version": "1.3.1",
        "baseline_grammar": "grammars/baseline.lark",
        "learned_grammar": "grammars/learned.lark",
        "database": db_status,
        "ml_models": {
            "primary": ml_primary_clf is not None,
            "baseline": ml_baseline_clf is not None
        }
    }


@app.get("/api/schema")
def get_schema() -> Dict[str, Any]:
    """Returns canonical database schema and column metadata."""
    return {
        "schema": SCHOOL_DB_SCHEMA,
        "metadata": SCHEMA_METADATA,
        "tables": list(SCHOOL_DB_SCHEMA.keys())
    }


def _run_ml_prediction(query: str) -> Dict[str, Any]:
    """Runs statistical ML classification on query using primary or baseline model."""
    target_clf = ml_primary_clf or ml_baseline_clf
    target_vec = ml_primary_vec or ml_baseline_vec

    if target_clf is None or target_vec is None:
        return {
            "available": False,
            "valid": False,
            "verdict": "UNAVAILABLE",
            "confidence": 0.0,
            "probability": 0.0,
            "model_type": "None",
            "stage_reached": "STATISTICAL",
            "message": "ML model artifacts not loaded.",
            "suggestion": "Train model via python ml/train_classifier.py."
        }

    try:
        feat = target_vec.transform([query])
        pred = int(target_clf.predict(feat)[0])

        prob_val = 0.5
        if hasattr(target_clf, "predict_proba"):
            probs = target_clf.predict_proba(feat)[0]
            prob_val = float(probs[1]) if len(probs) > 1 else (1.0 if pred == 1 else 0.0)
        else:
            prob_val = 1.0 if pred == 1 else 0.0

        decision_score = None
        if hasattr(target_clf, "decision_function"):
            try:
                decision_score = round(float(target_clf.decision_function(feat)[0]), 4)
            except Exception:
                decision_score = None

        is_calibrated = getattr(target_clf, "is_calibrated", False)
        calib_note = " (Platt Calibrated)" if is_calibrated else " (Sigmoid Score)"

        return {
            "available": True,
            "valid": is_valid,
            "verdict": "ACCEPT" if is_valid else "REJECT",
            "probability": round(prob_val, 4),
            "confidence": round(prob_val if is_valid else (1.0 - prob_val), 4),
            "decision_score": decision_score,
            "is_calibrated": is_calibrated,
            "model_type": model_desc,
            "stage_reached": "STATISTICAL (Black-Box)",
            "line": None,
            "column": None,
            "message": f"Statistical {model_desc}: {prob_val*100:.1f}% validity confidence{calib_note}. Model predicts {('ACCEPT' if is_valid else 'REJECT')}.",
            "suggestion": "Statistical classifier provides likelihood ranking only; compiler deterministic checks take precedence."
        }
    except Exception as e:
        logger.warning(f"ML inference error: {e}")
        return {
            "available": False,
            "valid": False,
            "verdict": "ERROR",
            "confidence": 0.0,
            "probability": 0.0,
            "model_type": "Error",
            "stage_reached": "STATISTICAL",
            "message": f"ML inference failed: {str(e)}",
            "suggestion": "Check input query formatting."
        }


def _format_grammar_verdict(val_res: Dict[str, Any]) -> Dict[str, Any]:
    """Transforms QueryValidator internal dict into frontend-friendly verdict structure."""
    diag = val_res["diagnostics"][0] if val_res["diagnostics"] else None
    is_valid = val_res["valid"]
    diag_dict = diag.to_dict() if diag else None

    # Determine failing stage for display
    stage_display = val_res.get("stage_reached", "UNKNOWN")
    if stage_display == "PASSED_ALL":
        stage_display = "Passed All (Stages 0–3)"
    elif stage_display == "SECURITY":
        stage_display = "Stage 0 (Security Gate)"
    elif stage_display == "LEXICAL":
        stage_display = "Stage 1 (Lexical Analysis)"
    elif stage_display == "SYNTAX":
        stage_display = "Stage 2 (Syntax Analysis)"
    elif stage_display == "SEMANTIC":
        stage_display = "Stage 3 (Semantic Validation)"
    elif stage_display == "BACKEND":
        stage_display = "Backend Error"
    elif stage_display == "INITIAL":
        stage_display = "Initial Check (Empty Input)"

    message = diag.message if diag else "Query is fully valid across all compiler stages."
    suggestion = diag.suggestion if diag else "Safe for relational database execution."

    return {
        "valid": is_valid,
        "verdict": "ACCEPT" if is_valid else "REJECT",
        "stage_reached": stage_display,
        "line": diag.line if (diag and diag.line is not None) else None,
        "column": diag.column if (diag and diag.column is not None) else None,
        "unexpected_token": diag.unexpected_token if diag else None,
        "expected_tokens": diag.expected_tokens if diag else [],
        "message": message,
        "suggestion": suggestion,
        "ascii_tree": val_res.get("parse_tree_ascii", ""),
        "tokens": val_res.get("tokens", []),
        "diagnostics": [d.to_dict() for d in val_res.get("diagnostics", [])]
    }


@app.post("/api/validate")
def validate_query(req: QueryValidationRequest) -> Dict[str, Any]:
    """
    Primary compiler validation endpoint.
    Invokes the real Python pipeline: Security -> Lexer -> Lark Parser -> Semantic Checker.
    Evaluates baseline and/or learned grammar and runs ML classification.
    """
    raw_query = req.query
    if raw_query is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query string is required.")

    query = raw_query.strip()
    if not query:
        empty_diag = {
            "valid": False,
            "verdict": "REJECT",
            "stage_reached": "Initial Check (Empty Input)",
            "line": None,
            "column": None,
            "message": "Query string is empty.",
            "suggestion": "Enter a valid SQL query.",
            "ascii_tree": "",
            "tokens": [],
            "diagnostics": []
        }
        return {
            "source": "Python Compiler (FastAPI Backend, Lark Parser v1.3.1)",
            "is_backend": True,
            "baseline": empty_diag,
            "learned": empty_diag,
            "ml": {
                "available": True,
                "valid": False,
                "verdict": "REJECT",
                "probability": 0.0,
                "confidence": 0.0,
                "message": "Query is empty.",
                "stage_reached": "STATISTICAL"
            },
            "tokens": []
        }

    try:
        # 1. Baseline validation via real Python QueryValidator
        base_res = validator.validate(query, grammar_choice="baseline", enforce_semantics=True)
        baseline_verdict = _format_grammar_verdict(base_res)

        # 2. Learned grammar validation via real Python QueryValidator
        learn_res = validator.validate(query, grammar_choice="learned", enforce_semantics=True)
        learned_verdict = _format_grammar_verdict(learn_res)

        # 3. Statistical ML classification
        ml_verdict = _run_ml_prediction(query)

        # 4. Extract token stream
        tokens = base_res.get("tokens") or learn_res.get("tokens") or [t.to_dict() for t in lexer.tokenize(query)]

        # Check grammar disagreement
        disagreement = (base_res["valid"] != learn_res["valid"])

        # Check compiler vs ML disagreement (ML never overrides compiler)
        compiler_accepted = bool(base_res["valid"])
        ml_accepted = bool(ml_verdict.get("valid", False))
        ml_disagreement = (compiler_accepted != ml_accepted)
        ml_override_msg = None
        if compiler_accepted and not ml_accepted:
            ml_override_msg = (
                "The compiler accepts this query. The experimental ML classifier disagrees and predicts REJECT. "
                "The ML prediction does not override compiler validation."
            )
        elif not compiler_accepted and ml_accepted:
            ml_override_msg = (
                "The compiler rejects this query. The experimental ML classifier predicts ACCEPT. "
                "The ML prediction does not override compiler validation."
            )

        return {
            "source": "Python Compiler (FastAPI Backend, Lark Parser v1.3.1)",
            "is_backend": True,
            "compiler_valid": compiler_accepted,
            "learned_valid": bool(learn_res["valid"]),
            "grammar_disagreement": disagreement,
            "ml_disagreement": ml_disagreement,
            "ml_override_message": ml_override_msg,
            "baseline": baseline_verdict,
            "learned": learned_verdict,
            "ml": ml_verdict,
            "tokens": tokens,
            "safe_to_execute": bool(base_res.get("safe_to_execute", False) and base_res.get("is_read_only", False)),
            "semantics": base_res.get("semantics") or learn_res.get("semantics", {})
        }
    except Exception as e:
        logger.error(f"Unexpected error in /api/validate: {e}", exc_info=True)
        # Never expose internal raw traceback to client
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Compiler pipeline encountered an internal error during validation.",
                "message": str(e),
                "is_backend": True
            }
        )


@app.post("/api/execute")
def execute_query(req: QueryExecutionRequest) -> Dict[str, Any]:
    """
    Safely executes an approved query against the relational database sandbox (SQLite or MySQL).
    Guards:
      - Validates query against Python compiler first.
      - Never executes rejected queries.
      - Enforces read-only SELECT constraints.
    """
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query cannot be empty.")

    # 1. Compiler Validation Guard: must pass baseline compiler
    val_res = validator.validate(query, grammar_choice="baseline", enforce_semantics=True)
    if not val_res["valid"]:
        diag = val_res["diagnostics"][0] if val_res["diagnostics"] else None
        return {
            "success": False,
            "blocked": True,
            "error": f"Execution blocked: Query failed compiler validation at {val_res.get('stage_reached')}.",
            "diagnostic": diag.message if diag else "Validation failed.",
            "columns": [],
            "rows": [],
            "row_count": 0
        }

    # 2. Read-only guard: only SELECT queries
    if not val_res.get("is_read_only", False):
        return {
            "success": False,
            "blocked": True,
            "error": "Execution safeguard: Only read-only SELECT queries are permitted in interactive execution.",
            "columns": [],
            "rows": [],
            "row_count": 0
        }

    # 3. Execute on sandbox / MySQL
    max_rows = min(max(1, req.max_rows or 50), 200)
    exec_res = db_manager.execute_query(query, read_only=True, max_rows=max_rows)
    return exec_res


# Serve website static files directly if site/ directory exists
site_dir = PROJECT_ROOT / "site"
if site_dir.exists():
    @app.get("/")
    def serve_index():
        return FileResponse(site_dir / "index.html")

    app.mount("/", StaticFiles(directory=str(site_dir), html=True), name="site")


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    logger.info(f"[*] Starting AutoGrammar API server at http://{host}:{port}")
    uvicorn.run("server:app", host=host, port=port, reload=False)
