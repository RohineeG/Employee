import React, { useState } from 'react';
import { 
  UserCheck, 
  Clock, 
  AlertCircle, 
  CheckCircle, 
  Filter, 
  User, 
  FileText,
  Save,
  MessageSquare
} from 'lucide-react';
import { SupportTicket, Employee, AuditLog } from '../types';

interface HumanDeskTabProps {
  tickets: SupportTicket[];
  currentUser: Employee;
  onUpdateTicket: (updated: SupportTicket) => void;
  onAddAuditLogs: (logs: AuditLog[]) => void;
}

export const HumanDeskTab: React.FC<HumanDeskTabProps> = ({
  tickets,
  currentUser,
  onUpdateTicket,
  onAddAuditLogs
}) => {
  const [statusFilter, setStatusFilter] = useState<string>('All');
  const [selectedTicketId, setSelectedTicketId] = useState<number | null>(
    tickets.find(t => t.currentTier === 'L3')?.id || (tickets[0] ? tickets[0].id : null)
  );
  const [assigneeInput, setAssigneeInput] = useState('Sam Carter');
  const [resolutionInput, setResolutionInput] = useState('');

  const filteredTickets = tickets.filter(t => {
    if (statusFilter === 'All') return true;
    if (statusFilter === 'L3_Only') return t.currentTier === 'L3' || t.status === 'Escalated_L3';
    return t.status === statusFilter;
  });

  const selectedTicket = tickets.find(t => t.id === selectedTicketId);

  const handleAssign = (ticket: SupportTicket) => {
    const updated: SupportTicket = {
      ...ticket,
      assignedHuman: assigneeInput,
      status: 'In_Review',
      updatedAt: new Date().toISOString().replace('T', ' ').substring(0, 19)
    };
    onUpdateTicket(updated);

    onAddAuditLogs([{
      id: Date.now(),
      timestamp: updated.updatedAt,
      userEmail: currentUser.email,
      userRole: currentUser.role,
      action: 'L3_TICKET_ASSIGNED',
      resourceType: 'SUPPORT_TICKET',
      resourceId: ticket.ticketCode,
      tier: 'L3',
      status: 'SUCCESS',
      details: `Assigned ticket ${ticket.ticketCode} to human specialist ${assigneeInput}.`
    }]);
  };

  const handleResolve = (ticket: SupportTicket) => {
    if (!resolutionInput.trim()) return;
    const now = new Date().toISOString().replace('T', ' ').substring(0, 19);
    const updated: SupportTicket = {
      ...ticket,
      status: 'Closed',
      l3HumanNotes: resolutionInput.trim(),
      resolutionSummary: `Resolved by ${currentUser.name} (L3 Support): ${resolutionInput.trim()}`,
      updatedAt: now
    };
    onUpdateTicket(updated);

    onAddAuditLogs([{
      id: Date.now(),
      timestamp: now,
      userEmail: currentUser.email,
      userRole: currentUser.role,
      action: 'L3_TICKET_RESOLVED',
      resourceType: 'SUPPORT_TICKET',
      resourceId: ticket.ticketCode,
      tier: 'L3',
      status: 'SUCCESS',
      details: `L3 Specialist resolved ticket ${ticket.ticketCode}: ${resolutionInput.slice(0, 50)}...`
    }]);

    setResolutionInput('');
  };

  return (
    <div id="human-desk-tab-content" className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white p-5 rounded-xl border border-slate-200/90 shadow-xs">
        <div>
          <div className="flex items-center gap-2 text-rose-600">
            <UserCheck className="w-5 h-5" />
            <h2 className="text-base font-semibold text-slate-900">L3 Human Escalation & Operations Desk</h2>
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Human specialist intervention queue for sensitive HR grievances, complex payroll adjustments, or unresolvable inquiries.
          </p>
        </div>

        {/* Filter controls */}
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            id="ticket-status-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-1.5 text-slate-700 focus:outline-none focus:ring-1 focus:ring-indigo-500 cursor-pointer"
          >
            <option value="All">All Statuses</option>
            <option value="L3_Only">L3 Escalations Only</option>
            <option value="In_Review">In Review</option>
            <option value="Closed">Closed</option>
          </select>
        </div>
      </div>

      {/* Two Column Layout: Ticket List & Ticket Detail */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left Column: Tickets List */}
        <div className="lg:col-span-5 space-y-3">
          <div className="text-xs font-semibold text-slate-600 uppercase tracking-wider">
            Escalated Tickets ({filteredTickets.length})
          </div>

          <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
            {filteredTickets.map(t => {
              const isSelected = t.id === selectedTicketId;
              return (
                <div
                  key={t.id}
                  id={`human-ticket-item-${t.id}`}
                  onClick={() => setSelectedTicketId(t.id)}
                  className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                    isSelected 
                      ? 'bg-indigo-50/70 border-indigo-300 shadow-xs' 
                      : 'bg-white border-slate-200/90 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-semibold text-slate-800">{t.ticketCode}</span>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${
                      t.currentTier === 'L3' ? 'bg-rose-100 text-rose-700' : 'bg-slate-100 text-slate-600'
                    }`}>
                      {t.status}
                    </span>
                  </div>

                  <div className="mt-1.5 text-xs text-slate-900 font-medium line-clamp-2">
                    {t.query}
                  </div>

                  <div className="mt-2 flex items-center justify-between text-[11px] text-slate-500">
                    <span>{t.userName} &bull; {t.department}</span>
                    {t.assignedHuman && (
                      <span className="text-indigo-600 font-medium">Assigned: {t.assignedHuman}</span>
                    )}
                  </div>
                </div>
              );
            })}

            {filteredTickets.length === 0 && (
              <div className="p-8 text-center bg-white rounded-xl border border-slate-200 text-xs text-slate-400">
                No tickets found for selected criteria.
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Ticket Inspector */}
        <div className="lg:col-span-7">
          {selectedTicket ? (
            <div id="ticket-detail-view" className="bg-white rounded-xl border border-slate-200/90 shadow-xs p-5 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-slate-900">{selectedTicket.ticketCode}</span>
                    <span className={`text-[11px] px-2 py-0.5 rounded-full font-bold ${
                      selectedTicket.priority === 'Critical' 
                        ? 'bg-rose-100 text-rose-700' 
                        : 'bg-amber-100 text-amber-700'
                    }`}>
                      {selectedTicket.priority} Priority
                    </span>
                    {selectedTicket.isSatisfied && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold border border-emerald-200 flex items-center gap-1">
                        <CheckCircle className="w-3 h-3 text-emerald-600" />
                        <span>Satisfied ({selectedTicket.satisfactionRating || 5}★)</span>
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-slate-500 mt-0.5">
                    Requested by: <strong>{selectedTicket.userName}</strong> ({selectedTicket.userRole} &bull; {selectedTicket.department})
                  </div>
                </div>

                <div className="text-right text-xs text-slate-400">
                  Created: {selectedTicket.createdAt}
                </div>
              </div>

              {/* Inquiry Prompt */}
              <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-800">
                <div className="font-semibold text-slate-500 text-[11px] uppercase tracking-wider mb-1">
                  Employee Query:
                </div>
                <div className="font-medium text-slate-900">{selectedTicket.query}</div>
              </div>

              {/* AI Diagnostic Notes */}
              <div className="space-y-1.5 text-xs">
                <div className="font-semibold text-slate-700 flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-slate-500" />
                  <span>AI Diagnostics & Pipeline Summary</span>
                </div>
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-slate-700 leading-relaxed text-[11px]">
                  {selectedTicket.resolutionSummary}
                </div>
              </div>

              {/* Human Assignment Form */}
              <div className="pt-2 border-t border-slate-100 space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <label className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                    <User className="w-3.5 h-3.5 text-indigo-600" />
                    <span>Assign Human Specialist</span>
                  </label>
                  <div className="flex items-center gap-2">
                    <select
                      id="assignee-select"
                      value={assigneeInput}
                      onChange={(e) => setAssigneeInput(e.target.value)}
                      className="text-xs bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-slate-700 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    >
                      <option value="Sam Carter">Sam Carter (L3 Operations Lead)</option>
                      <option value="Alice Vance">Alice Vance (Principal Security Admin)</option>
                      <option value="Rachel Green">Rachel Green (People Operations Director)</option>
                    </select>
                    <button
                      onClick={() => handleAssign(selectedTicket)}
                      className="px-3 py-1.5 bg-slate-800 hover:bg-slate-900 text-white rounded-lg text-xs font-medium cursor-pointer transition-colors"
                    >
                      Assign
                    </button>
                  </div>
                </div>

                {/* Resolution Notes */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                    <MessageSquare className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Resolution Notes & Human Sign-off</span>
                  </label>
                  <textarea
                    id="l3-resolution-textarea"
                    value={resolutionInput}
                    onChange={(e) => setResolutionInput(e.target.value)}
                    placeholder="Enter official human resolution findings, employee interview outcome, or policy exception approval..."
                    rows={3}
                    className="w-full text-xs rounded-lg border border-slate-300 p-2.5 text-slate-800 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                  />
                  <div className="flex justify-end">
                    <button
                      id="resolve-ticket-btn"
                      onClick={() => handleResolve(selectedTicket)}
                      disabled={!resolutionInput.trim()}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg flex items-center gap-1.5 transition-colors disabled:opacity-50 cursor-pointer"
                    >
                      <CheckCircle className="w-3.5 h-3.5" />
                      <span>Complete & Close Ticket</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-slate-200 p-12 text-center text-xs text-slate-400">
              Select a ticket on the left to view detailed diagnostics and take human operational action.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
