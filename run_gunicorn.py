#!/usr/bin/env python3
"""
Entry point for running the FastAPI app with gunicorn and uvicorn workers
"""
import subprocess
import sys

if __name__ == "__main__":
    # Run gunicorn with uvicorn worker for FastAPI
    cmd = [
        "gunicorn",
        "--worker-class", "uvicorn.workers.UvicornWorker",
        "--bind", "0.0.0.0:5000", 
        "--reuse-port",
        "--reload",
        "main:app"
    ]
    
    print(f"Starting gunicorn with command: {' '.join(cmd)}")
    subprocess.run(cmd)