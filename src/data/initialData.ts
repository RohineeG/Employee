import { Employee, KnowledgeArticle, SupportTicket, AuditLog } from '../types';

export const INITIAL_EMPLOYEES: Employee[] = [
  {
    id: 1,
    employeeCode: 'EMP001',
    name: 'Alex Morgan',
    email: 'alex.morgan@company.com',
    role: 'Employee',
    department: 'Engineering',
    jobTitle: 'Software Engineer',
    status: 'Active',
    leaveBalance: 18,
    sickLeaveBalance: 10,
    managerId: null,
    benefitsEnrolled: true,
    equipmentStatus: 'Delivered',
    salaryBand: 'L4'
  },
  {
    id: 2,
    employeeCode: 'EMP002',
    name: 'Sarah Connor',
    email: 'sarah.connor@company.com',
    role: 'Employee',
    department: 'DevOps',
    jobTitle: 'Infrastructure Engineer',
    status: 'Locked',
    leaveBalance: 15,
    sickLeaveBalance: 8,
    managerId: 1,
    benefitsEnrolled: true,
    equipmentStatus: 'Delivered',
    salaryBand: 'L5'
  },
  {
    id: 3,
    employeeCode: 'EMP003',
    name: 'Michael Scott',
    email: 'michael.scott@company.com',
    role: 'Team Lead',
    department: 'Sales',
    jobTitle: 'Regional Sales Manager',
    status: 'Active',
    leaveBalance: 5,
    sickLeaveBalance: 4,
    managerId: null,
    benefitsEnrolled: true,
    equipmentStatus: 'Delivered',
    salaryBand: 'L6'
  },
  {
    id: 4,
    employeeCode: 'EMP004',
    name: 'David Miller',
    email: 'david.miller@company.com',
    role: 'Employee',
    department: 'Marketing',
    jobTitle: 'Growth Analyst',
    status: 'Active',
    leaveBalance: 22,
    sickLeaveBalance: 10,
    managerId: 3,
    benefitsEnrolled: false,
    equipmentStatus: 'Requisition Pending',
    salaryBand: 'L3'
  },
  {
    id: 5,
    employeeCode: 'EMP005',
    name: 'Priya Sharma',
    email: 'priya.sharma@company.com',
    role: 'Employee',
    department: 'Product',
    jobTitle: 'UI/UX Designer',
    status: 'Active',
    leaveBalance: 12,
    sickLeaveBalance: 9,
    managerId: 1,
    benefitsEnrolled: true,
    equipmentStatus: 'In Repair',
    salaryBand: 'L4'
  },
  {
    id: 6,
    employeeCode: 'EMP006',
    name: 'Rachel Green',
    email: 'rachel.green@company.com',
    role: 'HR Manager',
    department: 'Human Resources',
    jobTitle: 'People Operations Director',
    status: 'Active',
    leaveBalance: 25,
    sickLeaveBalance: 12,
    managerId: null,
    benefitsEnrolled: true,
    equipmentStatus: 'Delivered',
    salaryBand: 'L7'
  },
  {
    id: 7,
    employeeCode: 'EMP007',
    name: 'Alice Vance',
    email: 'alice.vance@company.com',
    role: 'System Admin',
    department: 'IT Security',
    jobTitle: 'Principal Security Admin',
    status: 'Active',
    leaveBalance: 20,
    sickLeaveBalance: 10,
    managerId: null,
    benefitsEnrolled: true,
    equipmentStatus: 'Delivered',
    salaryBand: 'L6'
  },
  {
    id: 8,
    employeeCode: 'EMP008',
    name: 'Sam Carter',
    email: 'sam.carter@company.com',
    role: 'Support Specialist',
    department: 'Technical Support',
    jobTitle: 'L3 Operations Lead',
    status: 'Active',
    leaveBalance: 20,
    sickLeaveBalance: 10,
    managerId: null,
    benefitsEnrolled: true,
    equipmentStatus: 'Delivered',
    salaryBand: 'L5'
  }
];

