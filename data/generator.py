"""
Synthetic Indian School Dataset and Query Generator for AutoGrammar.
Generates:
  1. Synthetic database entities (Students, Classes, Teachers, Subjects, Marks, Attendance)
  2. Diverse SQL queries covering 16 categories (Valid & Invalid)
  3. Template-level grouped Train/Validation/Test splits (Data leakage prevention)
"""

import os
import json
import random
import datetime
from typing import List, Dict, Tuple, Any
import pandas as pd
import numpy as np

# Fixed random seed for reproducibility
RANDOM_SEED = 42

FIRST_NAMES_MALE = [
    "Aarav", "Arjun", "Rahul", "Sai Teja", "Karthik", "Rohit", "Aditya", "Harsha",
    "Pranav", "Vikram", "Suresh", "Manoj", "Ramesh", "Deepak", "Nikhil", "Varun",
    "Surya", "Ganesh", "Abhishek", "Vishal", "Kalyan", "Chaitanya", "Venkata", "Siddharth",
    "Tarun", "Anil", "Raghav", "Manish", "Gautam", "Lokesh", "Kiran", "Vijay"
]

FIRST_NAMES_FEMALE = [
    "Ananya", "Saanvi", "Priya", "Lakshmi", "Sneha", "Kavya", "Pooja", "Divya",
    "Meera", "Swathi", "Bhavana", "Deepika", "Shreya", "Rhea", "Sandhya", "Keerthi",
    "Aishwarya", "Shruti", "Anusha", "Pavani", "Sravani", "Harini", "Lavanya", "Tanvi",
    "Nandini", "Pallavi", "Geetha", "Sunita", "Archana", "Kusuma", "Nisha", "Swetha"
]

LAST_NAMES = [
    "Sharma", "Reddy", "Kumar", "Patel", "Nair", "Verma", "Rao", "Iyer",
    "Singh", "Menon", "Gupta", "Das", "Vardhan", "Chowdary", "Bhat", "Deshmukh",
    "Kulkarni", "Pillai", "Mukherjee", "Chatterjee", "Banerjee", "Mehta", "Joshi", "Mishra",
    "Naidu", "Gowda", "Hegde", "Shetty", "Patil", "Deshpande", "Sinha", "Shukla"
]

STATES_AND_CITIES = {
    "Andhra Pradesh": ["Visakhapatnam", "Vijayawada", "Guntur", "Nellore", "Tirupati", "Kakinada", "Kurnool"],
    "Telangana": ["Hyderabad", "Warangal", "Nizamabad", "Karimnagar", "Khammam"],
    "Karnataka": ["Bengaluru", "Mysuru", "Mangaluru", "Hubballi", "Belagavi"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem"],
    "Kerala": ["Kochi", "Thiruvananthapuram", "Kozhikode", "Thrissur", "Kollam"],
    "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad"],
    "Delhi": ["New Delhi", "North Delhi", "South Delhi", "West Delhi", "East Delhi"]
}

SCHOOL_NAMES = [
    "Sunrise Public School",
    "Vidya Bharathi High School",
    "Sri Chaitanya Model School",
    "Green Valley School",
    "Saraswati Vidya Mandir",
    "Little Scholars Academy",
    "Kendriya Vidyalaya Fictional",
    "Delhi Public Model School"
]

SUBJECTS_LIST = [
    (1, "Mathematics"),
    (2, "English"),
    (3, "Science"),
    (4, "Social Studies"),
    (5, "Hindi"),
    (6, "Computer Science")
]

EXAM_NAMES = ["Quarterly Exam", "Half-Yearly Exam", "Annual Final Exam", "Unit Test 1", "Unit Test 2"]
SECTIONS = ["A", "B", "C", "D"]
CLASS_NAMES = ["Class 6", "Class 7", "Class 8", "Class 9", "Class 10", "Class 11", "Class 12"]
GENDERS = ["Male", "Female"]
STATUSES = ["Active", "Active", "Active", "Active", "Transferred", "Graduated"]
ATTENDANCE_STATUSES = ["Present", "Present", "Present", "Present", "Absent", "Late", "Excused"]


