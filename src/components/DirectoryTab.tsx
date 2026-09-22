import React, { useState } from 'react';
import { 
  Users, 
  Search, 
  Unlock, 
  PlusCircle, 
  RefreshCw, 
  CheckCircle2, 
  AlertCircle,
  ShieldCheck,
  Building
} from 'lucide-react';
import { Employee, AuditLog } from '../types';

interface DirectoryTabProps {
  employees: Employee[];
  currentUser: Employee;
  onUpdateEmployee: (updated: Employee) => void;
  onAddAuditLogs: (logs: AuditLog[]) => void;
}

export const DirectoryTab: React.FC<DirectoryTabProps> = ({
  employees,
  currentUser,
  onUpdateEmployee,
  onAddAuditLogs
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [deptFilter, setDeptFilter] = useState('All');

  const canModify = currentUser.role === 'HR Manager' || currentUser.role === 'System Admin';

  const departments = ['All', ...Array.from(new Set(employees.map(e => e.department)))];

  const filtered = employees.filter(e => {
    const matchesSearch = 
      e.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      e.employeeCode.toLowerCase().includes(searchTerm.toLowerCase()) ||
      e.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      e.jobTitle.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesDept = deptFilter === 'All' || e.department === deptFilter;
    return matchesSearch && matchesDept;
  });

  const handleUnlock = (emp: Employee) => {
    if (!canModify && emp.id !== currentUser.id) return;
    const updated: Employee = { ...emp, status: 'Active' };
    onUpdateEmployee(updated);

    onAddAuditLogs([{
      id: Date.now(),
      timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
      userEmail: currentUser.email,
      userRole: currentUser.role,
      action: 'ADMIN_UNLOCK_EMPLOYEE',
      resourceType: 'EMPLOYEE_STATUS',
      resourceId: emp.employeeCode,
      tier: 'System',
      status: 'SUCCESS',
      details: `${currentUser.name} (${currentUser.role}) unlocked employee ${emp.name} account.`
    }]);
  };

  const handleAddPTO = (emp: Employee) => {
    if (!canModify) return;
    const updated: Employee = { ...emp, leaveBalance: emp.leaveBalance + 5 };
    onUpdateEmployee(updated);

    onAddAuditLogs([{
      id: Date.now(),
      timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
      userEmail: currentUser.email,
      userRole: currentUser.role,
      action: 'ADMIN_ADJUST_LEAVE',
      resourceType: 'EMPLOYEE_LEAVE',
      resourceId: emp.employeeCode,
      tier: 'System',
      status: 'SUCCESS',
      details: `${currentUser.name} granted +5 PTO days to ${emp.name} (New Balance: ${updated.leaveBalance}).`
    }]);
  };

  const handleToggleBenefits = (emp: Employee) => {
    if (!canModify) return;
    const updated: Employee = { ...emp, benefitsEnrolled: !emp.benefitsEnrolled };
    onUpdateEmployee(updated);

    onAddAuditLogs([{
      id: Date.now(),
      timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
      userEmail: currentUser.email,
      userRole: currentUser.role,
      action: 'ADMIN_SYNC_BENEFITS',
      resourceType: 'BENEFITS_STATUS',
      resourceId: emp.employeeCode,
      tier: 'System',
      status: 'SUCCESS',
      details: `${currentUser.name} updated benefits status to ${updated.benefitsEnrolled ? 'Enrolled' : 'Pending'} for ${emp.name}.`
    }]);
  };

  return (
    <div id="directory-tab-content" className="space-y-5">
      {/* Header & Permissions Banner */}
      <div className="bg-white p-5 rounded-xl border border-slate-200/90 shadow-xs space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-indigo-600">
            <Users className="w-5 h-5" />
            <h2 className="text-base font-semibold text-slate-900">EMS Employee Directory & Identity Store</h2>
          </div>

          <div className="flex items-center gap-2">
            <span className={`text-xs px-2.5 py-1 rounded-full font-medium flex items-center gap-1.5 ${
              canModify 
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                : 'bg-slate-100 text-slate-600'
            }`}>
              <ShieldCheck className="w-3.5 h-3.5" />
              {canModify ? 'Admin Write Permissions Active' : 'Read-Only Mode (Employee View)'}
            </span>
          </div>
        </div>

        {/* Search & Filter bar */}
        <div className="flex flex-col sm:flex-row gap-3 pt-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="text"
              id="directory-search-input"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by name, employee code, email, or job title..."
              className="w-full text-xs pl-9 pr-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-800 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          <div className="flex items-center gap-2">
            <Building className="w-4 h-4 text-slate-400" />
            <select
              id="department-filter"
              value={deptFilter}
              onChange={(e) => setDeptFilter(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-700 focus:outline-none focus:ring-1 focus:ring-indigo-500 cursor-pointer"
            >
              {departments.map(d => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Employees Table */}
      <div className="bg-white rounded-xl border border-slate-200/90 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-medium">
              <tr>
                <th className="p-3.5">Code</th>
                <th className="p-3.5">Employee</th>
                <th className="p-3.5">Role & Dept</th>
                <th className="p-3.5">Status</th>
                <th className="p-3.5">PTO Balance</th>
                <th className="p-3.5">Equipment</th>
                <th className="p-3.5">Benefits</th>
                {canModify && <th className="p-3.5 text-right">Admin Actions</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map(emp => (
                <tr key={emp.id} className="hover:bg-slate-50/70 transition-colors">
                  <td className="p-3.5 font-mono font-semibold text-slate-700">{emp.employeeCode}</td>
                  <td className="p-3.5">
                    <div className="font-semibold text-slate-900">{emp.name}</div>
                    <div className="text-[11px] text-slate-400">{emp.email}</div>
                  </td>
                  <td className="p-3.5">
                    <div className="text-slate-800 font-medium">{emp.role}</div>
                    <div className="text-[11px] text-slate-500">{emp.department} &bull; {emp.jobTitle}</div>
                  </td>
                  <td className="p-3.5">
                    <span className={`inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                      emp.status === 'Active'
                        ? 'bg-emerald-100/70 text-emerald-800'
                        : 'bg-rose-100/70 text-rose-800'
                    }`}>
                      {emp.status === 'Active' ? <CheckCircle2 className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
                      {emp.status}
                    </span>
                  </td>
                  <td className="p-3.5">
                    <span className="font-bold text-slate-800">{emp.leaveBalance} days</span>
                    <span className="text-[11px] text-slate-400 block">Sick: {emp.sickLeaveBalance}d</span>
                  </td>
                  <td className="p-3.5">
                    <span className="text-[11px] px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                      {emp.equipmentStatus}
                    </span>
                  </td>
                  <td className="p-3.5">
                    <span className={`text-[11px] font-medium ${emp.benefitsEnrolled ? 'text-emerald-600' : 'text-amber-600'}`}>
                      {emp.benefitsEnrolled ? 'Enrolled' : 'Pending / Error'}
                    </span>
                  </td>
                  {canModify && (
                    <td className="p-3.5 text-right space-x-1.5 whitespace-nowrap">
                      {emp.status === 'Locked' && (
                        <button
                          onClick={() => handleUnlock(emp)}
                          className="px-2 py-1 rounded bg-amber-50 hover:bg-amber-100 text-amber-700 text-[11px] font-medium border border-amber-200 transition-colors inline-flex items-center gap-1 cursor-pointer"
                        >
                          <Unlock className="w-3 h-3" />
                          <span>Unlock</span>
                        </button>
                      )}
                      <button
                        onClick={() => handleAddPTO(emp)}
                        className="px-2 py-1 rounded bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-[11px] font-medium border border-indigo-200 transition-colors inline-flex items-center gap-1 cursor-pointer"
                      >
                        <PlusCircle className="w-3 h-3" />
                        <span>+5 PTO</span>
                      </button>
                      <button
                        onClick={() => handleToggleBenefits(emp)}
                        className="px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] font-medium transition-colors inline-flex items-center gap-1 cursor-pointer"
                      >
                        <RefreshCw className="w-3 h-3" />
                        <span>Sync</span>
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
