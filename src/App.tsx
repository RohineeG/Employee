import React, { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { PortalTab } from './components/PortalTab';
import { HumanDeskTab } from './components/HumanDeskTab';
import { DirectoryTab } from './components/DirectoryTab';
import { KnowledgeBaseTab } from './components/KnowledgeBaseTab';
import { AgentCenterTab } from './components/AgentCenterTab';
import { AuditLogsTab } from './components/AuditLogsTab';

import { 
  INITIAL_EMPLOYEES, 
  INITIAL_KNOWLEDGE_BASE, 
  INITIAL_TICKETS, 
  INITIAL_AUDIT_LOGS 
} from './data/initialData';
import { Employee, KnowledgeArticle, SupportTicket, AuditLog } from './types';

export default function App() {
  const [employees, setEmployees] = useState<Employee[]>(INITIAL_EMPLOYEES);
  const [currentUserId, setCurrentUserId] = useState<number>(1);
  const [knowledgeBase, setKnowledgeBase] = useState<KnowledgeArticle[]>(INITIAL_KNOWLEDGE_BASE);
  const [tickets, setTickets] = useState<SupportTicket[]>(INITIAL_TICKETS);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>(INITIAL_AUDIT_LOGS);
  const [activeTab, setActiveTab] = useState<string>('portal');

  const currentUser = employees.find(e => e.id === currentUserId) || employees[0];

  const handleUpdateEmployee = (updated: Employee) => {
    setEmployees(prev => prev.map(e => e.id === updated.id ? updated : e));
  };

  const handleAddTicket = (ticket: SupportTicket) => {
    setTickets(prev => [ticket, ...prev]);
  };

  const handleUpdateTicket = (updated: SupportTicket) => {
    setTickets(prev => prev.map(t => t.id === updated.id ? updated : t));
  };

  const handleAddAuditLogs = (newLogs: AuditLog[]) => {
    setAuditLogs(prev => [...newLogs, ...prev]);
  };

  const handleAddArticle = (newArticle: KnowledgeArticle) => {
    setKnowledgeBase(prev => [newArticle, ...prev]);
  };

  return (
    <div id="ems-app-container" className="flex h-screen w-screen overflow-hidden bg-slate-100 font-sans text-slate-900">
      {/* Navigation Sidebar */}
      <Sidebar
        employees={employees}
        currentUserId={currentUserId}
        onSelectUser={setCurrentUserId}
        activeTab={activeTab}
        onSelectTab={setActiveTab}
      />

      {/* Main View Area */}
      <main id="main-content-scroll" className="flex-1 overflow-y-auto p-6 md:p-8">
        <div className="max-w-6xl mx-auto">
          {activeTab === 'portal' && (
            <PortalTab
              currentUser={currentUser}
              knowledgeBase={knowledgeBase}
              tickets={tickets}
              onAddTicket={handleAddTicket}
              onUpdateTicket={handleUpdateTicket}
              onUpdateEmployee={handleUpdateEmployee}
              onAddAuditLogs={handleAddAuditLogs}
            />
          )}

          {activeTab === 'human-desk' && (
            <HumanDeskTab
              tickets={tickets}
              currentUser={currentUser}
              onUpdateTicket={handleUpdateTicket}
              onAddAuditLogs={handleAddAuditLogs}
            />
          )}

          {activeTab === 'directory' && (
            <DirectoryTab
              employees={employees}
              currentUser={currentUser}
              onUpdateEmployee={handleUpdateEmployee}
              onAddAuditLogs={handleAddAuditLogs}
            />
          )}

          {activeTab === 'knowledge-base' && (
            <KnowledgeBaseTab
              knowledgeBase={knowledgeBase}
              currentUser={currentUser}
              onAddArticle={handleAddArticle}
              onAddAuditLogs={handleAddAuditLogs}
            />
          )}

          {activeTab === 'agent-center' && (
            <AgentCenterTab
              employees={employees}
              currentUser={currentUser}
              onUpdateEmployee={handleUpdateEmployee}
              onAddAuditLogs={handleAddAuditLogs}
            />
          )}

          {activeTab === 'audit-logs' && (
            <AuditLogsTab
              logs={auditLogs}
            />
          )}
        </div>
      </main>
    </div>
  );
}
