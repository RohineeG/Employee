"""
Audit Logging System for the Employee Management Support Architecture.
Ensures comprehensive compliance, traceability, and RBAC tracking.
"""
import sqlite3
import json
from datetime import datetime
from backend.database import get_db_connection

def log_audit(
    user_email: str,
    user_role: str,
    action: str,
    resource_type: str,
    resource_id: str = "",
    tier: str = "System", # L1, L2, L3, System, Auth
    status: str = "SUCCESS", # SUCCESS, FAILED, ESCALATED, WARNING
    details: dict | str = "",
    ip_address: str = "127.0.0.1"
):
    """
    Persists an immutable audit log entry into SQLite.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    details_str = json.dumps(details) if isinstance(details, (dict, list)) else str(details)
    
    cursor.execute("""
        INSERT INTO audit_logs (timestamp, user_email, user_role, action, resource_type, resource_id, tier, status, details, ip_address)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        user_email,
        user_role,
        action,
        resource_type,
        str(resource_id),
        tier,
        status,
        details_str,
        ip_address
    ))
    conn.commit()
    log_id = cursor.lastrowid
    conn.close()
    return log_id

def get_audit_logs(limit: int = 100, tier: str = None, user_email: str = None, action: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM audit_logs WHERE 1=1"
    params = []
    
    if tier and tier != "ALL":
        query += " AND tier = ?"
        params.append(tier)
    if user_email:
        query += " AND user_email LIKE ?"
        params.append(f"%{user_email}%")
    if action:
        query += " AND action LIKE ?"
        params.append(f"%{action}%")
        
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows
