"""
Application Frontend Bridge
Converted from TypeScript App.tsx to pure Python.
Points to the Streamlit interactive enterprise UI.
"""
import os
import sys

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def run_frontend():
    """Launches the Streamlit EMS AI Support System interface."""
    import subprocess
    cmd = [
        sys.executable, "-m", "streamlit", "run", "frontend/app.py",
        "--server.port", "3000",
        "--server.address", "0.0.0.0",
        "--server.headless", "true"
    ]
    subprocess.run(cmd)

if __name__ == "__main__":
    run_frontend()
