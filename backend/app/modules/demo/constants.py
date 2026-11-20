"""Stable identifiers for the showcase demo college."""

DEMO_TENANT_CODE = "sviet-demo"
DEMO_TENANT_NAME = "SVIET — Demo College of Engineering"
DEMO_SHORT_NAME = "SVIET Demo"
DEMO_INSTITUTION_EMAIL = "info@sviet-demo.edu"
DEMO_PASSWORD = "DemoCollege123!"

DEMO_ACADEMIC_YEAR = "2025-26"
DEMO_SEMESTER = "Odd"

DEPARTMENTS = (
    ("CSE", "Computer Science & Engineering", "BTECH-CSE", "B.Tech Computer Science"),
    ("ECE", "Electronics & Communication", "BTECH-ECE", "B.Tech ECE"),
    ("MECH", "Mechanical Engineering", "BTECH-MECH", "B.Tech Mechanical"),
    ("CIVIL", "Civil Engineering", "BTECH-CIVIL", "B.Tech Civil"),
    ("IT", "Information Technology", "BTECH-IT", "B.Tech IT"),
    ("MBA", "Master of Business Administration", "MBA-GEN", "MBA General"),
)

DEFAULT_STUDENT_COUNT = 180
DEFAULT_FACULTY_COUNT = 36

ROLE_ACCOUNTS = (
    ("college_admin", "admin@sviet-demo.edu", "Dr. Meena Rajagopal", "college_admin"),
    ("dept_admin", "deptadmin@sviet-demo.edu", "Prof. Karthik Srinivasan", "department_admin"),
    ("finance", "finance@sviet-demo.edu", "Ramesh Iyer", "finance_staff"),
    ("accounts", "accounts@sviet-demo.edu", "Lakshmi Venkat", "accounts_staff"),
    ("hr", "hr@sviet-demo.edu", "Anitha Mohan", "hr_staff"),
    ("exam", "examcell@sviet-demo.edu", "Suresh Kumar", "examination_cell"),
    ("hostel", "hostel@sviet-demo.edu", "Vijay Anand", "hostel_admin"),
    ("library", "library@sviet-demo.edu", "Priya Natarajan", "librarian"),
    ("parent", "parent@sviet-demo.edu", "Ravi Kumar (Parent)", "parent"),
)

LIBRARY_BOOKS = (
    ("ENG-PHY-001", "Engineering Physics", ["Halliday", "Resnick"]),
    ("ENG-MATH-002", "Higher Engineering Mathematics", ["B.S. Grewal"]),
    ("CSE-DS-003", "Data Structures in Python", ["Goodrich"]),
    ("CSE-DBMS-004", "Database System Concepts", ["Silberschatz"]),
    ("CSE-OS-005", "Operating System Concepts", ["Galvin"]),
    ("ECE-DIG-006", "Digital Design", ["Morris Mano"]),
    ("MECH-TOM-007", "Theory of Machines", ["R.S. Khurmi"]),
    ("CIVIL-SOM-008", "Strength of Materials", ["Timoshenko"]),
    ("MBA-HRM-009", "Human Resource Management", ["Dessler"]),
    ("CSE-AI-010", "Artificial Intelligence: A Modern Approach", ["Russell", "Norvig"]),
)