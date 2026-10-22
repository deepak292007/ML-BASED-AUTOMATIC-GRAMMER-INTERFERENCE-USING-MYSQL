# ⚡ AutoGrammar Showcase Website

A self-contained, dependency-free static website for evaluating and presenting the **AutoGrammar** project to examiners and evaluators during project reviews or viva examinations.

---

## 🚀 How to Open

The website has **zero external dependencies**, requires **no Node.js / npm build step**, and makes **no remote network requests**. It operates completely offline.

Simply double-click or open:

```
site/index.html
```

Or open in any modern browser via file URL:
```
file:///c:/Users/HANUMAN/compilor_design/site/index.html
```

Or start a local web server (optional):
```bash
python -m http.server 8000 --directory site
# Navigate to http://localhost:8000
```

---

## ⚙️ How to Edit the `CONFIG` Object

The website displays metadata (student name, guide name, institution, academic year) sourced from a single configuration object at the top of [`site/js/data.js`](js/data.js):

```javascript
const CONFIG = {
  projectTitle: "AutoGrammar",
  subtitle: "Machine Learning-Based Automatic Grammar Inference for SQL DSL over school_db",
  teamMembers: ["Deepak Kumar", "Antigravity Team"],
  guide: "Evaluator / Project Viva Showcase",
  institution: "Department of Computer Science & Engineering",
  academicYear: "2025 - 2026",
  mysqlVerified: false, // Set to true if running over live MySQL 8.0 server
  repoUrl: "https://github.com/deepak292007/ML-BASED-AUTOMATIC-GRAMMER-INTERFERENCE-USING-MYSQL"
};
```

You can customize names, titles, or institution without modifying any other HTML, CSS, or JS code.

---

## 🔄 How `data.js` Was Produced

[`site/js/data.js`](js/data.js) is compiled by [`site/tools/export_site_data.py`](tools/export_site_data.py):

```bash
python site/tools/export_site_data.py
```

### Process:
1. **Read-Only Inspection**: Reads existing evaluation results (`evaluation/results/model_comparison.json`, `parser_test_metrics.json`, `classifier_test_metrics.json`, `grammar_metrics.json`, `learning_curve.json`).
2. **Schema & Grammar Loading**: Loads `database/schema.sql`, `grammars/learned.lark`, and `grammars/baseline.lark`.
3. **Preset Verification**: Evaluates the 12 query presets through the real compiler pipeline (`QueryValidator`) and the saved ML baseline model (`ml/saved_models/classifier.joblib`), saving exact precomputed real Python verdicts.
4. **False Rejection Harvesting**: Evaluates the 840 valid test queries with Lark to record the 120 valid queries that the unrefined learned grammar rejects (all belonging to template `V_AGG_02` using `COUNT(*)`, demonstrating zero-leakage induction boundaries).
5. **ML Parameter Extraction**: Extracts the 3,243-term TF-IDF vocabulary, IDF weights, and Logistic Regression coefficients/intercept, enabling exact real-time scoring in pure JavaScript offline.

---

## ⌨️ Keyboard Shortcuts & Features

- **`?`**: Open / close keyboard shortcuts modal.
- **`/`**: Focus the SQL DSL query editor in the Live Demo.
- **`1` - `8`**: Load evaluation presets 1 through 8 directly.
- **`P`**: Toggle Presentation Slide Mode.
- **`←` / `→`**: Navigate previous / next section in Presentation Mode.
- **`☀️ Light` / `🌙 Dark`**: Toggle color theme (persisted in browser `localStorage`).
- **`Print (Ctrl+P)`**: Formats the entire single-page showcase into a clean, PDF-ready report.

---

## 📁 File Structure

```
site/
├── index.html                  # Main single-page showcase application
├── README.md                   # Documentation and usage guide
├── css/
│   └── style.css               # WCAG AA, dark/light theme, print stylesheet
├── js/
│   ├── data.js                 # Exported metrics, schema, presets, and ML weights
│   ├── validator.js            # 4-stage compiler re-implementation & Levenshtein
│   ├── charts.js               # Hand-written inline SVG charts and diagrams
│   └── app.js                  # UI controllers, presentation mode, sandbox logic
└── tools/
    └── export_site_data.py     # Read-only exporter script
```
