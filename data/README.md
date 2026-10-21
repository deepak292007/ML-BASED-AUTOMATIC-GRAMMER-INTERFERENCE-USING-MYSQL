# AutoGrammar School Student Dataset

## Overview
This dataset contains synthetic, culturally authentic Indian school management records and an extensive corpus of domain-specific SQL queries.

## Entities & Tables
- **synthetic_students.csv**: 10000 records (First/Last name, Class, Section, DOB, Gender, City, State, Enrollment Date, Status).
- **synthetic_teachers.csv**: 40 records (First/Last name, Subject specialty).
- **synthetic_classes.csv**: 7 records (Class name, Academic Year, Class Teacher ID).
- **synthetic_subjects.csv**: 6 records (Core curriculum subjects).
- **synthetic_marks.csv**: 6031 records (Exam evaluations).
- **synthetic_attendance.csv**: 6000 records (Daily student attendance).

## Query Dataset
- Total queries: 7000
- Valid queries: 5000 across 16 SQL DSL categories.
- Invalid queries: 2000 with documented error taxonomy (Lexical, Missing Clauses, Misplaced Keywords, Unbalanced Parentheses, Malformed Operators, Schema Mismatches, Unsupported Syntax).

## Data Leakage Prevention
Splits are grouped strictly by `template_id`:
- **Train**: 4826 queries (47 distinct templates)
- **Validation**: 1028 queries (10 distinct templates)
- **Test**: 1146 queries (11 distinct templates)

No template in the training set appears in validation or test splits.
