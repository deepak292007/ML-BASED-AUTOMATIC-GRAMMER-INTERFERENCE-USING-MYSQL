"""
Schema-Aware Semantic Validator for AutoGrammar SQL DSL.
Performs table resolution, column validation, alias mapping, and type sanity checks.
"""

from typing import Dict, List, Set, Any, Optional
from compiler.error_handler import CompilerDiagnostic


# Canonical school_db schema definition
SCHOOL_DB_SCHEMA: Dict[str, Dict[str, str]] = {
    "students": {
        "student_id": "INT",
        "admission_no": "VARCHAR",
        "first_name": "VARCHAR",
        "last_name": "VARCHAR",
        "class_id": "INT",
        "section": "VARCHAR",
        "date_of_birth": "DATE",
        "gender": "VARCHAR",
        "city": "VARCHAR",
        "state": "VARCHAR",
        "enrollment_date": "DATE",
        "status": "VARCHAR"
    },
    "classes": {
        "class_id": "INT",
        "class_name": "VARCHAR",
        "academic_year": "VARCHAR",
        "class_teacher_id": "INT"
    },
    "teachers": {
        "teacher_id": "INT",
        "first_name": "VARCHAR",
        "last_name": "VARCHAR",
        "subject_id": "INT"
    },
    "subjects": {
        "subject_id": "INT",
        "subject_name": "VARCHAR"
    },
    "marks": {
        "mark_id": "INT",
        "student_id": "INT",
        "subject_id": "INT",
        "exam_name": "VARCHAR",
        "marks_obtained": "INT",
        "maximum_marks": "INT",
        "exam_date": "DATE"
    },
    "attendance": {
        "attendance_id": "INT",
        "student_id": "INT",
        "attendance_date": "DATE",
        "attendance_status": "VARCHAR"
    }
}


class SemanticChecker:
    """Validates query entities against relational schema definitions."""

    def __init__(self, schema: Optional[Dict[str, Dict[str, str]]] = None):
        self.schema = schema or SCHOOL_DB_SCHEMA

    def validate_semantics(self, semantic_info: Dict[str, Any]) -> List[CompilerDiagnostic]:
        """
        Validates extracted query semantics (tables, columns, aliases) against the schema.
        Returns a list of CompilerDiagnostic errors (empty if valid).
        """
        diagnostics: List[CompilerDiagnostic] = []

        tables = semantic_info.get("tables", [])
        columns = semantic_info.get("columns", [])
        aliases = semantic_info.get("aliases", {})  # alias -> table_name

        # 1. Check Table Existence
        resolved_tables = {}
        for tbl in tables:
            if tbl not in self.schema:
                diagnostics.append(CompilerDiagnostic(
                    phase="SEMANTIC",
                    message=f"Nonexistent table '{tbl}' referenced in query.",
                    suggestion=f"Known tables are: {', '.join(sorted(self.schema.keys()))}"
                ))
            else:
                resolved_tables[tbl] = self.schema[tbl]

        # Invert alias mapping
        table_for_alias = {}
        for alias, tbl in aliases.items():
            if tbl in self.schema:
                table_for_alias[alias] = tbl

        # All known columns available in the scope of this query
        all_query_columns: Set[str] = set()
        for tbl in resolved_tables:
            for col in self.schema[tbl]:
                all_query_columns.add(col)

        # 2. Check Column Existence
        for col_ref in columns:
            if col_ref == "*":
                continue

            if "." in col_ref:
                qualifier, col_name = col_ref.split(".", 1)
                if col_name == "*":
                    continue

                target_tbl = None
                if qualifier in table_for_alias:
                    target_tbl = table_for_alias[qualifier]
                elif qualifier in resolved_tables:
                    target_tbl = qualifier

                if target_tbl:
                    if col_name not in self.schema[target_tbl]:
                        diagnostics.append(CompilerDiagnostic(
                            phase="SEMANTIC",
                            message=f"Column '{col_name}' does not exist on table '{target_tbl}' (aliased as '{qualifier}').",
                            suggestion=f"Available columns on '{target_tbl}': {', '.join(sorted(self.schema[target_tbl].keys()))}"
                        ))
                else:
                    diagnostics.append(CompilerDiagnostic(
                        phase="SEMANTIC",
                        message=f"Unknown table alias or qualifier '{qualifier}' in column reference '{col_ref}'.",
                        suggestion="Ensure all table qualifiers match the table name or assigned alias."
                    ))
            else:
                # Unqualified column
                if resolved_tables and col_ref not in all_query_columns:
                    diagnostics.append(CompilerDiagnostic(
                        phase="SEMANTIC",
                        message=f"Unknown column '{col_ref}'. Column does not exist in tables referenced by query: {', '.join(resolved_tables.keys())}.",
                        suggestion=f"Available columns in referenced tables: {', '.join(sorted(all_query_columns))}"
                    ))

        return diagnostics
