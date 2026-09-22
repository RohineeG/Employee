"""
Mock Data and Seed Records for EMS Automated Support System
Converted from TypeScript mockData.ts to Python.
"""
from typing import List, Dict, Any

INITIAL_EMPLOYEES: List[Dict[str, Any]] = [
    {"id": 1, "name": "Sarah Jenkins", "email": "sarah.j@enterprise.com", "department": "Engineering", "role": "Employee", "status": "Active", "leave_balance": 14, "benefits_enrolled": True, "equipment_status": "Delivered"},
    {"id": 2, "name": "David Vance", "email": "david.v@enterprise.com", "department": "Finance", "role": "Employee", "status": "Locked", "leave_balance": 18, "benefits_enrolled": True, "equipment_status": "Delivered"},
    {"id": 3, "name": "Elena Rostova", "email": "elena.r@enterprise.com", "department": "Human Resources", "role": "HR Manager", "status": "Active", "leave_balance": 22, "benefits_enrolled": True, "equipment_status": "Delivered"},
    {"id": 4, "name": "Marcus Chen", "email": "marcus.c@enterprise.com", "department": "Information Technology", "role": "IT Support", "status": "Active", "leave_balance": 16, "benefits_enrolled": True, "equipment_status": "Delivered"},
    {"id": 5, "name": "Rachel Hayes", "email": "rachel.h@enterprise.com", "department": "Operations", "role": "Support Specialist", "status": "Active", "leave_balance": 20, "benefits_enrolled": True, "equipment_status": "Delivered"},
    {"id": 6, "name": "Amanda Sterling", "email": "amanda.s@enterprise.com", "department": "Security & Compliance", "role": "System Admin", "status": "Active", "leave_balance": 25, "benefits_enrolled": True, "equipment_status": "Delivered"},
    {"id": 7, "name": "James Wilson", "email": "james.w@enterprise.com", "department": "Sales", "role": "Employee", "status": "Active", "leave_balance": 8, "benefits_enrolled": False, "equipment_status": "Pending Dispatch"},
    {"id": 8, "name": "Maya Patel", "email": "maya.p@enterprise.com", "department": "Product", "role": "Employee", "status": "Active", "leave_balance": 12, "benefits_enrolled": True, "equipment_status": "Hardware Stuck"},
]

INITIAL_ARTICLES: List[Dict[str, Any]] = [
    {
        "id": 1,
        "category": "Leave & Time Off",
        "title": "Annual Paid Time Off (PTO) Policy & Carryover Rules",
        "source_doc": "HR-POL-2024-01",
        "keywords": "pto, leave balance, vacation, carryover, sick days, holiday",
        "content": "Full-time employees receive 20 days of paid time off per calendar year accrued monthly. Up to 5 unused PTO days can be carried over into Q1 of the following year. Leave requests exceeding 3 consecutive business days require supervisor sign-off 14 days in advance.",
        "updated_at": "2026-03-15"
    },
    {
        "id": 2,
        "category": "IT Access & Credentials",
        "title": "Corporate VPN & Single Sign-On Access Protocols",
        "source_doc": "IT-SEC-2024-04",
        "keywords": "vpn, login, password, sso, locked, credentials, okta, mfa",
        "content": "All personnel must authenticate via Okta MFA. After 5 consecutive failed login attempts, accounts enter a safety lockout state. Account lockouts can be diagnosed and reset automatically by the L2 IT Support Agent or unlocked manually by IT support personnel.",
        "updated_at": "2026-04-10"
    },
    {
        "id": 3,
        "category": "Healthcare & Benefits",
        "title": "Health Benefits Enrollment & Open Season Guide",
        "source_doc": "BEN-POL-2024-02",
        "keywords": "health, dental, vision, benefits, enrollment, insurance, medical",
        "content": "Open enrollment occurs annually between November 1 and November 30. Qualifying Life Events permit 30-day enrollment exceptions. Coverage takes effect on the 1st of the following calendar month after HR approval.",
        "updated_at": "2026-01-20"
    },
    {
        "id": 4,
        "category": "Equipment & Workplace",
        "title": "Hardware Procurement & Home Office Ergonomics Subsidy",
        "source_doc": "OPS-EQUIP-2024-08",
        "keywords": "laptop, monitor, keyboard, equipment, hardware, broken, requisition",
        "content": "Employees receive a MacBook Pro or ThinkPad workstation, two 27-inch 4K monitors, and an annual $500 ergonomics stipend. Faulty equipment can be reported for expedited replacement dispatch via the automated equipment desk.",
        "updated_at": "2026-05-12"
    },
    {
        "id": 5,
        "category": "Payroll & Compensation",
        "title": "Payroll Schedule, Direct Deposit & Expense Reimbursement",
        "source_doc": "FIN-PAY-2024-03",
        "keywords": "payroll, salary, direct deposit, paystub, tax, w2, expenses",
        "content": "Payday is semi-monthly on the 15th and last business day of each month. Expense claims must be submitted via Concur by the 5th of each month for timely reimbursement.",
        "updated_at": "2026-02-28"
    }
]

