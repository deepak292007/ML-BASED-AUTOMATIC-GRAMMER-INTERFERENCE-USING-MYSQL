# AutoGrammar: Machine Learning-Based Automatic Grammar Inference for DSL with MySQL
### Repository: ML-BASED-AUTOMATIC-GRAMMER-INTERFERENCE-USING-MYSQL

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Lark Parser](https://img.shields.io/badge/Parser-Lark%20EBNF-purple.svg)](https://github.com/lark-parser/lark)
[![Streamlit UI](https://img.shields.io/badge/Interface-Streamlit-red.svg)](https://streamlit.io/)
[![MySQL 8.0+](https://img.shields.io/badge/Database-MySQL%208.0%2B%20%7C%20Relational%20Sandbox-green.svg)](https://www.mysql.com/)
[![Tests](https://img.shields.io/badge/Tests-25%2F25%20Passing-brightgreen.svg)]()

> **AutoGrammar** is an end-to-end compiler and machine learning system that automatically learns and infers formal Extended Backus-Naur Form (EBNF) grammar productions from an exemplar corpus of SQL queries written for a domain-specific school student management database (`school_db`).

---

## 🚀 Quick Launch (Examiner & Evaluator Walkthrough)

| Interface | Purpose | Launch Command |
| :--- | :--- | :--- |
| **Primary: Evaluator Dashboard** (`eval_app.py`) | **5-Minute Viva Walkthrough**: 4-stage pipeline, side-by-side 3-column evaluation (Baseline, Learned, ML), session grammar refinement sandbox, benchmarks, and learning curve. | `python -m streamlit run eval_app.py` |
| **Secondary: Developer Studio** (`app.py`) | **Full Administrative Interface**: On-demand dataset generation, multi-classifier retraining, direct MySQL schema configuration, and table browsing. | `python -m streamlit run app.py` |
| **Portable Showcase** (`site/index.html`) | **Zero-Dependency Static Showcase**: Runs in any modern browser offline without Python or Streamlit installed. | Open `site/index.html` in browser |

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
   - [G. Launch Web Applications](#g-launch-web-applications)
6. [Website Structure](#6-website-structure)
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
- **Relational Execution**: Seamless execution on MySQL 8.0+ or an automated in-memory relational sandbox (SQLite fallback).
- **Interactive Refinement Sandbox**: Users can submit novel query structures, inspect proposed grammar production modifications, and approve version-controlled updates (`grammars/versions/`).

---

## 2. System Architecture

```text
AutoGrammar/
├── eval_app.py                 # Primary Evaluator Dashboard (5-minute walkthrough, side-by-side)
├── app.py                      # Developer & Administration Studio (7-page workspace)
├── DEMO.md                     # Evaluator 5-minute walkthrough verification script
├── requirements.txt            # Python dependencies
├── README.md                   # Complete documentation & execution guide
├── .env.example                # Environment variable configuration template
├── site/                       # Zero-dependency portable static presentation showcase
│   ├── index.html              # Single-page offline showcase application
│   ├── css/style.css           # High-contrast accessible design system
│   ├── js/data.js              # Exported real evaluation metrics & schema
│   ├── js/validator.js         # In-browser compiler & baseline classifier scoring
│   ├── js/charts.js            # Inline responsive SVG charts
│   └── js/app.js               # Presentation mode & interactive playground controllers
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
│   ├── preprocess.py           # Feature pipelines (syntax abstraction + structural features)
│   ├── train_classifier.py     # Reproducible model training (Linear SVM & Logistic Regression)
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
│   ├── learning_curve.py       # Induction learning curve generator
│   └── results/                # Saved JSON/CSV evaluation metrics & charts
├── tests/
│   ├── test_dataset.py         # Schema, counts, and zero-leakage checks
│   ├── test_lexer.py           # Tokenization & line/column tracking
│   ├── test_grammar_induction.py # Induction & refinement tests
│   ├── test_parser.py          # Valid parsing & invalid rejection tests
│   ├── test_semantic_checker.py# Unknown table & column detection tests
│   ├── test_security.py        # DROP, multi-statement, unconstrained DML tests
│   └── test_web_app.py         # Application integration & missing file tests
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

### G. Launch Web Applications

#### 1. Primary: Evaluator Dashboard (`eval_app.py`)
Recommended for examiners, evaluators, and viva demonstrations (5-minute walkthrough):
```powershell
python -m streamlit run eval_app.py
```
Open your browser at `http://localhost:8501`.

#### 2. Secondary: Developer & Administration Studio (`app.py`)
Comprehensive 7-page studio for full administrative control, retraining, and dataset generation:
```powershell
python -m streamlit run app.py
```

#### 3. Portable Static Showcase (`site/index.html`)
Zero-dependency static HTML/CSS/JS presentation requiring no Python/Streamlit:
```powershell
# Open directly in browser or serve locally:
python -m http.server 8000 --directory site
```

---

## 6. Application Interfaces

### A. Primary Evaluator Dashboard (`eval_app.py` — 4 Pages)
- **1. Overview**: 4-stage pipeline diagram, live status chips (learned rule count, database mode, 0-leakage verification), and live `pytest` test runner.
- **2. Query Playground**: 8 preset queries with expected verdicts, side-by-side 3-column evaluation across Baseline Grammar, Learned Grammar, and Primary ML Model, with token stream inspector, ASCII parse tree renderer, and live database sandbox execution.
- **3. Grammar**: Inferred EBNF viewer, rule metrics (precision, recall, shared rules), and interactive refinement sandbox allowing candidate rules to be tested on session copies without corrupting disk files.
- **4. Evaluation**: Held-out test set benchmarks (1,146 queries), side-by-side confusion matrices, invalid category breakdown, false-rejection explorer, and learning curve plot.

### B. Developer Studio (`app.py` — 7 Pages)
- **Page A — Dashboard**: System overview and component health table.
- **Page B — SQL Query Playground**: 4-stage validator with sample presets.
- **Page C — Grammar Learning**: Grammar induction controls and Lark viewer.
- **Page D — Dataset Explorer**: Filterable browser across synthetic entities with on-demand regeneration.
- **Page E — ML Model**: Multi-classifier training and test evaluation controls.
- **Page F — MySQL Database**: MySQL connection testing, schema viewer, and table previews.
- **Page G — Evaluation and Results**: Model comparison table and export options.

---

## 7. Experimental Results

Evaluated on **1,146 held-out test queries** originating from completely unseen structural templates (840 valid queries, 306 invalid queries):

| Metric | Fixed Baseline Grammar | AutoGrammar Learned Grammar | Linear SVM (Primary ML) | Improved Logistic Reg. | Majority Baseline | Original ML Baseline (TF-IDF) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Overall Accuracy** | **100.00%** | **89.53%** | **76.09%** | 69.37% | 73.30% | 66.67% |
| **Valid Acceptance (TPR / Recall)** | 100.00% | 85.71% | 85.71% | 85.71% | 100.00% | 85.12% |
| **Invalid Rejection (TNR / Specificity)** | 100.00% | **100.00%** | 49.67% | 24.51% | 0.00% | 16.01% |
| **False Acceptance Rate (FAR)** | 0.00% | **0.00%** | 50.33% | 75.49% | 100.00% | 83.99% |
| **False Rejection Rate (FRR)** | 0.00% | 14.29% | 14.29% | 14.29% | 0.00% | 14.88% |
| **ROC-AUC** | 1.0000 | 0.9286 | **0.8754** | 0.7870 | 0.5000 | 0.4533 |
| **PR-AUC** | 1.0000 | 0.9619 | **0.9633** | 0.9294 | 0.7330 | 0.7452 |
| **Macro F1-Score** | 1.0000 | 0.8796 | **0.6830** | 0.5517 | 0.4230 | 0.4967 |
| **Weighted F1-Score** | 1.0000 | 0.8953 | **0.7562** | 0.6693 | 0.6198 | 0.6330 |
| **Generates Parse Tree** | Yes (100%) | Yes (100% on Accepted) | No | No | No | No |

### Scientific & Engineering Insights

1. **Investigation of the ROC-AUC < 0.5 Defect in the Baseline Classifier**:
   - The original ML baseline trained an unconstrained TF-IDF vectorizer (1-3 n-grams) on raw SQL queries.
   - In a template-disjoint benchmark split, lexical terms (e.g. column names, table names, and certain clauses like `COUNT(*)`) are not identically distributed across valid and invalid sets.
   - For instance, in the training set, `COUNT(*)` exclusively appeared in invalid perturbation templates (`I_SEM_04`, `I_SYN_09`), assigning it a strong negative weight (-1.2270). Conversely, common keywords in invalid test queries (`SELECT first_name, last_name FROM;`) had strong positive weights.
   - On held-out test templates, this inverted predictions on key templates (e.g. valid `V_AGG_02` queries were predicted invalid 100% of the time, while invalid `I_SYN_02` queries were predicted valid 100% of the time), driving ROC-AUC down to **0.4533** and accuracy to **66.67%**, worse than the majority-class baseline (**73.30%**).
   - By introducing **syntax token abstraction** (normalizing identifiers, literals, aggregates, and statement verbs) and **20+ dense structural syntax features** (parentheses depth/balance, quote balance, delimiter tracking, invalid composite operator checks, clause order), the Linear SVM model restores robust ranking: **ROC-AUC rises to 0.8754**, **PR-AUC reaches 0.9633**, and **Accuracy reaches 76.09%**, genuinely beating the majority-class baseline.
   - **Note on Sigmoid Decision Scores**: The custom Linear SVM maps margin distances through a sigmoid function into a [0, 1] interval. These are reported accurately as monotonic decision scores (hyperplane margin distance), not as calibrated Bayesian probabilities, because empirical calibration (Platt scaling) was not fitted.

2. **Parser Metrics Disambiguation (Task 3)**:
   - The historical report of 73.3% "parse-tree generation rate" on a 100% accurate baseline parser was an artifact of calculating `parse_trees_generated / total_corpus` (840 valid parse trees / 1,146 total test queries = 73.30%).
   - Invalid queries are syntactically malformed and intentionally fail parsing.
   - When computed over accepted queries or valid queries, the parse tree generation rate is **100.00% (840/840)**. Exactly **0 accepted queries** lacked a parse tree.

3. **Learning Curve Verification (Task 4)**:
   - At 10%, 25%, 50%, and 75% of training templates, the test accuracy on the held-out test set was identical at 0.7906.
   - Inspection of the saved grammar artifacts (`evaluation/results/grammars/learning_curve_<pct>pct.lark`) proves the generated grammars are **not identical**: rule counts grow from 26 -> 29 -> 32 -> 37 -> 40 rules as new constructs (`JOIN`, `UPDATE`, `IN`, `ORDER BY`, `INSERT`, `LIKE`, `LIMIT`) are learned.
   - The test set accuracy remained flat because the held-out test set valid templates only contained basic SELECT queries until `GROUP BY` was introduced at 100%, unlocking `V_JON_04` (which requires both JOIN and GROUP BY) and jumping accuracy to 89.53%.

4. **Authoritative Nature of Compiler Validation (Task 2)**:
   - Even the best ML classifier (Linear SVM) has a False Acceptance Rate of 50.33% because pure statistical models cannot perform catalog schema validation or verify context-free grammars deterministically.
   - Therefore, ML predictions serve only as auxiliary diagnostics and are never permitted to override the compiler's lexical, security, syntax, or semantic checks.

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

## 10. Evaluation Methodology & Limitations

### Evaluation Methodology
- **Template-Disjoint Benchmarking**: The dataset split partitions queries by structural template ID (`template_id`), ensuring zero query overlap or slot-filler leakage across train (70%), validation (15%), and test (15%) splits.
- **Model Selection & Threshold Tuning**: Model exploration, feature extractor fitting, and hyperparameter selection (`C` regularization parameters, decision thresholds) are conducted strictly on the training and validation sets. The test set (`data/test.csv`) is preserved as a held-out dataset evaluated only for final comparative benchmarking.
- **Reproducible Evaluation Metric Suite**: All systems are evaluated with exact, disambiguated metrics:
  - Overall accuracy, precision, recall, macro F1, and weighted F1 across both classes.
  - Receiver Operating Characteristic (ROC-AUC) and Precision-Recall (PR-AUC).
  - Explicit False Acceptance Rate (FAR) and False Rejection Rate (FRR).
  - Clarified parse-tree generation rates reported separately over accepted queries, valid queries, and the total corpus.
  - Exact confusion matrices saved as structured JSON and high-resolution figures.

### Limitations & Domain Boundary
- **Lexical Independence vs. Schema Context**: Statistical classifiers operating on raw SQL strings cannot access runtime database catalog state. Semantic schema errors (e.g. querying a nonexistent table like `student_fees`) appear syntactically sound and cannot be detected by string-level ML alone.
- **Black-Box Nature of ML**: Classifiers produce continuous probability estimates but cannot construct parse trees, enforce deterministic AST grammar rules, or generate compiler diagnostics.
- **Dialect Scope**: AutoGrammar intentionally targets a student DSL scope (`SELECT`, `INSERT`, `UPDATE`, `DELETE`, `JOIN`, subqueries, aggregations). Advanced administrative commands (`ALTER`, `DROP`, `GRANT`), stored procedures, and window functions are blocked at Stage 0 security.
- **Grammar Induction Diversity**: Inductive grammar synthesis generalizes only over structural constructs present in training exemplars. Unseen constructs require iterative human-in-the-loop grammar refinement.

---
*Built with Python, Lark, scikit-learn, and Streamlit.*

