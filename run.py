import os
import sys
import subprocess
import time
import signal

def main():
    port = "3000"
    host = "0.0.0.0"
    for i, arg in enumerate(sys.argv):
        if arg == "--port" and i + 1 < len(sys.argv):
            port = sys.argv[i + 1]
        elif arg == "--host" and i + 1 < len(sys.argv):
            host = sys.argv[i + 1]

    print(f"Starting FastAPI backend on 127.0.0.1:8001...", flush=True)
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8001", "--log-level", "info"],
        env=os.environ.copy()
    )

    # Wait briefly for FastAPI to initialize
    time.sleep(2)

    print(f"Starting Streamlit frontend on {host}:{port}...", flush=True)
    streamlit_proc = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", "frontend/app.py",
            "--server.port", port,
            "--server.address", host,
            "--server.headless", "true",
            "--server.enableCORS", "false",
            "--server.enableXsrfProtection", "false",
            "--browser.gatherUsageStats", "false"
        ],
        env=os.environ.copy()
    )

    def handle_signal(sig, frame):
        print(f"Caught signal {sig}, terminating child processes...")
        backend_proc.terminate()
        streamlit_proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        while True:
            # Check if any process exited unexpectedly
            b_poll = backend_proc.poll()
            s_poll = streamlit_proc.poll()
            if b_poll is not None:
                print(f"Backend process terminated with code {b_poll}")
                streamlit_proc.terminate()
                break
            if s_poll is not None:
                print(f"Streamlit process terminated with code {s_poll}")
                backend_proc.terminate()
                break
            time.sleep(1)
    except KeyboardInterrupt:
        backend_proc.terminate()
        streamlit_proc.terminate()

if __name__ == "__main__":
    main()
