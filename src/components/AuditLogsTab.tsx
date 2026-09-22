import React, { useState } from 'react';
import { 
  FileSpreadsheet, 
  Search, 
  Filter, 
  ShieldCheck, 
  AlertTriangle, 
  CheckCircle2, 
  ArrowUpRight,
  Clock
} from 'lucide-react';
import { AuditLog } from '../types';

interface AuditLogsTabProps {
  logs: AuditLog[];
}

export const AuditLogsTab: React.FC<AuditLogsTabProps> = ({ logs }) => {
  const [tierFilter, setTierFilter] = useState('All');
  const [searchTerm, setSearchTerm] = useState('');

  const filteredLogs = logs.filter(log => {
    const matchesTier = tierFilter === 'All' || log.tier === tierFilter;
    const term = searchTerm.toLowerCase();
    const matchesSearch = 
      log.action.toLowerCase().includes(term) ||
      log.userEmail.toLowerCase().includes(term) ||
      log.details.toLowerCase().includes(term) ||
      log.resourceType.toLowerCase().includes(term);
    return matchesTier && matchesSearch;
  });

  return (
    <div id="audit-logs-tab-content" className="space-y-5">
      {/* Header */}
      <div className="bg-white p-5 rounded-xl border border-slate-200/90 shadow-xs space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 text-indigo-600">
              <FileSpreadsheet className="w-5 h-5" />
              <h2 className="text-base font-semibold text-slate-900">Immutable Compliance & Audit Ledger</h2>
            </div>
            <p className="mt-1 text-xs text-slate-500">
              Every L1 retrieval, L2 database mutation, and L3 human assignment is cryptographically indexed for enterprise compliance.
            </p>
          </div>

          <div className="text-xs text-slate-500 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>Total Entries: <strong>{logs.length}</strong></span>
          </div>
        </div>

        {/* Filter bar */}
        <div className="flex flex-col sm:flex-row gap-3 pt-1">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="text"
              id="audit-search-input"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search audit actions, user emails, or details..."
              className="w-full text-xs pl-9 pr-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-800 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              id="audit-tier-filter"
              value={tierFilter}
              onChange={(e) => setTierFilter(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-700 focus:outline-none focus:ring-1 focus:ring-indigo-500 cursor-pointer"
            >
              <option value="All">All Tiers</option>
              <option value="L1">L1 RAG Only</option>
              <option value="L2">L2 Multi-Agent Only</option>
              <option value="L3">L3 Human Desk Only</option>
              <option value="System">System Admin Only</option>
            </select>
          </div>
        </div>
      </div>

      {/* Audit Logs Table */}
      <div className="bg-white rounded-xl border border-slate-200/90 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-medium">
              <tr>
                <th className="p-3.5">Timestamp</th>
                <th className="p-3.5">User / Initiator</th>
                <th className="p-3.5">Tier</th>
                <th className="p-3.5">Action & Resource</th>
                <th className="p-3.5">Status</th>
                <th className="p-3.5">Details & Trail</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
              {filteredLogs.map(log => (
                <tr key={log.id} className="hover:bg-slate-50/70 transition-colors">
                  <td className="p-3.5 text-slate-500 whitespace-nowrap">
                    <div className="flex items-center gap-1.5">
                      <Clock className="w-3 h-3 text-slate-400" />
                      <span>{log.timestamp}</span>
                    </div>
                  </td>
                  <td className="p-3.5 font-sans">
                    <div className="font-semibold text-slate-800">{log.userEmail}</div>
                    <div className="text-[10px] text-slate-400">{log.userRole}</div>
                  </td>
                  <td className="p-3.5">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      log.tier === 'L1'
                        ? 'bg-blue-100/70 text-blue-700'
                        : log.tier === 'L2'
                        ? 'bg-emerald-100/70 text-emerald-700'
                        : log.tier === 'L3'
                        ? 'bg-rose-100/70 text-rose-700'
                        : 'bg-slate-100 text-slate-700'
                    }`}>
                      {log.tier}
                    </span>
                  </td>
                  <td className="p-3.5 font-sans">
                    <span className="font-semibold text-slate-800">{log.action}</span>
                    <span className="text-slate-400 text-[10px] block font-mono">[{log.resourceType}: {log.resourceId || 'N/A'}]</span>
                  </td>
                  <td className="p-3.5">
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold ${
                      log.status === 'SUCCESS' 
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        : log.status === 'ESCALATED'
                        ? 'bg-rose-50 text-rose-700 border border-rose-200'
                        : 'bg-amber-50 text-amber-700 border border-amber-200'
                    }`}>
                      {log.status === 'SUCCESS' ? <CheckCircle2 className="w-3 h-3" /> : <AlertTriangle className="w-3 h-3" />}
                      {log.status}
                    </span>
                  </td>
                  <td className="p-3.5 font-sans text-slate-600 max-w-md">
                    {log.details}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