INITIAL_TICKETS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "ticket_code": "TKT-202609-1001",
        "user_id": 1,
        "user_name": "Sarah Jenkins",
        "user_email": "sarah.j@enterprise.com",
        "query": "What is our annual PTO carryover limit?",
        "current_tier": "L1",
        "status": "Resolved_L1",
        "created_at": "2026-09-20 09:14:22",
        "resolved_at": "2026-09-20 09:14:23",
        "diagnostics_json": '{"tier": "L1", "source": "HR-POL-2024-01"}'
    },
    {
        "id": 2,
        "ticket_code": "TKT-202609-1002",
        "user_id": 2,
        "user_name": "David Vance",
        "user_email": "david.v@enterprise.com",
        "query": "My account was locked after password expiration, please unlock it",
        "current_tier": "L2",
        "status": "Resolved_L2",
        "created_at": "2026-09-20 11:30:10",
        "resolved_at": "2026-09-20 11:30:12",
        "diagnostics_json": '{"root_cause": "Consecutive MFA failures triggered account lock flag in SQLite employees table", "remediation": "DatabaseAgent executed UPDATE employees SET status=\'Active\' WHERE id=2", "verified": true}'
    },
    {
        "id": 3,
        "ticket_code": "TKT-202609-1003",
        "user_id": 8,
        "user_name": "Maya Patel",
        "user_email": "maya.p@enterprise.com",
        "query": "My workstation monitor arrived cracked and IT depot says order is frozen.",
        "current_tier": "L3",
        "status": "Escalated_L3",
        "assigned_human": "Marcus Chen",
        "created_at": "2026-09-21 08:22:45",
        "diagnostics_json": '{"root_cause": "Hardware Requisition Stuck in Vendor Depot: requires physical asset replacement", "escalation_reason": "Automated agents cannot issue hardware return authorization codes"}'
    }
]

INITIAL_AUDIT_LOGS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "timestamp": "2026-09-21 08:22:45",
        "user_email": "maya.p@enterprise.com",
        "user_role": "Employee",
        "action": "L3_ESCALATION_DISPATCHED",
        "resource_type": "TICKET",
        "resource_id": "3",
        "tier": "L3",
        "status": "ESCALATED",
        "details": "Hardware replacement beyond automated scope. Dispatched to L3 Human Queue.",
        "ip_address": "10.0.4.12"
    },
    {
        "id": 2,
        "timestamp": "2026-09-20 11:30:12",
        "user_email": "david.v@enterprise.com",
        "user_role": "Employee",
        "action": "L2_DATABASE_REMEDIATION",
        "resource_type": "EMPLOYEE",
        "resource_id": "2",
        "tier": "L2",
        "status": "SUCCESS",
        "details": "DatabaseAgent unlocked employee account in SQLite: status set to Active.",
        "ip_address": "127.0.0.1"
    },
    {
        "id": 3,
        "timestamp": "2026-09-20 09:14:23",
        "user_email": "sarah.j@enterprise.com",
        "user_role": "Employee",
        "action": "L1_RAG_QUERY_RESOLVED",
        "resource_type": "KNOWLEDGE_BASE",
        "resource_id": "1",
        "tier": "L1",
        "status": "SUCCESS",
        "details": "Resolved query via HR-POL-2024-01 (Annual PTO Carryover Rules).",
        "ip_address": "10.0.1.88"
    }
]
