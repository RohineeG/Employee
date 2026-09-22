"""
L3 Support Tier: Human Operations and Escalated Resolution Center.
Handles tickets that could not be resolved by L1 RAG or L2 LangGraph Agents.
"""
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.database import get_db_connection
from backend.audit import log_audit

def generate_ticket_code() -> str:
    return f"TKT-{datetime.utcnow().strftime('%Y%m')}-{random.randint(1000, 9999)}"

def create_or_escalate_ticket(
    query: str,
    user_info: Dict[str, Any],
    l1_result: Dict[str, Any],
    l2_result: Optional[Dict[str, Any]] = None,
    current_tier: str = "L3"
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    ticket_code = generate_ticket_code()
    status = "Escalated_L3" if current_tier == "L3" else ("Resolved_L2" if current_tier == "L2" else "Resolved_L1")
    resolution_summary = ""
    
    if current_tier == "L1" and l1_result.get("resolved"):
        resolution_summary = l1_result.get("answer", "Resolved by L1 RAG Knowledge Base")
    elif current_tier == "L2" and l2_result and l2_result.get("is_resolved"):
        resolution_summary = l2_result.get("resolution_message", "Resolved by L2 Database Agent")
    elif current_tier == "L3":
        resolution_summary = f"Escalated to L3: {l2_result.get('escalation_reason', 'Requires human assessment') if l2_result else 'Unresolved at automated tiers'}"

    l1_json = json.dumps(l1_result)
    l2_json = json.dumps(l2_result) if l2_result else None

    cursor.execute("""
        INSERT INTO tickets (ticket_code, user_id, user_email, user_role, query, current_tier, status, resolution_summary, l1_rag_result, l2_agents_result)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ticket_code,
        user_info["id"],
        user_info["email"],
        user_info.get("role", "Employee"),
        query,
        current_tier,
        status,
        resolution_summary,
        l1_json,
        l2_json
    ))
    conn.commit()
    ticket_id = cursor.lastrowid
    
    cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    ticket = dict(cursor.fetchone())
    conn.close()

    log_audit(
        user_email=user_info["email"],
        user_role=user_info.get("role", "Employee"),
        action=f"TICKET_CREATED_{current_tier}",
        resource_type="TICKET",
        resource_id=str(ticket_id),
        tier=current_tier,
        status="ESCALATED" if current_tier == "L3" else "SUCCESS",
        details={
            "ticket_code": ticket_code,
            "query": query,
            "status": status,
            "current_tier": current_tier
        }
    )

    return ticket

def get_all_tickets(user_id: Optional[int] = None, tier: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM tickets WHERE 1=1"
    params = []
    
    if user_id is not None:
        query += " AND user_id = ?"
        params.append(user_id)
    if tier and tier != "ALL":
        query += " AND current_tier = ?"
        params.append(tier)
    if status and status != "ALL":
        query += " AND status = ?"
        params.append(status)
        
    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_ticket_by_id(ticket_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def assign_ticket(ticket_id: int, human_name: str, admin_email: str, admin_role: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tickets
        SET assigned_human = ?, status = 'In_Review', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (human_name, ticket_id))
    conn.commit()
    conn.close()

    log_audit(
        user_email=admin_email,
        user_role=admin_role,
        action="L3_TICKET_ASSIGNED",
        resource_type="TICKET",
        resource_id=str(ticket_id),
        tier="L3",
        status="SUCCESS",
        details={"assigned_to": human_name}
    )
    return True

def resolve_ticket_by_human(
    ticket_id: int,
    human_email: str,
    human_role: str,
    resolution_notes: str,
    new_status: str = "Closed"
) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tickets
        SET l3_human_notes = ?, status = ?, resolution_summary = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (resolution_notes, new_status, f"Human Resolved: {resolution_notes}", ticket_id))
    conn.commit()
    conn.close()

    log_audit(
        user_email=human_email,
        user_role=human_role,
        action="L3_TICKET_HUMAN_RESOLVED",
        resource_type="TICKET",
        resource_id=str(ticket_id),
        tier="L3",
        status="SUCCESS",
        details={"notes": resolution_notes, "final_status": new_status}
    )
    return True