export const INITIAL_KNOWLEDGE_BASE: KnowledgeArticle[] = [
  {
    id: 1,
    category: 'Leave & Time Off',
    title: 'Annual Paid Time Off (PTO) Policy & Carryover Rules',
    content: 'Full-time employees receive 20 days of paid time off per calendar year accrued monthly. Up to 5 unused PTO days can be carried forward into the first quarter of the following year. Leave requests exceeding 3 consecutive business days require advance manager approval via the EMS portal. Sick leave is tracked separately (10 days/year) and does not require advance notice but must be logged within 48 hours.',
    keywords: ['pto', 'annual leave', 'carryover', 'sick days', 'vacation', 'time off', 'holiday'],
    sourceDoc: 'HR-POL-2024-01',
    updatedAt: '2024-01-15'
  },
  {
    id: 2,
    category: 'IT Access & Credentials',
    title: 'Account Lockout & Multi-Factor Authentication (MFA) Reset Policy',
    content: 'Corporate domain and VPN accounts automatically lock after 5 consecutive failed login attempts to prevent brute-force intrusion. Locked accounts can be diagnosed and programmatically unlocked by the L2 IT Database Agent if no security incident is flagged, or through IT Helpdesk verification. MFA token resets require authorization from System Administration or Identity Management.',
    keywords: ['locked account', 'unlock', 'password', 'mfa', 'vpn', 'credentials', 'login failed', 'access denied'],
    sourceDoc: 'SEC-SOP-04',
    updatedAt: '2024-02-01'
  },
  {
    id: 3,
    category: 'Healthcare & Benefits',
    title: 'Health, Dental, and Life Insurance Enrollment Guidelines',
    content: 'New hires have 30 days from their start date to complete benefits enrollment in the EMS portal. Existing employees may alter their plan during the annual Open Enrollment period in November or following a Qualifying Life Event (marriage, child birth, relocation). If your benefits status displays as "Pending" or "Error" despite enrollment, the L2 Database Agent can synchronize records with the benefits carrier.',
    keywords: ['benefits', 'health insurance', 'medical', 'dental', 'enrollment', 'open enrollment', 'coverage', 'dependent'],
    sourceDoc: 'HR-BEN-2024-03',
    updatedAt: '2024-03-10'
  },
  {
    id: 4,
    category: 'Equipment & Workplace',
    title: 'Standard Equipment Requisition & Hardware Refresh',
    content: 'All engineering and design personnel are eligible for standard workstation hardware (MacBook Pro 16" or Dell XPS 15, plus dual 27" 4K monitors and noise-cancelling headset). Hardware refresh cycles occur every 36 months. If equipment status is "Requisition Pending" or "In Repair", loaner equipment can be requested through the IT hardware depot.',
    keywords: ['laptop', 'equipment', 'hardware', 'monitor', 'macbook', 'dell', 'requisition', 'repair', 'loaner'],
    sourceDoc: 'IT-HW-08',
    updatedAt: '2024-04-12'
  },
  {
    id: 5,
    category: 'Payroll & Compensation',
    title: 'Expense Reimbursement and Travel Expense Reporting',
    content: 'Business-related expenses incurred on behalf of the company must be submitted via the expense portal within 30 days accompanied by itemized receipts. Mileage reimbursement is calculated at standard IRS rates ($0.67/mile). Expenses under $500 require Team Lead signoff; expenses above $500 require HR/Finance Director approval.',
    keywords: ['reimbursement', 'expenses', 'travel', 'per diem', 'receipts', 'mileage', 'finance', 'refund'],
    sourceDoc: 'FIN-EXP-2024-02',
    updatedAt: '2024-05-18'
  },
  {
    id: 6,
    category: 'Onboarding & Performance',
    title: 'Employee Performance Review & Promotion Cycle',
    content: 'Performance evaluations take place semi-annually in June and December. Key performance indicators (KPIs) and OKRs are assessed collaboratively between employee and reporting manager. Formal salary band revisions (L3 to L8) follow the Q4 compensation calibration committee review.',
    keywords: ['performance review', 'promotion', 'kpi', 'okr', 'compensation calibration', 'salary band'],
    sourceDoc: 'HR-PERF-2024-05',
    updatedAt: '2024-06-20'
  }
];

