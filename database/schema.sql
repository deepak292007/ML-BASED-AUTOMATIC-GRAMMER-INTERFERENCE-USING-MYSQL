-- AutoGrammar: School Management Database Schema (MySQL 8.0+)
-- Database: school_db

CREATE DATABASE IF NOT EXISTS school_db;
USE school_db;

-- 1. Subjects Table
DROP TABLE IF EXISTS attendance;
DROP TABLE IF EXISTS marks;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS classes;
DROP TABLE IF EXISTS teachers;
DROP TABLE IF EXISTS subjects;

CREATE TABLE subjects (
    subject_id INT PRIMARY KEY,
    subject_name VARCHAR(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Teachers Table
CREATE TABLE teachers (
    teacher_id INT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    subject_id INT NULL,
    CONSTRAINT fk_teachers_subject FOREIGN KEY (subject_id) REFERENCES subjects (subject_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Classes Table
CREATE TABLE classes (
    class_id INT PRIMARY KEY,
    class_name VARCHAR(50) NOT NULL,
    academic_year VARCHAR(20) NOT NULL,
    class_teacher_id INT NULL,
    CONSTRAINT fk_classes_teacher FOREIGN KEY (class_teacher_id) REFERENCES teachers (teacher_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Students Table
CREATE TABLE students (
    student_id INT PRIMARY KEY,
    admission_no VARCHAR(30) UNIQUE NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    class_id INT NOT NULL,
    section VARCHAR(5) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(10) NOT NULL,
    city VARCHAR(50) NOT NULL,
    state VARCHAR(50) NOT NULL,
    enrollment_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL,
    INDEX idx_student_state (state),
    INDEX idx_student_city (city),
    INDEX idx_student_class (class_id),
    CONSTRAINT fk_students_class FOREIGN KEY (class_id) REFERENCES classes (class_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Marks Table
CREATE TABLE marks (
    mark_id INT PRIMARY KEY,
    student_id INT NOT NULL,
    subject_id INT NOT NULL,
    exam_name VARCHAR(100) NOT NULL,
    marks_obtained INT NOT NULL,
    maximum_marks INT NOT NULL DEFAULT 100,
    exam_date DATE NOT NULL,
    INDEX idx_marks_student (student_id),
    INDEX idx_marks_subject (subject_id),
    CONSTRAINT fk_marks_student FOREIGN KEY (student_id) REFERENCES students (student_id) ON DELETE CASCADE,
    CONSTRAINT fk_marks_subject FOREIGN KEY (subject_id) REFERENCES subjects (subject_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Attendance Table
CREATE TABLE attendance (
    attendance_id INT PRIMARY KEY,
    student_id INT NOT NULL,
    attendance_date DATE NOT NULL,
    attendance_status VARCHAR(20) NOT NULL,
    INDEX idx_attendance_student_date (student_id, attendance_date),
    CONSTRAINT fk_attendance_student FOREIGN KEY (student_id) REFERENCES students (student_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
