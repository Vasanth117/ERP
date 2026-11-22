"""Stable identifiers for the Grand Horizon Institute of Technology (GHIT) showcase tenant."""

# Tenant identity (maps to GHIT-DEMO in product docs; stored normalized as ghit-demo)
DEMO_TENANT_CODE = "ghit-demo"
DEMO_INSTITUTION_CODE = "GHIT"
DEMO_TENANT_NAME = "Grand Horizon Institute of Technology"
DEMO_SHORT_NAME = "GHIT"
DEMO_INSTITUTION_EMAIL = "info@ghit-demo.edu"
DEMO_EMAIL_DOMAIN = "ghit-demo.edu"
DEMO_PASSWORD = "DemoCollege123!"

DEMO_ACADEMIC_YEAR = "2025-26"
DEMO_SEMESTER = "Odd"

# department tuple: (code, name, programme_code, programme_label)
DEPARTMENTS = (
    ("CSE", "Computer Science and Engineering", "BTECH-CSE", "B.Tech Computer Science"),
    ("AIDS", "Artificial Intelligence and Data Science", "BTECH-AIDS", "B.Tech AI & DS"),
    ("IT", "Information Technology", "BTECH-IT", "B.Tech Information Technology"),
    ("ECE", "Electronics and Communication Engineering", "BTECH-ECE", "B.Tech ECE"),
    ("EEE", "Electrical and Electronics Engineering", "BTECH-EEE", "B.Tech EEE"),
    ("MECH", "Mechanical Engineering", "BTECH-MECH", "B.Tech Mechanical"),
    ("CIVIL", "Civil Engineering", "BTECH-CIVIL", "B.Tech Civil"),
    ("BMED", "Biomedical Engineering", "BTECH-BMED", "B.Tech Biomedical"),
    ("ROBO", "Robotics and Automation", "BTECH-ROBO", "B.Tech Robotics"),
    ("CYBR", "Cyber Security", "BTECH-CYBR", "B.Tech Cyber Security"),
    ("CSBS", "Computer Science and Business Systems", "BTECH-CSBS", "B.Tech CSBS"),
    ("MATH", "Mathematics", "BSC-MATH", "B.Sc Mathematics"),
    ("PHYS", "Physics", "BSC-PHYS", "B.Sc Physics"),
    ("CHEM", "Chemistry", "BSC-CHEM", "B.Sc Chemistry"),
    ("ENGL", "English", "BA-ENGL", "B.A English"),
    ("MBA", "Management Studies", "MBA-GEN", "MBA General Management"),
    ("MCA", "Master of Computer Applications", "MCA-GEN", "MCA"),
    ("RND", "Research and Development", "PHD-RND", "Ph.D Interdisciplinary"),
)

# (code, name, is_main, city)
CAMPUSES = (
    ("MAIN", "Main Campus — Coimbatore", True, "Coimbatore"),
    ("ENG", "Engineering Campus", False, "Coimbatore"),
    ("RNDC", "Research and Innovation Campus", False, "Coimbatore"),
)

# Legacy defaults kept for API query defaults (superseded by scale profiles)
DEFAULT_STUDENT_COUNT = 12_000
DEFAULT_FACULTY_COUNT = 650
DEFAULT_NON_FACULTY_EMPLOYEE_COUNT = 400

ROLE_ACCOUNTS = (
    ("college_admin", f"admin@{DEMO_EMAIL_DOMAIN}", "Dr. Anitha Menon", "college_admin"),
    ("dept_admin", f"deptadmin@{DEMO_EMAIL_DOMAIN}", "Prof. Karthik Iyer", "department_admin"),
    ("finance", f"finance@{DEMO_EMAIL_DOMAIN}", "Ramesh Subramanian", "finance_staff"),
    ("accounts", f"accounts@{DEMO_EMAIL_DOMAIN}", "Lakshmi Venkat", "accounts_staff"),
    ("hr", f"hr@{DEMO_EMAIL_DOMAIN}", "Priya Natarajan", "hr_staff"),
    ("exam", f"examcell@{DEMO_EMAIL_DOMAIN}", "Suresh Kumar", "examination_cell"),
    ("hostel", f"hostel@{DEMO_EMAIL_DOMAIN}", "Vijay Anand", "hostel_admin"),
    ("library", f"library@{DEMO_EMAIL_DOMAIN}", "Meena Rajesh", "librarian"),
    ("parent", f"parent@{DEMO_EMAIL_DOMAIN}", "Ravi Kumar (Parent)", "parent"),
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