export const INITIAL_TICKETS: SupportTicket[] = [
  {
    id: 101,
    ticketCode: 'TCK-2024-091',
    userId: 2,
    userName: 'Sarah Connor',
    userEmail: 'sarah.connor@company.com',
    userRole: 'Employee',
    department: 'DevOps',
    query: 'My account was locked after password expiration and VPN will not connect.',
    currentTier: 'L2',
    status: 'In_Review',
    priority: 'High',
    resolutionSummary: 'Pending account verification or security unlock confirmation.',
    l1RagResult: {
      matchedArticle: 'Account Lockout & Multi-Factor Authentication (MFA) Reset Policy',
      confidence: 0.94,
      answer: 'Account locked due to consecutive failed authentications. Forwarded to L2 IT Agent.',
      sourceDoc: 'SEC-SOP-04'
    },
    l2AgentsResult: {
      diagnosticNote: 'DiagnosticsAgent identified account locked in Identity Management registry.',
      actions: [
        {
          agent: 'DiagnosticsAgent',
          action: 'CHECK_ACCOUNT_LOCK_FLAG',
          status: 'SUCCESS',
          detail: 'Account EMP002 confirmed in Locked state. Security incident check: CLEAR.',
          timestamp: '2024-09-20 09:15:20'
        }
      ]
    },
    createdAt: '2024-09-20 09:14:00',
    updatedAt: '2024-09-20 09:16:30'
  },
  {
    id: 102,
    ticketCode: 'TCK-2024-092',
    userId: 4,
    userName: 'David Miller',
    userEmail: 'david.miller@company.com',
    userRole: 'Employee',
    department: 'Marketing',
    query: 'Health insurance enrollment is showing error code B-402 in the benefits portal.',
    currentTier: 'L3',
    status: 'Escalated_L3',
    priority: 'Medium',
    assignedHuman: 'Sam Carter',
    resolutionSummary: 'Carrier API rejected dependent verification document. Human review assigned.',
    createdAt: '2024-09-21 14:22:00',
    updatedAt: '2024-09-21 15:10:00'
  }
];

export const INITIAL_AUDIT_LOGS: AuditLog[] = [
  {
    id: 1,
    timestamp: '2024-09-22 01:00:00',
    userEmail: 'system@company.com',
    userRole: 'System Admin',
    action: 'DATABASE_INITIALIZATION',
    resourceType: 'SYSTEM',
    resourceId: 'SYS-INIT-01',
    tier: 'System',
    status: 'SUCCESS',
    details: 'Initialized EMS database with 8 employees, 6 KB policies, RBAC matrix, and audit ledger.'
  },
  {
    id: 2,
    timestamp: '2024-09-22 01:05:12',
    userEmail: 'sarah.connor@company.com',
    userRole: 'Employee',
    action: 'L1_QUERY_RETRIEVAL',
    resourceType: 'KNOWLEDGE_BASE',
    resourceId: 'SEC-SOP-04',
    tier: 'L1',
    status: 'SUCCESS',
    details: 'Matched query to SEC-SOP-04 (Account Lockout Policy) with 94% similarity.'
  },
  {
    id: 3,
    timestamp: '2024-09-22 01:05:14',
    userEmail: 'sarah.connor@company.com',
    userRole: 'Employee',
    action: 'L2_AGENT_TRIGGER',
    resourceType: 'EMPLOYEE_STATUS',
    resourceId: 'EMP002',
    tier: 'L2',
    status: 'WARNING',
    details: 'DiagnosticsAgent detected account EMP002 locked. Security clearance verified.'
  }
];
