import React, { useState, useRef, useEffect } from 'react';
import { 
  Sparkles, 
  Send, 
  CheckCircle2, 
  ArrowRight, 
  BookOpen, 
  Cpu, 
  AlertTriangle, 
  Clock, 
  Bot,
  Star,
  UserCheck,
  RotateCcw,
  MessageSquare,
  ShieldCheck,
  ChevronRight,
  Smile,
  HelpCircle
} from 'lucide-react';
import { Employee, KnowledgeArticle, SupportTicket, AuditLog, ChatMessage } from '../types';
import { processSupportQuery, PipelineResult } from '../services/aiPipeline';

interface PortalTabProps {
  currentUser: Employee;
  knowledgeBase: KnowledgeArticle[];
  tickets: SupportTicket[];
  onAddTicket: (ticket: SupportTicket) => void;
  onUpdateTicket?: (ticket: SupportTicket) => void;
  onUpdateEmployee: (updated: Employee) => void;
  onAddAuditLogs: (logs: AuditLog[]) => void;
}

export const PortalTab: React.FC<PortalTabProps> = ({
  currentUser,
  knowledgeBase,
  tickets,
  onAddTicket,
  onUpdateTicket,
  onUpdateEmployee,
  onAddAuditLogs,
}) => {
  const [queryInput, setQueryInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeStepIndex, setActiveStepIndex] = useState(0);
  const [activeTicket, setActiveTicket] = useState<SupportTicket | null>(null);
  const [isSatisfied, setIsSatisfied] = useState<boolean>(false);
  const [starRating, setStarRating] = useState<number>(5);
  const [feedbackNotes, setFeedbackNotes] = useState<string>('');
  const [feedbackSubmitted, setFeedbackSubmitted] = useState<boolean>(false);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  // Initial welcome message
  const initialWelcomeMessage: ChatMessage = {
    id: 'welcome-0',
    sender: 'assistant',
    content: `Hello **${currentUser.name}**! I am your enterprise AI Support Assistant. 
    
I can answer company policy questions via **L1 Knowledge Base (RAG)**, perform autonomous account diagnostics and central database changes via **L2 LangGraph Agents** (e.g. account unlock, PTO balance recalculation, benefits sync), or route sensitive issues directly to **L3 Human Specialists**.

*How can I help you today? Feel free to ask questions or select a scenario below—we'll continue chatting until you are 100% satisfied!*`,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    suggestedFollowUps: [
      '📖 What is our annual PTO policy and carryover rules?',
      '🔓 My account is locked, please unlock it and verify VPN',
      '⚖️ Recalculate my leave balance to 20 days',
      '🏥 Sync my health insurance benefits enrollment',
      '🚨 File confidential grievance with HR director'
    ]
  };

  const [messages, setMessages] = useState<ChatMessage[]>([initialWelcomeMessage]);

  // When currentUser changes (e.g. persona switch), refresh greeting if clean
  useEffect(() => {
    if (messages.length <= 1) {
      setMessages([
        {
          ...initialWelcomeMessage,
          content: `Hello **${currentUser.name}** (${currentUser.role} &bull; ${currentUser.department})! I am your enterprise AI Support Assistant. 
          
I can answer company policy questions via **L1 Knowledge Base**, perform autonomous account diagnostics and changes via **L2 LangGraph Agents**, or route sensitive issues directly to **L3 Human Specialists**.

*How can I help you today? We will continue chatting until you are fully satisfied!*`
        }
      ]);
      setActiveTicket(null);
      setIsSatisfied(false);
    }
  }, [currentUser.id]);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isProcessing]);

  // Stats calculation
  const totalQueries = tickets.length;
  const resolvedL1 = tickets.filter(t => t.currentTier === 'L1' || t.status === 'Resolved_L1').length;
  const resolvedL2 = tickets.filter(t => t.currentTier === 'L2' || t.status === 'Resolved_L2').length;
  const escalatedL3 = tickets.filter(t => t.currentTier === 'L3' || t.status === 'Escalated_L3').length;

  const handleRunQuery = async (queryText: string) => {
    if (!queryText.trim() || isProcessing) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      content: queryText.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setQueryInput('');
    setIsProcessing(true);
    setActiveStepIndex(0);

    // Simulate multi-tier progress
    await new Promise(r => setTimeout(r, 400));
    setActiveStepIndex(1);
    await new Promise(r => setTimeout(r, 450));
    setActiveStepIndex(2);

    const result: PipelineResult = processSupportQuery(
      queryText.trim(),
      currentUser,
      knowledgeBase,
      tickets.length,
      activeTicket,
      messages
    );

    // Update tickets in state
    if (activeTicket && onUpdateTicket) {
      onUpdateTicket(result.ticket);
    } else {
      onAddTicket(result.ticket);
    }
    setActiveTicket(result.ticket);

    // Update employee if database mutation occurred
    if (result.updatedEmployee) {
      onUpdateEmployee(result.updatedEmployee);
    }

    // Append audit logs
    if (result.auditLogs.length > 0) {
      onAddAuditLogs(result.auditLogs);
    }

    // Check if satisfaction was triggered by text
    if (result.ticket.isSatisfied || result.ticket.status === 'Resolved_Satisfied') {
      setIsSatisfied(true);
    }

    const assistantMsg: ChatMessage = {
      id: `assistant-${Date.now()}`,
      sender: 'assistant',
      content: result.assistantReply,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      tier: result.finalTier,
      l1RagResult: result.ticket.l1RagResult,
      l2AgentsResult: result.ticket.l2AgentsResult,
      l3Escalation: result.ticket.assignedHuman ? {
        assignedTo: result.ticket.assignedHuman,
        priority: result.ticket.priority,
        reason: result.ticket.resolutionSummary
      } : undefined,
      suggestedFollowUps: result.suggestedFollowUps,
      isSatisfiedPrompt: result.isSatisfiedPrompt
    };

    setMessages(prev => [...prev, assistantMsg]);
    setIsProcessing(false);
  };

  const handleMarkSatisfied = () => {
    if (!activeTicket) {
      // If user marks satisfied without an active ticket yet, run simple confirmation
      handleRunQuery("Yes, I am satisfied with the support provided. Issue resolved!");
      return;
    }

    const updatedTicket: SupportTicket = {
      ...activeTicket,
      isSatisfied: true,
      status: 'Resolved_Satisfied',
      resolutionSummary: `${activeTicket.resolutionSummary} (Employee marked as Satisfied)`,
      updatedAt: new Date().toISOString().replace('T', ' ').substring(0, 19)
    };

    if (onUpdateTicket) {
      onUpdateTicket(updatedTicket);
    }
    setActiveTicket(updatedTicket);
    setIsSatisfied(true);

    onAddAuditLogs([{
      id: Date.now(),
      timestamp: updatedTicket.updatedAt,
      userEmail: currentUser.email,
      userRole: currentUser.role,
      action: 'SUPPORT_SESSION_SATISFIED',
      resourceType: 'SUPPORT_TICKET',
      resourceId: activeTicket.ticketCode,
      tier: activeTicket.currentTier,
      status: 'SUCCESS',
      details: `Employee ${currentUser.name} officially marked ticket ${activeTicket.ticketCode} as Satisfied & Resolved.`
    }]);

    const confirmMsg: ChatMessage = {
      id: `system-sat-${Date.now()}`,
      sender: 'assistant',
      content: `🎉 Thank you, **${currentUser.name}**! I have officially resolved **${activeTicket.ticketCode}** and recorded your satisfaction in the compliance ledger.\n\nPlease take a second to rate your experience below. You can continue asking questions anytime or start a fresh session!`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      tier: activeTicket.currentTier,
      suggestedFollowUps: ['Start a new conversation', 'Check my updated profile', 'View compliance audit log']
    };

    setMessages(prev => [...prev, confirmMsg]);
  };

  const handleResetChat = () => {
    setActiveTicket(null);
    setIsSatisfied(false);
    setFeedbackSubmitted(false);
    setMessages([
      {
        ...initialWelcomeMessage,
        id: `welcome-${Date.now()}`
      }
    ]);
  };

  const handleSendFeedback = () => {
    setFeedbackSubmitted(true);
    if (activeTicket) {
      const updated: SupportTicket = {
        ...activeTicket,
        satisfactionRating: starRating,
        satisfactionFeedback: feedbackNotes
      };
      if (onUpdateTicket) {
        onUpdateTicket(updated);
      }
      onAddAuditLogs([{
        id: Date.now(),
        timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
        userEmail: currentUser.email,
        userRole: currentUser.role,
        action: 'CSAT_FEEDBACK_LOGGED',
        resourceType: 'SUPPORT_TICKET',
        resourceId: activeTicket.ticketCode,
        tier: activeTicket.currentTier,
        status: 'SUCCESS',
        details: `Employee gave ${starRating} Stars CSAT rating. Notes: "${feedbackNotes || 'No text feedback'}"`
      }]);
    }
  };

  const loadPastTicket = (ticket: SupportTicket) => {
    setActiveTicket(ticket);
    setIsSatisfied(ticket.isSatisfied || ticket.status === 'Resolved_Satisfied');
    setMessages([
      {
        id: `past-user-${ticket.id}`,
        sender: 'user',
        content: ticket.query,
        timestamp: ticket.createdAt
      },
      {
        id: `past-ai-${ticket.id}`,
        sender: 'assistant',
        content: `**Resolution Summary for ${ticket.ticketCode}**:\n${ticket.resolutionSummary}\n\n*Status: ${ticket.status} &bull; Tier: ${ticket.currentTier}*`,
        timestamp: ticket.updatedAt,
        tier: ticket.currentTier,
        l1RagResult: ticket.l1RagResult,
        l2AgentsResult: ticket.l2AgentsResult,
        l3Escalation: ticket.assignedHuman ? {
          assignedTo: ticket.assignedHuman,
          priority: ticket.priority,
          reason: ticket.resolutionSummary
        } : undefined,
        suggestedFollowUps: [
          'Ask a follow-up question on this issue',
          'Is this issue fully resolved?',
          'Start a new conversation'
        ],
        isSatisfiedPrompt: !ticket.isSatisfied
      }
    ]);
  };

  return (
    <div id="portal-tab-content" className="space-y-6">
      {/* Top Metrics Row */}
      <div id="portal-metrics-grid" className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div id="metric-card-total" className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-xs">
          <div className="text-xs font-medium text-slate-500">Total Support Queries</div>
          <div className="mt-1 text-2xl font-bold text-slate-900">{totalQueries}</div>
          <div className="mt-1 flex items-center text-[11px] text-slate-500">Across all enterprise tiers</div>
        </div>

        <div id="metric-card-l1" className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-xs">
          <div className="text-xs font-medium text-slate-500">L1 RAG Resolved</div>
          <div className="mt-1 text-2xl font-bold text-blue-600">{resolvedL1}</div>
          <div className="mt-1 flex items-center text-[11px] text-blue-600 font-medium">Knowledge Base retrieval</div>
        </div>

        <div id="metric-card-l2" className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-xs">
          <div className="text-xs font-medium text-slate-500">L2 Agent Remedied</div>
          <div className="mt-1 text-2xl font-bold text-emerald-600">{resolvedL2}</div>
          <div className="mt-1 flex items-center text-[11px] text-emerald-600 font-medium">State & DB automated actions</div>
        </div>

        <div id="metric-card-l3" className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-xs">
          <div className="text-xs font-medium text-slate-500">L3 Human Escalated</div>
          <div className="mt-1 text-2xl font-bold text-rose-600">{escalatedL3}</div>
          <div className="mt-1 flex items-center text-[11px] text-rose-600 font-medium">Human review required</div>
        </div>
      </div>

      {/* Main Continuous Chat Window */}
      <div id="continuous-chat-panel" className="bg-white rounded-xl border border-slate-200/90 shadow-sm overflow-hidden flex flex-col min-h-[620px]">
        {/* Chat Header */}
        <div className="p-4 border-b border-slate-200/80 bg-slate-50/80 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-indigo-600 text-white flex items-center justify-center shadow-xs">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-slate-900">EMS AI Support Dialog</h2>
                {activeTicket && (
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-200 text-slate-700 font-semibold">
                    {activeTicket.ticketCode}
                  </span>
                )}
                {isSatisfied ? (
                  <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                    <span>Resolved & Satisfied</span>
                  </span>
                ) : (
                  <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                    <span>Chat Active (until satisfied)</span>
                  </span>
                )}
              </div>
              <p className="text-[11px] text-slate-500">
                Connected as <strong className="text-slate-700">{currentUser.name}</strong> &bull; {currentUser.role} &bull; Status: <span className={currentUser.status === 'Active' ? 'text-emerald-600 font-semibold' : 'text-rose-600 font-semibold'}>{currentUser.status}</span> &bull; PTO: {currentUser.leaveBalance}d
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {!isSatisfied && activeTicket && (
              <button
                onClick={handleMarkSatisfied}
                id="header-mark-satisfied-btn"
                className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold flex items-center gap-1.5 shadow-2xs transition-colors cursor-pointer"
                title="Mark this session as resolved and satisfied"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>I&apos;m Satisfied</span>
              </button>
            )}

            <button
              onClick={handleResetChat}
              id="new-chat-btn"
              className="px-3 py-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-100 text-slate-700 text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>New Conversation</span>
            </button>
          </div>
        </div>

        {/* Message Feed Container */}
        <div id="chat-messages-container" className="flex-1 p-5 overflow-y-auto space-y-4 bg-slate-50/40 max-h-[500px]">
          {messages.map((msg, index) => {
            const isUser = msg.sender === 'user';
            return (
              <div
                key={msg.id || index}
                id={`chat-msg-${msg.id || index}`}
                className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
              >
                {!isUser && (
                  <div className="w-8 h-8 rounded-full bg-indigo-100 border border-indigo-200 text-indigo-700 flex items-center justify-center shrink-0 mt-0.5">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div className={`max-w-[85%] sm:max-w-[78%] space-y-2.5 ${isUser ? 'items-end text-right' : 'items-start text-left'}`}>
                  {/* Sender & Timestamp */}
                  <div className={`text-[10px] text-slate-400 flex items-center gap-1.5 ${isUser ? 'justify-end' : 'justify-start'}`}>
                    <span className="font-semibold text-slate-600">{isUser ? currentUser.name : 'EMS Support Agent'}</span>
                    <span>&bull;</span>
                    <span>{msg.timestamp}</span>
                    {msg.tier && (
                      <span className={`px-1.5 py-0.2 rounded text-[9px] font-bold ${
                        msg.tier === 'L1' ? 'bg-blue-100 text-blue-800' :
                        msg.tier === 'L2' ? 'bg-emerald-100 text-emerald-800' :
                        'bg-rose-100 text-rose-800'
                      }`}>
                        {msg.tier}
                      </span>
                    )}
                  </div>

                  {/* Message Bubble */}
                  <div
                    className={`p-4 rounded-2xl text-xs leading-relaxed shadow-2xs whitespace-pre-line ${
                      isUser
                        ? 'bg-indigo-600 text-white rounded-tr-xs font-normal'
                        : 'bg-white border border-slate-200/90 text-slate-800 rounded-tl-xs'
                    }`}
                  >
                    {msg.content}
                  </div>

                  {/* Optional L1 Citation Pill */}
                  {!isUser && msg.l1RagResult?.sourceDoc && (
                    <div className="p-2.5 bg-blue-50/70 border border-blue-200/80 rounded-xl text-left text-[11px] text-blue-900 flex items-center justify-between gap-2 shadow-2xs">
                      <div className="flex items-center gap-2">
                        <BookOpen className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                        <span><strong>Policy Source:</strong> {msg.l1RagResult.sourceDoc} &bull; {msg.l1RagResult.matchedArticle}</span>
                      </div>
                      <span className="font-mono text-[10px] text-blue-600 shrink-0 font-bold">
                        {Math.round(msg.l1RagResult.confidence * 100)}% match
                      </span>
                    </div>
                  )}

                  {/* Optional L2 Agent Action Detail Box */}
                  {!isUser && msg.l2AgentsResult && (
                    <div className="p-3 bg-emerald-50/60 border border-emerald-200 rounded-xl text-left text-[11px] space-y-1.5 shadow-2xs">
                      <div className="font-bold text-emerald-900 flex items-center gap-1.5">
                        <Cpu className="w-3.5 h-3.5 text-emerald-600" />
                        <span>LangGraph Multi-Agent Automated Execution</span>
                      </div>
                      <div className="space-y-1 pt-1">
                        {msg.l2AgentsResult.actions.map((act, i) => (
                          <div key={i} className="p-2 rounded bg-white border border-emerald-100 text-slate-700">
                            <span className="font-bold text-emerald-800">{act.agent}:</span> {act.detail}
                          </div>
                        ))}
                      </div>
                      {msg.l2AgentsResult.changesMade && (
                        <div className="text-[10px] font-semibold text-emerald-700 pt-0.5">
                          ✓ State Parity: {msg.l2AgentsResult.changesMade}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Optional L3 Escalation Card */}
                  {!isUser && msg.l3Escalation && (
                    <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-left text-[11px] space-y-1 text-rose-900 shadow-2xs">
                      <div className="font-bold flex items-center gap-1.5 text-rose-700">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        <span>L3 Human Desk Escalation</span>
                      </div>
                      <div>
                        Assigned Specialist: <strong>{msg.l3Escalation.assignedTo}</strong> ({msg.l3Escalation.priority} Priority)
                      </div>
                      <div className="text-[10px] text-rose-600">
                        Routing Protocol: Case added to confidential human review queue with chat transcript.
                      </div>
                    </div>
                  )}

                  {/* Satisfaction Confirmation Checkbar on latest assistant message */}
                  {!isUser && index === messages.length - 1 && !isSatisfied && msg.isSatisfiedPrompt && (
                    <div className="p-3 bg-amber-50/90 border border-amber-200/90 rounded-xl text-left space-y-2 shadow-2xs">
                      <div className="text-xs font-semibold text-amber-900 flex items-center justify-between">
                        <span className="flex items-center gap-1.5">
                          <HelpCircle className="w-3.5 h-3.5 text-amber-600" />
                          <span>Are you satisfied with this answer/resolution?</span>
                        </span>
                        <span className="text-[10px] text-amber-700 font-normal">Chat continues until satisfied</span>
                      </div>
                      <div className="flex flex-wrap gap-2 pt-0.5">
                        <button
                          onClick={handleMarkSatisfied}
                          className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold flex items-center gap-1.5 shadow-xs transition-colors cursor-pointer"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Yes, I&apos;m Satisfied</span>
                        </button>
                        <button
                          onClick={() => {
                            const input = document.getElementById('chat-query-input');
                            input?.focus();
                          }}
                          className="px-2.5 py-1.5 rounded-lg bg-white border border-amber-300 text-amber-800 hover:bg-amber-100 text-xs font-medium flex items-center gap-1 transition-colors cursor-pointer"
                        >
                          <MessageSquare className="w-3.5 h-3.5" />
                          <span>No, I have a follow-up</span>
                        </button>
                        <button
                          onClick={() => handleRunQuery("I want to speak with a human support specialist.")}
                          className="px-2.5 py-1.5 rounded-lg bg-white border border-rose-300 text-rose-700 hover:bg-rose-50 text-xs font-medium flex items-center gap-1 transition-colors cursor-pointer"
                        >
                          <UserCheck className="w-3.5 h-3.5" />
                          <span>Escalate to Human (L3)</span>
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Clickable Suggested Follow-Ups */}
                  {!isUser && index === messages.length - 1 && msg.suggestedFollowUps && msg.suggestedFollowUps.length > 0 && !isSatisfied && (
                    <div className="pt-1 text-left space-y-1.5">
                      <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                        Suggested Follow-Up Queries
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {msg.suggestedFollowUps.map((prompt, pIdx) => (
                          <button
                            key={pIdx}
                            onClick={() => {
                              if (prompt.includes('satisfied')) {
                                handleMarkSatisfied();
                              } else {
                                handleRunQuery(prompt);
                              }
                            }}
                            disabled={isProcessing}
                            className="px-2.5 py-1 rounded-lg bg-white hover:bg-slate-100 border border-slate-200 text-slate-700 text-[11px] font-medium transition-colors shadow-2xs flex items-center gap-1 cursor-pointer disabled:opacity-50"
                          >
                            <span>{prompt}</span>
                            <ChevronRight className="w-3 h-3 text-slate-400" />
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {isUser && (
                  <div className="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center shrink-0 mt-0.5 text-xs font-bold shadow-2xs">
                    {currentUser.name.charAt(0)}
                  </div>
                )}
              </div>
            );
          })}

          {/* Stepper / Processing animation */}
          {isProcessing && (
            <div className="flex gap-3 justify-start">
              <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4 animate-bounce" />
              </div>
              <div className="p-4 bg-white border border-indigo-200 rounded-2xl rounded-tl-xs shadow-xs space-y-2 max-w-[80%]">
                <div className="text-xs font-semibold text-indigo-900 flex items-center gap-2">
                  <div className="w-3 h-3 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
                  <span>Orchestrating Multi-Tier Pipeline...</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[10px]">
                  <div className={`p-1.5 rounded border ${activeStepIndex >= 0 ? 'bg-blue-50 border-blue-200 text-blue-800' : 'bg-slate-50 text-slate-400'}`}>
                    1. RAG Matching
                  </div>
                  <div className={`p-1.5 rounded border ${activeStepIndex >= 1 ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-slate-50 text-slate-400'}`}>
                    2. L2 Agent Diagnostics
                  </div>
                  <div className={`p-1.5 rounded border ${activeStepIndex >= 2 ? 'bg-indigo-50 border-indigo-200 text-indigo-800' : 'bg-slate-50 text-slate-400'}`}>
                    3. Remediation / Triage
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Celebratory Satisfaction Banner */}
          {isSatisfied && (
            <div id="satisfaction-celebration-card" className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl text-left space-y-3 shadow-xs">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-emerald-800 font-bold text-sm">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                  <span>Issue Resolved & User Confirmed Satisfied!</span>
                </div>
                <span className="text-[11px] text-emerald-700 font-mono">
                  {activeTicket ? activeTicket.ticketCode : 'TCK-CONFIRMED'}
                </span>
              </div>
              <p className="text-xs text-emerald-900/90">
                This support session is officially marked resolved. The resolution audit log has been committed to the compliance ledger.
              </p>

              {!feedbackSubmitted ? (
                <div className="space-y-2 pt-1 border-t border-emerald-200">
                  <div className="text-[11px] font-semibold text-emerald-900 flex items-center gap-1.5">
                    <Star className="w-3.5 h-3.5 text-amber-500 fill-amber-500" />
                    <span>How would you rate your support experience?</span>
                  </div>
                  <div className="flex items-center gap-1">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        key={star}
                        onClick={() => setStarRating(star)}
                        className="p-1 text-slate-300 hover:text-amber-400 cursor-pointer transition-colors"
                      >
                        <Star className={`w-5 h-5 ${star <= starRating ? 'text-amber-400 fill-amber-400' : 'text-slate-300'}`} />
                      </button>
                    ))}
                    <span className="text-xs font-semibold text-emerald-800 ml-2">{starRating} of 5 Stars</span>
                  </div>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={feedbackNotes}
                      onChange={(e) => setFeedbackNotes(e.target.value)}
                      placeholder="Optional feedback for support engineering..."
                      className="flex-1 text-xs px-3 py-1.5 bg-white border border-emerald-200 rounded-lg text-slate-800 focus:outline-none"
                    />
                    <button
                      onClick={handleSendFeedback}
                      className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold cursor-pointer"
                    >
                      Submit Rating
                    </button>
                  </div>
                </div>
              ) : (
                <div className="text-xs text-emerald-800 font-medium flex items-center gap-1.5 pt-1">
                  <Smile className="w-4 h-4 text-emerald-600" />
                  <span>Thank you for your rating of {starRating} stars! Your feedback was logged.</span>
                </div>
              )}

              <div className="pt-2 flex items-center justify-between border-t border-emerald-200">
                <span className="text-[11px] text-emerald-700">Need help with something else?</span>
                <button
                  onClick={handleResetChat}
                  className="px-3 py-1 rounded-lg bg-white border border-emerald-300 text-emerald-800 hover:bg-emerald-100 text-xs font-semibold transition-colors cursor-pointer"
                >
                  Start New Session
                </button>
              </div>
            </div>
          )}

          <div ref={chatBottomRef} />
        </div>

        {/* Input Bar (Continuous) */}
        <div className="p-4 border-t border-slate-200 bg-white">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleRunQuery(queryInput);
            }}
            className="space-y-2"
          >
            <div className="flex gap-2">
              <input
                id="chat-query-input"
                type="text"
                value={queryInput}
                onChange={(e) => setQueryInput(e.target.value)}
                placeholder={
                  isSatisfied 
                    ? "Ask another question to continue this conversation, or start a new session..." 
                    : "Type your question or follow-up (the chat continues until you're satisfied)..."
                }
                disabled={isProcessing}
                className="flex-1 text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-slate-800 placeholder:text-slate-400 disabled:bg-slate-50"
              />
              <button
                type="submit"
                id="chat-send-btn"
                disabled={!queryInput.trim() || isProcessing}
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50 shadow-xs cursor-pointer"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Send</span>
              </button>
            </div>

            <div className="flex flex-wrap items-center justify-between text-[11px] text-slate-400 pt-0.5">
              <span>
                Prompting as <strong>{currentUser.name}</strong> ({currentUser.role} &bull; {currentUser.department})
              </span>
              <span className="flex items-center gap-1 text-slate-400">
                <ShieldCheck className="w-3 h-3 text-emerald-500" />
                <span>Encrypted & Audited Enterprise Thread</span>
              </span>
            </div>
          </form>
        </div>
      </div>

      {/* Historical Tickets & Session Ledger */}
      <div id="query-history-section" className="space-y-3 pt-2">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
            <span>Enterprise Ticket History & Chat Sessions</span>
            <span className="text-xs font-normal text-slate-500">({tickets.length} total recorded)</span>
          </h3>
          <span className="text-xs text-slate-400">Click any ticket to view or continue conversation</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {tickets.map((t) => (
            <div
              key={t.id}
              id={`ticket-card-${t.id}`}
              onClick={() => loadPastTicket(t)}
              className={`p-4 rounded-xl bg-white border transition-all cursor-pointer shadow-2xs hover:shadow-xs ${
                activeTicket?.id === t.id ? 'border-indigo-500 ring-1 ring-indigo-500/30' : 'border-slate-200/90 hover:border-slate-300'
              }`}
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    t.currentTier === 'L1'
                      ? 'bg-blue-100 text-blue-700'
                      : t.currentTier === 'L2'
                      ? 'bg-emerald-100 text-emerald-700'
                      : 'bg-rose-100 text-rose-700'
                  }`}>
                    {t.currentTier}
                  </span>
                  <span className="text-xs font-mono font-bold text-slate-700">{t.ticketCode}</span>
                  {t.isSatisfied && (
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-0.5">
                      <CheckCircle2 className="w-2.5 h-2.5" />
                      Satisfied
                    </span>
                  )}
                </div>

                <div className="text-[10px] text-slate-400 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  <span>{t.createdAt}</span>
                </div>
              </div>

              <div className="mt-2 text-xs font-semibold text-slate-900 line-clamp-1">
                &ldquo;{t.query}&rdquo;
              </div>

              <div className="mt-2 p-2 rounded bg-slate-50 text-[11px] text-slate-600 flex items-start gap-1.5">
                <ArrowRight className="w-3 h-3 text-slate-400 shrink-0 mt-0.5" />
                <div className="line-clamp-2">
                  <span>{t.resolutionSummary}</span>
                </div>
              </div>

              <div className="mt-2 text-[10px] text-slate-400 flex items-center justify-between">
                <span>User: {t.userName} ({t.userRole})</span>
                <span className="text-indigo-600 font-medium hover:underline flex items-center gap-0.5">
                  <span>Open in chat</span>
                  <ChevronRight className="w-3 h-3" />
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
