import React from 'react';
import { 
  Shield, 
  MessageSquareText, 
  UserCheck, 
  Users, 
  BookOpen, 
  Cpu, 
  FileSpreadsheet,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { Employee } from '../types';

interface SidebarProps {
  employees: Employee[];
  currentUserId: number;
  onSelectUser: (id: number) => void;
  activeTab: string;
  onSelectTab: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  employees,
  currentUserId,
  onSelectUser,
  activeTab,
  onSelectTab
}) => {
  const currentUser = employees.find(e => e.id === currentUserId) || employees[0];

  const navItems = [
    { id: 'portal', label: 'AI Support Portal', icon: MessageSquareText, badge: 'L1/L2/L3' },
    { id: 'human-desk', label: 'L3 Human Support Desk', icon: UserCheck, badge: 'Human' },
    { id: 'directory', label: 'Employee Directory (EMS)', icon: Users, badge: `${employees.length}` },
    { id: 'knowledge-base', label: 'L1 Knowledge Base (RAG)', icon: BookOpen, badge: 'Docs' },
    { id: 'agent-center', label: 'L2 Multi-Agent Center', icon: Cpu, badge: 'Agents' },
    { id: 'audit-logs', label: 'Audit Logs & Compliance', icon: FileSpreadsheet, badge: 'Ledger' },
  ];

  return (
    <aside id="sidebar-container" className="w-80 bg-slate-900 text-slate-100 flex flex-col shrink-0 border-r border-slate-800">
      {/* Brand Header */}
      <div id="sidebar-header" className="p-5 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="w-10 h-10 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-semibold text-white leading-tight tracking-tight">EMS AI Support</h1>
            <p className="text-xs text-slate-400">Multi-Tier Automation</p>
          </div>
        </div>

        <div className="mt-4 flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>Pipeline & Engine Active</span>
        </div>
      </div>

      {/* RBAC Persona Switcher */}
      <div id="sidebar-rbac-section" className="p-4 border-b border-slate-800 bg-slate-950/40">
        <div className="flex items-center justify-between mb-2">
          <label htmlFor="rbac-user-select" className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Active Persona (RBAC)
          </label>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
            {currentUser.role}
          </span>
        </div>

        <select
          id="rbac-user-select"
          value={currentUserId}
          onChange={(e) => onSelectUser(Number(e.target.value))}
          className="w-full text-xs bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-2 text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 cursor-pointer"
        >
          {employees.map(u => (
            <option key={u.id} value={u.id}>
              {u.name} — {u.role} ({u.department})
            </option>
          ))}
        </select>

        {/* User Card */}
        <div className="mt-3 p-3 rounded-lg bg-slate-800/70 border border-slate-700/60 text-xs space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-slate-100">{currentUser.name}</span>
            <span className={`inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full ${
              currentUser.status === 'Active' 
                ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
            }`}>
              {currentUser.status === 'Active' ? <CheckCircle2 className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
              {currentUser.status}
            </span>
          </div>
          <div className="text-slate-400 text-[11px] truncate">{currentUser.jobTitle} &bull; {currentUser.department}</div>
          <div className="grid grid-cols-2 gap-1.5 pt-1 text-[11px] text-slate-300">
            <div className="bg-slate-900/60 px-2 py-1 rounded">
              PTO: <strong className="text-indigo-300">{currentUser.leaveBalance}d</strong>
            </div>
            <div className="bg-slate-900/60 px-2 py-1 rounded">
              Band: <strong className="text-amber-300">{currentUser.salaryBand}</strong>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <nav id="sidebar-navigation" className="flex-1 p-3 space-y-1 overflow-y-auto">
        <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider px-3 py-1.5">
          System Modules
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              id={`nav-btn-${item.id}`}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-colors ${
                isActive 
                  ? 'bg-indigo-600 text-white shadow-sm' 
                  : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </div>
              <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                isActive ? 'bg-indigo-700/80 text-indigo-100' : 'bg-slate-800 text-slate-400'
              }`}>
                {item.badge}
              </span>
            </button>
          );
        })}
      </nav>

      {/* Footer Info */}
      <div id="sidebar-footer" className="p-3 border-t border-slate-800 text-[11px] text-slate-500 flex items-center justify-between">
        <span>L1 RAG &bull; L2 Agents &bull; L3 Desk</span>
        <span className="text-slate-400 font-mono">v1.2.0</span>
      </div>
    </aside>
  );
};