def generate_database_records(num_students: int = 10000, seed: int = RANDOM_SEED) -> Dict[str, pd.DataFrame]:
    """Generates synthetic relational data for school_db."""
    random.seed(seed)
    np.random.seed(seed)

    # 1. Subjects
    subjects_df = pd.DataFrame(SUBJECTS_LIST, columns=["subject_id", "subject_name"])

    # 2. Teachers (40 teachers)
    teachers_data = []
    for tid in range(1, 41):
        gender = random.choice(GENDERS)
        first_name = random.choice(FIRST_NAMES_MALE if gender == "Male" else FIRST_NAMES_FEMALE)
        last_name = random.choice(LAST_NAMES)
        subject_id = random.choice(subjects_df["subject_id"].tolist())
        teachers_data.append({
            "teacher_id": tid,
            "first_name": first_name,
            "last_name": last_name,
            "subject_id": subject_id
        })
    teachers_df = pd.DataFrame(teachers_data)

    # 3. Classes (Classes 6 to 12)
    classes_data = []
    cid = 1
    for cname in CLASS_NAMES:
        class_teacher = random.choice(teachers_df["teacher_id"].tolist())
        classes_data.append({
            "class_id": cid,
            "class_name": cname,
            "academic_year": "2025-2026",
            "class_teacher_id": class_teacher
        })
        cid += 1
    classes_df = pd.DataFrame(classes_data)

    # 4. Students
    students_data = []
    base_dob = datetime.date(2008, 1, 1)
    base_enroll = datetime.date(2022, 6, 1)

    for sid in range(1, num_students + 1):
        adm_no = f"ADM-2025-{sid:05d}"
        gender = random.choice(GENDERS)
        first_name = random.choice(FIRST_NAMES_MALE if gender == "Male" else FIRST_NAMES_FEMALE)
        last_name = random.choice(LAST_NAMES)
        class_id = random.choice(classes_df["class_id"].tolist())
        section = random.choice(SECTIONS)

        state = random.choice(list(STATES_AND_CITIES.keys()))
        city = random.choice(STATES_AND_CITIES[state])

        dob_offset = random.randint(0, 365 * 6)
        dob = base_dob + datetime.timedelta(days=dob_offset)

        enroll_offset = random.randint(0, 365 * 3)
        enroll_date = base_enroll + datetime.timedelta(days=enroll_offset)
        status = random.choice(STATUSES)

        students_data.append({
            "student_id": sid,
            "admission_no": adm_no,
            "first_name": first_name,
            "last_name": last_name,
            "class_id": class_id,
            "section": section,
            "date_of_birth": str(dob),
            "gender": gender,
            "city": city,
            "state": state,
            "enrollment_date": str(enroll_date),
            "status": status
        })
    students_df = pd.DataFrame(students_data)

    # 5. Marks (sample for first 2000 students x 3 exams x 3 subjects to keep manageable size)
    marks_data = []
    mid = 1
    sample_student_ids = list(range(1, min(num_students + 1, 2001)))
    for sid in sample_student_ids:
        # Give each student 2 to 3 exam records
        for _ in range(random.randint(2, 4)):
            subj = random.choice(subjects_df["subject_id"].tolist())
            exam = random.choice(EXAM_NAMES)
            marks_obt = random.randint(35, 100)
            marks_data.append({
                "mark_id": mid,
                "student_id": sid,
                "subject_id": subj,
                "exam_name": exam,
                "marks_obtained": marks_obt,
                "maximum_marks": 100,
                "exam_date": "2025-09-15"
            })
            mid += 1
    marks_df = pd.DataFrame(marks_data)

    # 6. Attendance (sample records)
    attendance_data = []
    att_id = 1
    for sid in sample_student_ids[:1500]:
        for day in range(1, 5):
            att_date = f"2025-10-0{day}"
            status = random.choice(ATTENDANCE_STATUSES)
            attendance_data.append({
                "attendance_id": att_id,
                "student_id": sid,
                "attendance_date": att_date,
                "attendance_status": status
            })
            att_id += 1
    attendance_df = pd.DataFrame(attendance_data)

    return {
        "synthetic_students": students_df,
        "synthetic_teachers": teachers_df,
        "synthetic_classes": classes_df,
        "synthetic_subjects": subjects_df,
        "synthetic_marks": marks_df,
        "synthetic_attendance": attendance_df
    }


