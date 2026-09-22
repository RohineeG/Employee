"""
System & Server Configuration
Converted from TypeScript vite.config.ts to pure Python.
"""
import os

# Server Ports and Host configurations
HOST = os.getenv("HOST", "0.0.0.0")
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", "8001"))
STREAMLIT_PORT = int(os.getenv("PORT", "3000"))
DISABLE_HMR = os.getenv("DISABLE_HMR", "true").lower() == "true"

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
DIST_DIR = os.path.join(BASE_DIR, "dist")
DATABASE_PATH = os.path.join(BASE_DIR, "ems_support.db")

# Agent and Model Configuration
CONFIG = {
    "host": HOST,
    "fastapi_port": FASTAPI_PORT,
    "streamlit_port": STREAMLIT_PORT,
    "database": DATABASE_PATH,
    "disable_hmr": DISABLE_HMR,
    "tiers": ["L1_RAG", "L2_LANGGRAPH", "L3_HUMAN"],
    "specialized_agents": [
        "LeaveAgent",
        "AttendanceAgent",
        "PayrollAgent",
        "NetworkAgent",
        "SoftwareAgent",
        "DiagnosticsAgent",
        "DatabaseAgent",
        "PolicyVerifier"
    ]
}
