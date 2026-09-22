"""
API Client for communicating with the FastAPI backend.
"""
import requests
from typing import Dict, Any, List, Optional

BACKEND_URL = "http://127.0.0.1:8001"

def get_health() -> Dict[str, Any]:
    try:
        r = requests.get(f"{BACKEND_URL}/api/health", timeout=3)
        return r.json() if r.status_code == 200 else {"status": "offline"}
    except Exception as e:
        return {"status": "offline", "error": str(e)}

def get_roles() -> Dict[str, Any]:
    try:
        r = requests.get(f"{BACKEND_URL}/api/roles", timeout=4)
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}

def get_users() -> List[Dict[str, Any]]:
    try:
        r = requests.get(f"{BACKEND_URL}/api/users", timeout=4)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []

def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    try:
        r = requests.get(f"{BACKEND_URL}/api/users/{user_id}", timeout=4)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None

def update_user(user_id: int, admin_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
    try:
        payload = {"admin_id": admin_id, **updates}
        r = requests.patch(f"{BACKEND_URL}/api/users/{user_id}", json=payload, timeout=5)
        if r.status_code == 200:
            return {"success": True, "data": r.json()}
        return {"success": False, "error": r.json().get("detail", "Error updating employee")}
    except Exception as e:
        return {"success": False, "error": str(e)}

def submit_support_query(user_id: int, query: str) -> Dict[str, Any]:
    try:
        r = requests.post(f"{BACKEND_URL}/api/support/query", json={"user_id": user_id, "query": query}, timeout=20)
        if r.status_code == 200:
            return r.json()
        return {"final_tier": "Error", "is_resolved": False, "message": r.json().get("detail", "Failed to process query")}
    except Exception as e:
        return {"final_tier": "Error", "is_resolved": False, "message": f"Connection error: {str(e)}"}

def get_tickets(user_id: Optional[int] = None, tier: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
    try:
        params = {}
        if user_id:
            params["user_id"] = user_id
        if tier and tier != "ALL":
            params["tier"] = tier
        if status and status != "ALL":
            params["status"] = status
        r = requests.get(f"{BACKEND_URL}/api/tickets", params=params, timeout=5)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []

def get_ticket_detail(ticket_id: int) -> Optional[Dict[str, Any]]:
    try:
        r = requests.get(f"{BACKEND_URL}/api/tickets/{ticket_id}", timeout=4)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None

def assign_ticket(ticket_id: int, admin_id: int, assigned_human: str) -> Dict[str, Any]:
    try:
        r = requests.post(
            f"{BACKEND_URL}/api/tickets/{ticket_id}/assign",
            json={"admin_id": admin_id, "assigned_human": assigned_human},
            timeout=5
        )
        return {"success": r.status_code == 200, "data": r.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}

def resolve_ticket(ticket_id: int, admin_id: int, notes: str, status: str = "Closed") -> Dict[str, Any]:
    try:
        r = requests.post(
            f"{BACKEND_URL}/api/tickets/{ticket_id}/resolve",
            json={"admin_id": admin_id, "resolution_notes": notes, "status": status},
            timeout=5
        )
        return {"success": r.status_code == 200, "data": r.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_knowledge_base() -> List[Dict[str, Any]]:
    try:
        r = requests.get(f"{BACKEND_URL}/api/knowledge-base", timeout=4)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []

def add_kb_article(admin_id: int, article: Dict[str, Any]) -> Dict[str, Any]:
    try:
        payload = {"admin_id": admin_id, **article}
        r = requests.post(f"{BACKEND_URL}/api/knowledge-base", json=payload, timeout=5)
        return {"success": r.status_code == 200, "data": r.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_audit_logs(user_id: Optional[int] = None, tier: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    try:
        params = {"limit": limit}
        if user_id:
            params["user_id"] = user_id
        if tier and tier != "ALL":
            params["tier"] = tier
        r = requests.get(f"{BACKEND_URL}/api/audit-logs", params=params, timeout=5)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []

def get_stats() -> Dict[str, Any]:
    try:
        r = requests.get(f"{BACKEND_URL}/api/stats", timeout=4)
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}

# ----------------- Leaves API -----------------
def get_leaves(employee_id: Optional[int] = None) -> List[Dict[str, Any]]:
    try:
        params = {"employee_id": employee_id} if employee_id else {}
        r = requests.get(f"{BACKEND_URL}/api/leaves", params=params, timeout=5)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []

def apply_leave(employee_id: int, leave_type: str, start_date: str, end_date: str, days_requested: int, reason: str) -> Dict[str, Any]:
    try:
        payload = {
            "employee_id": employee_id,
            "leave_type": leave_type,
            "start_date": start_date,
            "end_date": end_date,
            "days_requested": days_requested,
            "reason": reason
        }
        r = requests.post(f"{BACKEND_URL}/api/leaves/apply", json=payload, timeout=5)
        return {"success": r.status_code == 200, "data": r.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ----------------- Attendance API -----------------
def get_attendance(employee_id: Optional[int] = None) -> List[Dict[str, Any]]:
    try:
        params = {"employee_id": employee_id} if employee_id else {}
        r = requests.get(f"{BACKEND_URL}/api/attendance", params=params, timeout=5)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []

def regularize_attendance(employee_id: int, attendance_id: int, reason: str) -> Dict[str, Any]:
    try:
        payload = {"employee_id": employee_id, "attendance_id": attendance_id, "reason": reason}
        r = requests.post(f"{BACKEND_URL}/api/attendance/regularize", json=payload, timeout=5)
        return {"success": r.status_code == 200, "data": r.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ----------------- Payroll API -----------------
def get_payroll(employee_id: Optional[int] = None, requesting_user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    try:
        params = {}
        if employee_id:
            params["employee_id"] = employee_id
        if requesting_user_id:
            params["requesting_user_id"] = requesting_user_id
        r = requests.get(f"{BACKEND_URL}/api/payroll", params=params, timeout=5)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []

# ----------------- Network Diagnostics API -----------------
def get_network_diagnostics(employee_id: Optional[int] = None) -> Any:
    try:
        params = {"employee_id": employee_id} if employee_id else {}
        r = requests.get(f"{BACKEND_URL}/api/network-diagnostics", params=params, timeout=5)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None

def test_and_repair_network(employee_id: int) -> Dict[str, Any]:
    try:
        r = requests.post(f"{BACKEND_URL}/api/network-diagnostics/test", json={"employee_id": employee_id}, timeout=5)
        return {"success": r.status_code == 200, "data": r.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ----------------- Software Management & Approval API -----------------
def get_software_catalog() -> List[Dict[str, Any]]:
    try:
        r = requests.get(f"{BACKEND_URL}/api/software/catalog", timeout=4)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []

def get_software_requests(employee_id: Optional[int] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
    try:
        params = {}
        if employee_id:
            params["employee_id"] = employee_id
        if status and status != "ALL":
            params["status"] = status
        r = requests.get(f"{BACKEND_URL}/api/software/requests", params=params, timeout=5)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []

def submit_software_request(employee_id: int, software_name: str, version: Optional[str] = None, justification: str = "") -> Dict[str, Any]:
    try:
        payload = {
            "employee_id": employee_id,
            "software_name": software_name,
            "version": version,
            "justification": justification
        }
        r = requests.post(f"{BACKEND_URL}/api/software/requests", json=payload, timeout=5)
        return {"success": r.status_code == 200, "data": r.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}

def approve_and_install_software(request_id: int, admin_id: int, notes: str = "") -> Dict[str, Any]:
    try:
        payload = {"admin_id": admin_id, "notes": notes}
        r = requests.post(f"{BACKEND_URL}/api/software/requests/{request_id}/approve-and-install", json=payload, timeout=8)
        return {"success": r.status_code == 200, "data": r.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}

