"""
EMS AI Automated Support System - Streamlit Frontend
Clean, Simple & Modern Architecture
- Frontend: Streamlit
- Backend: FastAPI
- AI: LangChain, LangGraph Multi-Agent Architecture
- Database: SQLite
- Role-Based Access Control (RBAC): Employee, Support, Admin
"""
import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime, date

# Import API Client
from frontend.api_client import (
    get_health, get_roles, get_users, get_user, update_user,
    submit_support_query, get_tickets, get_ticket_detail,
    assign_ticket, resolve_ticket, get_knowledge_base,
    add_kb_article, get_audit_logs, get_stats,
    get_leaves, apply_leave, get_attendance, regularize_attendance,
    get_payroll, get_network_diagnostics, test_and_repair_network,
    get_software_catalog, get_software_requests, submit_software_request,
    approve_and_install_software
)

st.set_page_config(
    page_title="EMS AI Support",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for clean aesthetics
st.markdown("""
<style>
    .stApp {
        background-color: #F8FAFC;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .metric-card {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .badge-role-emp {
        background-color: #EFF6FF;
        color: #1E40AF;
        border: 1px solid #BFDBFE;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 12px;
    }
    .badge-role-sup {
        background-color: #ECFDF5;
        color: #047857;
        border: 1px solid #A7F3D0;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 12px;
    }
    .badge-role-adm {
        background-color: #FAF5FF;
        color: #6B21A8;
        border: 1px solid #E9D5FF;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 12px;
    }
    .badge-active {
        background-color: #DCFCE7;
        color: #166534;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 500;
    }
    .badge-locked {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 500;
    }
    .badge-pending {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 3px 8px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 600;
    }
    .badge-installed {
        background-color: #D1FAE5;
        color: #065F46;
        padding: 3px 8px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- Role Category Helper -----------------
def get_role_category(role_str: str) -> str:
    role = (role_str or "").lower()
    if "admin" in role or "hr" in role or "lead" in role:
        return "Admin"
    elif "support" in role or "it" in role:
        return "Support"
    else:
        return "Employee"

# ----------------- Session State Initialization -----------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user_id" not in st.session_state:
    st.session_state.current_user_id = 1  # Alex Morgan by default
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "input_username" not in st.session_state:
    st.session_state.input_username = "alex.morgan"
if "input_password" not in st.session_state:
    st.session_state.input_password = "password123"
if "input_role" not in st.session_state:
    st.session_state.input_role = "Employee"

# ==============================================================================
# LOGIN SCREEN (WHEN NOT AUTHENTICATED)
# ==============================================================================
if not st.session_state.authenticated:
    st.markdown("""
    <div style="text-align: center; padding: 25px 0 15px 0;">
        <div style="display: inline-block; background: #EEF2F6; padding: 14px 18px; border-radius: 50%; margin-bottom: 10px;">
            <span style="font-size: 36px;">🛡️</span>
        </div>
        <h1 style="color: #0F172A; font-size: 26px; font-weight: 700; margin-bottom: 6px;">EMS Enterprise Login</h1>
        <p style="color: #64748B; font-size: 14px; max-width: 520px; margin: 0 auto;">
            Sign in with your enterprise credentials. Differentiating access between <b>Employee</b>, <b>Support</b>, and <b>Admin</b> roles.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_spacer_left, col_login, col_spacer_right = st.columns([1, 1.8, 1])

    with col_login:
        st.markdown("""
        <div style="background: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 14px;">
            <div style="font-weight: 600; font-size: 15px; color: #1E293B; margin-bottom: 2px;">Enterprise Portal Sign In</div>
            <div style="font-size: 13px; color: #64748B;">Enter your username, password, and assigned role:</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            form_username = st.text_input(
                "Username / Email",
                value=st.session_state.input_username,
                placeholder="e.g. alex.morgan or email address",
                key="field_username"
            )

            form_password = st.text_input(
                "Password",
                value=st.session_state.input_password,
                type="password",
                placeholder="Enter enterprise password",
                key="field_password"
            )

            role_options = ["Employee", "Support", "Admin"]
            current_role_idx = role_options.index(st.session_state.input_role) if st.session_state.input_role in role_options else 0
            form_role = st.selectbox(
                "Role",
                options=role_options,
                index=current_role_idx,
                key="field_role"
            )

            if form_role == "Employee":
                st.caption("🔒 **Employee**: Self-service portal & AI support. **Sensitive payroll access restricted**.")
            elif form_role == "Support":
                st.caption("🎧 **Support**: Operational triage, ticket resolution, software approval & installation.")
            else:
                st.caption("👑 **Admin**: Superuser access. Full payroll ledgers, corporate salary matrices & user management.")

            submit_login = st.form_submit_button("🚀 Log In", use_container_width=True, type="primary")

            if submit_login:
                if not form_username.strip() or not form_password.strip():
                    st.error("Please enter both username and password to log in.")
                else:
                    all_emps = get_users()
                    matched_emp = None
                    uname_clean = form_username.strip().lower()

                    for emp in all_emps:
                        emp_email = emp.get("email", "").lower()
                        emp_name = emp.get("name", "").lower()
                        emp_prefix = emp_email.split("@")[0] if "@" in emp_email else emp_email
                        if uname_clean in emp_email or uname_clean in emp_name or uname_clean == emp_prefix:
                            matched_emp = emp
                            break

                    if not matched_emp:
                        if form_role == "Employee":
                            matched_emp = next((e for e in all_emps if e["id"] == 1), all_emps[0] if all_emps else {"id": 1})
                        elif form_role == "Support":
                            matched_emp = next((e for e in all_emps if e["id"] == 8), all_emps[0] if all_emps else {"id": 8})
                        else:
                            matched_emp = next((e for e in all_emps if e["id"] == 7), all_emps[0] if all_emps else {"id": 7})

                    st.session_state.authenticated = True
                    st.session_state.current_user_id = matched_emp["id"]
                    st.session_state.selected_role = form_role
                    st.session_state.input_username = form_username
                    st.session_state.input_password = form_password
                    st.session_state.input_role = form_role
                    st.rerun()

        st.markdown("---")
        st.caption("💡 **Quick Demo Fill** (One-click presets):")
        c_emp, c_sup, c_adm = st.columns(3)
        with c_emp:
            if st.button("👤 Employee", key="prefill_emp", use_container_width=True):
                st.session_state.input_username = "alex.morgan"
                st.session_state.input_password = "password123"
                st.session_state.input_role = "Employee"
                st.rerun()
        with c_sup:
            if st.button("🎧 Support", key="prefill_sup", use_container_width=True):
                st.session_state.input_username = "sam.carter"
                st.session_state.input_password = "password123"
                st.session_state.input_role = "Support"
                st.rerun()
        with c_adm:
            if st.button("🛡️ Admin", key="prefill_adm", use_container_width=True):
                st.session_state.input_username = "alice.vance"
                st.session_state.input_password = "password123"
                st.session_state.input_role = "Admin"
                st.rerun()

    st.stop()

# ----------------- Active User & Role -----------------
current_user = get_user(st.session_state.current_user_id) or {
    "id": 1, "name": "Alex Morgan", "role": "Employee", "department": "Engineering",
    "job_title": "Software Engineer", "status": "Active", "leave_balance": 14, "equipment_status": "Delivered"
}
user_role_cat = st.session_state.get("selected_role") or get_role_category(current_user["role"])

# ----------------- Simple Sidebar -----------------
with st.sidebar:
    st.markdown("### 🏢 **EMS Portal**")
    
    role_badge_class = "badge-role-emp" if user_role_cat == "Employee" else ("badge-role-sup" if user_role_cat == "Support" else "badge-role-adm")
    status_color = "badge-active" if current_user.get("status") == "Active" else "badge-locked"
    
    st.markdown(f"""
    <div class="metric-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <span style="font-weight: 700; font-size: 15px;">{current_user['name']}</span>
            <span class="{role_badge_class}">{user_role_cat}</span>
        </div>
        <div style="font-size: 13px; color: #64748B;">{current_user.get('job_title', 'Staff')}</div>
        <div style="margin-top: 6px; font-size: 12px; line-height: 1.5;">
            <span>Dept: <b>{current_user.get('department', 'General')}</b></span><br>
            <span>PTO: <b>{current_user.get('leave_balance', 0)} days</b></span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 Sign Out", key="sidebar_logout_btn", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.pop("selected_role", None)
        st.rerun()

    st.markdown("---")
    st.markdown("#### **Navigation**")
    
    nav_options = [
        "💬 AI Support Assistant",
        "📋 My Workplace"
    ]
    if user_role_cat in ["Support", "Admin"]:
        nav_options.append("🛡️ Admin & Support Console")

    nav_selection = st.radio(
        "Menu:",
        nav_options,
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.caption("Switch Persona:")
    users = get_users()
    if users:
        user_options = {u["id"]: f"{u['name']} ({u['role']})" for u in users}
        selected_uid = st.selectbox(
            "User:",
            options=list(user_options.keys()),
            format_func=lambda x: user_options[x],
            index=list(user_options.keys()).index(st.session_state.current_user_id) if st.session_state.current_user_id in user_options else 0,
            key="sidebar_quick_switch",
            label_visibility="collapsed"
        )
        if selected_uid != st.session_state.current_user_id:
            st.session_state.current_user_id = selected_uid
            switched_u = get_user(selected_uid)
            if switched_u:
                st.session_state.selected_role = get_role_category(switched_u["role"])
            st.rerun()

# ==============================================================================
# 1. 💬 AI SUPPORT ASSISTANT (CONVERSATIONAL PORTAL)
# ==============================================================================
if nav_selection == "💬 AI Support Assistant":
    st.markdown("## 💬 AI Support Assistant")
    st.markdown("Ask questions, apply for leave, regularize attendance, check your personal payslip, or request software installations.")

    # 4 Simple Quick-Action Chips
    st.markdown("##### ⚡ Quick Requests:")
    c1, c2, c3, c4 = st.columns(4)
    preset_query = None
    with c1:
        if st.button("🌴 Apply for 2 Days PTO", use_container_width=True):
            preset_query = "What is my current leave balance? Please apply for 2 days PTO starting next Monday."
    with c2:
        if st.button("⏱️ Fix Missed Punch", use_container_width=True):
            preset_query = "Please regularize my missed punch for this week's attendance."
    with c3:
        if st.button("💵 Check My Payslip", use_container_width=True):
            preset_query = "Please show my latest itemized payslip with gross pay and deductions."
    with c4:
        if st.button("💻 Request Docker", use_container_width=True):
            preset_query = "Please install Docker Desktop on my workstation."

    st.markdown("")

    with st.form("support_query_form", clear_on_submit=True):
        user_query_input = st.text_input(
            "Type your request:",
            value=preset_query if preset_query else "",
            placeholder="e.g. Apply for leave, fix attendance punch, show payslip, or request software...",
            key="chat_text_input"
        )
        submit_btn = st.form_submit_button("Send Request 🚀", use_container_width=True, type="primary")

    if submit_btn and user_query_input.strip():
        with st.spinner("Processing request with specialized agents..."):
            res = submit_support_query(st.session_state.current_user_id, user_query_input.strip())
            st.session_state.chat_history.insert(0, {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "user": current_user["name"],
                "query": user_query_input.strip(),
                "response": res
            })

    # Render Chat History
    if st.session_state.chat_history:
        st.markdown("---")
        st.markdown("### Recent Requests & Resolutions")
        for item in st.session_state.chat_history:
            res = item["response"]
            is_res = res.get("is_resolved", False)
            status_icon = "✅" if is_res else "⏳"
            
            st.markdown(f"""
            <div style="background: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                    <b>{item['user']}</b>
                    <span style="color: #64748B; font-size: 12px;">{item['timestamp']}</span>
                </div>
                <div style="background: #F8FAFC; padding: 8px 12px; border-radius: 6px; font-size: 13px; margin-bottom: 8px;">
                    <b>Request:</b> {item['query']}
                </div>
                <div style="font-size: 14px; color: #1E293B;">
                    {status_icon} <b>Resolution:</b> {res.get('message', 'Processed')}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if "Awaiting Support Agent Approval" in res.get("message", ""):
                st.info("💡 **Status**: A Support Specialist has been notified to approve this installation.")

# ==============================================================================
# 2. 📋 MY WORKPLACE (SELF-SERVICE PORTAL)
# ==============================================================================
elif nav_selection == "📋 My Workplace":
    st.markdown("## 📋 My Workplace Self-Service Portal")
    st.markdown("Manage your personal leave, attendance timesheet, software requests, and view your private payslip.")

    tab_leave, tab_pay, tab_soft = st.tabs([
        "🌴 Leaves & Attendance",
        "💵 My Payslip",
        "💻 Software Requests"
    ])

    # TAB 1: LEAVES & ATTENDANCE
    with tab_leave:
        col_l1, col_l2 = st.columns([1, 1])
        
        with col_l1:
            st.markdown("### 🌴 Leave Management")
            m1, m2 = st.columns(2)
            m1.metric("Available PTO", f"{current_user.get('leave_balance', 0)} Days")
            leaves_data = get_leaves(current_user["id"])
            m2.metric("Leave Requests", len(leaves_data))

            with st.form("quick_leave_form"):
                st.markdown("#### Apply for Leave")
                l_type = st.selectbox("Leave Type:", ["PTO", "Sick Leave", "Casual Leave", "Emergency"])
                d1, d2 = st.columns(2)
                with d1:
                    start_d = st.date_input("Start Date:", value=date.today())
                with d2:
                    end_d = st.date_input("End Date:", value=date.today())
                reason = st.text_input("Reason:", value="Personal Time Off")
                sub_l = st.form_submit_button("Submit Leave Application", use_container_width=True)
                if sub_l:
                    days_cnt = max(1, (end_d - start_d).days + 1)
                    res = apply_leave(current_user["id"], l_type, str(start_d), str(end_d), days_cnt, reason)
                    if res.get("success"):
                        st.success(res.get("message", "Leave submitted successfully!"))
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(res.get("error", "Failed to apply leave"))

        with col_l2:
            st.markdown("### ⏱️ Attendance & Timesheet")
            att_records = get_attendance(current_user["id"])
            if att_records:
                adf = pd.DataFrame(att_records)
                cols = [c for c in ["date", "clock_in", "clock_out", "total_hours", "status"] if c in adf.columns]
                st.dataframe(adf[cols], use_container_width=True)
                
                has_missed = any(r.get("status") == "Missed_Punch" for r in att_records)
                if has_missed:
                    st.warning("⚠️ You have a missed punch on your record.")
                    if st.button("⚡ 1-Click Fix Missed Punch", use_container_width=True):
                        reg_res = regularize_attendance(current_user["id"], "Missed clock-out regularized via self-service portal")
                        if reg_res.get("success"):
                            st.success(reg_res.get("message", "Attendance regularized!"))
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(reg_res.get("error", "Failed to regularize"))
                else:
                    st.success("✅ Attendance timesheet is complete and in good standing.")

    # TAB 2: MY PAYSLIP (STRICT RBAC ENFORCEMENT)
    with tab_pay:
        st.markdown("### 💵 Personal Payslip Statement")
        
        if user_role_cat == "Employee":
            st.markdown("""
            <div style="background-color: #FEF2F2; border: 1px solid #FECACA; border-radius: 6px; padding: 10px 14px; margin-bottom: 14px;">
                <span style="color: #991B1B; font-size: 13px;">
                    🔒 <b>Privacy Protected:</b> Company-wide payroll rosters, peer salaries, and executive compensation matrices are restricted to Admin & Support roles.
                </span>
            </div>
            """, unsafe_allow_html=True)

        pay_records = get_payroll(current_user["id"], requesting_user_id=current_user["id"])
        if pay_records:
            pay = pay_records[0]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Net Salary Disbursed", f"${pay['net_salary']:,.2f}")
            c2.metric("Salary Band", "Confidential" if user_role_cat == "Employee" else pay.get("salary_band", "N/A"))
            c3.metric("Pay Period", f"{pay['month']} {pay['year']}")
            c4.metric("Disbursement Status", f"{pay['status']}", delta=f"Paid on {pay['payout_date']}")

            st.markdown("---")
            col_earn, col_ded = st.columns(2)
            with col_earn:
                st.markdown("#### Gross Earnings")
                gross = pay['base_salary'] + pay['hra_allowance'] + pay['special_allowance'] + pay['bonus']
                st.write(f"- Base Salary: **${pay['base_salary']:,.2f}**")
                st.write(f"- House Rent Allowance (HRA): **${pay['hra_allowance']:,.2f}**")
                st.write(f"- Special Role Allowance: **${pay['special_allowance']:,.2f}**")
                st.write(f"- Performance Bonus: **${pay['bonus']:,.2f}**")
                st.markdown(f"**Total Gross**: `${gross:,.2f}`")
            with col_ded:
                st.markdown("#### Deductions & Withholdings")
                total_ded = pay['tax_deductions'] + pay['pf_401k_deductions'] + pay['insurance_deduction']
                st.write(f"- Income Tax: **-${pay['tax_deductions']:,.2f}**")
                st.write(f"- 401(k) / Retirement: **-${pay['pf_401k_deductions']:,.2f}**")
                st.write(f"- Healthcare Premium: **-${pay['insurance_deduction']:,.2f}**")
                st.markdown(f"**Total Deductions**: `-${total_ded:,.2f}`")

            st.info(f"Direct Deposit Account: `•••• •••• •••• {pay['bank_account_last4']}`")
        else:
            st.info("No payslip records generated yet for this profile.")

    # TAB 3: SOFTWARE REQUESTS
    with tab_soft:
        st.markdown("### 💻 Software Requests")
        col_s1, col_s2 = st.columns([1, 1])
        
        with col_s1:
            st.markdown("#### Request Software")
            catalog = get_software_catalog()
            if catalog:
                s_choice = st.selectbox(
                    "Select Software Package:",
                    options=[s["name"] for s in catalog],
                    format_func=lambda x: f"{x} ({next(s['category'] for s in catalog if s['name'] == x)})"
                )
                sel_pkg = next(s for s in catalog if s["name"] == s_choice)
                s_just = st.text_input("Business Justification:", value="Required for engineering tasks")
                if st.button("Submit Installation Request", use_container_width=True):
                    res = submit_software_request(current_user["id"], sel_pkg["name"], sel_pkg["version"], s_just)
                    if res.get("success"):
                        st.success(f"Request for {sel_pkg['name']} submitted!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(res.get("error", "Failed to submit request"))

        with col_s2:
            st.markdown("#### My Software Requests")
            reqs = get_software_requests(current_user["id"])
            if reqs:
                for r in reqs:
                    badge = '<span class="badge-pending">⏳ PENDING APPROVAL</span>' if r["status"] == "PENDING_APPROVAL" else '<span class="badge-installed">✅ INSTALLED</span>'
                    st.markdown(f"""
                    <div style="background: white; border: 1px solid #E2E8F0; border-radius: 6px; padding: 12px; margin-bottom: 8px;">
                        <div style="display: flex; justify-content: space-between;">
                            <b>{r['software_name']} (v{r['version']})</b>
                            <div>{badge}</div>
                        </div>
                        <div style="font-size: 12px; color: #64748B; margin-top: 4px;">
                            Requested on: {r['requested_at']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No software requests found.")

# ==============================================================================
# 3. 🛡️ ADMIN & SUPPORT CONSOLE (FOR SUPPORT & ADMIN ROLES)
# ==============================================================================
elif nav_selection == "🛡️ Admin & Support Console":
    st.markdown(f"## 🛡️ Admin & Support Console")
    st.markdown(f"Operational management for **{user_role_cat}** role.")

    tab_apps, tab_corp_pay, tab_emps = st.tabs([
        "📋 Software Approvals & Tickets",
        "💵 Company Payroll & Compensation",
        "👥 Employee Directory"
    ])

    # TAB 1: SOFTWARE APPROVALS & TICKETS
    with tab_apps:
        st.markdown("### Software Installation Approvals")
        pending_soft = [r for r in get_software_requests() if r["status"] == "PENDING_APPROVAL"]
        if not pending_soft:
            st.success("✅ No software installation requests awaiting approval.")
        else:
            for r in pending_soft:
                with st.expander(f"⏳ {r['software_name']} (v{r['version']}) for {r['employee_name']}", expanded=True):
                    st.write(f"- **Employee**: {r['employee_name']} ({r['employee_email']})")
                    st.write(f"- **Software**: `{r['software_name']}` (v{r['version']})")
                    st.write(f"- **Justification**: {r.get('justification', 'Engineering need')}")
                    if st.button(f"✅ Approve & Install {r['software_name']}", key=f"appr_{r['id']}"):
                        with st.spinner("Authorizing and installing..."):
                            inst_res = approve_and_install_software(r["id"], current_user["id"], "Approved by Support")
                            if inst_res.get("success"):
                                st.success("Software approved and installed!")
                                time.sleep(0.5)
                                st.rerun()

        st.markdown("---")
        st.markdown("### Escalated L3 Support Tickets")
        l3_tickets = [t for t in get_tickets(tier="L3") if t["status"] != "Closed"]
        if not l3_tickets:
            st.info("No active tickets escalated to L3.")
        else:
            for t in l3_tickets:
                with st.expander(f"Ticket #{t['ticket_code']} - {t['user_email']}: {t['query'][:50]}..."):
                    st.write(f"**Query**: {t['query']}")
                    st.write(f"**Escalation Summary**: {t.get('resolution_summary', 'Awaiting review')}")
                    if st.button("Mark as Resolved", key=f"res_{t['id']}"):
                        resolve_ticket(t["id"], current_user["id"], "Resolved by Support specialist", "Closed")
                        st.success("Ticket closed!")
                        time.sleep(0.5)
                        st.rerun()

    # TAB 2: COMPANY PAYROLL
    with tab_corp_pay:
        st.markdown("### Company-Wide Payroll Ledger")
        all_pay = get_payroll(requesting_user_id=current_user["id"])
        if all_pay:
            tot_net = sum(p.get("net_salary", 0) for p in all_pay)
            tot_tax = sum(p.get("tax_deductions", 0) for p in all_pay)
            tot_pf = sum(p.get("pf_401k_deductions", 0) for p in all_pay)
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Monthly Net Payroll", f"${tot_net:,.2f}")
            m2.metric("Total Tax Withheld", f"${tot_tax:,.2f}")
            m3.metric("Total 401(k) Contributed", f"${tot_pf:,.2f}")
            m4.metric("Headcount", f"{len(all_pay)} Employees")

            st.markdown("---")
            pdf = pd.DataFrame(all_pay)
            cols = [c for c in ["id", "employee_id", "month", "year", "base_salary", "bonus", "tax_deductions", "net_salary", "salary_band", "status"] if c in pdf.columns]
            st.dataframe(pdf[cols], use_container_width=True)

            st.markdown("#### Corporate Salary Bands")
            bands_data = [
                {"Grade": "L3", "Title": "Associate / Junior", "Base Salary Range": "$50,000 - $75,000", "Bonus": "5%"},
                {"Grade": "L4", "Title": "Mid-Level Professional", "Base Salary Range": "$75,000 - $105,000", "Bonus": "8%"},
                {"Grade": "L5", "Title": "Senior Professional / Specialist", "Base Salary Range": "$105,000 - $145,000", "Bonus": "12%"},
                {"Grade": "L6", "Title": "Lead / Staff / Principal", "Base Salary Range": "$145,000 - $185,000", "Bonus": "15%"},
                {"Grade": "L7", "Title": "Director / Executive", "Base Salary Range": "$185,000 - $240,000+", "Bonus": "20%"},
            ]
            st.dataframe(pd.DataFrame(bands_data), use_container_width=True)
        else:
            st.info("No payroll records found.")

    # TAB 3: EMPLOYEE DIRECTORY
    with tab_emps:
        st.markdown("### Employee Directory")
        emps = get_users()
        if emps:
            edf = pd.DataFrame(emps)
            disp_cols = [c for c in ["id", "employee_code", "name", "email", "role", "department", "job_title", "status", "leave_balance"] if c in edf.columns]
            st.dataframe(edf[disp_cols], use_container_width=True)
