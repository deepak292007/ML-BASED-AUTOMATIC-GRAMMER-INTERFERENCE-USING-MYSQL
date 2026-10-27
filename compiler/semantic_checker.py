"""
Schema-Aware Semantic Validator for AutoGrammar SQL DSL.
Performs table resolution, column validation, alias mapping, and type sanity checks.
"""

from typing import Dict, List, Set, Any, Optional
from compiler.error_handler import CompilerDiagnostic


# Canonical school_db schema definition with column types
SCHOOL_DB_SCHEMA: Dict[str, Dict[str, str]] = {
    "students": {
        "student_id": "INT",
        "admission_no": "VARCHAR(30)",
        "first_name": "VARCHAR(50)",
        "last_name": "VARCHAR(50)",
        "class_id": "INT",
        "section": "VARCHAR(5)",
        "date_of_birth": "DATE",
        "gender": "VARCHAR(10)",
        "city": "VARCHAR(50)",
        "state": "VARCHAR(50)",
        "enrollment_date": "DATE",
        "status": "VARCHAR(20)"
    },
    "classes": {
        "class_id": "INT",
        "class_name": "VARCHAR(50)",
        "academic_year": "VARCHAR(20)",
        "class_teacher_id": "INT"
    },
    "teachers": {
        "teacher_id": "INT",
        "first_name": "VARCHAR(50)",
        "last_name": "VARCHAR(50)",
        "subject_id": "INT"
    },
    "subjects": {
        "subject_id": "INT",
        "subject_name": "VARCHAR(100)"
    },
    "marks": {
        "mark_id": "INT",
        "student_id": "INT",
        "subject_id": "INT",
        "exam_name": "VARCHAR(100)",
        "marks_obtained": "INT",
        "maximum_marks": "INT",
        "exam_date": "DATE"
    },
    "attendance": {
        "attendance_id": "INT",
        "student_id": "INT",
        "attendance_date": "DATE",
        "attendance_status": "VARCHAR(20)"
    }
}

