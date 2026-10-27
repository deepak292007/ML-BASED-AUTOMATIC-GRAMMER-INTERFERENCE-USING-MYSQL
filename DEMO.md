# ⚡ AutoGrammar: 5-Minute Evaluator Walkthrough Guide

This document provides a fast, step-by-step 5-minute verification walkthrough for examiners and evaluators inspecting the **AutoGrammar** compiler induction project.

---

## 🚀 Quick Launch Command

Run the evaluator dashboard from the project root directory:

```bash
python -m streamlit run eval_app.py
```

The web application will open at `http://localhost:8501`.

---

## ⏱️ 5-Minute Evaluation Walkthrough

### Minute 1: Page 1 — Overview & Pipeline Verification
- **Sidebar**: Navigate to `1. Overview`.
- **4-Stage Pipeline Graphic**:
  - Review the architecture: `Stage 0 (Security Gate) -> Stage 1 (Lexer) -> Stage 2 (Parser) -> Stage 3 (Semantic Check)`.
- **Status Chips**:
  - Verify **Learned Grammar Productions**: Shows `38 Rules` active from `grammars/learned.lark`.
  - Verify **Database Mode**: Shows `In-Memory Sandbox (SQLite)` loaded with 10,000 synthetic Indian school records (or live MySQL 8.0+ if connected).
  - Verify **LIVE Leakage Check**: Confirms **0 Overlap** across Train (29 templates), Val (19 templates), and Test (20 templates).
  - Click **"Run Tests (`pytest -q`)"**: Verifies that all 25 unit and integration tests pass live (`25 passed in 58s`).
- **Sample Inspector**: Expand the collapsed expander to view 20 actual query rows from `train.csv` and `test.csv`.

---

### Minute 2: Page 2 — Query Playground & 8 Presets
- **Sidebar**: Click `2. Query Playground`.
- Click each of the **8 preset buttons** and click **"Run Multi-System Evaluation"** to observe side-by-side comparison across **Baseline Grammar**, **Learned Grammar**, and the **ML Classifier**:
  1. `[1] Valid Join`: **ACCEPT** across all three systems.
  2. `[2] Valid Aggregate`: **ACCEPT** across all three systems.
  3. `[3] Valid Subquery`: **ACCEPT** across all three systems.
  4. `[4] Missing FROM`: **REJECT** at `Stage 2 (Syntax Parser)` with exact diagnostic and suggestion.
  5. `[5] Unknown Column`: **REJECT** at `Stage 3 (Semantic Check)` with unknown column diagnostic.
  6. `[6] Lexical Error`: **REJECT** at `Stage 1 (Lexer)` identifying illegal `@#$` characters.
  7. `[7] DROP TABLE`: **REJECT** at `Stage 0 (Security Gate)` blocking administrative DDL.
  8. `[8] Unbalanced Parentheses`: **REJECT** at `Stage 2 (Syntax Parser)` pointing to line 1 column 65.
- **Inspect Tabs**:
  - **Token Stream**: Inspect token classifications, lines, and columns.
  - **ASCII Parse Tree**: View the hierarchical AST generated for valid queries.
  - **Database Execution Result**: Confirm that only valid SELECT queries execute on the database sandbox, returning real data.

---

### Minute 3: Page 3 — EBNF Grammar & Refinement Sandbox
- **Sidebar**: Click `3. Grammar`.
- **Grammar Viewer & Metrics**:
  - Inspect the machine-inferred EBNF in `grammars/learned.lark`.
  - Review production precision (97.4%), recall (94.9%), and shared rule counts.
- **Interactive Refinement Sandbox**:
  - Select the valid query that the learned grammar initially rejects:  
    `SELECT class_id, COUNT(*) AS student_count FROM students GROUP BY class_id;`
  - Observe that the active grammar rejects this query because `COUNT` was held out in the zero-leakage test template split.
  - Notice the proposed rule adjustment:  
    `~ Modified Rule: AGG_FUNC.2: /(?i:AVG|COUNT|MAX|MIN)/`
  - Click **"Approve & Apply to Session Grammar"**:
    - Confirms that the candidate rule is applied strictly to a **SESSION COPY** without overwriting disk files.
    - Status immediately updates to **ACCEPTED**.
  - Test the **"Reset to Committed Grammar"** button to restore disk state.
  - Test the **"Save as New Version"** button to create a timestamped snapshot under `grammars/versions/`.

---

### Minute 4: Page 4 — Evaluation Benchmarks & False-Rejection Explorer
- **Sidebar**: Click `4. Evaluation`.
- **Held-Out Test Set Metrics Table**:
  - Review the 1,146 test query benchmarks:
    - **Baseline Grammar**: 100% Accuracy, 100% TPR, 100% TNR, 0% FAR, 0% FRR.
    - **Learned Grammar**: 89.53% Accuracy, 85.71% TPR, 100% TNR, 0% FAR, 14.29% FRR.
    - **ML Primary Model (Linear SVM)**: 76.09% Accuracy, 85.71% TPR, 49.67% TNR, 50.33% FAR, 14.29% FRR.
    - **ML Baseline (Logistic Regression)**: 66.67% Accuracy, 85.12% TPR, 16.01% TNR, 83.99% FAR, 14.88% FRR.
- **Confusion Matrices**: Inspect TP, TN, FP, FN side-by-side.
- **Invalid Category Breakdown**:
  - See how compilers achieve 100% rejection on Double Operator, Missing Table Name, Missing SET, and Unsupported CTE, whereas statistical classifiers falsely accept 50.3% to 84.0% of invalid queries (failing completely on missing table and missing SET clauses).
- **False-Rejection Explorer**: Filter the 120 valid queries rejected by the unrefined learned grammar by template.

---

### Minute 5: Learning Curve & Artifact Exports
- **Induction Learning Curve**:
  - Inspect the plot and table showing how grammar generalization scales across 10%, 25%, 50%, 75%, and 100% of training templates.
  - As templates reach 100%, FRR drops from 28.57% to 14.29% while maintaining a 0% False Acceptance Rate.
- **Export Artifacts**:
  - Test the download buttons for `model_comparison.csv`, `model_comparison.json`, and `learning_curve.csv`.
- **Review Interpretation & Caveats Box**:
  - Ground truth baseline represents compiler engineer reference; labels are template-generated; splits have zero template overlap.

---

## 🧪 Terminal Verification Commands

To verify independently from the CLI:

```bash
# 1. Run all unit and integration tests (25 tests)
python -m pytest tests -v

# 2. Run grammar induction on training queries
python compiler/grammar_builder.py

# 3. Run comparative model benchmark
python evaluation/compare_models.py

# 4. Generate learning curve data points and figure
python evaluation/learning_curve.py
```
