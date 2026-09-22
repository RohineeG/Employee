export type EmployeeRole = 
  | 'Employee' 
  | 'Team Lead' 
  | 'HR Manager' 
  | 'System Admin' 
  | 'Support Specialist';

export type EmployeeStatus = 'Active' | 'Locked' | 'Suspended' | 'On Leave';

export interface Employee {
  id: number;
  employeeCode: string;
  name: string;
  email: string;
  role: EmployeeRole;
  department: string;
  jobTitle: string;
  status: EmployeeStatus;
  leaveBalance: number;
  sickLeaveBalance: number;
  managerId: number | null;
  benefitsEnrolled: boolean;
  equipmentStatus: string;
  salaryBand: string;
}

export interface KnowledgeArticle {
  id: number;
  category: string;
  title: string;
  content: string;
  keywords: string[];
  sourceDoc: string;
  updatedAt: string;
}

export type SupportTier = 'L1' | 'L2' | 'L3';
export type TicketStatus = 'Resolved_L1' | 'Resolved_L2' | 'Escalated_L3' | 'In_Review' | 'Closed' | 'Open' | 'Resolved_Satisfied';

export interface AgentAction {
  agent: string;
  action: string;
  status: 'SUCCESS' | 'FAILED' | 'ESCALATED' | 'INFO';
  detail: string;
  timestamp: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  tier?: SupportTier;
  l1RagResult?: {
    matchedArticle?: string;
    confidence: number;
    answer: string;
    sourceDoc?: string;
  };
  l2AgentsResult?: {
    actions: AgentAction[];
    changesMade?: string;
    diagnosticNote?: string;
  };
  l3Escalation?: {
    assignedTo: string;
    priority: string;
    reason: string;
  };
  suggestedFollowUps?: string[];
  isSatisfiedPrompt?: boolean;
}

export interface SupportTicket {
  id: number;
  ticketCode: string;
  userId: number;
  userName: string;
  userEmail: string;
  userRole: EmployeeRole;
  department: string;
  query: string;
  currentTier: SupportTier;
  status: TicketStatus;
  resolutionSummary: string;
  isSatisfied?: boolean;
  satisfactionRating?: number;
  satisfactionFeedback?: string;
  conversationHistory?: ChatMessage[];
  l1RagResult?: {
    matchedArticle?: string;
    confidence: number;
    answer: string;
    sourceDoc?: string;
  };
  l2AgentsResult?: {
    actions: AgentAction[];
    changesMade?: string;
    diagnosticNote?: string;
  };
  l3HumanNotes?: string;
  assignedHuman?: string;
  createdAt: string;
  updatedAt: string;
  priority: 'Low' | 'Medium' | 'High' | 'Critical';
}

export interface AuditLog {
  id: number;
  timestamp: string;
  userEmail: string;
  userRole: EmployeeRole | 'System Admin' | 'System';
  action: string;
  resourceType: string;
  resourceId?: string;
  tier: 'L1' | 'L2' | 'L3' | 'System' | 'Auth';
  status: 'SUCCESS' | 'FAILED' | 'ESCALATED' | 'WARNING';
  details: string;
}
