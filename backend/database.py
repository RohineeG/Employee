"""
SQLite Database schema, connection and seed data for the Employee Management System (EMS).
"""
import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ems_support.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users / Employees table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        role TEXT NOT NULL,  -- Employee, Team Lead, HR Manager, System Admin, Support Specialist
        department TEXT NOT NULL,
        job_title TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Active', -- Active, Locked, Suspended, On Leave
        leave_balance INTEGER NOT NULL DEFAULT 20,
        sick_leave_balance INTEGER NOT NULL DEFAULT 10,
        manager_id INTEGER,
        benefits_enrolled INTEGER NOT NULL DEFAULT 1, -- 1 = Yes, 0 = Pending/Error
        equipment_status TEXT NOT NULL DEFAULT 'Delivered', -- Delivered, Requisition Pending, In Repair
        salary_band TEXT NOT NULL DEFAULT 'L4',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Knowledge Base for L1 RAG
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS knowledge_base (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        keywords TEXT NOT NULL,
        source_doc TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3. Support Tickets (L1 -> L2 -> L3 Lifecycle)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_code TEXT UNIQUE NOT NULL,
        user_id INTEGER NOT NULL,
        user_email TEXT NOT NULL,
        user_role TEXT NOT NULL,
        query TEXT NOT NULL,
        current_tier TEXT NOT NULL DEFAULT 'L1', -- L1, L2, L3
        status TEXT NOT NULL DEFAULT 'Open', -- Resolved_L1, Resolved_L2, Escalated_L3, In_Review, Closed
        resolution_summary TEXT,
        l1_rag_result TEXT,
        l2_agents_result TEXT,
        l3_human_notes TEXT,
        assigned_human TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES employees (id)
    );
    """)

    # 4. Detailed Audit Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        user_email TEXT NOT NULL,
        user_role TEXT NOT NULL,
        action TEXT NOT NULL,
        resource_type TEXT NOT NULL,
        resource_id TEXT,
        tier TEXT NOT NULL, -- L1, L2, L3, System, Auth
        status TEXT NOT NULL DEFAULT 'SUCCESS', -- SUCCESS, FAILED, ESCALATED, WARNING
        details TEXT,
        ip_address TEXT DEFAULT '127.0.0.1'
    );
    """)

    # 5. L2 Agent Operations Log
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agent_actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id INTEGER,
        agent_name TEXT NOT NULL, -- DatabaseAgent, DiagnosticsAgent, RemediationAgent, PolicyAgent, LeaveAgent, AttendanceAgent, PayrollAgent, NetworkAgent, SoftwareAgent
        action_taken TEXT NOT NULL,
        input_params TEXT,
        output_result TEXT,
        status TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (ticket_id) REFERENCES tickets (id)
    );
    """)

    # 6. Leaves Management Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leaves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        employee_email TEXT NOT NULL,
        leave_type TEXT NOT NULL, -- PTO, Sick, Casual, Parental, Unpaid
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        days_requested INTEGER NOT NULL,
        reason TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Approved', -- Approved, Pending, Rejected, Cancelled
        approved_by TEXT DEFAULT 'LeaveAgent (Automated)',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES employees (id)
    );
    """)

    # 7. Attendance Logs & Regularization Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        employee_email TEXT NOT NULL,
        date TEXT NOT NULL,
        clock_in TEXT,
        clock_out TEXT,
        total_hours REAL,
        status TEXT NOT NULL DEFAULT 'Present', -- Present, Late, Half-Day, Absent, Remote, Regularized
        regularized INTEGER DEFAULT 0,
        regularization_reason TEXT,
        notes TEXT,
        FOREIGN KEY (employee_id) REFERENCES employees (id)
    );
    """)

    # 8. Payroll & Payslips Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payroll (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        employee_email TEXT NOT NULL,
        month TEXT NOT NULL,
        year INTEGER NOT NULL,
        salary_band TEXT NOT NULL,
        base_salary REAL NOT NULL,
        hra_allowance REAL NOT NULL,
        special_allowance REAL NOT NULL,
        bonus REAL DEFAULT 0,
        tax_deductions REAL NOT NULL,
        pf_401k_deductions REAL NOT NULL,
        insurance_deduction REAL NOT NULL,
        net_salary REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'Paid', -- Paid, Processed, Pending
        payout_date TEXT NOT NULL,
        bank_account_last4 TEXT NOT NULL DEFAULT '4821',
        FOREIGN KEY (employee_id) REFERENCES employees (id)
    );
    """)

    # 9. Network Diagnostics & IT Connectivity Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS network_diagnostics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        employee_email TEXT NOT NULL,
        vpn_status TEXT NOT NULL DEFAULT 'Connected', -- Connected, Disconnected, Session Expired, Tunnel Error
        assigned_ip TEXT NOT NULL DEFAULT '10.240.12.84',
        gateway_ip TEXT NOT NULL DEFAULT '10.240.0.1',
        dns_server TEXT NOT NULL DEFAULT '1.1.1.1 (Cloudflare Enterprise)',
        wifi_ssid TEXT NOT NULL DEFAULT 'CorpNet-Secure-5G',
        latency_ms INTEGER NOT NULL DEFAULT 14,
        packet_loss_pct REAL NOT NULL DEFAULT 0.0,
        bandwidth_mbps INTEGER NOT NULL DEFAULT 350,
        subnet_access TEXT NOT NULL DEFAULT 'Engineering-VLAN-102',
        last_tested TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES employees (id)
    );
    """)

    # 10. Software Catalog Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS software_catalog (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        version TEXT NOT NULL,
        category TEXT NOT NULL, -- Developer Tools, Productivity, Security, Design
        license_type TEXT NOT NULL, -- Free, Enterprise, Commercial
        description TEXT NOT NULL,
        min_role TEXT NOT NULL DEFAULT 'Employee',
        security_risk TEXT NOT NULL DEFAULT 'Low' -- Low, Medium, High
    );
    """)

    # 11. Software Requests & Installation Workflows Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS software_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id INTEGER,
        ticket_code TEXT,
        employee_id INTEGER NOT NULL,
        employee_name TEXT NOT NULL,
        employee_email TEXT NOT NULL,
        software_name TEXT NOT NULL,
        version TEXT NOT NULL,
        justification TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'PENDING_APPROVAL', -- PENDING_APPROVAL, APPROVED, REJECTED, INSTALLED
        requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        reviewed_by_human TEXT,
        reviewed_at TIMESTAMP,
        human_notes TEXT,
        installed_at TIMESTAMP,
        install_logs TEXT,
        FOREIGN KEY (employee_id) REFERENCES employees (id)
    );
    """)

    conn.commit()

    # Seed tables if empty
    seed_data(conn)

    conn.close()

def seed_data(conn):
    cursor = conn.cursor()

    # Seed Employees if empty
    cursor.execute("SELECT COUNT(*) FROM employees;")
    if cursor.fetchone()[0] == 0:
        employees = [
            ("EMP001", "Alex Morgan", "alex.morgan@company.com", "Employee", "Engineering", "Software Engineer", "Active", 18, 10, None, 1, "Delivered", "L4"),
            ("EMP002", "Sarah Connor", "sarah.connor@company.com", "Employee", "DevOps", "Infrastructure Engineer", "Locked", 15, 8, 1, 1, "Delivered", "L5"),
            ("EMP003", "Michael Scott", "michael.scott@company.com", "Team Lead", "Sales", "Regional Sales Manager", "Active", 5, 4, None, 1, "Delivered", "L6"),
            ("EMP004", "David Miller", "david.miller@company.com", "Employee", "Marketing", "Growth Analyst", "Active", 22, 10, 3, 0, "Requisition Pending", "L3"),
            ("EMP005", "Priya Sharma", "priya.sharma@company.com", "Employee", "Product", "UI/UX Designer", "Active", 12, 9, 1, 1, "In Repair", "L4"),
            ("EMP006", "Rachel Green", "rachel.green@company.com", "HR Manager", "Human Resources", "People Operations Director", "Active", 25, 12, None, 1, "Delivered", "L7"),
            ("EMP007", "Alice Vance", "alice.vance@company.com", "System Admin", "IT Security", "Principal Security Admin", "Active", 20, 10, None, 1, "Delivered", "L6"),
            ("EMP008", "Sam Carter", "sam.carter@company.com", "Support Specialist", "Technical Support", "L3 Operations Lead", "Active", 20, 10, None, 1, "Delivered", "L5")
        ]
        cursor.executemany("""
        INSERT INTO employees (employee_code, name, email, role, department, job_title, status, leave_balance, sick_leave_balance, manager_id, benefits_enrolled, equipment_status, salary_band)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, employees)

    # Seed Knowledge Base for L1 RAG if empty
    cursor.execute("SELECT COUNT(*) FROM knowledge_base;")
    if cursor.fetchone()[0] == 0:
        kb_articles = [
        (
            "Leave & Time Off",
            "Annual Paid Time Off (PTO) Policy & Carryover Rules",
            "Full-time employees receive 20 days of paid time off per calendar year accrued monthly. Up to 5 unused PTO days can be carried forward into the first quarter of the following year. Leave requests exceeding 3 consecutive business days require advance manager approval via the EMS portal. Sick leave is tracked separately (10 days/year) and does not require advance notice but must be logged within 48 hours.",
            "pto, annual leave, carryover, sick days, vacation, time off, holiday",
            "HR-POL-2024-01"
        ),
        (
            "IT Access & Credentials",
            "Account Lockout & Multi-Factor Authentication (MFA) Reset Policy",
            "Corporate domain and VPN accounts automatically lock after 5 consecutive failed login attempts to prevent brute-force intrusion. Locked accounts can be diagnosed and programmatically unlocked by the L2 IT Database Agent if no security incident is flagged, or through IT Helpdesk verification. MFA token resets require authorization from System Administration or Identity Management.",
            "locked account, unlock, password, mfa, vpn, credentials, login failed, access denied",
            "SEC-SOP-04"
        ),
        (
            "Healthcare & Benefits",
            "Health, Dental, and Life Insurance Enrollment Guidelines",
            "New hires have 30 days from their start date to complete benefits enrollment in the EMS portal. Existing employees may alter their plan during the annual Open Enrollment period in November or following a Qualifying Life Event (marriage, child birth, relocation). If your benefits status displays as 'Pending' or 'Error' despite enrollment, the L2 Database Agent can synchronize records with the benefits carrier.",
            "benefits, health insurance, medical, dental, enrollment, open enrollment, coverage, dependent",
            "HR-BEN-2024-03"
        ),
        (
            "Equipment & Workplace",
            "Standard Equipment Requisition & Hardware Refresh",
            "All engineering and design personnel are eligible for standard workstation hardware (MacBook Pro 16\" or Dell XPS 15, plus dual 27\" 4K monitors and noise-cancelling headset). Hardware refresh cycles occur every 36 months. If equipment status is 'Requisition Pending' or 'In Repair', loaner equipment can be requested through the IT hardware depot.",
            "laptop, equipment, hardware, monitor, macbook, dell, requisition, repair, loaner",
            "IT-HW-08"
        ),
        (
            "Payroll & Compensation",
            "Expense Reimbursement and Travel Expense Reporting",
            "Business-related expenses incurred on behalf of the company must be submitted via the expense portal within 30 days accompanied by itemized receipts. Mileage reimbursement is calculated at standard IRS rates ($0.67/mile). Expenses under $500 require Team Lead signoff; expenses above $500 require HR/Finance Director approval.",
            "reimbursement, expenses, travel, per diem, receipts, mileage, finance, refund",
            "FIN-EXP-2024-02"
        ),
        (
            "Onboarding & Performance",
            "Employee Performance Review & Promotion Cycle",
            "Performance evaluations take place semi-annually in June and December. Key performance indicators (KPIs) and OKRs are assessed collaboratively between employee and reporting manager. Formal salary band revisions (L3 to L8) follow the Q4 compensation calibration committee review.",
            "performance review, promotion, kpi, okr, compensation calibration, salary band",
            "HR-PERF-2024-05"
        ),
        (
            "Leave & Time Off",
            "Leave Application and Balance Recalculation Rules",
            "Employees can apply for Paid Time Off (PTO), Sick Leave, Casual Leave, and Parental Leave via the AI Support portal or LeaveAgent. Standard PTO balance is 20 days annually. If an employee discovers a disparity in their leave balance, the LeaveAgent can run an automated recalculation against approved records. Unplanned sick leaves must be regularized within 48 hours.",
            "leave, apply leave, pto balance, sick leave, casual leave, vacation request, leave disparity, leave recalculation",
            "HR-LEAVE-2026-01"
        ),
        (
            "Attendance & Time Tracking",
            "Daily Clock-In, Attendance Regularization, and Remote Punch Rules",
            "Standard core work hours are 9:00 AM to 5:00 PM (minimum 8 hours/day). In the event of missed punches or network disconnection during clock-in, employees may submit an Attendance Regularization request directly via the AttendanceAgent. The agent will inspect session logs and adjust the daily record from 'Late' or 'Missed' to 'Present (Regularized)'.",
            "attendance, clock in, clock out, missed punch, regularize, late punch, working hours, remote punch, wfh log",
            "OPS-ATT-2026-02"
        ),
        (
            "Payroll & Compensation",
            "Monthly Pay Slip Breakdown, Tax Deductions, and Payout Schedule",
            "Salaries are disbursed on the 28th of every month. The monthly payslip includes Base Salary, House Rent Allowance (HRA), Special Allowances, Performance Bonuses, minus Statutory Taxes, PF/401(k), and Health Insurance Deductions. The PayrollAgent provides real-time explanations of deduction formulas, year-to-date tax withholdings, and salary band progression (L3 through L8).",
            "payroll, payslip, net pay, gross salary, tax deductions, 401k, provident fund, payday, direct deposit, compensation",
            "FIN-PAY-2026-03"
        ),
        (
            "Network & Infrastructure",
            "Corporate VPN, Wi-Fi 802.1X, and Tunnel Diagnostic Procedures",
            "Remote employees must connect to the GlobalProtect / WireGuard corporate VPN for internal repository and staging server access. In case of tunnel dropouts, IP routing collisions, or DNS resolution latency (>50ms), the NetworkAgent can execute automated DNS flushing, DHCP lease renewal, and VPN session reset.",
            "network, vpn, wifi, connection dropped, dns, ip address, latency, ping, gateway, tunnel error",
            "IT-NET-2026-04"
        ),
        (
            "Software & Applications",
            "Enterprise Software Requisitions and Support Specialist Approval Policy",
            "All software installations (including developer tools like Docker Desktop, VS Code, Postman, PyCharm, and collaboration software like Slack) require explicit administrative approval from a Human Support Specialist or System Admin to ensure compliance with enterprise security and licensing policies. Once the Support Specialist grants human approval, the SoftwareAgent automatically executes the installation and configures the environment.",
            "software, install software, docker, vscode, postman, pycharm, slack, install request, approval, support agent approval, package manager",
            "IT-SEC-SOFT-2026-05"
        )
    ]
        cursor.executemany("""
        INSERT INTO knowledge_base (category, title, content, keywords, source_doc)
        VALUES (?, ?, ?, ?, ?);
        """, kb_articles)

    # Seed Leaves
    cursor.execute("SELECT COUNT(*) FROM leaves;")
    if cursor.fetchone()[0] == 0:
        leaves = [
            (1, "alex.morgan@company.com", "PTO", "2026-08-10", "2026-08-12", 2, "Family vacation", "Approved", "LeaveAgent (Automated)"),
            (2, "sarah.connor@company.com", "Sick", "2026-09-02", "2026-09-03", 2, "Flu recovery", "Approved", "Rachel Green (HR Director)"),
            (3, "michael.scott@company.com", "PTO", "2026-07-15", "2026-07-20", 5, "Summer holiday", "Approved", "Rachel Green (HR Director)"),
            (4, "david.miller@company.com", "Casual", "2026-09-18", "2026-09-18", 1, "Personal errand", "Approved", "LeaveAgent (Automated)"),
            (5, "priya.sharma@company.com", "PTO", "2026-09-25", "2026-09-27", 3, "Design conference", "Approved", "LeaveAgent (Automated)")
        ]
        cursor.executemany("""
        INSERT INTO leaves (employee_id, employee_email, leave_type, start_date, end_date, days_requested, reason, status, approved_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, leaves)

    # Seed Attendance (Recent week logs)
    cursor.execute("SELECT COUNT(*) FROM attendance;")
    if cursor.fetchone()[0] == 0:
        attendance_records = [
            (1, "alex.morgan@company.com", "2026-09-21", "08:58", "17:15", 8.28, "Present", 0, None, "On-time arrival"),
            (1, "alex.morgan@company.com", "2026-09-20", "09:05", "17:30", 8.42, "Present", 0, None, "Standard workday"),
            (1, "alex.morgan@company.com", "2026-09-19", "09:45", "18:00", 8.25, "Late", 0, None, "Traffic delay"),
            (1, "alex.morgan@company.com", "2026-09-18", "09:00", "17:00", 8.00, "Remote", 0, None, "Approved WFH"),
            (2, "sarah.connor@company.com", "2026-09-21", "08:45", "17:00", 8.25, "Present", 0, None, "DevOps shift"),
            (2, "sarah.connor@company.com", "2026-09-20", None, None, 0.0, "Absent", 0, None, "Missed punch"),
            (3, "michael.scott@company.com", "2026-09-21", "09:15", "16:45", 7.50, "Present", 0, None, "Sales meeting"),
            (4, "david.miller@company.com", "2026-09-21", "09:00", "17:10", 8.16, "Present", 0, None, "Marketing sync"),
            (5, "priya.sharma@company.com", "2026-09-21", "09:10", "17:20", 8.16, "Present", 0, None, "UX sprint")
        ]
        cursor.executemany("""
        INSERT INTO attendance (employee_id, employee_email, date, clock_in, clock_out, total_hours, status, regularized, regularization_reason, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, attendance_records)

    # Seed Payroll (Latest payslip)
    cursor.execute("SELECT COUNT(*) FROM payroll;")
    if cursor.fetchone()[0] == 0:
        payrolls = [
            (1, "alex.morgan@company.com", "August", 2026, "L4", 7500.0, 1800.0, 800.0, 500.0, 1500.0, 600.0, 200.0, 8300.0, "Paid", "2026-08-28", "4821"),
            (2, "sarah.connor@company.com", "August", 2026, "L5", 9200.0, 2200.0, 1000.0, 800.0, 2000.0, 750.0, 250.0, 10200.0, "Paid", "2026-08-28", "1903"),
            (3, "michael.scott@company.com", "August", 2026, "L6", 11000.0, 2600.0, 1400.0, 2000.0, 2600.0, 900.0, 300.0, 13200.0, "Paid", "2026-08-28", "8829"),
            (4, "david.miller@company.com", "August", 2026, "L3", 5800.0, 1400.0, 600.0, 300.0, 1050.0, 450.0, 180.0, 6420.0, "Paid", "2026-08-28", "3312"),
            (5, "priya.sharma@company.com", "August", 2026, "L4", 7600.0, 1850.0, 850.0, 600.0, 1550.0, 620.0, 200.0, 8530.0, "Paid", "2026-08-28", "7741")
        ]
        cursor.executemany("""
        INSERT INTO payroll (employee_id, employee_email, month, year, salary_band, base_salary, hra_allowance, special_allowance, bonus, tax_deductions, pf_401k_deductions, insurance_deduction, net_salary, status, payout_date, bank_account_last4)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, payrolls)

    # Seed Network Diagnostics
    cursor.execute("SELECT COUNT(*) FROM network_diagnostics;")
    if cursor.fetchone()[0] == 0:
        network_diags = [
            (1, "alex.morgan@company.com", "Connected", "10.240.12.84", "10.240.0.1", "1.1.1.1 (Cloudflare Enterprise)", "CorpNet-Secure-5G", 14, 0.0, 350, "Engineering-VLAN-102"),
            (2, "sarah.connor@company.com", "Tunnel Error", "10.240.15.112", "10.240.0.1", "10.240.0.53 (Internal DNS Stale)", "Home-Fiber-WiFi", 88, 4.5, 45, "DevOps-VLAN-105"),
            (3, "michael.scott@company.com", "Connected", "10.240.22.40", "10.240.0.1", "1.1.1.1 (Cloudflare Enterprise)", "CorpNet-Guest-5G", 18, 0.1, 280, "Sales-VLAN-201"),
            (4, "david.miller@company.com", "Connected", "10.240.18.99", "10.240.0.1", "1.1.1.1 (Cloudflare Enterprise)", "CorpNet-Secure-5G", 12, 0.0, 380, "Marketing-VLAN-301"),
            (5, "priya.sharma@company.com", "Session Expired", "10.240.12.95", "10.240.0.1", "1.1.1.1 (Cloudflare Enterprise)", "CorpNet-Secure-5G", 42, 1.2, 110, "Product-VLAN-104")
        ]
        cursor.executemany("""
        INSERT INTO network_diagnostics (employee_id, employee_email, vpn_status, assigned_ip, gateway_ip, dns_server, wifi_ssid, latency_ms, packet_loss_pct, bandwidth_mbps, subnet_access)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, network_diags)

    # Seed Software Catalog
    cursor.execute("SELECT COUNT(*) FROM software_catalog;")
    if cursor.fetchone()[0] == 0:
        softwares = [
            ("Docker Desktop", "4.33.0", "Developer Tools", "Enterprise", "Enterprise container virtualization and local Kubernetes engine.", "Employee", "Medium"),
            ("Visual Studio Code", "1.92.0", "Developer Tools", "Free", "Lightweight multi-language code editor with corporate plugin repository.", "Employee", "Low"),
            ("Postman Enterprise", "11.8.0", "Developer Tools", "Commercial", "Collaborative API design, testing, and mocking platform.", "Employee", "Low"),
            ("Slack Desktop", "4.39.95", "Productivity", "Enterprise", "Corporate real-time messaging, channels, and team huddles.", "Employee", "Low"),
            ("JetBrains PyCharm Pro", "2024.2", "Developer Tools", "Commercial", "Full-featured Python and Data Science integrated development environment.", "Employee", "Medium"),
            ("Wireshark Network Analyzer", "4.2.6", "Security", "Free", "Deep-packet packet inspection tool for protocol auditing.", "System Admin", "High"),
            ("Tableau Desktop", "2024.2", "Analytics", "Commercial", "Visual data analytics, BI dashboarding, and reporting suite.", "Employee", "Low"),
            ("Figma Desktop", "124.0.2", "Design", "Commercial", "Collaborative UI/UX wireframing, prototyping, and design system tool.", "Employee", "Low")
        ]
        cursor.executemany("""
        INSERT INTO software_catalog (name, version, category, license_type, description, min_role, security_risk)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """, softwares)

    # Seed Software Requests
    cursor.execute("SELECT COUNT(*) FROM software_requests;")
    if cursor.fetchone()[0] == 0:
        software_requests = [
            (None, "TKT-202609-1092", 1, "Alex Morgan", "alex.morgan@company.com", "Docker Desktop", "4.33.0", "Required for local containerized microservices development", "INSTALLED", "Sam Carter (Support Specialist)", "2026-09-15 11:20:00", "Approved enterprise license. Auto-installed via SoftwareAgent.", "2026-09-15 11:22:15", "Package installed to /opt/docker-desktop. Version 4.33.0 verified. Daemon started."),
            (None, "TKT-202609-3891", 4, "David Miller", "david.miller@company.com", "Tableau Desktop", "2024.2", "Data visualization for marketing analytics cohort", "PENDING_APPROVAL", None, None, None, None, None)
        ]
        cursor.executemany("""
        INSERT INTO software_requests (ticket_id, ticket_code, employee_id, employee_name, employee_email, software_name, version, justification, status, reviewed_by_human, reviewed_at, human_notes, installed_at, install_logs)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, software_requests)

    # Seed Initial Audit Log entry
    cursor.execute("""
    INSERT INTO audit_logs (user_email, user_role, action, resource_type, resource_id, tier, status, details)
    VALUES ('system@company.com', 'System Admin', 'DATABASE_INITIALIZATION', 'SYSTEM', '1', 'System', 'SUCCESS', 'Initialized EMS SQLite Database with seeded employees, RBAC rules, and L1 knowledge base');
    """)

    conn.commit()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DB_PATH)
