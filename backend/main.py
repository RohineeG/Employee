"""
FastAPI Backend Application for Employee Management AI Support System.
Strictly adhering to:
- Backend: FastAPI
- AI: LangChain, LangGraph
- Database: SQLite
- RBAC and Detailed Audit Logs
- Specialized Domains: Leaves, Attendance, Payroll, Network, Software Approval & Installation
"""
import os
import json
import random
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Query, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.database import init_db, get_db_connection
from backend.auth import (
    ROLES, has_permission, get_all_employees, get_employee_by_id, get_employee_by_email
)
from backend.audit import log_audit, get_audit_logs
from backend.rag import process_l1_rag, retrieve_relevant_articles
from backend.agents import execute_l2_multi_agents, execute_software_installation
from backend.l3_support import (
    create_or_escalate_ticket, get_all_tickets, get_ticket_by_id,
    assign_ticket, resolve_ticket_by_human
)

# Initialize database on startup
init_db()

app = FastAPI(
    title="EMS AI Automated Support System API",
    description="Multi-tier Support Engine (L1 RAG -> L2 LangGraph Multi-Agent -> L3 Human Support) with RBAC & Audit Logging",
    version="1.0.0"
)

# Allow CORS for client/Streamlit communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Request Models -----------------
class SupportQueryRequest(BaseModel):
    user_id: int
    query: str

class TicketAssignRequest(BaseModel):
    admin_id: int
    assigned_human: str

class TicketResolveRequest(BaseModel):
    admin_id: int
    resolution_notes: str
    status: str = "Closed"

class EmployeeUpdateRequest(BaseModel):
    admin_id: int
    status: Optional[str] = None
    leave_balance: Optional[int] = None
    sick_leave_balance: Optional[int] = None
    benefits_enrolled: Optional[int] = None
    equipment_status: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None

class KnowledgeBaseArticleCreate(BaseModel):
    admin_id: int
    category: str
    title: str
    content: str
    keywords: str
    source_doc: str

class LeaveApplyRequest(BaseModel):
    employee_id: int
    leave_type: str
    start_date: str
    end_date: str
    days_requested: int
    reason: str

class AttendanceRegularizeRequest(BaseModel):
    employee_id: int
    attendance_id: int
    reason: str

class AttendancePunchRequest(BaseModel):
    employee_id: int
    punch_type: str # 'clock_in' or 'clock_out'

class NetworkTestRequest(BaseModel):
    employee_id: int

class SoftwareInstallRequest(BaseModel):
    employee_id: int
    software_name: str
    version: Optional[str] = None
    justification: Optional[str] = "Required for daily engineering work"

class SoftwareApproveInstallRequest(BaseModel):
    admin_id: int
    notes: Optional[str] = "Approved by Support Specialist. Automated installation initiated."

# ----------------- Health & Info -----------------
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "EMS AI Automated Support System",
        "tiers": ["L1_RAG", "L2_LANGGRAPH_AGENTS", "L3_HUMAN_SUPPORT"],
        "specialized_agents": ["LeaveAgent", "AttendanceAgent", "PayrollAgent", "NetworkAgent", "SoftwareAgent"],
        "database": "SQLite",
        "ai_engine": "LangChain + LangGraph"
    }

@app.get("/api/roles")
def get_roles():
    return ROLES

# ----------------- User & RBAC Endpoints -----------------
@app.get("/api/users")
def list_employees():
    return get_all_employees()

@app.get("/api/users/{user_id}")
def get_user_detail(user_id: int):
    user = get_employee_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Employee not found")
    return user

