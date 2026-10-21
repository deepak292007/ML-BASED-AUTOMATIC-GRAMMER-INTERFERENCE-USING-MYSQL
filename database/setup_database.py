"""
Database Setup and Seeding Script for AutoGrammar.
Generates seed_data.sql from synthetic CSV files and initializes school_db in MySQL if accessible.
"""

import os
import sys
import pandas as pd
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import db_manager, MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

load_dotenv()


def generate_seed_data_sql(
    data_dir: str = "data",
    output_sql: str = "database/seed_data.sql"
):
    """Converts synthetic CSV files into an executable SQL seed script."""
    print(f"[*] Generating SQL insert statements from CSV files in {data_dir}...")
    os.makedirs(os.path.dirname(output_sql), exist_ok=True)

    with open(output_sql, "w", encoding="utf-8") as out:
        out.write("-- AutoGrammar Synthetic School Data Seeding Script\n")
        out.write("USE school_db;\n\n")

        # 1. Subjects
        sub_path = os.path.join(data_dir, "synthetic_subjects.csv")
        if os.path.exists(sub_path):
            df = pd.read_csv(sub_path)
            out.write("-- Subjects\n")
            for _, r in df.iterrows():
                name = str(r['subject_name']).replace("'", "''")
                out.write(f"INSERT INTO subjects (subject_id, subject_name) VALUES ({r['subject_id']}, '{name}');\n")
            out.write("\n")

        # 2. Teachers
        tea_path = os.path.join(data_dir, "synthetic_teachers.csv")
        if os.path.exists(tea_path):
            df = pd.read_csv(tea_path)
            out.write("-- Teachers\n")
            for _, r in df.iterrows():
                fn = str(r['first_name']).replace("'", "''")
                ln = str(r['last_name']).replace("'", "''")
                sub = "NULL" if pd.isna(r['subject_id']) else int(r['subject_id'])
                out.write(f"INSERT INTO teachers (teacher_id, first_name, last_name, subject_id) VALUES ({r['teacher_id']}, '{fn}', '{ln}', {sub});\n")
            out.write("\n")

        # 3. Classes
        cls_path = os.path.join(data_dir, "synthetic_classes.csv")
        if os.path.exists(cls_path):
            df = pd.read_csv(cls_path)
            out.write("-- Classes\n")
            for _, r in df.iterrows():
                cn = str(r['class_name']).replace("'", "''")
                ay = str(r['academic_year']).replace("'", "''")
                ct = "NULL" if pd.isna(r['class_teacher_id']) else int(r['class_teacher_id'])
                out.write(f"INSERT INTO classes (class_id, class_name, academic_year, class_teacher_id) VALUES ({r['class_id']}, '{cn}', '{ay}', {ct});\n")
            out.write("\n")

        # 4. Students (sample top 500 for seed_data.sql to keep file size reasonable)
        stu_path = os.path.join(data_dir, "synthetic_students.csv")
        if os.path.exists(stu_path):
            df = pd.read_csv(stu_path).head(500)
            out.write("-- Students (Top 500 seed sample)\n")
            for _, r in df.iterrows():
                fn = str(r['first_name']).replace("'", "''")
                ln = str(r['last_name']).replace("'", "''")
                sec = str(r['section']).replace("'", "''")
                cty = str(r['city']).replace("'", "''")
                st = str(r['state']).replace("'", "''")
                sta = str(r['status']).replace("'", "''")
                out.write(
                    f"INSERT INTO students (student_id, admission_no, first_name, last_name, class_id, section, date_of_birth, gender, city, state, enrollment_date, status) "
                    f"VALUES ({r['student_id']}, '{r['admission_no']}', '{fn}', '{ln}', {r['class_id']}, '{sec}', '{r['date_of_birth']}', '{r['gender']}', '{cty}', '{st}', '{r['enrollment_date']}', '{sta}');\n"
                )
            out.write("\n")

    print(f"[+] Seed script generated: {output_sql}")


def setup_mysql_database():
    """Applies schema and seed data to live MySQL if accessible."""
    conn_info = db_manager.test_connection()
    print(f"[*] Database Status: {conn_info['status']} ({conn_info['engine']})")

    if not db_manager.mysql_available:
        print("[!] MySQL server is not accessible with current credentials.")
        print("    AutoGrammar will operate in seamless Relational Sandbox mode.")
        return False

    import pymysql
    schema_path = "database/schema.sql"
    seed_path = "database/seed_data.sql"

    try:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            autocommit=True
        )
        with conn.cursor() as cursor:
            print("[*] Executing database/schema.sql...")
            with open(schema_path, "r", encoding="utf-8") as f:
                commands = f.read().split(";")
                for cmd in commands:
                    if cmd.strip():
                        cursor.execute(cmd)

            if os.path.exists(seed_path):
                print("[*] Executing database/seed_data.sql...")
                with open(seed_path, "r", encoding="utf-8") as f:
                    seed_cmds = f.read().split(";")
                    for cmd in seed_cmds:
                        if cmd.strip():
                            cursor.execute(cmd)
        conn.close()
        print("[+] MySQL school_db successfully initialized and seeded!")
        return True
    except Exception as e:
        print(f"[-] MySQL setup encountered error: {e}")
        return False


if __name__ == "__main__":
    generate_seed_data_sql()
    setup_mysql_database()
