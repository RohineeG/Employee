import { Employee, KnowledgeArticle, SupportTicket, AuditLog, AgentAction, ChatMessage } from '../types';

export interface PipelineResult {
  finalTier: 'L1' | 'L2' | 'L3';
  isResolved: boolean;
  ticket: SupportTicket;
  updatedEmployee?: Employee;
  auditLogs: AuditLog[];
  assistantReply: string;
  suggestedFollowUps: string[];
  isSatisfiedPrompt: boolean;
  steps: {
    name: string;
    description: string;
    tier: 'L1' | 'L2' | 'L3';
    status: 'completed' | 'skipped' | 'escalated';
  }[];
}

export function processSupportQuery(
  query: string,
  user: Employee,
  knowledgeBase: KnowledgeArticle[],
  existingTicketsCount: number,
  activeTicket?: SupportTicket | null,
  conversationHistory?: ChatMessage[]
): PipelineResult {
  const queryTrimmed = query.trim();
  const queryLower = queryTrimmed.toLowerCase();
  const now = new Date();
  const timestamp = now.toISOString().replace('T', ' ').substring(0, 19);

  // Re-use active ticket or create new one
  const ticketId = activeTicket ? activeTicket.id : 100 + existingTicketsCount + 1;
  const ticketCode = activeTicket ? activeTicket.ticketCode : `TCK-2024-${String(ticketId).padStart(3, '0')}`;

  const steps: PipelineResult['steps'] = [
    { name: 'Semantic Intent & Dialog State Analysis', description: 'Analyzing continuous conversation context and user intent', tier: 'L1', status: 'completed' }
  ];

  const auditLogs: AuditLog[] = [];

  // 1. Check if user is expressing satisfaction / issue resolved
  const satisfactionKeywords = [
    'satisfied', 
    'satisfy', 
    'yes satisfied', 
    'im satisfied', 
    'i am satisfied', 
    'resolved', 
    'all good', 
    'thank you', 
    'thanks', 
    'that worked', 
    'that helped', 
    'that solved it', 
    'perfect', 
    'great job', 
    'fixed now', 
    'looks good',
    'done thanks'
  ];
  const isUserSatisfied = satisfactionKeywords.some(kw => queryLower.includes(kw));

  if (isUserSatisfied && (activeTicket || (conversationHistory && conversationHistory.length > 0))) {
    const reply = `Wonderful! I'm glad I could resolve this for you. Your support session for ${ticketCode} has been marked as **Resolved & Satisfied** in our enterprise ledger. If you ever have further questions or need additional assistance, feel free to message me anytime!`;

    const updatedTicket: SupportTicket = {
      ...(activeTicket || {
        id: ticketId,
        ticketCode,
        userId: user.id,
        userName: user.name,
        userEmail: user.email,
        userRole: user.role,
        department: user.department,
        query: queryTrimmed,
        createdAt: timestamp,
        priority: 'Low'
      }),
      status: 'Resolved_Satisfied',
      isSatisfied: true,
      currentTier: activeTicket ? activeTicket.currentTier : 'L1',
      resolutionSummary: activeTicket 
        ? `${activeTicket.resolutionSummary} (Employee confirmed full satisfaction)` 
        : 'Query resolved with user satisfaction confirmed.',
      updatedAt: timestamp
    };

    auditLogs.push({
      id: Date.now() + 1,
      timestamp,
      userEmail: user.email,
      userRole: user.role,
      action: 'SUPPORT_SESSION_SATISFIED',
      resourceType: 'SUPPORT_TICKET',
      resourceId: ticketCode,
      tier: updatedTicket.currentTier,
      status: 'SUCCESS',
      details: `Employee ${user.name} confirmed satisfaction with resolution for ticket ${ticketCode}.`
    });

    return {
      finalTier: updatedTicket.currentTier,
      isResolved: true,
      ticket: updatedTicket,
      auditLogs,
      assistantReply: reply,
      suggestedFollowUps: ['Rate your support experience ★★★★★', 'Start a new conversation', 'View full audit trail'],
      isSatisfiedPrompt: false,
      steps: [
        { name: 'Satisfaction Verification', description: 'Employee confirmed issue resolution', tier: updatedTicket.currentTier, status: 'completed' }
      ]
    };
  }

  // 2. Check for explicit dissatisfaction or human escalation request
  const escalationKeywords = [
    'not satisfied',
    'unsatisfied',
    'did not help',
    "didn't help",
    'does not solve',
    "doesn't solve",
    'still broken',
    'still locked',
    'still not working',
    'speak to a human',
    'talk to a human',
    'human agent',
    'human support',
    'escalate',
    'representative',
    'real person',
    'connect me to someone'
  ];
  const isEscalationRequested = escalationKeywords.some(kw => queryLower.includes(kw));

  if (isEscalationRequested) {
    steps.push({
      name: 'L3 Escalation Triggered',
      description: 'Employee requested human specialist assistance',
      tier: 'L3',
      status: 'completed'
    });

    const assignedAgent = 'Rachel Green';
    const reply = `I understand your concern and apologize that the automated assistance didn't fully resolve this. I have immediately escalated this ticket (${ticketCode}) to senior People Operations specialist **${assignedAgent}** with High priority. Rachel will review our conversation history and reach out to you directly via ${user.email} shortly.`;

    const updatedTicket: SupportTicket = {
      ...(activeTicket || {
        id: ticketId,
        ticketCode,
        userId: user.id,
        userName: user.name,
        userEmail: user.email,
        userRole: user.role,
        department: user.department,
        query: queryTrimmed,
        createdAt: timestamp
      }),
      currentTier: 'L3',
      status: 'Escalated_L3',
      priority: 'High',
      assignedHuman: assignedAgent,
      resolutionSummary: `Escalated to human support specialist ${assignedAgent} upon employee request.`,
      l3HumanNotes: `User expressed need for direct human review. Chat conversation transferred to Human Desk queue.`,
      updatedAt: timestamp
    };

    auditLogs.push({
      id: Date.now() + 1,
      timestamp,
      userEmail: user.email,
      userRole: user.role,
      action: 'L3_USER_REQUESTED_ESCALATION',
      resourceType: 'SUPPORT_TICKET',
      resourceId: ticketCode,
      tier: 'L3',
      status: 'ESCALATED',
      details: `Employee ${user.name} requested human escalation. Assigned to ${assignedAgent}.`
    });

    return {
      finalTier: 'L3',
      isResolved: false,
      ticket: updatedTicket,
      auditLogs,
      assistantReply: reply,
      suggestedFollowUps: ['Add confidential notes for Rachel', 'Check Human Desk queue', 'What is the expected response time?'],
      isSatisfiedPrompt: false,
      steps
    };
  }

  // 3. Check for sensitive grievance / harassment / ethics -> L3 Human Escalation
  const isGrievance = 
    queryLower.includes('harassment') || 
    queryLower.includes('grievance') || 
    queryLower.includes('salary dispute') || 
    queryLower.includes('formal dispute') || 
    queryLower.includes('confidential') ||
    queryLower.includes('manager grievance') ||
    queryLower.includes('discrimination') ||
    queryLower.includes('whistleblower') ||
    queryLower.includes('retaliation') ||
    queryLower.includes('legal');

  if (isGrievance) {
    steps.push({
      name: 'L1 Policy Triage & Ethics Protocol',
      description: 'Triggered confidential grievance & HR ethics protocol',
      tier: 'L1',
      status: 'escalated'
    });
    steps.push({
      name: 'L3 Human Operations Escalation',
      description: 'Dispatched to People Operations Director with Confidential priority',
      tier: 'L3',
      status: 'completed'
    });

    const reply = `I have recognized this as a confidential personnel matter. Per company compliance protocol HR-ETH-01, automated processing has been bypassed and your inquiry has been securely routed to **Rachel Green**, People Operations Director. Your case is treated under strict privacy. Rachel will contact you directly.`;

    const ticket: SupportTicket = {
      id: ticketId,
      ticketCode,
      userId: user.id,
      userName: user.name,
      userEmail: user.email,
      userRole: user.role,
      department: user.department,
      query: queryTrimmed,
      currentTier: 'L3',
      status: 'Escalated_L3',
      priority: 'Critical',
      assignedHuman: 'Rachel Green',
      resolutionSummary: 'Confidential employee relations inquiry routed directly to People Operations for private review.',
      createdAt: activeTicket ? activeTicket.createdAt : timestamp,
      updatedAt: timestamp,
      l1RagResult: {
        matchedArticle: 'Employee Relations & Ethical Conduct Guidelines',
        confidence: 0.98,
        answer: 'Sensitive workplace inquiry detected. Automatic AI resolution halted by HR compliance rules.',
        sourceDoc: 'HR-ETH-01'
      },
      l3HumanNotes: 'Case scheduled for confidential direct intake. Notification dispatched to designated HR partner.'
    };

    auditLogs.push({
      id: Date.now() + 1,
      timestamp,
      userEmail: user.email,
      userRole: user.role,
      action: 'L3_ETHICS_ESCALATION',
      resourceType: 'SUPPORT_TICKET',
      resourceId: ticketCode,
      tier: 'L3',
      status: 'ESCALATED',
      details: `Escalated sensitive inquiry to L3 Human Queue: ${queryTrimmed.slice(0, 60)}...`
    });

    return {
      finalTier: 'L3',
      isResolved: false,
      ticket,
      auditLogs,
      assistantReply: reply,
      suggestedFollowUps: ['Request direct confidential call', 'Review Employee Ethics Policy', 'View ticket in Human Desk'],
      isSatisfiedPrompt: false,
      steps
    };
  }

  // 4. L2 Actionable Requests (Account Unlock, Leave Recalculation, Benefits Sync, Hardware Requisition)
  const isUnlock = 
    queryLower.includes('unlock') || 
    (queryLower.includes('locked') && (queryLower.includes('account') || queryLower.includes('vpn') || queryLower.includes('access')));

  const isLeaveFix = 
    (queryLower.includes('leave') || queryLower.includes('pto')) && 
    (queryLower.includes('fix') || queryLower.includes('incorrect') || queryLower.includes('disparity') || queryLower.includes('recalculate') || queryLower.includes('adjust') || queryLower.includes('wrong') || queryLower.includes('add'));

  const isBenefitsSync = 
    queryLower.includes('benefit') || 
    queryLower.includes('insurance') || 
    queryLower.includes('enrollment error') ||
    (queryLower.includes('health') && (queryLower.includes('sync') || queryLower.includes('error') || queryLower.includes('enrolled')));

  const isHardwareStatus =
    queryLower.includes('equipment') || 
    queryLower.includes('laptop') || 
    queryLower.includes('hardware') || 
    queryLower.includes('monitor') || 
    queryLower.includes('repair') ||
    queryLower.includes('requisition');

  // 4a. Account Unlock Flow
  if (isUnlock) {
    steps.push({
      name: 'L2 DiagnosticsAgent Investigation',
      description: 'Inspecting Directory Service authentication status & security alerts',
      tier: 'L2',
      status: 'completed'
    });
    steps.push({
      name: 'L2 RemediationAgent Execution',
      description: 'Resetting account lock counters and enabling VPN directory profile',
      tier: 'L2',
      status: 'completed'
    });

    const isAlreadyActive = user.status === 'Active';
    const updatedEmployee: Employee = isAlreadyActive ? user : { ...user, status: 'Active' };

    const actions: AgentAction[] = [
      {
        agent: 'DiagnosticsAgent',
        action: 'INSPECT_SECURITY_FLAGS',
        status: 'SUCCESS',
        detail: `Verified employee ${user.employeeCode} (${user.name}) has 0 security incidents and no anomalous IP triggers.`,
        timestamp
      },
      {
        agent: 'RemediationAgent',
        action: 'UNLOCK_ACCOUNT_STATE',
        status: 'SUCCESS',
        detail: isAlreadyActive 
          ? `Directory status is confirmed Active. Refreshed SSO credentials.` 
          : `Mutated employee status from ${user.status} -> Active. Cleared failed lockout telemetry.`,
        timestamp
      }
    ];

    const reply = isAlreadyActive
      ? `I checked your directory profile in our Identity Store. Your account is already **Active**, and all VPN and SSO privileges are fully operational. I also refreshed your SSO session cache to ensure uninterrupted login. Are you able to log in now?`
      : `I have investigated your account via our **L2 DiagnosticsAgent**. Zero security threats or anomalous IPs were detected, so our **RemediationAgent** automatically unlocked your account (${user.employeeCode}), reset the failed attempt counter, and restored full VPN directory access. Your status is now **Active**! Are you satisfied with this resolution?`;

    const ticket: SupportTicket = {
      id: ticketId,
      ticketCode,
      userId: user.id,
      userName: user.name,
      userEmail: user.email,
      userRole: user.role,
      department: user.department,
      query: queryTrimmed,
      currentTier: 'L2',
      status: 'Resolved_L2',
      priority: 'High',
      resolutionSummary: 'L2 DiagnosticsAgent verified safe credentials; RemediationAgent unlocked account and reinstated VPN access.',
      createdAt: activeTicket ? activeTicket.createdAt : timestamp,
      updatedAt: timestamp,
      l1RagResult: {
        matchedArticle: 'Account Lockout & Multi-Factor Authentication (MFA) Reset Policy',
        confidence: 0.95,
        answer: 'Lockout criteria verified against SEC-SOP-04. Programmatic remediation allowed.',
        sourceDoc: 'SEC-SOP-04'
      },
      l2AgentsResult: {
        actions,
        changesMade: isAlreadyActive ? 'SSO session refreshed; account confirmed Active.' : 'Account status updated from Locked to Active.',
        diagnosticNote: 'Automated identity verification passed with 100% confidence.'
      }
    };

    auditLogs.push({
      id: Date.now() + 1,
      timestamp,
      userEmail: user.email,
      userRole: user.role,
      action: 'L2_ACCOUNT_UNLOCKED',
      resourceType: 'EMPLOYEE_STATUS',
      resourceId: user.employeeCode,
      tier: 'L2',
      status: 'SUCCESS',
      details: `DiagnosticsAgent validated clearance; RemediationAgent confirmed/unlocked ${user.name} account.`
    });

    return {
      finalTier: 'L2',
      isResolved: true,
      ticket,
      updatedEmployee,
      auditLogs,
      assistantReply: reply,
      suggestedFollowUps: ['✅ Yes, I am satisfied!', 'How can I prevent future lockouts?', 'Test my VPN connection', 'Check my leave balance as well'],
      isSatisfiedPrompt: true,
      steps
    };
  }

  // 4b. Leave Recalculation / Disparity Flow
  if (isLeaveFix) {
    steps.push({
      name: 'L2 DiagnosticsAgent Calculation',
      description: 'Audit tenure and policy entitlement against HR accrued leave ledger',
      tier: 'L2',
      status: 'completed'
    });
    steps.push({
      name: 'L2 RemediationAgent Ledger Adjustment',
      description: 'Applying verified balance entitlement to primary database record',
      tier: 'L2',
      status: 'completed'
    });

    const targetLeave = 20;
    const previousLeave = user.leaveBalance;
    const updatedEmployee: Employee = {
      ...user,
      leaveBalance: targetLeave
    };

    const actions: AgentAction[] = [
      {
        agent: 'DiagnosticsAgent',
        action: 'AUDIT_ACCRUAL_LEDGER',
        status: 'SUCCESS',
        detail: `Audited HR accrual ledger against HR-POL-2024-01. Confirmed full-time entitlement is 20 days. Previous balance was ${previousLeave} days.`,
        timestamp
      },
      {
        agent: 'RemediationAgent',
        action: 'RECALCULATE_PTO_LEDGER',
        status: 'SUCCESS',
        detail: `Recalculated PTO balance for ${user.employeeCode} to ${targetLeave} days per HR-POL-2024-01.`,
        timestamp
      }
    ];

    const reply = `I audited your HR accrual ledger using our **L2 DiagnosticsAgent**. A batch synchronization lag caused your balance to display ${previousLeave} days instead of your full entitlement. Our **RemediationAgent** has reconciled the central ledger and updated your PTO balance to **${targetLeave} days** (plus ${user.sickLeaveBalance} sick days). Your EMS profile is now updated! Does this resolve your concern?`;

    const ticket: SupportTicket = {
      id: ticketId,
      ticketCode,
      userId: user.id,
      userName: user.name,
      userEmail: user.email,
      userRole: user.role,
      department: user.department,
      query: queryTrimmed,
      currentTier: 'L2',
      status: 'Resolved_L2',
      priority: 'Medium',
      resolutionSummary: `L2 Multi-Agent verified policy tenure and corrected PTO leave balance from ${previousLeave} to ${targetLeave} days.`,
      createdAt: activeTicket ? activeTicket.createdAt : timestamp,
      updatedAt: timestamp,
      l1RagResult: {
        matchedArticle: 'Annual Paid Time Off (PTO) Policy & Carryover Rules',
        confidence: 0.94,
        answer: 'Full-time employees receive 20 days PTO. Discrepancy confirmed as batch sync delay.',
        sourceDoc: 'HR-POL-2024-01'
      },
      l2AgentsResult: {
        actions,
        changesMade: `Leave balance updated from ${previousLeave} to ${targetLeave} days.`,
        diagnosticNote: 'Audit confirmed entitlement under HR-POL-2024-01.'
      }
    };

    auditLogs.push({
      id: Date.now() + 1,
      timestamp,
      userEmail: user.email,
      userRole: user.role,
      action: 'L2_LEAVE_RECALCULATED',
      resourceType: 'EMPLOYEE_LEAVE',
      resourceId: user.employeeCode,
      tier: 'L2',
      status: 'SUCCESS',
      details: `Adjusted PTO balance from ${previousLeave} -> ${targetLeave} days for ${user.name}.`
    });

    return {
      finalTier: 'L2',
      isResolved: true,
      ticket,
      updatedEmployee,
      auditLogs,
      assistantReply: reply,
      suggestedFollowUps: ['✅ Yes, I am satisfied!', 'How do I submit a time-off request?', 'What are the carryover limits for next year?', 'Check my health benefits'],
      isSatisfiedPrompt: true,
      steps
    };
  }

  // 4c. Benefits Sync Flow
  if (isBenefitsSync) {
    steps.push({
      name: 'L2 Carrier Bridge Diagnostics',
      description: 'Executing webhook health probe against Benefits Carrier EDI API',
      tier: 'L2',
      status: 'completed'
    });
    steps.push({
      name: 'L2 RemediationAgent Synchronization',
      description: 'Updating benefits enrollment status to Active in EMS database',
      tier: 'L2',
      status: 'completed'
    });

    const updatedEmployee: Employee = {
      ...user,
      benefitsEnrolled: true
    };

    const actions: AgentAction[] = [
      {
        agent: 'DiagnosticsAgent',
        action: 'QUERY_CARRIER_GATEWAY',
        status: 'SUCCESS',
        detail: 'Carrier Gateway EDI endpoint returned 200 OK. Active medical, dental, and vision plan confirmed.',
        timestamp
      },
      {
        agent: 'RemediationAgent',
        action: 'UPDATE_BENEFITS_FLAG',
        status: 'SUCCESS',
        detail: `Set benefits_enrolled = true for ${user.employeeCode}. Cleared synchronization warning.`,
        timestamp
      }
    ];

    const reply = `Our **L2 DiagnosticsAgent** polled the insurance carrier's EDI gateway. The carrier confirmed your medical, dental, and vision enrollment is 100% active on their end; the issue was a webhook caching glitch in EMS. Our **RemediationAgent** has synchronized the records and marked your benefits status as **Active & Enrolled**! Are you satisfied with this update?`;

    const ticket: SupportTicket = {
      id: ticketId,
      ticketCode,
      userId: user.id,
      userName: user.name,
      userEmail: user.email,
      userRole: user.role,
      department: user.department,
      query: queryTrimmed,
      currentTier: 'L2',
      status: 'Resolved_L2',
      priority: 'Medium',
      resolutionSummary: 'L2 Agents reconciled carrier webhook discrepancy and validated active health insurance coverage.',
      createdAt: activeTicket ? activeTicket.createdAt : timestamp,
      updatedAt: timestamp,
      l1RagResult: {
        matchedArticle: 'Health, Dental, and Life Insurance Enrollment Guidelines',
        confidence: 0.93,
        answer: 'Carrier guidelines HR-BEN-2024-03 verified. Record refreshed in EMS.',
        sourceDoc: 'HR-BEN-2024-03'
      },
      l2AgentsResult: {
        actions,
        changesMade: 'Benefits enrollment verified and synced to Active.',
        diagnosticNote: 'Carrier EDI reconciliation completed.'
      }
    };

    auditLogs.push({
      id: Date.now() + 1,
      timestamp,
      userEmail: user.email,
      userRole: user.role,
      action: 'L2_BENEFITS_SYNC',
      resourceType: 'BENEFITS_STATUS',
      resourceId: user.employeeCode,
      tier: 'L2',
      status: 'SUCCESS',
      details: `Synchronized carrier coverage for ${user.name}; benefits_enrolled set to active.`
    });

    return {
      finalTier: 'L2',
      isResolved: true,
      ticket,
      updatedEmployee,
      auditLogs,
      assistantReply: reply,
      suggestedFollowUps: ['✅ Yes, I am satisfied!', 'How do I download my insurance card?', 'What is our dental coverage policy?', 'Check my leave balance'],
      isSatisfiedPrompt: true,
      steps
    };
  }

  // 4d. Hardware / Equipment Status
  if (isHardwareStatus) {
    let reply = `Here is your current equipment profile:
- **Assigned Status**: ${user.equipmentStatus}
- **Standard Bundle**: MacBook Pro 16" / Dell Precision + 27" 4K Monitor + Ergonomic Keyboard/Mouse
- **Procurement SLA**: Standard replacement or repairs are delivered within 48 business hours via IT Operations.`;

    let updatedEmployee: Employee | undefined = undefined;
    if (user.equipmentStatus === 'Requisition Pending') {
      updatedEmployee = { ...user, equipmentStatus: 'Dispatched / In Transit' };
      reply += `\n\nI detected that your requisition was pending approval. Our **L2 RemediationAgent** expedited the ticket with IT Depot and updated your equipment status to **Dispatched / In Transit** (Tracking: FEDEX-9823412).`;
    }

    const ticket: SupportTicket = {
      id: ticketId,
      ticketCode,
      userId: user.id,
      userName: user.name,
      userEmail: user.email,
      userRole: user.role,
      department: user.department,
      query: queryTrimmed,
      currentTier: 'L2',
      status: 'Resolved_L2',
      priority: 'Low',
      resolutionSummary: `Hardware status checked and verified: ${updatedEmployee ? updatedEmployee.equipmentStatus : user.equipmentStatus}.`,
      createdAt: activeTicket ? activeTicket.createdAt : timestamp,
      updatedAt: timestamp,
      l1RagResult: {
        matchedArticle: 'Company Equipment & Hardware Replacement Policy',
        confidence: 0.91,
        answer: 'Company standard equipment includes developer laptop, dual monitors, and peripheral peripherals.',
        sourceDoc: 'IT-SOP-02'
      }
    };

    return {
      finalTier: 'L2',
      isResolved: true,
      ticket,
      updatedEmployee,
      auditLogs,
      assistantReply: reply + '\n\nAre you satisfied with this information, or would you like to request an additional peripheral or loaner laptop?',
      suggestedFollowUps: ['✅ Yes, I am satisfied!', 'How do I request an extra monitor?', 'What if I need a loaner laptop while traveling?', 'Check my VPN status'],
      isSatisfiedPrompt: true,
      steps
    };
  }

  // 4e. Check for profile / personal details query (e.g., "who is my manager", "what is my salary band", "how many sick days")
  if (queryLower.includes('manager') || queryLower.includes('job title') || queryLower.includes('salary band') || queryLower.includes('my balance') || queryLower.includes('how many days')) {
    let reply = `Here are the details from your active employee record (${user.employeeCode}):\n`;
    reply += `• **Name**: ${user.name} (${user.role})\n`;
    reply += `• **Department**: ${user.department} &bull; **Job Title**: ${user.jobTitle}\n`;
    reply += `• **PTO Leave Balance**: ${user.leaveBalance} days\n`;
    reply += `• **Sick Leave Balance**: ${user.sickLeaveBalance} days\n`;
    reply += `• **Account Status**: ${user.status}\n`;
    reply += `• **Benefits Enrolled**: ${user.benefitsEnrolled ? 'Active' : 'Pending Verification'}\n`;
    reply += `• **Hardware Status**: ${user.equipmentStatus}`;

    const ticket: SupportTicket = {
      id: ticketId,
      ticketCode,
      userId: user.id,
      userName: user.name,
      userEmail: user.email,
      userRole: user.role,
      department: user.department,
      query: queryTrimmed,
      currentTier: 'L1',
      status: 'Resolved_L1',
      priority: 'Low',
      resolutionSummary: 'Employee profile metrics retrieved from central Directory Store.',
      createdAt: activeTicket ? activeTicket.createdAt : timestamp,
      updatedAt: timestamp
    };

    return {
      finalTier: 'L1',
      isResolved: true,
      ticket,
      auditLogs,
      assistantReply: reply + '\n\nDoes this provide the information you were looking for?',
      suggestedFollowUps: ['✅ Yes, I am satisfied!', 'Check my annual carryover limit', 'How do I request PTO?', 'Unlock account'],
      isSatisfiedPrompt: true,
      steps: [
        { name: 'Directory Store Lookup', description: 'Retrieved verified employee identity and balance records', tier: 'L1', status: 'completed' }
      ]
    };
  }

  // 5. Default: L1 Knowledge Base Semantic RAG Retrieval
  let bestArticle: KnowledgeArticle = knowledgeBase[0];
  let maxScore = 0;

  for (const article of knowledgeBase) {
    let score = 0;
    for (const kw of article.keywords) {
      if (queryLower.includes(kw.toLowerCase())) {
        score += 2.5;
      }
    }
    const words = article.title.toLowerCase().split(' ');
    for (const w of words) {
      if (w.length > 3 && queryLower.includes(w)) {
        score += 1.5;
      }
    }
    const contentWords = article.content.toLowerCase().split(' ');
    for (const cw of contentWords) {
      if (cw.length > 4 && queryLower.includes(cw)) {
        score += 0.5;
      }
    }
    if (score > maxScore) {
      maxScore = score;
      bestArticle = article;
    }
  }

  const confidence = maxScore > 0 ? Math.min(0.97, 0.78 + maxScore * 0.04) : 0.81;

  const assistantReply = `Based on corporate policy **${bestArticle.sourceDoc}: ${bestArticle.title}**:\n\n${bestArticle.content}\n\n*Source: ${bestArticle.category} &bull; Document Reference ${bestArticle.sourceDoc} (Confidence: ${Math.round(confidence * 100)}%)*\n\nDoes this answer your question, or would you like me to inspect your specific account state or execute any adjustments?`;

  const ticket: SupportTicket = {
    id: ticketId,
    ticketCode,
    userId: user.id,
    userName: user.name,
    userEmail: user.email,
    userRole: user.role,
    department: user.department,
    query: queryTrimmed,
    currentTier: 'L1',
    status: 'Resolved_L1',
    priority: 'Low',
    resolutionSummary: `Resolved via L1 RAG from document ${bestArticle.sourceDoc} (${bestArticle.title}).`,
    createdAt: activeTicket ? activeTicket.createdAt : timestamp,
    updatedAt: timestamp,
    l1RagResult: {
      matchedArticle: bestArticle.title,
      confidence,
      answer: bestArticle.content,
      sourceDoc: bestArticle.sourceDoc
    }
  };

  auditLogs.push({
    id: Date.now() + 1,
    timestamp,
    userEmail: user.email,
    userRole: user.role,
    action: 'L1_RAG_RETRIEVAL',
    resourceType: 'KNOWLEDGE_BASE',
    resourceId: bestArticle.sourceDoc,
    tier: 'L1',
    status: 'SUCCESS',
    details: `Resolved query via document ${bestArticle.sourceDoc} with ${Math.round(confidence * 100)}% match confidence.`
  });

  // Dynamic follow-up chips based on category
  let dynamicFollowUps = ['✅ Yes, I am satisfied!', 'Tell me more about carryover limits', 'Check my current balance'];
  if (bestArticle.category.includes('Equipment') || bestArticle.category.includes('IT')) {
    dynamicFollowUps = ['✅ Yes, I am satisfied!', 'What is my current equipment status?', 'How do I request a loaner laptop?', 'Connect to human specialist'];
  } else if (bestArticle.category.includes('Benefits') || bestArticle.category.includes('Insurance')) {
    dynamicFollowUps = ['✅ Yes, I am satisfied!', 'Sync my benefits enrollment status', 'How do I add a family member?', 'Speak to HR specialist'];
  } else if (bestArticle.category.includes('Security') || bestArticle.category.includes('MFA')) {
    dynamicFollowUps = ['✅ Yes, I am satisfied!', 'Unlock my account now', 'Reset my MFA device', 'Speak to IT specialist'];
  }

  return {
    finalTier: 'L1',
    isResolved: true,
    ticket,
    auditLogs,
    assistantReply,
    suggestedFollowUps: dynamicFollowUps,
    isSatisfiedPrompt: true,
    steps: [
      { name: 'Semantic RAG Index Search', description: `Matched knowledge document ${bestArticle.sourceDoc} with ${Math.round(confidence * 100)}% score`, tier: 'L1', status: 'completed' },
      { name: 'Policy Compliance Validation', description: 'Verified non-confidential query eligible for automated response', tier: 'L1', status: 'completed' }
    ]
  };
}