# Detailed column metadata for UI and tools
SCHEMA_METADATA: Dict[str, List[Dict[str, Any]]] = {
    "subjects": [
        {"name": "subject_id", "type": "INT", "pk": True, "fk": None, "desc": "Unique subject identifier"},
        {"name": "subject_name", "type": "VARCHAR(100)", "pk": False, "fk": None, "desc": "Subject title"}
    ],
    "teachers": [
        {"name": "teacher_id", "type": "INT", "pk": True, "fk": None, "desc": "Unique teacher ID"},
        {"name": "first_name", "type": "VARCHAR(50)", "pk": False, "fk": None, "desc": "Teacher given name"},
        {"name": "last_name", "type": "VARCHAR(50)", "pk": False, "fk": None, "desc": "Teacher family name"},
        {"name": "subject_id", "type": "INT", "pk": False, "fk": "subjects.subject_id", "desc": "Specialization subject ID"}
    ],
    "classes": [
        {"name": "class_id", "type": "INT", "pk": True, "fk": None, "desc": "Unique class level identifier"},
        {"name": "class_name", "type": "VARCHAR(50)", "pk": False, "fk": None, "desc": "Class designation (e.g. Class 5)"},
        {"name": "academic_year", "type": "VARCHAR(20)", "pk": False, "fk": None, "desc": "Academic session"},
        {"name": "class_teacher_id", "type": "INT", "pk": False, "fk": "teachers.teacher_id", "desc": "Assigned class teacher"}
    ],
    "students": [
        {"name": "student_id", "type": "INT", "pk": True, "fk": None, "desc": "Unique student primary key"},
        {"name": "admission_no", "type": "VARCHAR(30)", "pk": False, "fk": None, "desc": "Unique admission / roll number"},
        {"name": "first_name", "type": "VARCHAR(50)", "pk": False, "fk": None, "desc": "Student given name"},
        {"name": "last_name", "type": "VARCHAR(50)", "pk": False, "fk": None, "desc": "Student family name"},
        {"name": "class_id", "type": "INT", "pk": False, "fk": "classes.class_id", "desc": "Enrolled class level"},
        {"name": "section", "type": "VARCHAR(5)", "pk": False, "fk": None, "desc": "Class section (A/B/C)"},
        {"name": "date_of_birth", "type": "DATE", "pk": False, "fk": None, "desc": "Student birth date"},
        {"name": "gender", "type": "VARCHAR(10)", "pk": False, "fk": None, "desc": "Gender (Male/Female)"},
        {"name": "city", "type": "VARCHAR(50)", "pk": False, "fk": None, "desc": "Residence city"},
        {"name": "state", "type": "VARCHAR(50)", "pk": False, "fk": None, "desc": "Residence state"},
        {"name": "enrollment_date", "type": "DATE", "pk": False, "fk": None, "desc": "Date of enrollment"},
        {"name": "status", "type": "VARCHAR(20)", "pk": False, "fk": None, "desc": "Enrollment status (Active/Transferred)"}
    ],
    "marks": [
        {"name": "mark_id", "type": "INT", "pk": True, "fk": None, "desc": "Unique mark record identifier"},
        {"name": "student_id", "type": "INT", "pk": False, "fk": "students.student_id", "desc": "Foreign key to students"},
        {"name": "subject_id", "type": "INT", "pk": False, "fk": "subjects.subject_id", "desc": "Foreign key to subjects"},
        {"name": "exam_name", "type": "VARCHAR(100)", "pk": False, "fk": None, "desc": "Exam name"},
        {"name": "marks_obtained", "type": "INT", "pk": False, "fk": None, "desc": "Exam score obtained (0-100)"},
        {"name": "maximum_marks", "type": "INT", "pk": False, "fk": None, "desc": "Maximum possible marks"},
        {"name": "exam_date", "type": "DATE", "pk": False, "fk": None, "desc": "Date of examination"}
    ],
    "attendance": [
        {"name": "attendance_id", "type": "INT", "pk": True, "fk": None, "desc": "Unique attendance record identifier"},
        {"name": "student_id", "type": "INT", "pk": False, "fk": "students.student_id", "desc": "Foreign key to students"},
        {"name": "attendance_date", "type": "DATE", "pk": False, "fk": None, "desc": "Date of recorded attendance"},
        {"name": "attendance_status", "type": "VARCHAR(20)", "pk": False, "fk": None, "desc": "Status (Present/Absent)"}
    ]
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

                target_tbl = None
                if qualifier in table_for_alias:
                    target_tbl = table_for_alias[qualifier]
                elif qualifier in resolved_tables:
                    target_tbl = qualifier

                if not target_tbl:
                    diagnostics.append(CompilerDiagnostic(
                        phase="SEMANTIC",
                        message=f"Unknown table alias or qualifier '{qualifier}' in column reference '{col_ref}'.",
                        suggestion="Ensure all table qualifiers match the table name or assigned alias."
                    ))
                    continue

                if col_name == "*":
                    continue

                if col_name not in self.schema[target_tbl]:
                    diagnostics.append(CompilerDiagnostic(
                        phase="SEMANTIC",
                        message=f"Column '{col_name}' does not exist on table '{target_tbl}' (aliased as '{qualifier}').",
                        suggestion=f"Available columns on '{target_tbl}': {', '.join(sorted(self.schema[target_tbl].keys()))}"
                    ))
            else:
                # Unqualified column
                if resolved_tables and col_ref not in all_query_columns:
                    diagnostics.append(CompilerDiagnostic(
                        phase="SEMANTIC",
                        message=f"Unknown column '{col_ref}'. Column does not exist in tables referenced by query: {', '.join(resolved_tables.keys())}.",
                        suggestion=f"Available columns in referenced tables: {', '.join(sorted(all_query_columns))}"
                    ))
                elif len(resolved_tables) > 1 and "JOIN" in semantic_info.get("clauses", []):
                    # Check for ambiguity when multiple tables are joined in query
                    matching_tables = [tbl for tbl in resolved_tables if col_ref in self.schema[tbl]]
                    if len(matching_tables) > 1:
                        diagnostics.append(CompilerDiagnostic(
                            phase="SEMANTIC",
                            message=f"Ambiguous column reference '{col_ref}'. Column exists in multiple referenced tables: {', '.join(sorted(matching_tables))}.",
                            suggestion=f"Qualify '{col_ref}' with table name or alias (e.g. {matching_tables[0]}.{col_ref})."
                        ))

        return diagnostics
