"""
Python Type Definitions and Data Models
Converted from TypeScript interfaces to Python dataclasses and Pydantic-compatible types.
"""
from typing import Literal, Optional, List, Dict, Any
from dataclasses import dataclass, field

Role = Literal['Employee', 'HR Manager', 'IT Support', 'Support Specialist', 'System Admin', 'Team Lead']

@dataclass
class Employee:
    id: int
    name: str
    email: str
    department: str
    role: Role
    status: Literal['Active', 'Locked', 'Suspended']
    leave_balance: int
    benefits_enrolled: bool
    equipment_status: str
    sick_leave_balance: int = 10

@dataclass
class KnowledgeArticle:
    id: int
    category: str
    title: str
    content: str
    keywords: str
    source_doc: str
    updated_at: str

@dataclass
class AgentStep:
    step: str
    agent: str
    details: str
    status: Literal['COMPLETED', 'VERIFIED', 'ESCALATING', 'ESCALATED', 'SKIPPED']

@dataclass
class DbAction:
    agent: str
    action: str
    success: bool
    summary: str
    timestamp: str

@dataclass
class Ticket:
    id: int
    ticket_code: str
    user_id: int
    user_email: str
    user_name: str
    query: str
    current_tier: Literal['L1', 'L2', 'L3']
    status: Literal['Resolved_L1', 'Resolved_L2', 'Escalated_L3', 'In_Progress', 'Resolved_L3', 'Closed']
    assigned_human: Optional[str] = None
    resolution_notes: Optional[str] = None
    diagnostics_json: Optional[str] = None
    created_at: str = ""
    resolved_at: Optional[str] = None

@dataclass
class AuditLog:
    id: int
    timestamp: str
    user_email: str
    user_role: str
    action: str
    resource_type: str
    tier: Literal['L1', 'L2', 'L3', 'System', 'Auth']
    status: Literal['SUCCESS', 'ESCALATED', 'FAILED']
    details: str
    ip_address: str
    resource_id: Optional[str] = None

@dataclass
class LeaveRecord:
    id: int
    employee_id: int
    leave_type: Literal['PTO', 'Sick', 'Casual', 'Parental']
    start_date: str
    end_date: str
    days_requested: int
    status: Literal['APPROVED', 'PENDING', 'REJECTED']
    approved_by: str
    reason: str
    created_at: str

@dataclass
class AttendanceRecord:
    id: int
    employee_id: int
    date: str
    clock_in: str
    clock_out: str
    total_hours: float
    status: Literal['Present', 'Late', 'Half_Day', 'Absent', 'Missed_Punch']
    regularized: int = 0
    regularization_reason: Optional[str] = None

@dataclass
class PayrollRecord:
    id: int
    employee_id: int
    month: str
    year: int
    base_salary: float
    hra_allowance: float
    special_allowance: float
    bonus: float
    tax_deductions: float
    pf_401k_deductions: float
    insurance_deduction: float
    net_salary: float
    status: Literal['Disbursed', 'Pending']
    payout_date: str
    salary_band: str
    bank_account_last4: str

@dataclass
class SoftwareRequestRecord:
    id: int
    employee_id: int
    software_name: str
    version: str
    justification: str
    status: Literal['PENDING_APPROVAL', 'INSTALLED', 'REJECTED']
    requested_at: str
    ticket_id: Optional[int] = None
    reviewed_by_human: Optional[str] = None
    installed_at: Optional[str] = None
    install_logs: Optional[str] = None

@dataclass
class SupportQueryResponse:
    final_tier: Literal['L1', 'L2', 'L3']
    is_resolved: bool
    status: str
    message: str
    ticket: Optional[Ticket] = None
    trace: Dict[str, Any] = field(default_factory=dict)
