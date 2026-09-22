#!/usr/bin/env python3
"""
Production Build Script for EMS AI Automated Support System
Strictly written in Python.
Builds and packages the application output into dist/ for deployment.
"""
import os
import shutil
import json

def build():
    print("[Python Build] Starting build process...")
    dist_dir = os.path.join(os.getcwd(), "dist")
    
    # Ensure dist directory exists
    os.makedirs(dist_dir, exist_ok=True)
    
    # Copy public assets if they exist
    public_dir = os.path.join(os.getcwd(), "public")
    if os.path.exists(public_dir):
        dist_public = os.path.join(dist_dir, "public")
        if os.path.exists(dist_public):
            shutil.rmtree(dist_public)
        shutil.copytree(public_dir, dist_public)
    
    # Generate standalone production index.html that connects to the Streamlit app
    index_html_path = os.path.join(dist_dir, "index.html")
    with open(index_html_path, "w", encoding="utf-8") as f:
        f.write("""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>EMS AI Automated Support System</title>
  <meta name="description" content="Pure Python Multi-tiered AI support system for Employee Management Systems featuring L1 RAG, L2 LangGraph multi-agent diagnostic and database resolution, L3 human escalation, role-based access control, and comprehensive audit logs.">
  <style>
    body, html {
      margin: 0;
      padding: 0;
      width: 100%;
      height: 100%;
      overflow: hidden;
      background-color: #F8FAFC;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    iframe {
      width: 100%;
      height: 100%;
      border: none;
    }
    .loading-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100vh;
      color: #1E293B;
    }
    .spinner {
      border: 4px solid #E2E8F0;
      border-top: 4px solid #2563EB;
      border-radius: 50%;
      width: 40px;
      height: 40px;
      animation: spin 1s linear infinite;
      margin-bottom: 16px;
    }
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  </style>
</head>
<body>
  <iframe src="/?embed=true" title="EMS AI Automated Support System"></iframe>
</body>
</html>
""")
    
    # Generate metadata build artifact
    build_meta = {
        "app": "EMS AI Automated Support System",
        "engine": "Python (FastAPI + Streamlit + LangGraph)",
        "status": "ready",
        "timestamp": os.path.getmtime(index_html_path)
    }
    with open(os.path.join(dist_dir, "build_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(build_meta, f, indent=2)
        
    print(f"[Python Build] Build succeeded! Generated artifacts in {dist_dir}")

if __name__ == "__main__":
    build()
