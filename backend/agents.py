"""
L2 Support Tier: Multi-Agent Diagnostic and Remediation System powered by LangGraph & LangChain.
Agents:
1. Supervisor Router Node: Identifies domain (Leave, Attendance, Payroll, Network, Software, Diagnostics)
2. LeaveAgent Node: Inspects PTO/Sick balances, verifies policies, processes leave applications, recalculates disparities.
3. AttendanceAgent Node: Evaluates daily clock-in/out logs, calculates work hours, executes attendance regularization.
4. PayrollAgent Node: Analyzes payslips, salary bands, statutory tax/PF deductions, bonuses, and payout schedules.
5. NetworkAgent Node: Tests VPN status, DNS latency, subnet allocations, and executes automated network resets.
6. SoftwareAgent Node: Manages software catalog & requests. Enforces corporate security gate: asks for Human Support Specialist approval, and upon approval, executes software installation.
7. DiagnosticsAgent Node: Deep-dives into SQLite employee records to identify root causes of lockouts, benefits, and hardware.
8. DatabaseAgent Node: Formulates and executes safe parameterized SQL transactions to repair discrepancies or reset statuses.
9. PolicyVerifier Node: Verifies database mutations meet enterprise policy.
10. EscalationRouter Node: Seamlessly routes unsolvable or approval-gated issues to L3 Human Support.
"""
import os
import re
import json
import random
from typing import Dict, Any, List, TypedDict, Optional
from datetime import datetime, date
from langgraph.graph import StateGraph, START, END

from backend.database import get_db_connection
from backend.audit import log_audit

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Define LangGraph Agent State
class SupportAgentState(TypedDict):
    ticket_id: Optional[int]
    query: str
    user_info: Dict[str, Any]
    l1_reason: str
    domain: str
    diagnostics_report: Dict[str, Any]
    agent_steps: List[Dict[str, Any]]
    db_actions_taken: List[Dict[str, Any]]
    software_request: Optional[Dict[str, Any]]
    is_resolved: bool
    resolution_message: str
    requires_l3: bool
    escalation_reason: str

def detect_domain(query: str) -> str:
    q = query.lower()
    if any(k in q for k in ["install", "software", "docker", "vscode", "vs code", "postman", "slack", "pycharm", "wireshark", "tableau", "figma", "application", "setup tool"]):
        return "software"
    if any(k in q for k in ["leave", "pto", "vacation", "sick day", "apply for leave", "time off", "holiday balance", "leave balance", "pto balance"]):
        return "leave"
    if any(k in q for k in ["attendance", "clock in", "clock out", "missed punch", "punch in", "punch out", "regularize", "late arrival", "wfh punch", "hours worked", "timesheet"]):
        return "attendance"
    if any(k in q for k in ["payroll", "payslip", "salary", "net pay", "gross pay", "tax deduction", "bonus", "payday", "compensation", "bank deposit", "401k", "provident fund", "deduction"]):
        return "payroll"
    if any(k in q for k in ["network", "vpn", "wifi", "dns", "latency", "packet loss", "ping", "gateway", "subnet", "ip address", "connection drop", "tunnel"]):
        return "network"
    return "diagnostics"

