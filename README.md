# AutoGrammar: Machine Learning-Based Automatic Grammar Inference for DSL with MySQL

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Lark Parser](https://img.shields.io/badge/Parser-Lark%20EBNF-purple.svg)](https://github.com/lark-parser/lark)
[![Streamlit UI](https://img.shields.io/badge/Interface-Streamlit-red.svg)](https://streamlit.io/)
[![MySQL 8.0+](https://img.shields.io/badge/Database-MySQL%208.0%2B%20%7C%20Relational%20Sandbox-green.svg)](https://www.mysql.com/)
[![Tests](https://img.shields.io/badge/Tests-19%2F19%20Passing-brightgreen.svg)]()

> **AutoGrammar** is an end-to-end compiler and machine learning system that automatically learns and infers formal Extended Backus-Naur Form (EBNF) grammar productions from an exemplar corpus of SQL queries written for a domain-specific school student management database (`school_db`).

---

## Table of Contents
1. [Overview & Highlights](#1-overview--highlights)
2. [System Architecture](#2-system-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Prerequisites & Installation](#4-prerequisites--installation)
5. [Step-by-Step Execution Guide](#5-step-by-step-execution-guide)
   - [A. Generate Synthetic Dataset](#a-generate-synthetic-dataset)
   - [B. Build & Induce EBNF Grammar](#b-build--induce-ebnf-grammar)
   - [C. Train & Evaluate ML Baseline](#c-train--evaluate-ml-baseline)
   - [D. Setup Database & Seed Data](#d-setup-database--seed-data)
   - [E. Run Automated Test Suite](#e-run-automated-test-suite)
   - [F. Run Comparative Benchmarks](#f-run-comparative-benchmarks)
6. [Website Structure (7 Pages)](#6-website-structure-7-pages)
7. [Experimental Results](#7-experimental-results)
8. [Example Queries & Pipeline Behavior](#8-example-queries--pipeline-behavior)
9. [Troubleshooting](#9-troubleshooting)
10. [Limitations & Future Work](#10-limitations--future-work)

---

## 1. Overview & Highlights

AutoGrammar goes far beyond traditional static parsers or simple text classifiers:
- **Genuine Rule Induction**: Reads tokenized training queries, identifies recurring clause skeletons, generalizes identifiers and literals, and synthesizes valid Lark EBNF grammar files (`grammars/learned.lark`).
- **Data Leakage Prevention**: Partitions the 7,000 query corpus strictly by underlying structural template (`template_id`), ensuring zero slot-filler leakage between Train (70%), Validation (15%), and Test (15%) splits.
- **Indian School Management Domain**: Generates 10,000 synthetic student records with regionally authentic Indian names, cities, states, classes, subjects, marks, and attendance records.
- **4-Stage Compiler Pipeline**:
  - **Stage 0 (Security Gate)**: Blocks dangerous administrative operations (`DROP`, `TRUNCATE`, `ALTER`) and multi-statement injection attacks.
  - **Stage 1 (Lexical Analysis)**: Regex-based tokenizer with line and column coordinate tracking.
  - **Stage 2 (Syntax Analysis)**: Lark-powered Earley/LALR parser generating full hierarchical parse trees.
  - **Stage 3 (Semantic Validation)**: Schema-aware resolution of tables, columns, and aliases against `school_db`.
- **Relational Execution**: Seamless execution on MySQL 8.0+ or an automated in-memory relational sandbox.
- **Interactive Refinement Sandbox**: Users can submit novel query structures, inspect proposed grammar production modifications, and approve version-controlled updates (`grammars/versions/`).

---

## 2. System Architecture

```text
AutoGrammar/
├── app.py                      # Interactive Streamlit Web Application
├── requirements.txt            # Python dependencies
├── README.md                   # Complete documentation & execution guide
├── .env.example                # Environment variable configuration template
├── config/
│   └── settings.yaml           # Global parameters and seed configuration
├── data/
│   ├── generator.py            # Synthetic school data & query generator
│   ├── synthetic_students.csv  # 10,000 Indian student records
│   ├── synthetic_teachers.csv  # 40 teacher records
│   ├── synthetic_classes.csv   # 7 academic classes (Classes 6-12)
│   ├── synthetic_subjects.csv  # 6 core curriculum subjects
│   ├── synthetic_marks.csv     # 6,031 exam marks evaluations
│   ├── synthetic_attendance.csv# 6,000 attendance records
│   ├── valid_queries.csv       # 5,000 valid SQL queries
│   ├── invalid_queries.csv     # 2,000 invalid queries with error taxonomy
│   ├── query_dataset.csv       # Combined query corpus (7,000 queries)
│   ├── train.csv               # 4,826 training queries (disjoint templates)
│   ├── validation.csv          # 1,028 validation queries (disjoint templates)
│   ├── test.csv                # 1,146 held-out test queries (disjoint templates)
│   └── dataset_statistics.json # Generation counts & template distributions
├── ml/
│   ├── preprocess.py           # TF-IDF token/n-gram vectorizer
│   ├── train_classifier.py     # Logistic Regression training pipeline
│   ├── evaluate_classifier.py  # Test set metrics & confusion matrix
│   └── saved_models/           # Serialized model & vectorizer artifacts
├── compiler/
│   ├── lexer.py                # Regex tokenizer with line/col tracking
│   ├── token_types.py          # Token types and categories
│   ├── baseline_grammar.py     # Reference baseline loader
│   ├── grammar_induction.py    # Automatic EBNF rule induction engine
│   ├── grammar_builder.py      # Induction CLI trainer
│   ├── parser.py               # Lark-based baseline/learned parser
│   ├── parse_tree.py           # Tree nodes, ASCII renderer & semantic extractor
│   ├── semantic_checker.py     # Schema-aware validator for school_db
│   ├── error_handler.py        # Diagnostic reporting with suggestions
│   └── query_validator.py      # 4-stage compiler & security pipeline
├── grammars/
│   ├── baseline.lark           # Handcrafted authoritative baseline grammar
│   ├── learned.lark            # Machine-learned EBNF grammar
│   └── versions/               # Timestamped grammar versions
├── database/
│   ├── schema.sql              # MySQL DDL with indexes and foreign keys
│   ├── seed_data.sql           # Populated SQL insert statements
│   ├── connection.py           # MySQL manager with SQLite sandbox fallback
│   └── setup_database.py       # Automated DDL & seeding script
├── evaluation/
│   ├── evaluate_grammar.py     # Production precision, recall, F1
│   ├── evaluate_parser.py      # Parser TPR, TNR, FAR, FRR on held-out test set
│   ├── compare_models.py       # Comparative benchmarking script
│   └── results/                # Saved JSON/CSV evaluation metrics & charts
├── tests/
│   ├── test_dataset.py         # Schema, counts, and zero-leakage checks
│   ├── test_lexer.py           # Tokenization & line/column tracking
│   ├── test_grammar_induction.py # Induction & refinement tests
│   ├── test_parser.py          # Valid parsing & invalid rejection tests
│   ├── test_semantic_checker.py# Unknown table & column detection tests
│   └── test_security.py        # DROP, multi-statement, unconstrained DML tests
├── docs/
│   ├── architecture.md         # Detailed system design
│   ├── methodology.md          # Synthetic data & template splitting details
│   └── limitations.md          # Domain scope and theoretical trade-offs
└── report/
    ├── main.tex                # Academic research report (LaTeX)
    ├── references.bib          # Verified academic bibliography
    └── figures/                # System diagrams and performance charts
```

---

## 3. Technology Stack

- **Core Logic & Compiler**: Python 3.10+ / 3.14
- **Parsing Toolkit**: [Lark](https://github.com/lark-parser/lark) (Earley & LALR parsers)
- **Machine Learning**: [scikit-learn](https://scikit-learn.org/) (TF-IDF, Logistic Regression)
- **Data Engineering**: Pandas, NumPy
- **Relational Databases**: MySQL 8.0+ via PyMySQL / SQLite in-memory sandbox
- **Web Interface**: [Streamlit](https://streamlit.io/)
- **Visualizations**: Matplotlib, Seaborn
- **Testing**: Pytest

---

## 4. Prerequisites & Installation

### Prerequisites
- Python 3.10 or higher installed.
- Python 3.10 or higher installed.
- (Optional) MySQL Server 8.0+ running on port 3306. If MySQL is not running or unconfigured, AutoGrammar operates automatically in seamless in-memory Relational Sandbox mode.

### Installation Steps (Windows PowerShell)

Open PowerShell in the project root (`c:\Users\HANUMAN\compilor_design`):

```powershell
# 1. Create a virtual environment
py -3 -m venv .venv

# 2. Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# 3. Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> **Safe Alternative if PowerShell blocks script activation (`PSSecurityException`)**:
> If your Windows execution policy prevents running `Activate.ps1`, you do not need to weaken system-wide security settings. Instead, run directly using the virtual environment's executable:
> ```powershell
> # Direct execution with .venv python (no activation required)
> .\.venv\Scripts\python.exe -m pip install --upgrade pip
> .\.venv\Scripts\pip.exe install -r requirements.txt
> .\.venv\Scripts\python.exe -m streamlit run app.py
> ```
> Or temporarily enable script execution for the current session only:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> .\.venv\Scripts\Activate.ps1
> ```

*(On Linux / macOS)*:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 5. Step-by-Step Execution Guide

### A. Generate Synthetic Dataset
Generates 10,000 synthetic Indian students, relational tables, 7,000 queries, and template-disjoint splits:
```powershell
python data/generator.py
```

### B. Build & Induce EBNF Grammar
Runs the grammar induction engine on training queries and outputs `grammars/learned.lark`:
```powershell
python compiler/grammar_builder.py
```

### C. Train & Evaluate ML Baseline
Trains the TF-IDF + Logistic Regression statistical baseline and evaluates on held-out test data:
```powershell
python ml/train_classifier.py
python ml/evaluate_classifier.py
```

### D. Setup Database & Seed Data
Generates `database/seed_data.sql` and initializes `school_db` in MySQL (or verifies sandbox):
```powershell
python database/setup_database.py
```

### E. Run Automated Test Suite
Executes the full suite of 25 unit and integration tests:
```powershell
python -m pytest tests -v
```

### F. Run Comparative Benchmarks
Runs grammar rule evaluation, parser testing, and generates comparison tables and charts:
```powershell
python evaluation/compare_models.py
```

### G. Launch Streamlit Web Application
Launches the interactive web dashboard with all 7 pages:
```powershell
python -m streamlit run app.py
```
Open your browser at:
`http://localhost:8501`

---

## 6. Website Structure (7 Pages)

- **Page A — Dashboard**: Dynamic project health status, student entity counts, active grammar production count, and ML model status.
- **Page B — SQL Query Playground**: Multiline editor with preset library, 5-stage compiler pipeline diagnostic, token stream inspector, ASCII parse tree renderer, and safe database query execution table.
- **Page C — Grammar Learning**: Interactive buttons to infer candidate EBNF productions, reload active grammar, compare against baseline, and an Interactive Refinement Sandbox requiring explicit user confirmation before applying grammar updates.
- **Page D — Dataset Explorer**: Filterable browser across synthetic entities (`students`, `teachers`, `classes`, `subjects`, `marks`, `attendance`) and query corpora (`train.csv`, `validation.csv`, `test.csv`). Includes on-demand generation.
- **Page E — ML Model**: Training and test set evaluation controls for TF-IDF + Logistic Regression with real confusion matrix, precision, recall, F1, and educational context on bag-of-words limitations.
- **Page F — MySQL Database**: Connection monitor (MySQL 8.0+ vs. In-Memory SQLite Relational Sandbox), schema introspection, and table data preview with dialect documentation.
- **Page G — Evaluation and Results**: Comprehensive side-by-side benchmark comparison (Baseline vs. Learned vs. ML Classifier) across 1,146 test queries, with generated accuracy/recall charts and scientific discussion.

---

## 7. Experimental Results

Evaluated on **1,146 held-out test queries** originating from completely unseen structural templates:

| Metric | Fixed Baseline Grammar | AutoGrammar Learned Grammar | ML Baseline Classifier |
| :--- | :--- | :--- | :--- |
| **Overall Accuracy** | **100.00%** | **89.53%** | 66.67% |
| **Valid Query Acceptance (TPR)** | 100.00% | 85.71% | 85.12% |
| **Invalid Query Rejection (TNR)**| 100.00% | **100.00%** | 16.01% |
| **False Acceptance Rate (FAR)**  | 0.00% | **0.00%** | 83.99% |
| **False Rejection Rate (FRR)**   | 0.00% | 14.29% | 14.88% |
| **EBNF Production F1-Score**    | 1.0000 | **0.9873** | N/A (Black-box) |
| **Generates Parse Tree**        | Yes (Deterministic) | **Yes (Deterministic)** | No |

### Scientific Insights
1. **Zero False Acceptances**: The automatically learned grammar achieves **0.00% False Acceptance Rate**, rejecting 100% of invalid queries (syntax errors, lexical errors, malformed parentheses, misplaced keywords).
2. **Failure of Bag-of-Words**: The TF-IDF Logistic Regression model achieves only 66.67% accuracy and incurs an 83.99% False Acceptance Rate. It recognizes vocabulary words (e.g., `SELECT`, `WHERE`) but cannot verify grammatical sequencing.
3. **Generalization Gap**: The 14.29% False Rejection Rate of the learned grammar reflects queries whose structural skeletons were held out in validation/test splits. These can be integrated interactively using the Refinement Sandbox.

---

## 8. Example Queries & Pipeline Behavior

### Example 1: Valid Join Query
```sql
SELECT s.first_name, s.last_name, m.marks_obtained 
FROM students AS s 
INNER JOIN marks AS m ON s.student_id = m.student_id 
WHERE m.marks_obtained >= 80;
```
- **Lexer**: Successfully tokenizes tokens.
- **Parser**: Parses cleanly, generates hierarchical parse tree.
- **Semantic Validator**: Validates `students`, `marks`, aliases `s`, `m`, and fields.
- **Execution**: Returns matching records from `school_db`.

### Example 2: Syntax Error (Missing FROM)
```sql
SELECT first_name, last_name WHERE state = 'Andhra Pradesh';
```
- **Stage 2 Error**: Syntax analysis failed.
- **Diagnostic**: `Line 1, Col 30: Expected FROM clause before WHERE condition.`

### Example 3: Semantic Error (Nonexistent Column)
```sql
SELECT first_name, blood_group FROM students WHERE state = 'Delhi';
```
- **Stage 3 Error**: `Unknown column 'blood_group'. Column does not exist on table 'students'.`
- **Suggestion**: `Available columns: student_id, admission_no, first_name, last_name, class_id, section, date_of_birth, gender, city, state, enrollment_date, status.`

### Example 4: Security Violation (Administrative DROP)
```sql
DROP TABLE students;
```
- **Stage 0 Error**: `Dangerous SQL command 'DROP' is prohibited in student DSL environment.`
- **Action**: Execution blocked immediately.

---

## 9. Troubleshooting

- **`ModuleNotFoundError: No module named 'compiler'`**:
  Ensure you are running commands from the root directory (`c:\Users\HANUMAN\compilor_design`) or use `python -m pytest tests`.
- **MySQL Connection Failed**:
  If MySQL is not installed or your password differs from `.env`, AutoGrammar operates automatically in Relational Sandbox mode using SQLite loaded with the exact synthetic data. To connect to your local MySQL, copy `.env.example` to `.env` and configure your credentials.
- **Port Conflicts**:
  If port 8501 is busy, run `python -m streamlit run app.py --server.port 8502`.

---

## 10. Limitations & Future Work

- **Dialect Scope**: Supports student DSL querying (`SELECT`, `INSERT`, `UPDATE`, `DELETE`, `JOIN`, subqueries, aggregations). Does not include administrative commands, stored procedures, or window functions.
- **Exemplar Dependence**: Grammar induction is bounded by the variety of training exemplars provided; unseen constructs are flagged until introduced through interactive refinement.
- **Future Directions**: Exploring Probabilistic Context-Free Grammars (PCFGs) and Transformer-guided proposal engines.

---
*Built with Python, Lark, scikit-learn, and Streamlit.*
