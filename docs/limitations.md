# AutoGrammar Limitations and Future Directions

## 1. Domain-Specific Scope
- **SQL Subset**: AutoGrammar is targeted to a school student management domain-specific language (DSL). It supports `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `JOIN`, aggregations, and subqueries, but explicitly excludes advanced MySQL features such as stored procedures, triggers, window functions (`OVER PARTITION BY`), CTEs (`WITH`), and spatial data types.
- **Dialect Assumption**: The dialect assumes MySQL 8.0+ syntax conventions (single-quoted string literals, case-insensitive keywords, standard comparisons).

---

## 2. Grammar Induction Boundaries
- **Exemplar Dependency**: Grammar rule induction requires representative training exemplars. If a language construct (such as `DELETE` or recursive CTEs) is absent from the training set due to template disjointness, the induced grammar correctly flags it as unsupported unless updated via the interactive refinement loop.
- **Structural Generalization vs Over-generalization**: Rule induction balances precision and recall. Over-generalization (e.g. allowing arbitrary token permutations) would cause invalid queries to pass; AutoGrammar maintains high specificity (100% invalid query rejection on test queries) by constraining rule expansions to verified clause sequences.

---

## 3. Machine Learning Classifier Trade-offs
- **N-gram Bag-of-Words Limitations**: As proven in experimental benchmarking, statistical classifiers (TF-IDF + Logistic Regression) achieve only 66.7% accuracy on unseen templates with an 84.0% false acceptance rate on invalid queries. Statistical n-gram models recognize token frequencies but lack recursive hierarchical parsing capability.
- **Explainability**: Statistical classifiers output only scalar confidence scores, whereas compiler parsers output deterministic parse trees and exact `(line, column)` syntax diagnostics.

---

## 4. Future Directions
1. **Probabilistic Context-Free Grammars (PCFG)**: Learning production rule probabilities directly from query frequencies.
2. **Neural Guided Induction**: Utilizing transformer-based semantic parsers (e.g., CodeT5) as candidate proposal mechanisms paired with formal Lark grammar verification.
3. **Multi-Dialect Support**: Expanding induction beyond MySQL to PostgreSQL and SQLite dialect variants.
