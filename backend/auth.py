"""
Role-Based Access Control (RBAC) definitions and permission checks.
"""
from typing import Dict, List, Optional
from backend.database import get_db_connection

ROLES = {
    "Employee": {
        "description": "Standard staff member. Can view personal profile, query AI support, review own tickets and personal audit events.",
        "permissions": ["view_own_profile", "submit_support_query", "view_own_tickets", "view_own_audit_logs"]
    },
    "Team Lead": {
        "description": "Department manager. Can view department members' summaries, submit support queries, and review team requests.",
        "permissions": ["view_own_profile", "submit_support_query", "view_own_tickets", "view_department_employees", "view_own_audit_logs"]
    },
    "HR Manager": {
        "description": "Human Resources Administrator. Can manage employee records, adjust leave and benefits, update L1 RAG knowledge base, and resolve escalated HR tickets.",
        "permissions": [
            "view_own_profile", "submit_support_query", "view_all_employees", "edit_employee_records",
            "adjust_leave_balance", "sync_benefits", "manage_knowledge_base", "view_audit_logs", "resolve_l3_tickets"
        ]
    },
    "System Admin": {
        "description": "Enterprise IT & Security Administrator. Full administrative access across all databases, user lockouts, L2 multi-agent configurations, and comprehensive audit logs.",
        "permissions": [
            "view_own_profile", "submit_support_query", "view_all_employees", "edit_employee_records",
            "unlock_accounts", "adjust_leave_balance", "sync_benefits", "manage_knowledge_base",
            "view_audit_logs", "resolve_l3_tickets", "manage_system_settings"
        ]
    },
    "Support Specialist": {
        "description": "Technical & Operations L3 Support Agent. Handles escalated support tickets, reviews LangGraph diagnostic traces, and executes human resolutions.",
        "permissions": [
            "view_own_profile", "submit_support_query", "view_all_employees", "unlock_accounts",
            "resolve_l3_tickets", "view_audit_logs", "add_ticket_notes"
        ]
    }
}

def has_permission(role: str, permission: str) -> bool:
    role_config = ROLES.get(role)
    if not role_config:
        return False
    return permission in role_config["permissions"]

def get_employee_by_email(email: str) -> Optional[dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_employee_by_id(emp_id: int) -> Optional[dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE id = ?", (emp_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_employees() -> List[dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees ORDER BY id ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows
