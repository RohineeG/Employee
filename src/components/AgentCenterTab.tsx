import React, { useState } from 'react';
import { 
  Cpu, 
  Workflow, 
  CheckCircle2, 
  ArrowRight, 
  Database, 
  ShieldCheck, 
  Terminal,
  Activity,
  Play
} from 'lucide-react';
import { Employee, AuditLog } from '../types';

interface AgentCenterTabProps {
  employees: Employee[];
  currentUser: Employee;
  onUpdateEmployee: (updated: Employee) => void;
  onAddAuditLogs: (logs: AuditLog[]) => void;
}

export const AgentCenterTab: React.FC<AgentCenterTabProps> = ({
  employees,
  currentUser,
  onUpdateEmployee,
  onAddAuditLogs
}) => {
  const [selectedTargetId, setSelectedTargetId] = useState<number>(employees[1]?.id || employees[0]?.id);
  const [simulationLog, setSimulationLog] = useState<string[]>([]);
  const [isRunningSim, setIsRunningSim] = useState(false);

  const targetEmployee = employees.find(e => e.id === selectedTargetId) || employees[0];

  const agentNodes = [
    {
      name: 'Query Router',
      role: 'Triage & Intent Parser',
      description: 'Parses employee natural language, extracts entities, evaluates if L1 static RAG suffices or if L2 execution is required.',
      color: 'border-blue-300 bg-blue-50/50 text-blue-900'
    },
    {
      name: 'DiagnosticsAgent',
      role: 'State & Security Auditor',
      description: 'Queries Directory Services, checks account lockout flags, investigates anomalous IP histories, audits PTO accrual math.',
      color: 'border-emerald-300 bg-emerald-50/50 text-emerald-900'
    },
    {
      name: 'PolicyAgent',
      role: 'RBAC & Guardrail Validator',
      description: 'Enforces corporate policies (HR-POL-2024, SEC-SOP-04). Ensures no privilege escalation or prohibited mutations occur.',
      color: 'border-purple-300 bg-purple-50/50 text-purple-900'
    },
    {
      name: 'RemediationAgent',
      role: 'Transactional Mutator',
      description: 'Performs safe atomic database operations (unlock status, leave balance reconciliation, benefits synchronization).',
      color: 'border-amber-300 bg-amber-50/50 text-amber-900'
    },
    {
      name: 'VerificationAgent',
      role: 'Post-Execution Verifier',
      description: 'Confirms state parity in target database, checks telemetry feeds, and signs off on the audit log ledger.',
      color: 'border-indigo-300 bg-indigo-50/50 text-indigo-900'
    }
  ];

  const handleRunDiagnostics = async () => {
    setIsRunningSim(true);
    setSimulationLog([]);

    const addLog = (msg: string) => {
      setSimulationLog(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`]);
    };

    addLog(`Initiating LangGraph Multi-Agent execution on target: ${targetEmployee.name} (${targetEmployee.employeeCode})`);
    await new Promise(r => setTimeout(r, 350));

    addLog(`[Router]: Intent recognized -> IDENTITY_DIAGNOSTICS & STATE_CORRECTION.`);
    await new Promise(r => setTimeout(r, 400));

    addLog(`[DiagnosticsAgent]: Querying user record: status=${targetEmployee.status}, leave=${targetEmployee.leaveBalance}d, benefits=${targetEmployee.benefitsEnrolled}.`);
    await new Promise(r => setTimeout(r, 400));

    if (targetEmployee.status === 'Locked') {
      addLog(`[DiagnosticsAgent]: Account locked flag confirmed. Security clearance check: ZERO adverse signals.`);
      await new Promise(r => setTimeout(r, 350));
      addLog(`[PolicyAgent]: Rule SEC-SOP-04 permits automated unlock for non-incident triggers.`);
      await new Promise(r => setTimeout(r, 350));
      addLog(`[RemediationAgent]: Mutating status Locked -> Active in primary database.`);
      
      const updated: Employee = { ...targetEmployee, status: 'Active' };
      onUpdateEmployee(updated);

      onAddAuditLogs([{
        id: Date.now(),
        timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
        userEmail: currentUser.email,
        userRole: currentUser.role,
        action: 'AGENT_SIM_UNLOCK',
        resourceType: 'EMPLOYEE_STATUS',
        resourceId: targetEmployee.employeeCode,
        tier: 'L2',
        status: 'SUCCESS',
        details: `LangGraph RemediationAgent unlocked account for ${targetEmployee.name}.`
      }]);
    } else {
      addLog(`[DiagnosticsAgent]: Account status is healthy (${targetEmployee.status}). Checking leave balance parity.`);
      await new Promise(r => setTimeout(r, 350));
      addLog(`[PolicyAgent]: HR-POL-2024 verified entitlement. Integrity score: 100%.`);
    }

    addLog(`[VerificationAgent]: Execution completed with exit code 0 (SUCCESS). Audit trail written.`);
    setIsRunningSim(false);
  };

  return (
    <div id="agent-center-tab-content" className="space-y-6">
      {/* Header */}
      <div className="bg-white p-5 rounded-xl border border-slate-200/90 shadow-xs">
        <div className="flex items-center gap-2 text-emerald-600">
          <Cpu className="w-5 h-5" />
          <h2 className="text-base font-semibold text-slate-900">L2 LangGraph Multi-Agent Architecture</h2>
        </div>
        <p className="mt-1 text-xs text-slate-500 max-w-3xl">
          Automated multi-agent state machines orchestrate diagnostics, rule validation, and database updates with transaction rollbacks and verifiable audit logs.
        </p>
      </div>

      {/* Multi-Agent Visual Graph */}
      <div className="bg-white p-5 rounded-xl border border-slate-200/90 shadow-xs">
        <div className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-4 flex items-center gap-2">
          <Workflow className="w-4 h-4 text-indigo-600" />
          <span>LangGraph Node Pipeline</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 relative">
          {agentNodes.map((node, i) => (
            <div
              key={i}
              className={`p-4 rounded-xl border ${node.color} flex flex-col justify-between shadow-2xs relative`}
            >
              <div>
                <div className="flex items-center justify-between text-[11px] font-semibold text-slate-500 mb-1">
                  <span>Step 0{i + 1}</span>
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                </div>
                <h3 className="text-sm font-bold text-slate-900">{node.name}</h3>
                <div className="text-[11px] font-medium text-indigo-600 mt-0.5">{node.role}</div>
                <p className="mt-2 text-[11px] text-slate-600 leading-relaxed">
                  {node.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Live Agent Diagnostic Tester */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        <div className="lg:col-span-5 bg-white p-5 rounded-xl border border-slate-200/90 shadow-xs space-y-4">
          <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
            <Activity className="w-4 h-4 text-emerald-600" />
            <span>Interactive Agent Probe</span>
          </h3>

          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-600 block">Select Employee to Inspect:</label>
            <select
              value={selectedTargetId}
              onChange={(e) => setSelectedTargetId(Number(e.target.value))}
              className="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-2.5 text-slate-800"
            >
              {employees.map(e => (
                <option key={e.id} value={e.id}>
                  {e.name} &bull; {e.jobTitle} [{e.status}]
                </option>
              ))}
            </select>
          </div>

          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs space-y-1 text-slate-600">
            <div>Current Status: <strong className={targetEmployee.status === 'Active' ? 'text-emerald-600' : 'text-rose-600'}>{targetEmployee.status}</strong></div>
            <div>PTO Balance: <strong className="text-slate-800">{targetEmployee.leaveBalance} days</strong></div>
            <div>Benefits Sync: <strong className="text-slate-800">{targetEmployee.benefitsEnrolled ? 'Active' : 'Pending'}</strong></div>
            <div>Equipment: <strong className="text-slate-800">{targetEmployee.equipmentStatus}</strong></div>
          </div>

          <button
            onClick={handleRunDiagnostics}
            disabled={isRunningSim}
            className="w-full py-2.5 px-4 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold flex items-center justify-center gap-2 transition-colors disabled:opacity-50 cursor-pointer shadow-xs"
          >
            {isRunningSim ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Executing LangGraph Graph...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5" />
                <span>Execute L2 Agent Diagnostics</span>
              </>
            )}
          </button>
        </div>

        {/* Console / Terminal Log */}
        <div className="lg:col-span-7 bg-slate-950 p-5 rounded-xl border border-slate-800 shadow-md font-mono text-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800 text-slate-400 text-[11px]">
              <span className="flex items-center gap-1.5">
                <Terminal className="w-3.5 h-3.5 text-emerald-400" />
                <span>LangGraph Agent Telemetry Stream</span>
              </span>
              <span className="text-[10px] text-slate-500">JSON-RPC / SQLite</span>
            </div>

            <div className="mt-3 space-y-1.5 min-h-[160px] text-slate-300">
              {simulationLog.length === 0 ? (
                <div className="text-slate-600 italic py-8 text-center">
                  Click &ldquo;Execute L2 Agent Diagnostics&rdquo; to run LangGraph state graph.
                </div>
              ) : (
                simulationLog.map((line, idx) => (
                  <div key={idx} className="leading-relaxed">
                    <span className="text-emerald-400">&gt;</span> {line}
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="pt-3 border-t border-slate-900 text-[10px] text-slate-600 flex items-center justify-between">
            <span>Graph status: {isRunningSim ? 'RUNNING' : 'IDLE'}</span>
            <span>Thread safety: TRANSACTION_ISOLATION_SERIALIZABLE</span>
          </div>
        </div>
      </div>
    </div>
  );
};
