"""
L1 Support Tier: Retrieval-Augmented Generation (RAG) for Employee Knowledge Base.
Searches enterprise policies, FAQs, and procedures. If the issue is purely informational
and addressed with high confidence, L1 resolves it. If it requires system actions,
diagnostics, or account remediation, L1 flags it for L2 multi-agent intervention.
"""
import os
import re
import math
from typing import Dict, Any, List, Tuple
from backend.database import get_db_connection
from backend.audit import log_audit

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

def retrieve_relevant_articles(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Retrieves top knowledge base articles matching the employee's query using TF-IDF / keyword scoring.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, category, title, content, keywords, source_doc FROM knowledge_base")
    articles = [dict(r) for r in cursor.fetchall()]
    conn.close()

    query_tokens = set(re.findall(r'\w+', query.lower()))
    scored_articles = []

    for art in articles:
        text_tokens = re.findall(r'\w+', (art["title"] + " " + art["content"] + " " + art["keywords"]).lower())
        token_count = len(text_tokens)
        if token_count == 0:
            continue
        
        matches = sum(1 for token in query_tokens if token in text_tokens)
        
        # Keyword matches have higher weight
        keyword_tokens = re.findall(r'\w+', art["keywords"].lower())
        kw_matches = sum(2 for token in query_tokens if token in keyword_tokens)
        
        # Title matches have highest weight
        title_tokens = re.findall(r'\w+', art["title"].lower())
        title_matches = sum(3 for token in query_tokens if token in title_tokens)
        
        score = (matches + kw_matches + title_matches) / (math.log(token_count + 1) + 1)
        scored_articles.append((score, art))

    scored_articles.sort(key=lambda x: x[0], reverse=True)
    return [art for score, art in scored_articles[:top_k] if score > 0.3]

def query_requires_action_or_diagnosis(query: str) -> Tuple[bool, str]:
    """
    Checks if the user's issue represents a system problem, lockout, mismatch, or request for action
    that cannot be solved by reading text alone and requires L2 Agent intervention.
    """
    q_lower = query.lower()
    
    action_patterns = [
        (r'\b(install|software|docker|vscode|vs code|postman|slack|pycharm|wireshark|tableau|figma|application)\b', "Software installation request requires L2 SoftwareAgent and Support Specialist approval"),
        (r'\b(leave|pto|sick day|vacation|apply for leave|holiday balance|take off|leave balance|pto balance)\b', "Leave request or balance inquiry requires L2 LeaveAgent inspection & processing"),
        (r'\b(attendance|clock in|clock out|missed punch|punch in|punch out|regularize|late arrival|wfh punch|hours worked)\b', "Attendance inquiry or regularization requires L2 AttendanceAgent verification"),
        (r'\b(payroll|payslip|salary|net pay|gross pay|tax deduction|bonus|payday|compensation|bank deposit|401k)\b', "Payroll and compensation inquiry requires L2 PayrollAgent inspection & explanation"),
        (r'\b(network|vpn|wifi|dns|latency|packet loss|ping|gateway|subnet|ip address|connection drop)\b', "Network and connectivity diagnostics require L2 NetworkAgent testing & repair"),
        (r'\b(locked|lockout|can\'t login|cannot log in|access denied|unblock|unlock)\b', "Account lockout or access credentials failure requires L2 Database Agent diagnosis & reset"),
        (r'\b(benefits? (error|pending|missing|not showing|failed|sync|issue))\b', "Benefits enrollment status requires L2 Database Agent synchronization"),
        (r'\b(equipment|laptop|monitor|requisition|repair|broken|hardware stuck)\b', "Hardware requisition / equipment status requires L2 Equipment & IT Agent diagnosis"),
        (r'\b(salary dispute|harassment|grievance|termination|resign|legal|severance)\b', "Sensitive HR/legal issue requires immediate L3 Human escalation"),
        (r'\b(fix|repair|resolve|update|change|correct|modify|approve)\b', "Actionable request detected requiring active system execution beyond informational RAG")
    ]
    
    for pattern, reason in action_patterns:
        if re.search(pattern, q_lower):
            return True, reason
            
    return False, ""

def generate_rag_answer_with_llm(query: str, articles: List[Dict[str, Any]], user_info: Dict[str, Any]) -> str:
    """
    Uses Gemini LLM to formulate an authoritative response if API key is active, or high-fidelity structured summary.
    """
    context_text = "\n\n".join([
        f"Document [{a['source_doc']}] - {a['title']} ({a['category']}):\n{a['content']}"
        for a in articles
    ])
    
    if GEMINI_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=GEMINI_API_KEY,
                temperature=0.2
            )
            prompt = (
                f"You are the L1 AI Tier of the Employee Management Support System for {user_info.get('name', 'the employee')}.\n"
                f"Using ONLY the official knowledge base policies below, provide a clear, accurate, professional resolution.\n"
                f"Cite the source document codes.\n\n"
                f"Knowledge Base Context:\n{context_text}\n\n"
                f"Employee Query:\n{query}\n\n"
                f"Resolution:"
            )
            response = llm.invoke(prompt)
            return response.content
        except Exception as e:
            # Fallback to deterministic formatted response
            pass
            
    # Deterministic fallback response
    top_art = articles[0]
    return (
        f"**Official EMS Policy Reference ({top_art['source_doc']} - {top_art['title']})**:\n\n"
        f"{top_art['content']}\n\n"
        f"*Reference: Department of {top_art['category']} | Knowledge Base Article #{top_art['id']}*"
    )