def define_query_templates() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Defines distinct structural templates for valid and invalid queries.
    Templates are uniquely identified with template_id to prevent data leakage across splits.
    """
    # 1. Valid Query Templates (spanning 16 categories)
    valid_templates = [
        # Cat 1: Simple SELECTs
        {"template_id": "V_SEL_01", "cat": "SELECT", "complexity": "Simple", "clauses": ["SELECT", "FROM"],
         "fmt": "SELECT {cols} FROM {table};"},
        {"template_id": "V_SEL_02", "cat": "SELECT", "complexity": "Simple", "clauses": ["SELECT", "FROM"],
         "fmt": "SELECT DISTINCT {col} FROM {table};"},
        {"template_id": "V_SEL_03", "cat": "SELECT", "complexity": "Simple", "clauses": ["SELECT", "FROM"],
         "fmt": "SELECT * FROM {table};"},

        # Cat 2: WHERE equality & comparison
        {"template_id": "V_WHR_01", "cat": "WHERE", "complexity": "Moderate", "clauses": ["SELECT", "FROM", "WHERE"],
         "fmt": "SELECT {cols} FROM students WHERE state = '{state}';"},
        {"template_id": "V_WHR_02", "cat": "WHERE", "complexity": "Moderate", "clauses": ["SELECT", "FROM", "WHERE"],
         "fmt": "SELECT {cols} FROM students WHERE city = '{city}';"},
        {"template_id": "V_WHR_03", "cat": "WHERE", "complexity": "Moderate", "clauses": ["SELECT", "FROM", "WHERE"],
         "fmt": "SELECT {cols} FROM students WHERE class_id = {class_id};"},
        {"template_id": "V_WHR_04", "cat": "WHERE", "complexity": "Moderate", "clauses": ["SELECT", "FROM", "WHERE"],
         "fmt": "SELECT mark_id, student_id, marks_obtained FROM marks WHERE marks_obtained >= {marks};"},
        {"template_id": "V_WHR_05", "cat": "WHERE", "complexity": "Moderate", "clauses": ["SELECT", "FROM", "WHERE"],
         "fmt": "SELECT mark_id, student_id, marks_obtained FROM marks WHERE marks_obtained < {marks};"},
        {"template_id": "V_WHR_06", "cat": "WHERE", "complexity": "Moderate", "clauses": ["SELECT", "FROM", "WHERE"],
         "fmt": "SELECT * FROM students WHERE status != 'Graduated';"},

        # Cat 3: AND, OR, NOT
        {"template_id": "V_LOG_01", "cat": "LOGICAL_OPS", "complexity": "Moderate", "clauses": ["SELECT", "FROM", "WHERE"],
         "fmt": "SELECT {cols} FROM students WHERE state = '{state}' AND gender = '{gender}';"},
        {"template_id": "V_LOG_02", "cat": "LOGICAL_OPS", "complexity": "Moderate", "clauses": ["SELECT", "FROM", "WHERE"],
         "fmt": "SELECT {cols} FROM students WHERE city = '{city}' OR state = '{state}';"},
        {"template_id": "V_LOG_03", "cat": "LOGICAL_OPS", "complexity": "Complex", "clauses": ["SELECT", "FROM", "WHERE"],
         "fmt": "SELECT {cols} FROM students WHERE (state = '{state}' OR state = '{alt_state}') AND gender = '{gender}';"},
        {"template_id": "V_LOG_04", "cat": "LOGICAL_OPS", "complexity": "Moderate", "clauses": ["SELECT", "FROM", "WHERE"],
         "fmt": "SELECT {cols} FROM students WHERE NOT (status = 'Transferred');"},

        # Cat 4: IN, BETWEEN, LIKE, IS NULL
        {"template_id": "V_OPR_01", "cat": "OPERATORS", "complexity": "Moderate", "clauses": ["SELECT", "FROM", "WHERE"],
         "fmt": "SELECT {cols} FROM students WHERE city IN ('{city}', '{alt_city}');"},
        {"template_id": "V_OPR_02", "cat": "OPERATORS", "complexity": "Moderate", "clauses": ["SELECT", "FROM", "WHERE"],
         "fmt": "SELECT mark_id, marks_obtained FROM marks WHERE marks_obtained BETWEEN {low_mark} AND {high_mark};"},
        {"template_id": "V_OPR_03", "cat": "OPERATORS", "complexity": "Moderate", "clauses": ["SELECT", "FROM", "WHERE"],
         "fmt": "SELECT first_name, last_name FROM students WHERE first_name LIKE '{char_prefix}%';"},
        {"template_id": "V_OPR_04", "cat": "OPERATORS", "complexity": "Moderate", "clauses": ["SELECT", "FROM", "WHERE"],
         "fmt": "SELECT teacher_id, first_name FROM teachers WHERE subject_id IS NULL;"},
        {"template_id": "V_OPR_05", "cat": "OPERATORS", "complexity": "Moderate", "clauses": ["SELECT", "FROM", "WHERE"],
         "fmt": "SELECT teacher_id, first_name FROM teachers WHERE subject_id IS NOT NULL;"},

        # Cat 5: ORDER BY and LIMIT
        {"template_id": "V_ORD_01", "cat": "ORDER_LIMIT", "complexity": "Moderate", "clauses": ["SELECT", "FROM", "ORDER BY", "LIMIT"],
         "fmt": "SELECT first_name, last_name, date_of_birth FROM students ORDER BY last_name ASC LIMIT {limit};"},
        {"template_id": "V_ORD_02", "cat": "ORDER_LIMIT", "complexity": "Moderate", "clauses": ["SELECT", "FROM", "ORDER BY", "LIMIT"],
         "fmt": "SELECT student_id, marks_obtained FROM marks ORDER BY marks_obtained DESC LIMIT {limit};"},
        {"template_id": "V_ORD_03", "cat": "ORDER_LIMIT", "complexity": "Complex", "clauses": ["SELECT", "FROM", "WHERE", "ORDER BY"],
         "fmt": "SELECT first_name, last_name, admission_no FROM students WHERE state = '{state}' ORDER BY enrollment_date DESC;"},

        # Cat 6: Aggregations & GROUP BY / HAVING
        {"template_id": "V_AGG_01", "cat": "AGGREGATION", "complexity": "Simple", "clauses": ["SELECT", "FROM"],
         "fmt": "SELECT COUNT(*) AS total_students FROM students;"},
        {"template_id": "V_AGG_02", "cat": "AGGREGATION", "complexity": "Moderate", "clauses": ["SELECT", "FROM", "GROUP BY"],
         "fmt": "SELECT class_id, COUNT(*) AS student_count FROM students GROUP BY class_id;"},
        {"template_id": "V_AGG_03", "cat": "AGGREGATION", "complexity": "Moderate", "clauses": ["SELECT", "FROM", "GROUP BY"],
         "fmt": "SELECT state, COUNT(*) AS count_per_state FROM students GROUP BY state;"},
        {"template_id": "V_AGG_04", "cat": "AGGREGATION", "complexity": "Complex", "clauses": ["SELECT", "FROM", "GROUP BY", "HAVING"],
         "fmt": "SELECT subject_id, AVG(marks_obtained) AS avg_score FROM marks GROUP BY subject_id HAVING AVG(marks_obtained) >= {marks};"},
        {"template_id": "V_AGG_05", "cat": "AGGREGATION", "complexity": "Moderate", "clauses": ["SELECT", "FROM"],
         "fmt": "SELECT MIN(marks_obtained) AS min_m, MAX(marks_obtained) AS max_m FROM marks;"},

        # Cat 7: JOINs (INNER and LEFT JOIN)
        {"template_id": "V_JON_01", "cat": "JOINS", "complexity": "Complex", "clauses": ["SELECT", "FROM", "JOIN", "WHERE"],
         "fmt": "SELECT s.first_name, s.last_name, m.marks_obtained FROM students AS s INNER JOIN marks AS m ON s.student_id = m.student_id WHERE m.marks_obtained >= {marks};"},
        {"template_id": "V_JON_02", "cat": "JOINS", "complexity": "Complex", "clauses": ["SELECT", "FROM", "JOIN", "WHERE"],
         "fmt": "SELECT s.first_name, s.last_name, a.attendance_status FROM students AS s LEFT JOIN attendance AS a ON s.student_id = a.student_id WHERE a.attendance_status = 'Absent';"},
        {"template_id": "V_JON_03", "cat": "JOINS", "complexity": "Complex", "clauses": ["SELECT", "FROM", "JOIN"],
         "fmt": "SELECT s.admission_no, s.first_name, c.class_name FROM students AS s INNER JOIN classes AS c ON s.class_id = c.class_id;"},
        {"template_id": "V_JON_04", "cat": "JOINS", "complexity": "Complex", "clauses": ["SELECT", "FROM", "JOIN", "GROUP BY"],
         "fmt": "SELECT sub.subject_name, AVG(m.marks_obtained) AS avg_mark FROM subjects AS sub INNER JOIN marks AS m ON sub.subject_id = m.subject_id GROUP BY sub.subject_name;"},

        # Cat 8: Date-based queries
        {"template_id": "V_DTE_01", "cat": "DATE_FILTER", "complexity": "Moderate", "clauses": ["SELECT", "FROM", "WHERE"],
         "fmt": "SELECT first_name, last_name, enrollment_date FROM students WHERE enrollment_date >= '{date}';"},
        {"template_id": "V_DTE_02", "cat": "DATE_FILTER", "complexity": "Moderate", "clauses": ["SELECT", "FROM", "WHERE"],
         "fmt": "SELECT student_id, attendance_status, attendance_date FROM attendance WHERE attendance_date = '{att_date}';"},

        # Cat 9: INSERT statements
        {"template_id": "V_INS_01", "cat": "INSERT", "complexity": "Moderate", "clauses": ["INSERT", "VALUES"],
         "fmt": "INSERT INTO subjects (subject_id, subject_name) VALUES ({new_id}, '{new_subject}');"},
        {"template_id": "V_INS_02", "cat": "INSERT", "complexity": "Complex", "clauses": ["INSERT", "VALUES"],
         "fmt": "INSERT INTO classes (class_id, class_name, academic_year, class_teacher_id) VALUES ({new_cid}, '{cname}', '2025-2026', {tid});"},

        # Cat 10: UPDATE statements
        {"template_id": "V_UPD_01", "cat": "UPDATE", "complexity": "Moderate", "clauses": ["UPDATE", "SET", "WHERE"],
         "fmt": "UPDATE students SET status = 'Transferred' WHERE student_id = {sid};"},
        {"template_id": "V_UPD_02", "cat": "UPDATE", "complexity": "Moderate", "clauses": ["UPDATE", "SET", "WHERE"],
         "fmt": "UPDATE students SET section = '{section}' WHERE class_id = {class_id};"},

        # Cat 11: DELETE statements
        {"template_id": "V_DEL_01", "cat": "DELETE", "complexity": "Moderate", "clauses": ["DELETE", "FROM", "WHERE"],
         "fmt": "DELETE FROM attendance WHERE attendance_id = {aid};"},
        {"template_id": "V_DEL_02", "cat": "DELETE", "complexity": "Moderate", "clauses": ["DELETE", "FROM", "WHERE"],
         "fmt": "DELETE FROM marks WHERE marks_obtained < {marks};"},

        # Cat 12: Subqueries
        {"template_id": "V_SUB_01", "cat": "SUBQUERY", "complexity": "Complex", "clauses": ["SELECT", "FROM", "WHERE", "SUBQUERY"],
         "fmt": "SELECT first_name, last_name FROM students WHERE student_id IN (SELECT student_id FROM marks WHERE marks_obtained >= {marks});"},
        {"template_id": "V_SUB_02", "cat": "SUBQUERY", "complexity": "Complex", "clauses": ["SELECT", "FROM", "WHERE", "SUBQUERY"],
         "fmt": "SELECT student_id, marks_obtained FROM marks WHERE marks_obtained > (SELECT AVG(marks_obtained) FROM marks);"},

        # Cat 13: Attendance & Marks Multi-Condition
        {"template_id": "V_MUL_01", "cat": "MULTI_CONDITION", "complexity": "Complex", "clauses": ["SELECT", "FROM", "WHERE", "ORDER BY"],
         "fmt": "SELECT first_name, last_name, city, state FROM students WHERE (state = '{state}' AND status = 'Active') ORDER BY first_name ASC;"},
        {"template_id": "V_MUL_02", "cat": "MULTI_CONDITION", "complexity": "Complex", "clauses": ["SELECT", "FROM", "WHERE"],
         "fmt": "SELECT mark_id, exam_name, marks_obtained FROM marks WHERE subject_id = {subject_id} AND marks_obtained BETWEEN {low_mark} AND {high_mark};"}
    ]

    # 2. Invalid Query Templates (with explicit error categories)
    invalid_templates = [
        # Lexical Errors
        {"template_id": "I_LEX_01", "cat": "INVALID_LEXICAL", "error_type": "Lexical Error", "complexity": "Simple",
         "fmt": "SELECT first_name @#$ last_name FROM students;"},
        {"template_id": "I_LEX_02", "cat": "INVALID_LEXICAL", "error_type": "Lexical Error", "complexity": "Simple",
         "fmt": "SELECT * FROM students WHERE `city` = 'Hyderabad';"}, # backticks unsupported or illegal token
        {"template_id": "I_LEX_03", "cat": "INVALID_LEXICAL", "error_type": "Lexical Error", "complexity": "Simple",
         "fmt": "SELECT 123abc_var FROM students;"},

        # Syntax Errors - Missing Clauses
        {"template_id": "I_SYN_01", "cat": "INVALID_SYNTAX", "error_type": "Missing FROM Clause", "complexity": "Simple",
         "fmt": "SELECT first_name, last_name WHERE state = '{state}';"},
        {"template_id": "I_SYN_02", "cat": "INVALID_SYNTAX", "error_type": "Missing Table Name", "complexity": "Simple",
         "fmt": "SELECT first_name, last_name FROM;"},
        {"template_id": "I_SYN_03", "cat": "INVALID_SYNTAX", "error_type": "Missing WHERE Condition", "complexity": "Simple",
         "fmt": "SELECT first_name FROM students WHERE;"},
        {"template_id": "I_SYN_04", "cat": "INVALID_SYNTAX", "error_type": "Missing Target Table in INSERT", "complexity": "Simple",
         "fmt": "INSERT INTO VALUES (10, 'Art');"},
        {"template_id": "I_SYN_05", "cat": "INVALID_SYNTAX", "error_type": "Missing SET in UPDATE", "complexity": "Simple",
         "fmt": "UPDATE students status = 'Active' WHERE student_id = 1;"},
        {"template_id": "I_SYN_06", "cat": "INVALID_SYNTAX", "error_type": "Missing Columns in SELECT", "complexity": "Simple",
         "fmt": "SELECT FROM students;"},

        # Syntax Errors - Misplaced Keywords & Clause Order
        {"template_id": "I_SYN_07", "cat": "INVALID_SYNTAX", "error_type": "Misplaced WHERE Before FROM", "complexity": "Moderate",
         "fmt": "SELECT first_name WHERE state = '{state}' FROM students;"},
        {"template_id": "I_SYN_08", "cat": "INVALID_SYNTAX", "error_type": "ORDER BY Before WHERE", "complexity": "Moderate",
         "fmt": "SELECT first_name FROM students ORDER BY first_name WHERE state = '{state}';"},
        {"template_id": "I_SYN_09", "cat": "INVALID_SYNTAX", "error_type": "GROUP BY After ORDER BY", "complexity": "Moderate",
         "fmt": "SELECT class_id, COUNT(*) FROM students ORDER BY class_id GROUP BY class_id;"},

        # Syntax Errors - Unbalanced Parentheses
        {"template_id": "I_SYN_10", "cat": "INVALID_SYNTAX", "error_type": "Unclosed Parenthesis", "complexity": "Moderate",
         "fmt": "SELECT first_name FROM students WHERE (state = '{state}' AND gender = '{gender}';"},
        {"template_id": "I_SYN_11", "cat": "INVALID_SYNTAX", "error_type": "Extra Closing Parenthesis", "complexity": "Moderate",
         "fmt": "SELECT first_name FROM students WHERE (state = '{state}'));"},
        {"template_id": "I_SYN_12", "cat": "INVALID_SYNTAX", "error_type": "Unclosed IN List", "complexity": "Moderate",
         "fmt": "SELECT * FROM students WHERE city IN ('{city}', '{alt_city}';"},

        # Syntax Errors - Invalid Operators & Malformed Expressions
        {"template_id": "I_SYN_13", "cat": "INVALID_SYNTAX", "error_type": "Double Operator", "complexity": "Moderate",
         "fmt": "SELECT * FROM marks WHERE marks_obtained > = {marks};"},
        {"template_id": "I_SYN_14", "cat": "INVALID_SYNTAX", "error_type": "Malformed BETWEEN Expression", "complexity": "Moderate",
         "fmt": "SELECT * FROM marks WHERE marks_obtained BETWEEN {low_mark} OR {high_mark};"},
        {"template_id": "I_SYN_15", "cat": "INVALID_SYNTAX", "error_type": "Trailing Comma in SELECT", "complexity": "Simple",
         "fmt": "SELECT first_name, last_name, FROM students;"},
        {"template_id": "I_SYN_16", "cat": "INVALID_SYNTAX", "error_type": "Missing ON Clause in JOIN", "complexity": "Moderate",
         "fmt": "SELECT s.first_name, m.marks_obtained FROM students AS s JOIN marks AS m WHERE m.marks_obtained > 50;"},

        # Semantic & Schema Errors (Syntactically looks like SQL, but invalid schema/type)
        {"template_id": "I_SEM_01", "cat": "INVALID_SCHEMA", "error_type": "Nonexistent Table", "complexity": "Simple",
         "fmt": "SELECT student_id, fee_amount FROM student_fees WHERE fee_amount > 1000;"},
        {"template_id": "I_SEM_02", "cat": "INVALID_SCHEMA", "error_type": "Nonexistent Column", "complexity": "Simple",
         "fmt": "SELECT first_name, blood_group FROM students WHERE state = '{state}';"},
        {"template_id": "I_SEM_03", "cat": "INVALID_SCHEMA", "error_type": "Ambiguous or Wrong Table Column", "complexity": "Moderate",
         "fmt": "SELECT s.first_name, s.exam_name FROM students AS s;"},
        {"template_id": "I_SEM_04", "cat": "INVALID_SCHEMA", "error_type": "Invalid Column in GROUP BY", "complexity": "Moderate",
         "fmt": "SELECT non_existent_col, COUNT(*) FROM students GROUP BY non_existent_col;"},

        # Unsupported SQL Construct (Out of Domain DSL Scope)
        {"template_id": "I_USP_01", "cat": "UNSUPPORTED_SYNTAX", "error_type": "Unsupported Window Function", "complexity": "Complex",
         "fmt": "SELECT first_name, ROW_NUMBER() OVER (PARTITION BY class_id ORDER BY student_id) FROM students;"},
        {"template_id": "I_USP_02", "cat": "UNSUPPORTED_SYNTAX", "error_type": "Unsupported UNION ALL", "complexity": "Complex",
         "fmt": "SELECT first_name FROM students UNION ALL SELECT class_name FROM classes;"},
        {"template_id": "I_USP_03", "cat": "UNSUPPORTED_SYNTAX", "error_type": "Unsupported CTE", "complexity": "Complex",
         "fmt": "WITH ActiveStudents AS (SELECT * FROM students WHERE status = 'Active') SELECT * FROM ActiveStudents;"}
    ]

    return valid_templates, invalid_templates


def instantiate_template(template: Dict[str, Any], rng: random.Random) -> str:
    """Fills a query template format string with concrete randomized parameters."""
    state = rng.choice(list(STATES_AND_CITIES.keys()))
    alt_state = rng.choice([s for s in STATES_AND_CITIES.keys() if s != state])
    city = rng.choice(STATES_AND_CITIES[state])
    alt_city = rng.choice(STATES_AND_CITIES[alt_state])
    cols = rng.choice([
        "first_name, last_name",
        "student_id, first_name, last_name, city",
        "first_name, class_id, section, state",
        "admission_no, first_name, last_name",
        "first_name, gender, status"
    ])
    col = rng.choice(["state", "city", "gender", "status", "section"])
    table = rng.choice(["students", "classes", "teachers", "subjects", "marks", "attendance"])

    marks = rng.choice([50, 60, 70, 75, 80, 85, 90])
    low_mark = rng.choice([35, 40, 50])
    high_mark = rng.choice([70, 80, 95])
    limit = rng.choice([5, 10, 20, 50, 100])
    class_id = rng.randint(1, 7)
    tid = rng.randint(1, 40)
    sid = rng.randint(1, 1000)
    aid = rng.randint(1, 500)
    new_id = rng.randint(10, 99)
    new_cid = rng.randint(15, 50)
    new_subject = rng.choice(["Environmental Science", "Physical Education", "Art & Craft", "Sanskrit", "Economics"])
    cname = rng.choice(["Class 5", "Playgroup", "Kindergarten", "Class 11 Vocational"])
    section = rng.choice(SECTIONS)
    subject_id = rng.choice([1, 2, 3, 4, 5, 6])
    gender = rng.choice(GENDERS)
    date = rng.choice(["2023-01-01", "2024-06-01", "2025-01-01"])
    att_date = rng.choice(["2025-10-01", "2025-10-02", "2025-10-03"])
    char_prefix = rng.choice(["A", "S", "R", "K", "P", "M"])

    query = template["fmt"].format(
        cols=cols, col=col, table=table, state=state, alt_state=alt_state,
        city=city, alt_city=alt_city, marks=marks, low_mark=low_mark, high_mark=high_mark,
        limit=limit, class_id=class_id, tid=tid, sid=sid, aid=aid, new_id=new_id,
        new_cid=new_cid, new_subject=new_subject, cname=cname, section=section,
        subject_id=subject_id, gender=gender, date=date, att_date=att_date, char_prefix=char_prefix
    )
    return query


def generate_query_dataset(
    target_valid: int = 5000,
    target_invalid: int = 2000,
    seed: int = RANDOM_SEED
) -> pd.DataFrame:
    """
    Generates valid and invalid queries, tagged with template_id and attributes.
    """
    rng = random.Random(seed)
    valid_templates, invalid_templates = define_query_templates()

    queries = []
    qid = 1

    # Generate valid queries evenly distributed over templates
    per_valid_tpl = (target_valid // len(valid_templates)) + 1
    for tpl in valid_templates:
        for _ in range(per_valid_tpl):
            if len([q for q in queries if q["validity_label"] == 1]) >= target_valid:
                break
            q_text = instantiate_template(tpl, rng)
            queries.append({
                "query_id": f"QRY_{qid:06d}",
                "template_id": tpl["template_id"],
                "query_text": q_text,
                "query_type": tpl["cat"],
                "validity_label": 1,
                "error_category": "None",
                "clause_types": ";".join(tpl.get("clauses", ["SELECT"])),
                "complexity_level": tpl["complexity"],
                "grammar_source": "GroundTruthTemplate",
                "expected_parse_status": "SUCCESS"
            })
            qid += 1

    # Generate invalid queries evenly distributed over templates
    per_invalid_tpl = (target_invalid // len(invalid_templates)) + 1
    for tpl in invalid_templates:
        for _ in range(per_invalid_tpl):
            if len([q for q in queries if q["validity_label"] == 0]) >= target_invalid:
                break
            q_text = instantiate_template(tpl, rng)
            queries.append({
                "query_id": f"QRY_{qid:06d}",
                "template_id": tpl["template_id"],
                "query_text": q_text,
                "query_type": tpl["cat"],
                "validity_label": 0,
                "error_category": tpl.get("error_type", "Syntax Error"),
                "clause_types": "MALFORMED",
                "complexity_level": tpl["complexity"],
                "grammar_source": "PerturbationTemplate",
                "expected_parse_status": "PARSE_ERROR"
            })
            qid += 1

    df = pd.DataFrame(queries)
    return df


def split_dataset_by_template(
    df: pd.DataFrame,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = RANDOM_SEED
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Mandatory Data Leakage Prevention:
    Splits the dataset by `template_id` so that structural templates present in train
    do NOT leak into validation or test sets. Both valid and invalid templates are partitioned.
    """
    rng = random.Random(seed)

    valid_tpls = sorted(df[df["validity_label"] == 1]["template_id"].unique())
    invalid_tpls = sorted(df[df["validity_label"] == 0]["template_id"].unique())

    rng.shuffle(valid_tpls)
    rng.shuffle(invalid_tpls)

    def partition_list(items):
        n = len(items)
        n_train = max(1, int(round(n * train_ratio)))
        n_val = max(1, int(round(n * val_ratio)))
        train_items = items[:n_train]
        val_items = items[n_train:n_train + n_val]
        test_items = items[n_train + n_val:]
        if not test_items:  # guarantee test set has at least 1 template
            test_items = val_items[-1:]
            val_items = val_items[:-1]
        return train_items, val_items, test_items

    v_tr, v_va, v_te = partition_list(valid_tpls)
    i_tr, i_va, i_te = partition_list(invalid_tpls)

    train_tpls = set(v_tr + i_tr)
    val_tpls = set(v_va + i_va)
    test_tpls = set(v_te + i_te)

    # Disjoint check
    assert len(train_tpls.intersection(val_tpls)) == 0, "Train and Val template overlap!"
    assert len(train_tpls.intersection(test_tpls)) == 0, "Train and Test template overlap!"
    assert len(val_tpls.intersection(test_tpls)) == 0, "Val and Test template overlap!"

    train_df = df[df["template_id"].isin(train_tpls)].sample(frac=1.0, random_state=seed).reset_index(drop=True)
    val_df = df[df["template_id"].isin(val_tpls)].sample(frac=1.0, random_state=seed).reset_index(drop=True)
    test_df = df[df["template_id"].isin(test_tpls)].sample(frac=1.0, random_state=seed).reset_index(drop=True)

    return train_df, val_df, test_df


