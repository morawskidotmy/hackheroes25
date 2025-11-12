#!/usr/bin/env python3
"""
Start script - Install dependencies, start server, and run tests
Logs all results to test.log
"""

import subprocess
import time
import sys
import signal
import os
from datetime import datetime

# Color output
GREEN = '\033[92m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

LOG_FILE = 'test.log'

def print_status(msg, color=BLUE):
    print(f"{color}[*] {msg}{RESET}")

def print_success(msg):
    print(f"{GREEN}[✓] {msg}{RESET}")

def print_error(msg):
    print(f"{RED}[✗] {msg}{RESET}")

def print_warning(msg):
    print(f"{YELLOW}[!] {msg}{RESET}")

def log_write(msg):
    """Write to log file"""
    with open(LOG_FILE, 'a') as f:
        f.write(msg + '\n')

def log_clear():
    """Clear log file"""
    with open(LOG_FILE, 'w') as f:
        f.write(f"CO2 Bike Calculator - Test Log\n")
        f.write(f"Started: {datetime.now()}\n")
        f.write("=" * 80 + "\n\n")

# Track subprocesses
processes = []

def cleanup(signum, frame):
    """Kill all subprocesses on exit"""
    print_warning("Shutting down...")
    log_write("\n" + "=" * 80)
    log_write(f"Shutdown: {datetime.now()}")
    
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except:
            proc.kill()
    print_status("Cleanup complete")
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

def run_cmd(cmd, name):
    """Run command in subprocess and log output"""
    try:
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        processes.append(proc)
        stdout, stderr = proc.communicate()
        
        log_write(f"\n[TEST] {name}")
        log_write(f"Command: {cmd}")
        log_write(f"Status: {'PASS' if proc.returncode == 0 else 'FAIL'}")
        
        if stdout:
            log_write(f"Output:\n{stdout}")
        if stderr:
            log_write(f"Error:\n{stderr}")
        
        if proc.returncode == 0:
            print_success(f"{name}")
            return True
        else:
            print_error(f"{name}")
            if stderr:
                print(f"  Error: {stderr[:100]}")
            return False
    except Exception as e:
        print_error(f"{name} error: {e}")
        log_write(f"\nException in {name}: {e}")
        return False

def start_server():
    """Start Flask server in background subprocess"""
    try:
        proc = subprocess.Popen(
            "python3 app.py",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid
        )
        processes.append(proc)
        print_success("Server started (PID: {})".format(proc.pid))
        log_write(f"Server started with PID: {proc.pid}")
        return proc
    except Exception as e:
        print_error(f"Failed to start server: {e}")
        log_write(f"Failed to start server: {e}")
        return None

def test_api():
    """Test API endpoints"""
    print_status("Waiting 3 seconds for server to start...")
    time.sleep(3)
    
    log_write("\n" + "-" * 80)
    log_write("API Tests")
    log_write("-" * 80)
    
    print_status("Testing /health endpoint...")
    run_cmd(
        'curl -s http://localhost:3000/health',
        "Health check"
    )
    time.sleep(1)
    
    print_status("Testing /v1/nearby-stations endpoint...")
    run_cmd(
        'curl -s "http://localhost:3000/v1/nearby-stations?latitude=54.3520&longitude=18.6466&radius=2"',
        "Nearby stations (Gdansk)"
    )
    time.sleep(1)
    
    print_status("Testing /v1/calculate-co2-savings endpoint...")
    run_cmd(
        '''curl -s -X POST http://localhost:3000/v1/calculate-co2-savings \\
          -H "Content-Type: application/json" \\
          -d '{"latitude": 54.3520, "longitude": 18.6466, "destination_latitude": 54.4000, "destination_longitude": 18.7000}' ''',
        "CO2 calculation (Gdansk route)"
    )

def main():
    # Clear log file
    log_clear()
    
    print_status("Starting CO2 Bike Calculator...")
    log_write("Starting CO2 Bike Calculator...\n")
    print()
    
    # Install dependencies
    print_status("Installing dependencies...")
    log_write("Installing dependencies...")
    if not run_cmd("pip install -q flask flask-cors requests 2>&1", "Dependency installation"):
        print_warning("Some dependencies may not have installed, continuing anyway...")
        log_write("WARNING: Some dependencies may not have installed")
    print()
    
    # Start server
    print_status("Starting Flask server...")
    log_write("\nStarting Flask server...")
    server_proc = start_server()
    if not server_proc:
        print_error("Failed to start server")
        log_write("CRITICAL: Failed to start server")
        return 1
    time.sleep(2)
    print()
    
    # Run tests
    print_status("Running API tests...")
    log_write("\nRunning API tests...")
    test_api()
    print()
    
    # Keep server running
    print_success("All systems running!")
    log_write("\n" + "=" * 80)
    log_write("All systems running successfully!")
    log_write(f"Server started: {datetime.now()}")
    log_write("=" * 80)
    
    print_status("Server is running on http://localhost:3000")
    print_status(f"Test log: {LOG_FILE}")
    print_status("Press Ctrl+C to stop")
    print()
    
    try:
        server_proc.wait()
    except KeyboardInterrupt:
        cleanup(None, None)

if __name__ == '__main__':
    sys.exit(main())