def process_l1_rag(query: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes L1 Support Tier logic:
    1. Retrieve relevant knowledge base documents.
    2. Check if the query is an actionable database problem or purely informational.
    3. If informational with valid reference -> Resolve at L1.
    4. If action required or no reference found -> Escalate to L2.
    """
    articles = retrieve_relevant_articles(query)
    needs_action, action_reason = query_requires_action_or_diagnosis(query)
    
    # Check if query is actionable
    if needs_action:
        log_audit(
            user_email=user_info.get("email", "unknown"),
            user_role=user_info.get("role", "Employee"),
            action="L1_RAG_EVALUATION",
            resource_type="KNOWLEDGE_BASE",
            tier="L1",
            status="ESCALATED",
            details={
                "query": query,
                "reason": action_reason,
                "decision": "ESCALATE_TO_L2",
                "retrieved_articles_count": len(articles)
            }
        )
        return {
            "tier": "L1",
            "resolved": False,
            "escalate_to": "L2",
            "reason": action_reason,
            "retrieved_articles": articles,
            "message": f"L1 RAG evaluated query: {action_reason}. Escalating to L2 Multi-Agent Tier."
        }
        
    if not articles:
        reason = "No matching knowledge base policy or procedure found in L1 repository."
        log_audit(
            user_email=user_info.get("email", "unknown"),
            user_role=user_info.get("role", "Employee"),
            action="L1_RAG_MISSING_POLICY",
            resource_type="KNOWLEDGE_BASE",
            tier="L1",
            status="ESCALATED",
            details={"query": query, "decision": "ESCALATE_TO_L2"}
        )
        return {
            "tier": "L1",
            "resolved": False,
            "escalate_to": "L2",
            "reason": reason,
            "retrieved_articles": [],
            "message": "L1 RAG could not locate an exact policy match. Escalating to L2 Diagnostic Agents."
        }

    # Informational question successfully resolved at L1
    answer = generate_rag_answer_with_llm(query, articles, user_info)
    
    log_audit(
        user_email=user_info.get("email", "unknown"),
        user_role=user_info.get("role", "Employee"),
        action="L1_RAG_QUERY_RESOLVED",
        resource_type="KNOWLEDGE_BASE",
        resource_id=str(articles[0]["id"]),
        tier="L1",
        status="SUCCESS",
        details={
            "query": query,
            "primary_source": articles[0]["source_doc"],
            "category": articles[0]["category"]
        }
    )
    
    return {
        "tier": "L1",
        "resolved": True,
        "escalate_to": None,
        "answer": answer,
        "retrieved_articles": articles,
        "message": "Resolved by L1 RAG Knowledge Base."
    }
