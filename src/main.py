"""
Application Main Entry Point
Converted from TypeScript main.tsx to pure Python.
Orchestrates backend and frontend services.
"""
import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from run import main

if __name__ == "__main__":
    main()
