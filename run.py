import os
import sys
import subprocess

def start_api():
    """
    Start the Digital Twin Platform API using the correct port.
    """
    print("Starting Digital Twin Platform API...")
    
    # Use port 7777 which we know works
    port = 7777
    
    # Check if port is in use
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    in_use = False
    try:
        sock.bind(('127.0.0.1', port))
    except socket.error:
        in_use = True
    finally:
        sock.close()
    
    if in_use:
        print(f"Warning: Port {port} is already in use!")
        print("You may need to close other applications or choose a different port.")
        response = input(f"Try a different port? (Y/n): ").lower()
        if response != 'n':
            # Try port+1
            port = port + 1
            print(f"Trying port {port} instead...")
    
    print(f"Starting API server on http://127.0.0.1:{port}")
    print("Press CTRL+C to stop the server")
    
    # Run the uvicorn command with the correct port
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--app-dir", os.path.dirname(os.path.abspath(__file__)),
            "--host", "127.0.0.1",
            "--port", str(port)
        ])
    except KeyboardInterrupt:
        print("\nServer stopped")

if __name__ == "__main__":
    start_api()
