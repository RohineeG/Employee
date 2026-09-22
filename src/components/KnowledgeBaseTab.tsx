import React, { useState } from 'react';
import { 
  BookOpen, 
  Search, 
  Plus, 
  Tag, 
  FileText, 
  Calendar,
  Check,
  ShieldAlert
} from 'lucide-react';
import { KnowledgeArticle, Employee, AuditLog } from '../types';

interface KnowledgeBaseTabProps {
  knowledgeBase: KnowledgeArticle[];
  currentUser: Employee;
  onAddArticle: (article: KnowledgeArticle) => void;
  onAddAuditLogs: (logs: AuditLog[]) => void;
}

export const KnowledgeBaseTab: React.FC<KnowledgeBaseTabProps> = ({
  knowledgeBase,
  currentUser,
  onAddArticle,
  onAddAuditLogs
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newCategory, setNewCategory] = useState('General Policy');
  const [newContent, setNewContent] = useState('');
  const [newKeywords, setNewKeywords] = useState('');
  const [newDocId, setNewDocId] = useState('HR-SOP-2024-');

  const canAdd = currentUser.role === 'HR Manager' || currentUser.role === 'System Admin';

  const filteredArticles = knowledgeBase.filter(a => {
    const term = searchTerm.toLowerCase();
    return (
      a.title.toLowerCase().includes(term) ||
      a.category.toLowerCase().includes(term) ||
      a.content.toLowerCase().includes(term) ||
      a.keywords.some(k => k.toLowerCase().includes(term))
    );
  });

  const handleSaveArticle = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newContent.trim()) return;

    const keywordsList = newKeywords.split(',').map(k => k.trim()).filter(Boolean);
    const newArticle: KnowledgeArticle = {
      id: Date.now(),
      title: newTitle.trim(),
      category: newCategory.trim(),
      content: newContent.trim(),
      keywords: keywordsList.length > 0 ? keywordsList : ['policy', 'standard'],
      sourceDoc: newDocId.trim() || 'HR-DOC-2024',
      updatedAt: new Date().toISOString().substring(0, 10)
    };

    onAddArticle(newArticle);

    onAddAuditLogs([{
      id: Date.now(),
      timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
      userEmail: currentUser.email,
      userRole: currentUser.role,
      action: 'KB_ARTICLE_PUBLISHED',
      resourceType: 'KNOWLEDGE_BASE',
      resourceId: newArticle.sourceDoc,
      tier: 'L1',
      status: 'SUCCESS',
      details: `${currentUser.name} published new policy article: "${newArticle.title}"`
    }]);

    setNewTitle('');
    setNewContent('');
    setNewKeywords('');
    setShowAddForm(false);
  };

  return (
    <div id="knowledge-base-tab-content" className="space-y-5">
      {/* Header & Controls */}
      <div className="bg-white p-5 rounded-xl border border-slate-200/90 shadow-xs space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 text-blue-600">
              <BookOpen className="w-5 h-5" />
              <h2 className="text-base font-semibold text-slate-900">L1 Knowledge Base & Semantic Policy Index</h2>
            </div>
            <p className="mt-1 text-xs text-slate-500">
              The primary retrieval corpus queried by the L1 RAG engine before triggering agent actions or human escalation.
            </p>
          </div>

          <div className="flex items-center gap-2">
            {canAdd ? (
              <button
                id="add-kb-article-btn"
                onClick={() => setShowAddForm(!showAddForm)}
                className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>{showAddForm ? 'Cancel Form' : 'Add Policy Article'}</span>
              </button>
            ) : (
              <span className="text-[11px] text-slate-400 flex items-center gap-1 bg-slate-50 px-2.5 py-1 rounded-md border border-slate-200">
                <ShieldAlert className="w-3.5 h-3.5 text-amber-500" />
                <span>Authoring restricted to HR/Admin</span>
              </span>
            )}
          </div>
        </div>

        {/* Search input */}
        <div className="relative pt-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-4" />
          <input
            type="text"
            id="kb-search-input"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search policies by keyword (e.g. pto, vpn, benefits, loaner, reimbursement)..."
            className="w-full text-xs pl-9 pr-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-800 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>
      </div>

      {/* Add Article Form */}
      {showAddForm && (
        <form onSubmit={handleSaveArticle} className="p-5 bg-white rounded-xl border border-indigo-200 shadow-sm space-y-3">
          <h3 className="text-xs font-bold text-indigo-900 uppercase tracking-wider">Publish New Knowledge Base Document</h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="text-[11px] font-semibold text-slate-600 block mb-1">Category</label>
              <input
                type="text"
                value={newCategory}
                onChange={e => setNewCategory(e.target.value)}
                className="w-full text-xs p-2 rounded-lg border border-slate-300"
                required
              />
            </div>
            <div>
              <label className="text-[11px] font-semibold text-slate-600 block mb-1">Doc Code</label>
              <input
                type="text"
                value={newDocId}
                onChange={e => setNewDocId(e.target.value)}
                className="w-full text-xs p-2 rounded-lg border border-slate-300 font-mono"
                required
              />
            </div>
            <div>
              <label className="text-[11px] font-semibold text-slate-600 block mb-1">Keywords (comma-separated)</label>
              <input
                type="text"
                value={newKeywords}
                onChange={e => setNewKeywords(e.target.value)}
                placeholder="e.g. stipend, remote, wifi"
                className="w-full text-xs p-2 rounded-lg border border-slate-300"
              />
            </div>
          </div>
          <div>
            <label className="text-[11px] font-semibold text-slate-600 block mb-1">Document Title</label>
            <input
              type="text"
              value={newTitle}
              onChange={e => setNewTitle(e.target.value)}
              placeholder="e.g. Remote Work Stipend & Internet Expense Policy"
              className="w-full text-xs p-2 rounded-lg border border-slate-300"
              required
            />
          </div>
          <div>
            <label className="text-[11px] font-semibold text-slate-600 block mb-1">Full Policy Content</label>
            <textarea
              rows={4}
              value={newContent}
              onChange={e => setNewContent(e.target.value)}
              placeholder="Provide exact policy rules, eligibility, and step-by-step procedures..."
              className="w-full text-xs p-2.5 rounded-lg border border-slate-300"
              required
            />
          </div>
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setShowAddForm(false)}
              className="px-3 py-1.5 rounded-lg text-xs text-slate-600 hover:bg-slate-100"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold cursor-pointer"
            >
              Publish to Corpus
            </button>
          </div>
        </form>
      )}

      {/* Articles Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredArticles.map(article => (
          <div
            key={article.id}
            id={`kb-card-${article.id}`}
            className="bg-white p-5 rounded-xl border border-slate-200/90 shadow-2xs hover:border-slate-300 transition-all flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between gap-2">
                <span className="text-[11px] px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 font-semibold border border-blue-100">
                  {article.category}
                </span>
                <span className="text-[11px] font-mono text-slate-400">
                  {article.sourceDoc}
                </span>
              </div>

              <h3 className="mt-2 text-sm font-bold text-slate-900 leading-snug">
                {article.title}
              </h3>

              <p className="mt-2 text-xs text-slate-600 leading-relaxed">
                {article.content}
              </p>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100">
              <div className="flex flex-wrap gap-1 mb-2">
                {article.keywords.map((kw, idx) => (
                  <span key={idx} className="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                    <Tag className="w-2.5 h-2.5 text-slate-400" />
                    {kw}
                  </span>
                ))}
              </div>
              <div className="text-[10px] text-slate-400 flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                <span>Last updated: {article.updatedAt}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
