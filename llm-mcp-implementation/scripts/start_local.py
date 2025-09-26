#!/usr/bin/env python3
"""
scripts/start_local.py

Bootstraps local Ollama server and FastAPI shim.
Usage: python scripts/start_local.py
"""

import subprocess
import sys
import time
import socket
import shutil
import os
import signal

# Configuration
OLLAMA_CMD = "ollama"
MODEL_NAME = "phi3:mini"
FASTAPI_MODULE = "uvicorn"
FASTAPI_APP = "app.main:app"
FASTAPI_PORT = "8000"

# Helpers
def is_port_in_use(port: int) -> bool:
    """Check if localhost:port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0

def run_subprocess(cmd_list, stdout=None, stderr=None):
    """Start a subprocess; return Popen."""
    return subprocess.Popen(cmd_list, stdout=stdout, stderr=stderr)

def ensure_ollama_running():
    # By default Ollama serves on port 11434
    OLLAMA_PORT = 11434
    if is_port_in_use(OLLAMA_PORT):
        print(f"Ollama appears running on port {OLLAMA_PORT}")
        return None
    # Start Ollama serve
    print("Starting Ollama server...")
    try:
        # On Windows, might need shell=True; but recommend Ollama in PATH
        proc = run_subprocess([OLLAMA_CMD, "serve"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        print("Error: 'ollama' not found in PATH. Please install Ollama.")
        sys.exit(1)
    # Wait briefly for server to start
    for _ in range(10):
        if is_port_in_use(OLLAMA_PORT):
            print("Ollama server is now running.")
            return proc
        time.sleep(0.5)
    print("Warning: Ollama server did not start in time. Check logs.")
    return proc

def ensure_model_pulled():
    # Use `ollama list` to check
    try:
        result = subprocess.run([OLLAMA_CMD, "list"], capture_output=True, text=True)
        if MODEL_NAME in result.stdout:
            print(f"Model {MODEL_NAME} already pulled.")
            return
    except Exception:
        pass
    print(f"Pulling model {MODEL_NAME}...")
    pull = subprocess.run([OLLAMA_CMD, "pull", MODEL_NAME])
    if pull.returncode != 0:
        print(f"Failed to pull model {MODEL_NAME}.")
        sys.exit(1)

def start_fastapi():
    if is_port_in_use(int(FASTAPI_PORT)):
        print(f"FastAPI appears running on port {FASTAPI_PORT}")
        return None
    print("Starting FastAPI server...")
    # uvicorn app.main:app --reload --port 8000
    cmd = [sys.executable, "-m", FASTAPI_MODULE, FASTAPI_APP, "--reload", "--port", FASTAPI_PORT]
    proc = run_subprocess(cmd)
    return proc

def main():
    print("=== Sampatti Local Bootstrap ===")
    ollama_proc = ensure_ollama_running()
    ensure_model_pulled()
    fastapi_proc = start_fastapi()

    print("All services launched. Press Ctrl+C to stop.")
    try:
        # Wait indefinitely; relay output if desired
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down services...")
        # Terminate FastAPI
        if fastapi_proc and fastapi_proc.poll() is None:
            fastapi_proc.terminate()
        # Terminate Ollama
        if ollama_proc and ollama_proc.poll() is None:
            ollama_proc.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()