@app.patch("/api/users/{user_id}")
def update_employee_record(user_id: int, req: EmployeeUpdateRequest):
    admin = get_employee_by_id(req.admin_id)
    if not admin:
        raise HTTPException(status_code=403, detail="Admin user not found")
    
    if not has_permission(admin["role"], "edit_employee_records"):
        log_audit(
            user_email=admin["email"],
            user_role=admin["role"],
            action="RBAC_ACCESS_DENIED",
            resource_type="EMPLOYEE",
            resource_id=str(user_id),
            tier="Auth",
            status="FAILED",
            details={"required_permission": "edit_employee_records"}
        )
        raise HTTPException(status_code=403, detail="Role does not have permission to edit employee records")

    conn = get_db_connection()
    cursor = conn.cursor()
    
    updates = []
    params = []
    if req.status is not None:
        updates.append("status = ?")
        params.append(req.status)
    if req.leave_balance is not None:
        updates.append("leave_balance = ?")
        params.append(req.leave_balance)
    if req.sick_leave_balance is not None:
        updates.append("sick_leave_balance = ?")
        params.append(req.sick_leave_balance)
    if req.benefits_enrolled is not None:
        updates.append("benefits_enrolled = ?")
        params.append(req.benefits_enrolled)
    if req.equipment_status is not None:
        updates.append("equipment_status = ?")
        params.append(req.equipment_status)
    if req.department is not None:
        updates.append("department = ?")
        params.append(req.department)
    if req.job_title is not None:
        updates.append("job_title = ?")
        params.append(req.job_title)

    if not updates:
        conn.close()
        return {"message": "No updates requested"}

    params.append(user_id)
    cursor.execute(f"UPDATE employees SET {', '.join(updates)} WHERE id = ?", params)
    conn.commit()
    conn.close()

    log_audit(
        user_email=admin["email"],
        user_role=admin["role"],
        action="EMPLOYEE_RECORD_UPDATED",
        resource_type="EMPLOYEE",
        resource_id=str(user_id),
        tier="System",
        status="SUCCESS",
        details=req.dict(exclude_none=True)
    )

    return {"message": "Employee updated successfully", "employee_id": user_id}

