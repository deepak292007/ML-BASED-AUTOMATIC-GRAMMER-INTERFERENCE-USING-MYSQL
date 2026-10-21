# AutoGrammar Methodology & Experimental Design

## 1. Synthetic Indian School Data Generation

To ensure reproducible domain-specific realism without scraping personal information, AutoGrammar synthesizes cultural and administrative school management entities:
- **First Names**: Configurable regionally diverse lists spanning northern, southern, and western India (e.g., *Aarav, Ananya, Arjun, Priya, Sai Teja, Karthik, Sneha, Harsha*).
- **Surnames**: Pan-Indian naming patterns (e.g., *Sharma, Reddy, Kumar, Patel, Nair, Rao, Iyer, Gupta, Deshmukh*).
- **Locations**: Fictional combinations of Indian states and corresponding cities across Andhra Pradesh, Telangana, Karnataka, Tamil Nadu, Kerala, Maharashtra, and Delhi.
- **Relational Tables**:
  - `students`: 10,000 records
  - `teachers`: 40 records
  - `classes`: 7 academic classes (Class 6 to Class 12)
  - `subjects`: 6 core subjects (Mathematics, English, Science, Social Studies, Hindi, Computer Science)
  - `marks`: 6,031 exam evaluation records
  - `attendance`: 6,000 daily attendance records

---

## 2. Query Corpus and Error Taxonomy

The query generator constructs 7,000 domain-specific queries across 16 categories:
1. Simple `SELECT` statements (wildcard, column lists, `DISTINCT`)
2. Equality and comparison filters (`=`, `!=`, `<`, `>`, `<=`, `>=`)
3. Logical operations (`AND`, `OR`, `NOT`, nested parentheses)
4. Set and pattern operators (`IN`, `BETWEEN`, `LIKE`, `IS NULL`, `IS NOT NULL`)
5. Sorting and pagination (`ORDER BY`, `LIMIT`)
6. Aggregations (`COUNT`, `SUM`, `AVG`, `MIN`, `MAX`, `GROUP BY`, `HAVING`)
7. Table relational joins (`INNER JOIN`, `LEFT JOIN` with `ON` predicates)
8. Date-based queries (`enrollment_date`, `attendance_date`)
9. DML queries (`INSERT`, `UPDATE`, `DELETE`)
10. Nested subqueries (`WHERE col IN (SELECT ...)`, scalar subqueries)

### Invalid Query Taxonomy
Invalid queries are generated systematically:
- **Lexical Errors**: Illegal characters (`@#$`, unsupported tokens).
- **Syntax Errors**: Missing clauses (`SELECT without FROM`), misplaced clauses (`ORDER BY before WHERE`), unbalanced parentheses, malformed `BETWEEN...OR` operators, trailing commas.
- **Semantic Errors**: Syntactically valid SQL referencing nonexistent tables (e.g. `student_fees`) or unknown columns (e.g. `blood_group`).
- **Unsupported Syntax**: Constructs beyond the school DSL (e.g. Window functions, `UNION ALL`, `CTEs`).

---

## 3. Mandatory Data Leakage Prevention

To ensure rigorous scientific validity:
- Queries are generated from 68 distinct structural templates (`template_id`).
- Dataset splitting is performed **at the template level**, rather than by random individual query sampling.
- **Train (70%)**: 4,826 queries across 29 valid and 18 invalid templates.
- **Validation (15%)**: 1,028 queries across 6 valid and 4 invalid templates.
- **Test (15%)**: 1,146 queries across 7 valid and 4 invalid templates.

Because no template in the training set appears in validation or test sets, models cannot achieve high performance simply by memorizing literal slot fillers (e.g. swapping `'Guntur'` for `'Vijayawada'`). Models must generalize grammatical structure.