def run_full_generation(output_dir: str = "data", num_students: int = 10000,
                        target_valid: int = 5000, target_invalid: int = 2000):
    """Executes end-to-end dataset generation and saves all required CSV and JSON files."""
    os.makedirs(output_dir, exist_ok=True)
    print(f"[*] Generating {num_students} synthetic student records and relational tables...")
    tables = generate_database_records(num_students=num_students, seed=RANDOM_SEED)

    for name, df in tables.items():
        filepath = os.path.join(output_dir, f"{name}.csv")
        df.to_csv(filepath, index=False)
        print(f"    Saved {filepath} ({len(df)} rows)")

    print(f"[*] Generating SQL query dataset (target: {target_valid} valid, {target_invalid} invalid)...")
    query_df = generate_query_dataset(target_valid=target_valid, target_invalid=target_invalid, seed=RANDOM_SEED)

    valid_queries_df = query_df[query_df["validity_label"] == 1]
    invalid_queries_df = query_df[query_df["validity_label"] == 0]

    valid_queries_df.to_csv(os.path.join(output_dir, "valid_queries.csv"), index=False)
    invalid_queries_df.to_csv(os.path.join(output_dir, "invalid_queries.csv"), index=False)
    query_df.to_csv(os.path.join(output_dir, "query_dataset.csv"), index=False)

    print(f"[*] Performing template-based disjoint split (leakage prevention)...")
    train_df, val_df, test_df = split_dataset_by_template(query_df, seed=RANDOM_SEED)

    train_df.to_csv(os.path.join(output_dir, "train.csv"), index=False)
    val_df.to_csv(os.path.join(output_dir, "validation.csv"), index=False)
    test_df.to_csv(os.path.join(output_dir, "test.csv"), index=False)

    stats = {
        "generated_timestamp": datetime.datetime.now().isoformat(),
        "random_seed": RANDOM_SEED,
        "database_records": {name: len(df) for name, df in tables.items()},
        "query_dataset": {
            "total_queries": len(query_df),
            "valid_queries": len(valid_queries_df),
            "invalid_queries": len(invalid_queries_df),
            "unique_templates": int(query_df["template_id"].nunique()),
            "valid_templates": int(valid_queries_df["template_id"].nunique()),
            "invalid_templates": int(invalid_queries_df["template_id"].nunique())
        },
        "splits": {
            "train": {
                "count": len(train_df),
                "valid": int((train_df["validity_label"] == 1).sum()),
                "invalid": int((train_df["validity_label"] == 0).sum()),
                "templates": sorted(train_df["template_id"].unique().tolist())
            },
            "validation": {
                "count": len(val_df),
                "valid": int((val_df["validity_label"] == 1).sum()),
                "invalid": int((val_df["validity_label"] == 0).sum()),
                "templates": sorted(val_df["template_id"].unique().tolist())
            },
            "test": {
                "count": len(test_df),
                "valid": int((test_df["validity_label"] == 1).sum()),
                "invalid": int((test_df["validity_label"] == 0).sum()),
                "templates": sorted(test_df["template_id"].unique().tolist())
            }
        }
    }

    stats_path = os.path.join(output_dir, "dataset_statistics.json")
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    # Write data/README.md
    readme_content = f"""# AutoGrammar School Student Dataset

## Overview
This dataset contains synthetic, culturally authentic Indian school management records and an extensive corpus of domain-specific SQL queries.

## Entities & Tables
- **synthetic_students.csv**: {len(tables['synthetic_students'])} records (First/Last name, Class, Section, DOB, Gender, City, State, Enrollment Date, Status).
- **synthetic_teachers.csv**: {len(tables['synthetic_teachers'])} records (First/Last name, Subject specialty).
- **synthetic_classes.csv**: {len(tables['synthetic_classes'])} records (Class name, Academic Year, Class Teacher ID).
- **synthetic_subjects.csv**: {len(tables['synthetic_subjects'])} records (Core curriculum subjects).
- **synthetic_marks.csv**: {len(tables['synthetic_marks'])} records (Exam evaluations).
- **synthetic_attendance.csv**: {len(tables['synthetic_attendance'])} records (Daily student attendance).

## Query Dataset
- Total queries: {len(query_df)}
- Valid queries: {len(valid_queries_df)} across 16 SQL DSL categories.
- Invalid queries: {len(invalid_queries_df)} with documented error taxonomy (Lexical, Missing Clauses, Misplaced Keywords, Unbalanced Parentheses, Malformed Operators, Schema Mismatches, Unsupported Syntax).

## Data Leakage Prevention
Splits are grouped strictly by `template_id`:
- **Train**: {len(train_df)} queries ({len(stats['splits']['train']['templates'])} distinct templates)
- **Validation**: {len(val_df)} queries ({len(stats['splits']['validation']['templates'])} distinct templates)
- **Test**: {len(test_df)} queries ({len(stats['splits']['test']['templates'])} distinct templates)

No template in the training set appears in validation or test splits.
"""
    with open(os.path.join(output_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)

    print(f"[*] Dataset generation complete. Statistics written to {stats_path}.")


if __name__ == "__main__":
    run_full_generation()
