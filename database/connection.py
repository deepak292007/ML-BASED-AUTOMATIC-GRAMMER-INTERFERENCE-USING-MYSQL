"""
Database Connection Manager and Execution Sandbox for AutoGrammar.
Supports:
  1. Direct MySQL (8.0+) connection via PyMySQL with connection pooling / checks.
  2. Fallback SQLite in-memory sandbox populated with synthetic data when MySQL is not configured.
  3. Query execution safeguards and schema introspection.
"""

import os
import sqlite3
from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "school_db")


class DatabaseManager:
    """Manages database connectivity and safe query execution."""

    def __init__(self):
        self.mysql_available = False
        self._sqlite_conn: Optional[sqlite3.Connection] = None
        self._check_mysql_availability()

    def _check_mysql_availability(self) -> bool:
        """Attempts a quick handshake with the MySQL server."""
        try:
            import pymysql
            conn = pymysql.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                connect_timeout=2
            )
            conn.close()
            self.mysql_available = True
            return True
        except Exception:
            self.mysql_available = False
            return False

    def get_connection(self):
        """Returns active database connection (MySQL or Fallback Sandbox)."""
        if self.mysql_available:
            import pymysql
            return pymysql.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False
            )
        else:
            return self.get_sqlite_sandbox_connection()

    def get_sqlite_sandbox_connection(self) -> sqlite3.Connection:
        """Initializes or returns an in-memory SQLite sandbox loaded with synthetic CSV data."""
        if self._sqlite_conn is None:
            conn = sqlite3.connect(":memory:", check_same_thread=False)
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
            csv_map = {
                "subjects": "synthetic_subjects.csv",
                "teachers": "synthetic_teachers.csv",
                "classes": "synthetic_classes.csv",
                "students": "synthetic_students.csv",
                "marks": "synthetic_marks.csv",
                "attendance": "synthetic_attendance.csv"
            }
            for table_name, fname in csv_map.items():
                fpath = os.path.join(data_dir, fname)
                if os.path.exists(fpath):
                    df = pd.read_csv(fpath)
                    df.to_sql(table_name, conn, if_exists="replace", index=False)
            self._sqlite_conn = conn
        return self._sqlite_conn

    def test_connection(self) -> Dict[str, Any]:
        """Tests database connectivity and reports mode."""
        self._check_mysql_availability()
        if self.mysql_available:
            return {
                "status": "ONLINE",
                "engine": "MySQL 8.0+",
                "host": MYSQL_HOST,
                "database": MYSQL_DATABASE,
                "user": MYSQL_USER
            }
        else:
            return {
                "status": "SANDBOX_MODE",
                "engine": "In-Memory Relational Sandbox (SQLite)",
                "note": "Local MySQL server is offline or authentication required; running with loaded synthetic school data."
            }

    def execute_query(
        self,
        query: str,
        read_only: bool = True,
        max_rows: int = 100
    ) -> Dict[str, Any]:
        """
        Executes a validated SQL query against the database engine.
        Enforces read-only safeguards unless explicitly overridden.
        """
        cleaned = query.strip().rstrip(";")
        upper_q = cleaned.upper()

        if read_only and not upper_q.startswith("SELECT"):
            return {
                "success": False,
                "error": "Query execution blocked: only read-only SELECT queries are permitted in interactive execution.",
                "rows": [],
                "columns": [],
                "row_count": 0
            }

        try:
            if self.mysql_available:
                import pymysql
                conn = self.get_connection()
                try:
                    with conn.cursor() as cursor:
                        cursor.execute(cleaned)
                        rows = cursor.fetchmany(max_rows)
                        columns = [col[0] for col in cursor.description] if cursor.description else []
                        return {
                            "success": True,
                            "engine": "MySQL 8.0+",
                            "columns": columns,
                            "rows": rows,
                            "row_count": len(rows),
                            "truncated": len(rows) == max_rows
                        }
                finally:
                    conn.close()
            else:
                conn = self.get_sqlite_sandbox_connection()
                cursor = conn.cursor()
                cursor.execute(cleaned)
                raw_rows = cursor.fetchmany(max_rows)
                columns = [col[0] for col in cursor.description] if cursor.description else []
                rows = [dict(zip(columns, r)) for r in raw_rows]
                return {
                    "success": True,
                    "engine": "Relational Sandbox",
                    "columns": columns,
                    "rows": rows,
                    "row_count": len(rows),
                    "truncated": len(rows) == max_rows
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "rows": [],
                "columns": [],
                "row_count": 0
            }

    def get_tables(self) -> List[str]:
        """Returns list of tables present in active database."""
        return ["students", "teachers", "classes", "subjects", "marks", "attendance"]

    def preview_table(self, table_name: str, limit: int = 10) -> Dict[str, Any]:
        """Returns top rows of given table."""
        if table_name not in self.get_tables():
            return {"success": False, "error": f"Invalid table '{table_name}'", "rows": []}
        return self.execute_query(f"SELECT * FROM {table_name} LIMIT {int(limit)};", read_only=True)


# Singleton database manager instance
db_manager = DatabaseManager()