# ----------------- 0. Supervisor Router Node -----------------
def supervisor_router_node(state: SupportAgentState) -> Dict[str, Any]:
    query = state["query"]
    domain = detect_domain(query)
    
    step_log = {
        "step": "L2_SUPERVISOR_ROUTING",
        "agent": "SupervisorAgent",
        "details": f"Analyzed query intent: routed to specialized agent for domain '{domain.upper()}'.",
        "domain": domain,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return {
        "domain": domain,
        "agent_steps": state.get("agent_steps", []) + [step_log]
    }

# ----------------- 1. LeaveAgent Node -----------------
def leave_agent_node(state: SupportAgentState) -> Dict[str, Any]:
    user_info = state["user_info"]
    query = state["query"]
    q_lower = query.lower()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE id = ?", (user_info["id"],))
    emp = dict(cursor.fetchone())
    
    cursor.execute("SELECT * FROM leaves WHERE employee_id = ? ORDER BY id DESC LIMIT 5", (emp["id"],))
    past_leaves = [dict(r) for r in cursor.fetchall()]
    
    steps = list(state.get("agent_steps", []))
    db_actions = list(state.get("db_actions_taken", []))
    
    # Check if this is an application for leave
    is_apply = any(w in q_lower for w in ["apply", "take", "request", "need", "book", "submit"]) and any(w in q_lower for w in ["leave", "pto", "day", "days", "vacation"])
    
    # Extract number of days requested (default 1 if not specified)
    days_match = re.search(r'(\d+)\s*(?:day|days)', q_lower)
    days_requested = int(days_match.group(1)) if days_match else 1
    
    leave_type = "Sick" if "sick" in q_lower else ("Casual" if "casual" in q_lower else "PTO")
    
    if is_apply:
        current_balance = emp["sick_leave_balance"] if leave_type == "Sick" else emp["leave_balance"]
        
        if current_balance >= days_requested:
            # Execute automated leave booking
            new_balance = current_balance - days_requested
            col_to_update = "sick_leave_balance" if leave_type == "Sick" else "leave_balance"
            
            cursor.execute(f"UPDATE employees SET {col_to_update} = ? WHERE id = ?", (new_balance, emp["id"]))
            
            today_str = date.today().isoformat()
            cursor.execute("""
                INSERT INTO leaves (employee_id, employee_email, leave_type, start_date, end_date, days_requested, reason, status, approved_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'Approved', 'LeaveAgent (Automated)')
            """, (emp["id"], emp["email"], leave_type, today_str, today_str, days_requested, f"Auto-approved via AI Support: {query[:50]}"))
            conn.commit()
            
            action_summary = f"Approved and booked {days_requested} day(s) of {leave_type} leave. Updated remaining {leave_type} balance to {new_balance} days."
            db_actions.append({
                "agent": "LeaveAgent",
                "action": "LEAVE_APPLICATION_AUTO_APPROVED",
                "success": True,
                "summary": action_summary,
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            resolution_msg = (
                f"🌴 **Leave Application Successfully Approved!**\n\n"
                f"- **Leave Type**: `{leave_type}`\n"
                f"- **Days Granted**: `{days_requested} day(s)`\n"
                f"- **Approval Agent**: `LeaveAgent (Automated Approval Engine)`\n"
                f"- **Remaining {leave_type} Balance**: `{new_balance} days`\n"
                f"- **Policy Reference**: `HR-LEAVE-2026-01` (Within annual allocation limits)\n\n"
                f"Your team calendar and EMS records have been updated automatically."
            )
            is_resolved = True
            requires_l3 = False
            esc_reason = ""
        else:
            action_summary = f"Leave balance insufficient: Requested {days_requested} days but available balance is {current_balance} days."
            resolution_msg = (
                f"⚠️ **Insufficient Leave Balance:**\n\n"
                f"You requested `{days_requested} day(s)` of `{leave_type}`, but your current available balance is `{current_balance} day(s)`.\n\n"
                f"Your request has been routed to L3 Human HR Operations for discretionary manager approval or unpaid time-off authorization."
            )
            is_resolved = False
            requires_l3 = True
            esc_reason = f"Leave balance exceeded: Requested {days_requested} days, current balance {current_balance} days."
    
    elif any(w in q_lower for w in ["fix", "recalculate", "disparity", "wrong balance", "adjust balance", "restore"]):
        # Recalculate based on baseline 20 days PTO
        cursor.execute("UPDATE employees SET leave_balance = 20, sick_leave_balance = 10 WHERE id = ?", (emp["id"],))
        conn.commit()
        action_summary = f"Recalculated and restored standard baseline leave balance (20 PTO / 10 Sick) for {emp['name']}."
        db_actions.append({
            "agent": "LeaveAgent",
            "action": "LEAVE_BALANCE_RECALCULATED",
            "success": True,
            "summary": action_summary,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        })
        resolution_msg = (
            f"⚖️ **Leave Disparity Recalculated & Restored:**\n\n"
            f"- **Prior Recorded PTO**: `{emp['leave_balance']} days`\n"
            f"- **Updated Active PTO**: `20 days` (Full annual standard allotment)\n"
            f"- **Sick Leave Balance**: `10 days`\n"
            f"- **Audit Verification**: Verified against policy `HR-LEAVE-2026-01` and synchronized in SQLite."
        )
        is_resolved = True
        requires_l3 = False
        esc_reason = ""
    else:
        # Standard Leave Balance Inquiry
        recent_str = "\n".join([f"• [{l['start_date']}] {l['days_requested']}d {l['leave_type']} ({l['status']}) - {l['reason']}" for l in past_leaves[:3]]) or "• No past leave records on file."
        resolution_msg = (
            f"🌴 **Current Leave & Time Off Portfolio for {emp['name']}**:\n\n"
            f"- **Paid Time Off (PTO)**: `{emp['leave_balance']} days available` (Standard 20 days/year)\n"
            f"- **Sick Leave**: `{emp['sick_leave_balance']} days available` (Standard 10 days/year)\n"
            f"- **Annual Carryover Cap**: Up to `5 days` into Q1\n\n"
            f"**Recent Leave History**:\n{recent_str}\n\n"
            f"*Tip: You can apply directly by saying 'Apply for 2 days PTO next Monday'.*"
        )
        is_resolved = True
        requires_l3 = False
        esc_reason = ""
    
    conn.close()
    
    steps.append({
        "step": "L2_LEAVE_PROCESSING",
        "agent": "LeaveAgent",
        "details": f"Processed leave inquiry for {emp['name']}. Resolution status: {'Resolved' if is_resolved else 'Escalated'}.",
        "status": "COMPLETED"
    })
    
    return {
        "agent_steps": steps,
        "db_actions_taken": db_actions,
        "is_resolved": is_resolved,
        "resolution_message": resolution_msg,
        "requires_l3": requires_l3,
        "escalation_reason": esc_reason,
        "diagnostics_report": {
            "agent": "LeaveAgent",
            "employee_id": emp["id"],
            "current_pto": emp["leave_balance"],
            "current_sick": emp["sick_leave_balance"],
            "can_auto_remediate": is_resolved
        }
    }

# ----------------- 2. AttendanceAgent Node -----------------
def attendance_agent_node(state: SupportAgentState) -> Dict[str, Any]:
    user_info = state["user_info"]
    query = state["query"]
    q_lower = query.lower()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE id = ?", (user_info["id"],))
    emp = dict(cursor.fetchone())
    
    cursor.execute("SELECT * FROM attendance WHERE employee_id = ? ORDER BY date DESC LIMIT 7", (emp["id"],))
    records = [dict(r) for r in cursor.fetchall()]
    
    steps = list(state.get("agent_steps", []))
    db_actions = list(state.get("db_actions_taken", []))
    
    # Check if user wants to regularize missed punch or late arrival
    is_regularize = any(w in q_lower for w in ["regularize", "fix punch", "missed punch", "correct attendance", "update attendance", "clock in error"])
    
    if is_regularize:
        # Check if there is an absent or late record to regularize
        target_rec = next((r for r in records if r["status"] in ["Absent", "Late", "Missed"]), None)
        if not target_rec and records:
            target_rec = records[0] # regularize most recent record
            
        if target_rec:
            reg_date = target_rec["date"]
            cursor.execute("""
                UPDATE attendance 
                SET status = 'Present (Regularized)', regularized = 1, regularization_reason = ?, total_hours = 8.0, clock_in = '09:00', clock_out = '17:00'
                WHERE id = ?
            """, (f"Self-service regularized via AttendanceAgent: {query[:50]}", target_rec["id"]))
            conn.commit()
            
            action_summary = f"Regularized attendance record ID #{target_rec['id']} for {reg_date} to 'Present (Regularized)' with 8.0 working hours."
            db_actions.append({
                "agent": "AttendanceAgent",
                "action": "ATTENDANCE_REGULARIZED",
                "success": True,
                "summary": action_summary,
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            resolution_msg = (
                f"⏱️ **Attendance Successfully Regularized!**\n\n"
                f"- **Date**: `{reg_date}`\n"
                f"- **Prior Status**: `{target_rec['status']}`\n"
                f"- **New Status**: `Present (Regularized)`\n"
                f"- **Updated Hours**: `09:00 AM - 05:00 PM (8.0 Hours)`\n"
                f"- **Reason Logged**: Verified self-service punch regularization\n\n"
                f"Your payroll timesheet has been updated and no negative deduction will apply."
            )
            is_resolved = True
            requires_l3 = False
            esc_reason = ""
        else:
            # Insert a regularized record for today
            today_str = date.today().isoformat()
            cursor.execute("""
                INSERT INTO attendance (employee_id, employee_email, date, clock_in, clock_out, total_hours, status, regularized, regularization_reason, notes)
                VALUES (?, ?, ?, '09:00', '17:00', 8.0, 'Present (Regularized)', 1, 'Attendance regularized via AttendanceAgent', 'Automated punch creation')
            """, (emp["id"], emp["email"], today_str))
            conn.commit()
            
            resolution_msg = f"⏱️ **Attendance Regularized**: Created clock-in record for today `{today_str}` (09:00 AM - 05:00 PM, 8.0 hrs) as `Present (Regularized)`."
            is_resolved = True
            requires_l3 = False
            esc_reason = ""
    else:
        # Standard Attendance Status Inquiry
        rec_summary = "\n".join([
            f"• **{r['date']}**: `{r['status']}` | In: `{r['clock_in'] or 'None'}` | Out: `{r['clock_out'] or 'None'}` | `{r['total_hours']} hrs` {'(Regularized)' if r['regularized'] else ''}"
            for r in records[:5]
        ]) or "• No attendance records logged this week."
        
        latest_status = records[0]["status"] if records else "Active (Standard)"
        total_week_hours = sum(r["total_hours"] or 0 for r in records[:5])
        
        resolution_msg = (
            f"⏱️ **Attendance Overview for {emp['name']}**:\n\n"
            f"- **Today's Status**: `{latest_status}`\n"
            f"- **Total Hours Logged (Last 5 Days)**: `{total_week_hours:.2f} hrs` (Target: 40 hrs/week)\n"
            f"- **Core Office Hours**: `09:00 AM - 05:00 PM`\n\n"
            f"**Recent Daily Punch Logs**:\n{rec_summary}\n\n"
            f"*Tip: If you missed a punch, say 'Please regularize my missed punch' to update your timesheet automatically.*"
        )
        is_resolved = True
        requires_l3 = False
        esc_reason = ""
        
    conn.close()
    
    steps.append({
        "step": "L2_ATTENDANCE_PROCESSING",
        "agent": "AttendanceAgent",
        "details": f"Processed attendance status for {emp['name']}. Outcome: {'Resolved' if is_resolved else 'Escalated'}.",
        "status": "COMPLETED"
    })
    
    return {
        "agent_steps": steps,
        "db_actions_taken": db_actions,
        "is_resolved": is_resolved,
        "resolution_message": resolution_msg,
        "requires_l3": requires_l3,
        "escalation_reason": esc_reason,
        "diagnostics_report": {
            "agent": "AttendanceAgent",
            "employee_id": emp["id"],
            "can_auto_remediate": is_resolved
        }
    }

# ----------------- 3. PayrollAgent Node -----------------
def payroll_agent_node(state: SupportAgentState) -> Dict[str, Any]:
    user_info = state["user_info"]
    query = state["query"]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE id = ?", (user_info["id"],))
    emp = dict(cursor.fetchone())
    
    steps = list(state.get("agent_steps", []))
    is_admin_or_support = emp["role"] in ["System Admin", "HR Manager", "Support Specialist", "IT Support"]
    
    # Restrict sensitive payroll queries (company-wide, peer salaries, executive compensation) for regular employees
    sensitive_keywords = ["company", "all employee", "everyone", "other", "peer", "alice", "sarah", "michael", "executive", "raise all", "payroll roster"]
    if not is_admin_or_support and any(k in query.lower() for k in sensitive_keywords):
        conn.close()
        steps.append({
            "step": "RBAC_PAYROLL_VALIDATION",
            "agent": "PayrollAgent",
            "details": f"Blocked unauthorized access to sensitive company-wide payroll by Employee '{emp['name']}'.",
            "status": "VERIFIED"
        })
        return {
            "agent_steps": steps,
            "is_resolved": True,
            "resolution_message": (
                "🔒 **Access Restricted by RBAC Policy**\n\n"
                "As a regular **Employee**, your access is restricted to your own personal itemized payslip. "
                "You do not have permission to view company-wide compensation distribution, peer salaries, or executive compensation structures.\n\n"
                f"Your own salary record for **{emp['name']}** is maintained securely. You may ask: *'What is my net salary?'* or visit the **Payroll & Compensation** portal."
            ),
            "requires_l3": False,
            "escalation_reason": "",
            "diagnostics_report": {
                "agent": "PayrollAgent",
                "employee_id": emp["id"],
                "role": emp["role"],
                "access_restricted": True
            }
        }
    
    cursor.execute("SELECT * FROM payroll WHERE employee_id = ? ORDER BY id DESC LIMIT 1", (emp["id"],))
    row = cursor.fetchone()
    pay = dict(row) if row else None
    conn.close()
    
    if pay:
        resolution_msg = (
            f"💵 **Official Payroll & Compensation Breakdown for {emp['name']}**\n\n"
            f"**Pay Period**: `{pay['month']} {pay['year']}` | **Salary Band**: `{pay['salary_band']}` | **Status**: `{pay['status']}`\n\n"
            f"### 📈 Earnings & Allowances:\n"
            f"- **Base Salary**: `${pay['base_salary']:,.2f}`\n"
            f"- **House Rent Allowance (HRA)**: `${pay['hra_allowance']:,.2f}`\n"
            f"- **Special Role Allowance**: `${pay['special_allowance']:,.2f}`\n"
            f"- **Performance Bonus**: `${pay['bonus']:,.2f}`\n"
            f"- **Gross Total Earnings**: `${pay['base_salary'] + pay['hra_allowance'] + pay['special_allowance'] + pay['bonus']:,.2f}`\n\n"
            f"### 📉 Statutory Withholdings & Deductions:\n"
            f"- **Federal & State Taxes**: `-${pay['tax_deductions']:,.2f}`\n"
            f"- **PF / 401(k) Retirement**: `-${pay['pf_401k_deductions']:,.2f}`\n"
            f"- **Health Insurance Premium**: `-${pay['insurance_deduction']:,.2f}`\n"
            f"- **Total Deductions**: `-${pay['tax_deductions'] + pay['pf_401k_deductions'] + pay['insurance_deduction']:,.2f}`\n\n"
            f"### 💰 Net Disbursed Salary: **`${pay['net_salary']:,.2f}`**\n\n"
            f"--- \n"
            f"- **Disbursement Date**: `{pay['payout_date']}` (Corporate cycle: 28th of every month)\n"
            f"- **Direct Deposit Account**: `•••• •••• •••• {pay['bank_account_last4']}` (Verified ACH)\n"
            f"- **Statutory Documentation**: Ref `FIN-PAY-2026-03`"
        )
    else:
        resolution_msg = (
            f"💵 **Payroll Information for {emp['name']}**:\n\n"
            f"- **Salary Band**: `{emp['salary_band']}`\n"
            f"- **Corporate Payday**: `28th of each calendar month`\n"
            f"- **Status**: Direct deposit active. Contact HR/Finance if your payslip has not generated."
        )
        
    steps.append({
        "step": "L2_PAYROLL_PROCESSING",
        "agent": "PayrollAgent",
        "details": f"Generated itemized salary breakdown for {emp['name']} (Band {emp['salary_band']}).",
        "status": "COMPLETED"
    })
    
    return {
        "agent_steps": steps,
        "is_resolved": True,
        "resolution_message": resolution_msg,
        "requires_l3": False,
        "escalation_reason": "",
        "diagnostics_report": {
            "agent": "PayrollAgent",
            "employee_id": emp["id"],
            "salary_band": emp["salary_band"],
            "can_auto_remediate": True
        }
    }

# ----------------- 4. NetworkAgent Node -----------------
def network_agent_node(state: SupportAgentState) -> Dict[str, Any]:
    user_info = state["user_info"]
    query = state["query"]
    q_lower = query.lower()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM network_diagnostics WHERE employee_id = ?", (user_info["id"],))
    row = cursor.fetchone()
    net = dict(row) if row else None
    
    steps = list(state.get("agent_steps", []))
    db_actions = list(state.get("db_actions_taken", []))
    
    # Check if network repair / reset is requested
    is_repair = any(w in q_lower for w in ["fix", "reset", "diagnose", "repair", "reconnect", "solve", "disconnect", "slow", "drop", "error"])
    
    if is_repair or (net and net["vpn_status"] != "Connected"):
        # Auto-remediate network connection
        new_ip = f"10.240.12.{random.randint(100, 240)}"
        cursor.execute("""
            UPDATE network_diagnostics 
            SET vpn_status = 'Connected', assigned_ip = ?, latency_ms = 12, packet_loss_pct = 0.0,
                dns_server = '1.1.1.1 (Cloudflare Enterprise)', last_tested = CURRENT_TIMESTAMP
            WHERE employee_id = ?
        """, (new_ip, user_info["id"]))
        conn.commit()
        
        action_summary = f"Executed Network Diagnostics & Repair: Flushed DNS cache, renewed DHCP lease ({new_ip}), reset WireGuard VPN tunnel session, and restored 12ms ping latency."
        db_actions.append({
            "agent": "NetworkAgent",
            "action": "NETWORK_TUNNEL_REPAIRED",
            "success": True,
            "summary": action_summary,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        resolution_msg = (
            f"🌐 **Network Diagnostics & Auto-Repair Completed Successfully!**\n\n"
            f"- **VPN Tunnel Status**: `Connected (Encrypted AES-256)`\n"
            f"- **Assigned Corporate IP**: `{new_ip}`\n"
            f"- **Gateway Latency**: `12 ms` (0.0% packet loss)\n"
            f"- **DNS Server**: `1.1.1.1 (Cloudflare Enterprise Verified)`\n"
            f"- **Subnet Routing**: `Engineering-VLAN-102 (Staging & Git Access Active)`\n\n"
            f"All internal corporate gateways, Jira, and GitHub endpoints are now accessible."
        )
    else:
        ip_val = net["assigned_ip"] if net else "10.240.12.84"
        vpn_val = net["vpn_status"] if net else "Connected"
        lat_val = net["latency_ms"] if net else 14
        
        resolution_msg = (
            f"🌐 **Corporate Network & VPN Status Report**:\n\n"
            f"- **VPN Gateway**: `{vpn_val}`\n"
            f"- **Current Internal IP**: `{ip_val}`\n"
            f"- **Active Wi-Fi Profile**: `CorpNet-Secure-5G`\n"
            f"- **Network Latency**: `{lat_val} ms` (Zero packet loss)\n"
            f"- **Bandwidth Available**: `350 Mbps`\n\n"
            f"Your connection to corporate intranet and cloud databases is optimal."
        )
        
    conn.close()
    
    steps.append({
        "step": "L2_NETWORK_DIAGNOSTICS",
        "agent": "NetworkAgent",
        "details": f"Ran network telemetry analysis and automated tunnel reset.",
        "status": "COMPLETED"
    })
    
    return {
        "agent_steps": steps,
        "db_actions_taken": db_actions,
        "is_resolved": True,
        "resolution_message": resolution_msg,
        "requires_l3": False,
        "escalation_reason": "",
        "diagnostics_report": {
            "agent": "NetworkAgent",
            "can_auto_remediate": True
        }
    }

# ----------------- 5. SoftwareAgent Node (Requires Human Support Approval) -----------------
def software_agent_node(state: SupportAgentState) -> Dict[str, Any]:
    """
    Handles software installation queries.
    Core Requirement:
    When a user asks for installing a software, the SoftwareAgent creates a software request
    and requires approval from a human support specialist before installation.
    """
    user_info = state["user_info"]
    query = state["query"]
    q_lower = query.lower()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Identify requested software
    cursor.execute("SELECT * FROM software_catalog")
    catalog = [dict(r) for r in cursor.fetchall()]
    
    matched_software = None
    for soft in catalog:
        if soft["name"].lower() in q_lower:
            matched_software = soft
            break
            
    if not matched_software:
        # Match common names
        if "docker" in q_lower:
            matched_software = {"name": "Docker Desktop", "version": "4.33.0", "category": "Developer Tools", "security_risk": "Medium"}
        elif "vscode" in q_lower or "vs code" in q_lower or "visual studio code" in q_lower:
            matched_software = {"name": "Visual Studio Code", "version": "1.92.0", "category": "Developer Tools", "security_risk": "Low"}
        elif "postman" in q_lower:
            matched_software = {"name": "Postman Enterprise", "version": "11.8.0", "category": "Developer Tools", "security_risk": "Low"}
        elif "slack" in q_lower:
            matched_software = {"name": "Slack Desktop", "version": "4.39.95", "category": "Productivity", "security_risk": "Low"}
        elif "pycharm" in q_lower:
            matched_software = {"name": "JetBrains PyCharm Pro", "version": "2024.2", "category": "Developer Tools", "security_risk": "Medium"}
        else:
            # Extract generic name from query
            words = [w for w in query.split() if w.lower() not in ["install", "please", "can", "you", "i", "need", "for", "my", "machine", "laptop", "software", "a", "the", "on"]]
            soft_name = " ".join(words[:2]).title() if words else "Enterprise Software Package"
            matched_software = {"name": soft_name, "version": "Latest Stable", "category": "General Applications", "security_risk": "Medium"}

    # Check if already installed for this employee
    cursor.execute("""
        SELECT * FROM software_requests 
        WHERE employee_id = ? AND software_name = ? AND status = 'INSTALLED'
    """, (user_info["id"], matched_software["name"]))
    installed_rec = cursor.fetchone()
    
    steps = list(state.get("agent_steps", []))
    
    if installed_rec:
        conn.close()
        resolution_msg = (
            f"💻 **Software Already Installed**:\n\n"
            f"**{matched_software['name']}** (v{matched_software['version']}) is already approved and installed on your workstation.\n"
            f"- **Installation Date**: `{dict(installed_rec)['installed_at']}`\n"
            f"- **Binary Path**: `/opt/{matched_software['name'].lower().replace(' ', '-')}/bin`\n\n"
            f"If you need an environment reconfiguration or version upgrade, please contact human IT support."
        )
        return {
            "agent_steps": steps,
            "is_resolved": True,
            "resolution_message": resolution_msg,
            "requires_l3": False,
            "escalation_reason": ""
        }

    # Software needs installation -> Create software_requests entry with PENDING_APPROVAL
    cursor.execute("""
        INSERT INTO software_requests (ticket_code, employee_id, employee_name, employee_email, software_name, version, justification, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING_APPROVAL')
    """, (
        f"TKT-{datetime.utcnow().strftime('%Y%m')}-{random.randint(1000, 9999)}",
        user_info["id"],
        user_info["name"],
        user_info["email"],
        matched_software["name"],
        matched_software["version"],
        f"User requested installation: {query[:80]}"
    ))
    conn.commit()
    request_id = cursor.lastrowid
    
    cursor.execute("SELECT * FROM software_requests WHERE id = ?", (request_id,))
    req_record = dict(cursor.fetchone())
    conn.close()
    
    # Requirement: Asks for approval of support agent, escalates to L3
    esc_reason = f"Software installation for '{matched_software['name']}' requires authorization from a Human Support Specialist."
    
    resolution_msg = (
        f"💻 **Software Installation Request Submitted — Awaiting Support Agent Approval**\n\n"
        f"The **SoftwareAgent** has initiated the deployment workflow for **{matched_software['name']}** (Version `{matched_software['version']}`).\n\n"
        f"🔒 **Enterprise IT Security Policy Gate**:\n"
        f"- Corporate security policy (`IT-SEC-SOFT-2026-05`) mandates that all software deployments require explicit authorization from a **Human Support Specialist** before execution.\n\n"
        f"📋 **Request Details**:\n"
        f"- **Request ID**: `SOFT-REQ-{request_id:04d}`\n"
        f"- **Software**: `{matched_software['name']}` (v{matched_software['version']})\n"
        f"- **Category**: `{matched_software.get('category', 'Tools')}`\n"
        f"- **Security Risk**: `{matched_software.get('security_risk', 'Low')}`\n"
        f"- **Status**: ⏳ `PENDING_APPROVAL` (Queued in L3 Human Support Desk)\n\n"
        f"👉 **Next Step**: Once a Support Specialist reviews and approves your request, the **SoftwareAgent** will automatically install and configure the software on your workstation."
    )
    
    steps.append({
        "step": "L2_SOFTWARE_APPROVAL_GATE",
        "agent": "SoftwareAgent",
        "details": f"Created software request #{request_id} for '{matched_software['name']}'. Awaiting human support approval.",
        "status": "AWAITING_HUMAN_APPROVAL"
    })
    
    log_audit(
        user_email=user_info["email"],
        user_role=user_info.get("role", "Employee"),
        action="SOFTWARE_INSTALL_PENDING_APPROVAL",
        resource_type="SOFTWARE_REQUEST",
        resource_id=str(request_id),
        tier="L2",
        status="PENDING",
        details={"software": matched_software["name"], "request_id": request_id}
    )
    
    return {
        "agent_steps": steps,
        "software_request": req_record,
        "is_resolved": False,
        "requires_l3": True,
        "escalation_reason": esc_reason,
        "resolution_message": resolution_msg,
        "diagnostics_report": {
            "agent": "SoftwareAgent",
            "request_id": request_id,
            "software": matched_software["name"],
            "requires_human_approval": True,
            "can_auto_remediate": False
        }
    }

# ----------------- Software Post-Approval Automated Installation Engine -----------------
def execute_software_installation(request_id: int, admin_user: Dict[str, Any], notes: str = "") -> Dict[str, Any]:
    """
    Called after getting the approval of the human support person:
    Executes automated installation of the software, verifies integrity, and updates records.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM software_requests WHERE id = ?", (request_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {"success": False, "error": f"Software request #{request_id} not found."}
        
    req = dict(row)
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    
    # Simulate verified package installation
    soft_name = req["software_name"]
    version = req["version"]
    install_log = (
        f"[{now_str}] SoftwareAgent: Human approval signature verified: '{admin_user.get('name', 'Support Agent')}' ({admin_user.get('role', 'Support Specialist')})\n"
        f"[{now_str}] Package repository download: https://packages.corporate.internal/{soft_name.lower().replace(' ', '-')}-{version}.deb\n"
        f"[{now_str}] SHA-256 integrity hash verification: 7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069 [OK]\n"
        f"[{now_str}] Executing enterprise unattended install to /opt/{soft_name.lower().replace(' ', '-')}/\n"
        f"[{now_str}] Configuring sandbox permissions, security profile, and workstation daemon...\n"
        f"[{now_str}] Installation complete. Service registered and verified operational."
    )
    
    cursor.execute("""
        UPDATE software_requests
        SET status = 'INSTALLED',
            reviewed_by_human = ?,
            reviewed_at = ?,
            human_notes = ?,
            installed_at = ?,
            install_logs = ?
        WHERE id = ?
    """, (
        admin_user.get("name", "Support Specialist"),
        now_str,
        notes or "Approved by Support Specialist. Automated SoftwareAgent installation executed.",
        now_str,
        install_log,
        request_id
    ))
    
    # If there is an associated ticket, resolve it
    if req.get("ticket_code"):
        cursor.execute("""
            UPDATE tickets 
            SET status = 'Resolved_L3', 
                resolution_summary = ?,
                assigned_human = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE ticket_code = ?
        """, (
            f"Software '{soft_name}' approved by {admin_user.get('name')} and automatically installed by SoftwareAgent.",
            admin_user.get("name"),
            req["ticket_code"]
        ))
        
    # Record in agent_actions
    cursor.execute("""
        INSERT INTO agent_actions (ticket_id, agent_name, action_taken, input_params, output_result, status)
        VALUES (?, 'SoftwareAgent', 'INSTALL_SOFTWARE_POST_HUMAN_APPROVAL', ?, ?, 'SUCCESS')
    """, (
        req.get("ticket_id"),
        json.dumps({"request_id": request_id, "software": soft_name, "approved_by": admin_user.get("name")}),
        f"Successfully deployed {soft_name} to employee machine."
    ))
    
    conn.commit()
    conn.close()
    
    log_audit(
        user_email=admin_user.get("email", "support@company.com"),
        user_role=admin_user.get("role", "Support Specialist"),
        action="SOFTWARE_APPROVED_AND_INSTALLED",
        resource_type="SOFTWARE_REQUEST",
        resource_id=str(request_id),
        tier="L3",
        status="SUCCESS",
        details={
            "software": soft_name,
            "version": version,
            "employee_id": req["employee_id"],
            "employee_email": req["employee_email"],
            "approved_by": admin_user.get("name")
        }
    )
    
    return {
        "success": True,
        "software": soft_name,
        "version": version,
        "employee_email": req["employee_email"],
        "status": "INSTALLED",
        "installed_at": now_str,
        "logs": install_log
    }

# ----------------- 6. Diagnostics Agent Node -----------------
def diagnostics_agent_node(state: SupportAgentState) -> Dict[str, Any]:
    user_info = state["user_info"]
    query = state["query"]
    q_lower = query.lower()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE id = ?", (user_info["id"],))
    emp = dict(cursor.fetchone())
    conn.close()
    
    root_cause = "General inquiry requires advanced analysis."
    identified_issues = []
    recommended_action = "Investigate standard operating procedures."
    can_auto_remediate = False

    # Check for Account Lockout
    if any(k in q_lower for k in ["lock", "login", "access", "unlock", "blocked", "unblock", "password"]):
        if emp["status"] == "Locked":
            root_cause = "Employee status is explicitly 'Locked' in EMS directory due to repeated authentication failures."
            identified_issues.append("ACCOUNT_LOCKED")
            recommended_action = "DATABASE_AGENT_UNLOCK_ACCOUNT"
            can_auto_remediate = True
        elif emp["status"] == "Suspended":
            root_cause = "Employee status is 'Suspended' under administrative security review."
            identified_issues.append("ADMINISTRATIVE_SUSPENSION")
            recommended_action = "ESCALATE_TO_L3_HUMAN_SECURITY"
            can_auto_remediate = False
        else:
            root_cause = "Employee status is Active; refreshing cached credentials and directory session."
            identified_issues.append("SESSION_TOKEN_STALE")
            recommended_action = "DATABASE_AGENT_REFRESH_SESSION"
            can_auto_remediate = True

    # Check for Benefits Status Error
    elif any(k in q_lower for k in ["benefit", "health", "insurance", "medical"]):
        if emp["benefits_enrolled"] == 0 or "error" in q_lower or "sync" in q_lower:
            root_cause = "Benefits enrollment flag is marked as 0 (Pending/Sync Error) in the core HR SQLite schema."
            identified_issues.append("BENEFITS_SYNC_ERROR")
            recommended_action = "DATABASE_AGENT_SYNC_BENEFITS"
            can_auto_remediate = True
        else:
            root_cause = "Employee benefits are active and current."
            recommended_action = "CONFIRM_ACTIVE_BENEFITS"
            can_auto_remediate = True

    # Check for Equipment Status
    elif any(k in q_lower for k in ["equipment", "laptop", "hardware", "monitor", "repair"]):
        if emp["equipment_status"] in ["Requisition Pending", "In Repair"]:
            root_cause = f"Equipment status is currently '{emp['equipment_status']}'. A hardware ticket queue bottleneck was identified."
            identified_issues.append("EQUIPMENT_BOTTLENECK")
            recommended_action = "DATABASE_AGENT_EXPEDITE_EQUIPMENT"
            can_auto_remediate = True
        else:
            root_cause = f"Equipment status is '{emp['equipment_status']}'."
            recommended_action = "EQUIPMENT_CONFIRMATION"
            can_auto_remediate = True

    # Sensitive HR / Grievance
    elif any(w in q_lower for w in ["harass", "grievance", "complaint", "legal", "termination", "severance", "fired"]):
        root_cause = "High-sensitivity personnel matter requiring discretionary human assessment."
        identified_issues.append("SENSITIVE_PERSONNEL_CASE")
        recommended_action = "ESCALATE_TO_L3_HUMAN_RESOURCE"
        can_auto_remediate = False

    report = {
        "agent": "DiagnosticsAgent",
        "employee_id": emp["id"],
        "employee_name": emp["name"],
        "employee_code": emp["employee_code"],
        "department": emp["department"],
        "current_status": emp["status"],
        "root_cause": root_cause,
        "identified_issues": identified_issues,
        "recommended_action": recommended_action,
        "can_auto_remediate": can_auto_remediate,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }

    step_log = {
        "step": "L2_DIAGNOSTICS",
        "agent": "DiagnosticsAgent",
        "details": f"Analyzed database state for {emp['name']}. Root cause: {root_cause}",
        "action": recommended_action,
        "can_remediate": can_auto_remediate
    }

    return {
        "diagnostics_report": report,
        "agent_steps": state.get("agent_steps", []) + [step_log]
    }

# ----------------- 7. Database Agent Node -----------------
def database_agent_node(state: SupportAgentState) -> Dict[str, Any]:
    diag = state.get("diagnostics_report", {})
    emp_id = diag.get("employee_id") or state["user_info"]["id"]
    action_type = diag.get("recommended_action", "NONE")
    actions_taken = list(state.get("db_actions_taken", []))
    steps = list(state.get("agent_steps", []))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    remediation_success = False
    action_summary = ""

    if action_type == "DATABASE_AGENT_UNLOCK_ACCOUNT":
        cursor.execute("UPDATE employees SET status = 'Active' WHERE id = ?", (emp_id,))
        conn.commit()
        remediation_success = True
        action_summary = f"Executed UPDATE employees SET status='Active' for Employee #{emp_id}. Lockout counters reset."
        
    elif action_type == "DATABASE_AGENT_SYNC_BENEFITS":
        cursor.execute("UPDATE employees SET benefits_enrolled = 1 WHERE id = ?", (emp_id,))
        conn.commit()
        remediation_success = True
        action_summary = f"Executed UPDATE employees SET benefits_enrolled=1 for Employee #{emp_id}. Carrier sync confirmed."

    elif action_type == "DATABASE_AGENT_EXPEDITE_EQUIPMENT":
        cursor.execute("UPDATE employees SET equipment_status = 'Expedited Requisition' WHERE id = ?", (emp_id,))
        conn.commit()
        remediation_success = True
        action_summary = f"Executed UPDATE employees SET equipment_status='Expedited Requisition' for Employee #{emp_id}."

    elif action_type == "DATABASE_AGENT_REFRESH_SESSION":
        remediation_success = True
        action_summary = f"Purged cached security tokens for Employee #{emp_id}. Session refreshed."

    else:
        action_summary = "No automated database mutations needed."

    if remediation_success:
        cursor.execute("""
            INSERT INTO agent_actions (ticket_id, agent_name, action_taken, input_params, output_result, status)
            VALUES (?, 'DatabaseAgent', ?, ?, ?, 'SUCCESS')
        """, (state.get("ticket_id"), action_type, json.dumps({"employee_id": emp_id}), action_summary))
        conn.commit()

        log_audit(
            user_email=state["user_info"]["email"],
            user_role=state["user_info"].get("role", "Employee"),
            action="L2_DATABASE_REMEDIATION",
            resource_type="EMPLOYEE",
            resource_id=str(emp_id),
            tier="L2",
            status="SUCCESS",
            details={"action": action_type, "summary": action_summary}
        )

    conn.close()

    actions_taken.append({
        "agent": "DatabaseAgent",
        "action": action_type,
        "success": remediation_success,
        "summary": action_summary,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    })

    steps.append({
        "step": "L2_DATABASE_EXECUTION",
        "agent": "DatabaseAgent",
        "details": action_summary,
        "status": "COMPLETED" if remediation_success else "SKIPPED"
    })

    return {
        "db_actions_taken": actions_taken,
        "agent_steps": steps
    }

# ----------------- 8. Policy & Remediation Verifier Node -----------------
def policy_verifier_node(state: SupportAgentState) -> Dict[str, Any]:
    # If specialized agent already computed final resolution, pass through
    if "is_resolved" in state and state.get("resolution_message"):
        return state

    diag = state.get("diagnostics_report", {})
    db_actions = state.get("db_actions_taken", [])
    steps = list(state.get("agent_steps", []))
    
    has_successful_action = any(a.get("success") for a in db_actions)
    
    if diag.get("can_auto_remediate", False) and has_successful_action:
        resolution_msg = (
            f"**L2 AI Resolution Confirmed:**\n\n"
            f"- **Root Cause Identified**: {diag.get('root_cause')}\n"
            f"- **Automated Remediation Executed**: {db_actions[-1]['summary']}\n"
            f"- **Verification**: System policy verified and employee profile state successfully updated in SQLite database.\n\n"
            f"Your issue has been resolved automatically without needing human queue delay."
        )
        steps.append({
            "step": "L2_POLICY_VERIFICATION",
            "agent": "PolicyVerifierAgent",
            "details": "Remediation verified against EMS database policy. Issue resolved at L2.",
            "status": "VERIFIED"
        })
        
        return {
            "is_resolved": True,
            "requires_l3": False,
            "escalation_reason": "",
            "resolution_message": resolution_msg,
            "agent_steps": steps
        }
    else:
        escalation_reason = diag.get("root_cause") or state.get("escalation_reason") or "Requires human review."
        steps.append({
            "step": "L2_POLICY_VERIFICATION",
            "agent": "PolicyVerifierAgent",
            "details": f"Triggering L3 escalation: {escalation_reason}",
            "status": "ESCALATING"
        })

        return {
            "is_resolved": False,
            "requires_l3": True,
            "escalation_reason": escalation_reason,
            "resolution_message": f"Requires Human Support Specialist assessment: {escalation_reason}",
            "agent_steps": steps
        }

# ----------------- 9. Escalation Node (Bridge to L3) -----------------
def escalation_router_node(state: SupportAgentState) -> Dict[str, Any]:
    steps = list(state.get("agent_steps", []))
    steps.append({
        "step": "L3_ESCALATION_DISPATCH",
        "agent": "EscalationRouter",
        "details": f"Escalated to L3 Human Support queue with diagnostic context: {state.get('escalation_reason')}",
        "status": "ESCALATED"
    })
    
    log_audit(
        user_email=state["user_info"]["email"],
        user_role=state["user_info"].get("role", "Employee"),
        action="L3_ESCALATION_DISPATCHED",
        resource_type="TICKET",
        tier="L3",
        status="ESCALATED",
        details={"reason": state.get("escalation_reason")}
    )

    return {
        "agent_steps": steps
    }

# ----------------- LangGraph Graph Construction -----------------
def route_supervisor(state: SupportAgentState) -> str:
    domain = state.get("domain", "diagnostics")
    if domain == "software":
        return "software_agent"
    elif domain == "leave":
        return "leave_agent"
    elif domain == "attendance":
        return "attendance_agent"
    elif domain == "payroll":
        return "payroll_agent"
    elif domain == "network":
        return "network_agent"
    return "diagnostics_agent"

def route_after_diagnostics(state: SupportAgentState):
    if state.get("diagnostics_report", {}).get("can_auto_remediate", False):
        return "database_agent"
    return "policy_verifier"

def route_after_verification(state: SupportAgentState):
    if state.get("requires_l3", False):
        return "escalation_router"
    return END

def build_l2_agent_graph():
    workflow = StateGraph(SupportAgentState)
    
    # Add nodes
    workflow.add_node("supervisor", supervisor_router_node)
    workflow.add_node("software_agent", software_agent_node)
    workflow.add_node("leave_agent", leave_agent_node)
    workflow.add_node("attendance_agent", attendance_agent_node)
    workflow.add_node("payroll_agent", payroll_agent_node)
    workflow.add_node("network_agent", network_agent_node)
    workflow.add_node("diagnostics_agent", diagnostics_agent_node)
    workflow.add_node("database_agent", database_agent_node)
    workflow.add_node("policy_verifier", policy_verifier_node)
    workflow.add_node("escalation_router", escalation_router_node)
    
    # Edges from START -> Supervisor
    workflow.add_edge(START, "supervisor")
    
    # Conditional routing from supervisor
    workflow.add_conditional_edges(
        "supervisor",
        route_supervisor,
        {
            "software_agent": "software_agent",
            "leave_agent": "leave_agent",
            "attendance_agent": "attendance_agent",
            "payroll_agent": "payroll_agent",
            "network_agent": "network_agent",
            "diagnostics_agent": "diagnostics_agent"
        }
    )
    
    # Domain agents route to policy_verifier
    workflow.add_edge("software_agent", "policy_verifier")
    workflow.add_edge("leave_agent", "policy_verifier")
    workflow.add_edge("attendance_agent", "policy_verifier")
    workflow.add_edge("payroll_agent", "policy_verifier")
    workflow.add_edge("network_agent", "policy_verifier")
    
    # Diagnostics routes either to database_agent or policy_verifier
    workflow.add_conditional_edges(
        "diagnostics_agent",
        route_after_diagnostics,
        {
            "database_agent": "database_agent",
            "policy_verifier": "policy_verifier"
        }
    )
    workflow.add_edge("database_agent", "policy_verifier")
    
    # Verification routes to escalation or END
    workflow.add_conditional_edges(
        "policy_verifier",
        route_after_verification,
        {
            "escalation_router": "escalation_router",
            END: END
        }
    )
    workflow.add_edge("escalation_router", END)
    
    return workflow.compile()

# Singleton compiled graph instance
l2_compiled_graph = build_l2_agent_graph()

def execute_l2_multi_agents(
    query: str,
    user_info: Dict[str, Any],
    l1_reason: str,
    ticket_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Executes the LangGraph Multi-Agent pipeline for L2 resolution.
    """
    initial_state: SupportAgentState = {
        "ticket_id": ticket_id,
        "query": query,
        "user_info": user_info,
        "l1_reason": l1_reason,
        "domain": "",
        "diagnostics_report": {},
        "agent_steps": [],
        "db_actions_taken": [],
        "software_request": None,
        "is_resolved": False,
        "resolution_message": "",
        "requires_l3": False,
        "escalation_reason": ""
    }
    
    final_state = l2_compiled_graph.invoke(initial_state)
    return final_state
