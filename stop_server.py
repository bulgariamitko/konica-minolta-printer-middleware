#!/usr/bin/env python3
"""Script to stop the middleware server."""

import subprocess
import sys

def stop_server():
    """Stop any running uvicorn processes."""
    try:
        # Find uvicorn processes
        result = subprocess.run(['pgrep', '-f', 'uvicorn'], capture_output=True, text=True)
        
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    print(f"Stopping process {pid}...")
                    subprocess.run(['kill', pid])
            print("Server stopped successfully!")
        else:
            print("No running server found.")
    
    except Exception as e:
        print(f"Error stopping server: {e}")

if __name__ == "__main__":
    stop_server()