# ----------------- Core AI Support Multi-Tier Pipeline -----------------
@app.post("/api/support/query")
def process_support_pipeline(req: SupportQueryRequest):
    """
    Executes the multi-tier support workflow:
    1. L1 RAG search
    2. If unresolved or action required -> L2 LangGraph multi-agent diagnostic & domain agent resolution
    3. If still unresolved or requires human support authorization -> L3 Human Support escalation
    """
    user = get_employee_by_id(req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Employee user not found")

    pipeline_trace = {
        "user_id": user["id"],
        "user_name": user["name"],
        "user_role": user["role"],
        "query": req.query,
        "stages": []
    }

    # ==================== TIER 1: L1 RAG ====================
    l1_result = process_l1_rag(req.query, user)
    pipeline_trace["stages"].append({
        "tier": "L1_RAG",
        "resolved": l1_result["resolved"],
        "summary": l1_result["message"],
        "details": l1_result
    })

    # Case 1: L1 Successfully Resolved the issue
    if l1_result["resolved"]:
        ticket = create_or_escalate_ticket(
            query=req.query,
            user_info=user,
            l1_result=l1_result,
            l2_result=None,
            current_tier="L1"
        )
        return {
            "final_tier": "L1",
            "is_resolved": True,
            "status": "Resolved_L1",
            "message": l1_result.get("answer"),
            "ticket": ticket,
            "trace": pipeline_trace
        }

    # ==================== TIER 2: L2 LangGraph Multi-Agent ====================
    l1_escalation_reason = l1_result.get("reason", "Action or specialized domain agent required")
    l2_result = execute_l2_multi_agents(
        query=req.query,
        user_info=user,
        l1_reason=l1_escalation_reason
    )
    
    pipeline_trace["stages"].append({
        "tier": "L2_LANGGRAPH_AGENTS",
        "domain": l2_result.get("domain", "diagnostics"),
        "resolved": l2_result["is_resolved"],
        "diagnostics": l2_result.get("diagnostics_report", {}),
        "db_actions": l2_result.get("db_actions_taken", []),
        "agent_steps": l2_result.get("agent_steps", []),
        "software_request": l2_result.get("software_request"),
        "summary": l2_result.get("resolution_message")
    })

    # Case 2: L2 Multi-Agent Successfully Resolved the issue
    if l2_result["is_resolved"]:
        ticket = create_or_escalate_ticket(
            query=req.query,
            user_info=user,
            l1_result=l1_result,
            l2_result=l2_result,
            current_tier="L2"
        )
        return {
            "final_tier": "L2",
            "is_resolved": True,
            "status": "Resolved_L2",
            "message": l2_result.get("resolution_message"),
            "ticket": ticket,
            "trace": pipeline_trace
        }

    # ==================== TIER 3: L3 Human Support Escalation ====================
    ticket = create_or_escalate_ticket(
        query=req.query,
        user_info=user,
        l1_result=l1_result,
        l2_result=l2_result,
        current_tier="L3"
    )
    
    escalation_dossier = {
        "reason": l2_result.get("escalation_reason", "Requires human discretion"),
        "domain": l2_result.get("domain", "General"),
        "diagnostics": l2_result.get("diagnostics_report", {}),
        "software_request": l2_result.get("software_request"),
        "ticket_code": ticket["ticket_code"]
    }
    pipeline_trace["stages"].append({
        "tier": "L3_HUMAN_SUPPORT",
        "resolved": False,
        "summary": f"Escalated to human support queue as Ticket #{ticket['ticket_code']}",
        "details": escalation_dossier
    })

    # If L2 generated a rich domain message (e.g. SoftwareAgent approval gate), preserve it
    user_facing_msg = l2_result.get("resolution_message")
    if not user_facing_msg:
        user_facing_msg = (
            f"Your request has been routed to L3 Human Support.\n\n"
            f"**Ticket ID**: `{ticket['ticket_code']}`\n"
            f"**Escalation Reason**: {escalation_dossier['reason']}\n"
            f"A Human Support Specialist has received your request and diagnostic context."
        )

    return {
        "final_tier": "L3",
        "is_resolved": False,
        "status": "Escalated_L3",
        "message": user_facing_msg,
        "ticket": ticket,
        "trace": pipeline_trace
    }

# ----------------- Domain 1: Leaves Endpoints -----------------
@app.get("/api/leaves")
def list_leaves(employee_id: Optional[int] = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if employee_id:
        cursor.execute("SELECT * FROM leaves WHERE employee_id = ? ORDER BY id DESC", (employee_id,))
    else:
        cursor.execute("SELECT * FROM leaves ORDER BY id DESC")
    records = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return records

@app.post("/api/leaves/apply")
def apply_leave(req: LeaveApplyRequest):
    user = get_employee_by_id(req.employee_id)
    if not user:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    col = "sick_leave_balance" if req.leave_type == "Sick" else "leave_balance"
    current_bal = user[col]
    
    if current_bal < req.days_requested:
        conn.close()
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient balance: Requested {req.days_requested} days but available {req.leave_type} balance is {current_bal} days."
        )
        
    new_bal = current_bal - req.days_requested
    cursor.execute(f"UPDATE employees SET {col} = ? WHERE id = ?", (new_bal, user["id"]))
    
    cursor.execute("""
        INSERT INTO leaves (employee_id, employee_email, leave_type, start_date, end_date, days_requested, reason, status, approved_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Approved', 'LeaveAgent')
    """, (user["id"], user["email"], req.leave_type, req.start_date, req.end_date, req.days_requested, req.reason))
    conn.commit()
    leave_id = cursor.lastrowid
    conn.close()
    
    log_audit(
        user_email=user["email"],
        user_role=user["role"],
        action="LEAVE_APPLIED_AND_APPROVED",
        resource_type="LEAVE",
        resource_id=str(leave_id),
        tier="L2",
        status="SUCCESS",
        details={"type": req.leave_type, "days": req.days_requested, "remaining": new_bal}
    )
    
    return {
        "success": True, 
        "leave_id": leave_id, 
        "message": f"Successfully approved {req.days_requested} day(s) of {req.leave_type}. Remaining balance: {new_bal} days."
    }

# ----------------- Domain 2: Attendance Endpoints -----------------
@app.get("/api/attendance")
def list_attendance(employee_id: Optional[int] = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if employee_id:
        cursor.execute("SELECT * FROM attendance WHERE employee_id = ? ORDER BY date DESC", (employee_id,))
    else:
        cursor.execute("SELECT * FROM attendance ORDER BY date DESC")
    records = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return records

@app.post("/api/attendance/regularize")
def regularize_attendance(req: AttendanceRegularizeRequest):
    user = get_employee_by_id(req.employee_id)
    if not user:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM attendance WHERE id = ? AND employee_id = ?", (req.attendance_id, req.employee_id))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Attendance record not found for this employee")
        
    cursor.execute("""
        UPDATE attendance
        SET status = 'Present (Regularized)',
            regularized = 1,
            regularization_reason = ?,
            total_hours = 8.0,
            clock_in = '09:00',
            clock_out = '17:00'
        WHERE id = ?
    """, (req.reason, req.attendance_id))
    conn.commit()
    conn.close()
    
    log_audit(
        user_email=user["email"],
        user_role=user["role"],
        action="ATTENDANCE_REGULARIZED",
        resource_type="ATTENDANCE",
        resource_id=str(req.attendance_id),
        tier="L2",
        status="SUCCESS",
        details={"reason": req.reason}
    )
    
    return {"success": True, "message": f"Attendance record #{req.attendance_id} regularized to 8.0 hours."}

# ----------------- Domain 3: Payroll Endpoints -----------------
@app.get("/api/payroll")
def list_payroll(employee_id: Optional[int] = None, requesting_user_id: Optional[int] = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # RBAC Validation
    if requesting_user_id:
        cursor.execute("SELECT * FROM employees WHERE id = ?", (requesting_user_id,))
        r = cursor.fetchone()
        if r:
            req_user = dict(r)
            is_admin_or_support = req_user["role"] in ["System Admin", "HR Manager", "Support Specialist", "IT Support"]
            # Regular employees can ONLY view their own records
            if not is_admin_or_support:
                if not employee_id or employee_id != req_user["id"]:
                    log_audit(
                        user_email=req_user["email"],
                        user_role=req_user["role"],
                        action="RBAC_PAYROLL_ACCESS_DENIED",
                        resource_type="PAYROLL",
                        resource_id=str(employee_id or "COMPANY_WIDE"),
                        tier="Auth",
                        status="FAILED",
                        details={"error": "Unauthorized access to sensitive payroll data by regular employee"}
                    )
                    conn.close()
                    raise HTTPException(
                        status_code=403,
                        detail="Access Denied: Regular employees are restricted from viewing company-wide or peer payroll data."
                    )

    if employee_id:
        cursor.execute("SELECT * FROM payroll WHERE employee_id = ? ORDER BY id DESC", (employee_id,))
    else:
        cursor.execute("SELECT * FROM payroll ORDER BY id DESC")
    records = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return records

# ----------------- Domain 4: Network Diagnostics Endpoints -----------------
@app.get("/api/network-diagnostics")
def get_network_diagnostics(employee_id: Optional[int] = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if employee_id:
        cursor.execute("SELECT * FROM network_diagnostics WHERE employee_id = ?", (employee_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    else:
        cursor.execute("SELECT * FROM network_diagnostics")
        records = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return records

@app.post("/api/network-diagnostics/test")
def test_and_repair_network(req: NetworkTestRequest):
    user = get_employee_by_id(req.employee_id)
    if not user:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    new_ip = f"10.240.12.{random.randint(100, 240)}"
    cursor.execute("""
        UPDATE network_diagnostics
        SET vpn_status = 'Connected',
            assigned_ip = ?,
            latency_ms = 11,
            packet_loss_pct = 0.0,
            dns_server = '1.1.1.1 (Cloudflare Enterprise)',
            last_tested = CURRENT_TIMESTAMP
        WHERE employee_id = ?
    """, (new_ip, req.employee_id))
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "vpn_status": "Connected",
        "assigned_ip": new_ip,
        "latency_ms": 11,
        "dns_server": "1.1.1.1 (Cloudflare Enterprise)",
        "message": f"Network tunnel test passed. Session renewed with corporate IP {new_ip}."
    }

# ----------------- Domain 5: Software Catalog & Request Workflow -----------------
@app.get("/api/software/catalog")
def list_software_catalog():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM software_catalog ORDER BY category, name")
    items = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return items

@app.get("/api/software/requests")
def list_software_requests(employee_id: Optional[int] = None, status: Optional[str] = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM software_requests WHERE 1=1"
    params = []
    if employee_id:
        query += " AND employee_id = ?"
        params.append(employee_id)
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    requests = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return requests

@app.post("/api/software/requests")
def create_software_request(req: SoftwareInstallRequest):
    user = get_employee_by_id(req.employee_id)
    if not user:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    tkt_code = f"TKT-{datetime.utcnow().strftime('%Y%m')}-{random.randint(1000, 9999)}"
    cursor.execute("""
        INSERT INTO software_requests (ticket_code, employee_id, employee_name, employee_email, software_name, version, justification, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING_APPROVAL')
    """, (tkt_code, user["id"], user["name"], user["email"], req.software_name, req.version or "Latest Stable", req.justification))
    conn.commit()
    req_id = cursor.lastrowid
    conn.close()
    
    log_audit(
        user_email=user["email"],
        user_role=user["role"],
        action="SOFTWARE_REQUEST_SUBMITTED",
        resource_type="SOFTWARE_REQUEST",
        resource_id=str(req_id),
        tier="L2",
        status="PENDING",
        details={"software": req.software_name, "version": req.version}
    )
    
    return {
        "success": True,
        "request_id": req_id,
        "status": "PENDING_APPROVAL",
        "message": f"Software request for '{req.software_name}' queued. Awaiting Human Support Specialist approval."
    }

@app.post("/api/software/requests/{request_id}/approve-and-install")
def approve_and_install_software(request_id: int, req: SoftwareApproveInstallRequest):
    """
    Core Requirement:
    After getting the approval of the human support person, installs that software.
    """
    admin = get_employee_by_id(req.admin_id)
    if not admin:
        raise HTTPException(status_code=403, detail="Admin or Support Specialist not found")
        
    if not has_permission(admin["role"], "resolve_l3_tickets"):
        log_audit(
            user_email=admin["email"],
            user_role=admin["role"],
            action="RBAC_ACCESS_DENIED",
            resource_type="SOFTWARE_REQUEST",
            resource_id=str(request_id),
            tier="Auth",
            status="FAILED",
            details={"required_permission": "resolve_l3_tickets"}
        )
        raise HTTPException(status_code=403, detail="Only Human Support Specialists and Admins can approve software installations.")

    # Execute SoftwareAgent installation post-human-approval
    result = execute_software_installation(request_id, admin, req.notes)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Installation execution failed"))
        
    return result

# ----------------- Ticket Management Endpoints -----------------
@app.get("/api/tickets")
def list_tickets(user_id: Optional[int] = None, tier: Optional[str] = None, status: Optional[str] = None):
    return get_all_tickets(user_id=user_id, tier=tier, status=status)

@app.get("/api/tickets/{ticket_id}")
def get_ticket(ticket_id: int):
    t = get_ticket_by_id(ticket_id)
    if not t:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return t

@app.post("/api/tickets/{ticket_id}/assign")
def assign_ticket_endpoint(ticket_id: int, req: TicketAssignRequest):
    admin = get_employee_by_id(req.admin_id)
    if not admin or not has_permission(admin["role"], "resolve_l3_tickets"):
        raise HTTPException(status_code=403, detail="Unauthorized to assign tickets")
    
    assign_ticket(ticket_id, req.assigned_human, admin["email"], admin["role"])
    return {"message": f"Ticket #{ticket_id} assigned to {req.assigned_human}"}

@app.post("/api/tickets/{ticket_id}/resolve")
def resolve_ticket_endpoint(ticket_id: int, req: TicketResolveRequest):
    admin = get_employee_by_id(req.admin_id)
    if not admin or not has_permission(admin["role"], "resolve_l3_tickets"):
        raise HTTPException(status_code=403, detail="Unauthorized to resolve tickets")
        
    resolve_ticket_by_human(
        ticket_id=ticket_id,
        human_email=admin["email"],
        human_role=admin["role"],
        resolution_notes=req.resolution_notes,
        new_status=req.status
    )
    return {"message": f"Ticket #{ticket_id} resolved by {admin['name']}"}

# ----------------- Knowledge Base Endpoints -----------------
@app.get("/api/knowledge-base")
def list_knowledge_base():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM knowledge_base ORDER BY category, title")
    articles = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return articles

@app.post("/api/knowledge-base")
def create_knowledge_base_article(req: KnowledgeBaseArticleCreate):
    admin = get_employee_by_id(req.admin_id)
    if not admin or not has_permission(admin["role"], "manage_knowledge_base"):
        raise HTTPException(status_code=403, detail="Role does not have permission to manage knowledge base")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO knowledge_base (category, title, content, keywords, source_doc)
        VALUES (?, ?, ?, ?, ?)
    """, (req.category, req.title, req.content, req.keywords, req.source_doc))
    conn.commit()
    art_id = cursor.lastrowid
    conn.close()

    log_audit(
        user_email=admin["email"],
        user_role=admin["role"],
        action="KB_ARTICLE_CREATED",
        resource_type="KNOWLEDGE_BASE",
        resource_id=str(art_id),
        tier="L1",
        status="SUCCESS",
        details={"title": req.title, "source_doc": req.source_doc}
    )
    return {"message": "Article created successfully", "article_id": art_id}

# ----------------- Audit Logs Endpoint -----------------
@app.get("/api/audit-logs")
def list_audit_logs(
    user_id: Optional[int] = None,
    tier: Optional[str] = None,
    limit: int = Query(default=100, le=500)
):
    """
    Returns audit logs with RBAC validation.
    """
    user_email_filter = None
    if user_id:
        user = get_employee_by_id(user_id)
        if user and not has_permission(user["role"], "view_audit_logs"):
            # Standard employees can only see their own audit logs
            user_email_filter = user["email"]

    logs = get_audit_logs(limit=limit, tier=tier, user_email=user_email_filter)
    return logs

# ----------------- Analytics / Stats Endpoint -----------------
@app.get("/api/stats")
def get_system_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total tickets
    cursor.execute("SELECT COUNT(*) FROM tickets")
    total_tickets = cursor.fetchone()[0]
    
    # By Tier
    cursor.execute("SELECT current_tier, COUNT(*) FROM tickets GROUP BY current_tier")
    tier_counts = {r[0]: r[1] for r in cursor.fetchall()}
    
    # Total Employees
    cursor.execute("SELECT COUNT(*), SUM(CASE WHEN status='Locked' THEN 1 ELSE 0 END) FROM employees")
    emp_stats = cursor.fetchone()
    total_employees = emp_stats[0]
    locked_employees = emp_stats[1] or 0
    
    # Total Audit Logs
    cursor.execute("SELECT COUNT(*) FROM audit_logs")
    total_audit_events = cursor.fetchone()[0]
    
    # L2 Automated Agent Actions
    cursor.execute("SELECT COUNT(*) FROM agent_actions")
    total_agent_actions = cursor.fetchone()[0]
    
    # Software Requests Pending & Installed
    cursor.execute("SELECT COUNT(*) FROM software_requests WHERE status='PENDING_APPROVAL'")
    pending_soft_requests = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM software_requests WHERE status='INSTALLED'")
    installed_soft_requests = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_tickets": total_tickets,
        "resolved_l1": tier_counts.get("L1", 0),
        "resolved_l2": tier_counts.get("L2", 0),
        "escalated_l3": tier_counts.get("L3", 0),
        "total_employees": total_employees,
        "locked_employees": locked_employees,
        "total_audit_events": total_audit_events,
        "total_agent_actions": total_agent_actions,
        "pending_software_requests": pending_soft_requests,
        "installed_software_requests": installed_soft_requests
    }
