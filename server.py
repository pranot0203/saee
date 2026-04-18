import os
import sys
from waitress import serve
from app import app, init_db

def run_server():
    print("--- DYP-UT Election Portal Server ---")
    
    # 1. Initialize Database
    print("[1/3] Initializing Database...")
    try:
        init_db()
        print("      Success: Database ready.")
    except Exception as e:
        print(f"      Error: Could not initialize database: {e}")
        sys.exit(1)

    # 2. Check for Uploads Folder
    print("[2/3] Checking Static Assets...")
    upload_path = os.path.join('static', 'uploads')
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
        print(f"      Created: {upload_path}")
    else:
        print(f"      Verified: {upload_path} exists.")

    # 3. Start Production Server
    port = int(os.environ.get("PORT", 5000))
    print(f"[3/3] Starting Production Server on port {port}...")
    print(f"--- SERVER LIVE AT: http://localhost:{port} ---")
    print("(Press Ctrl+C to stop)")
    
    serve(app, host='0.0.0.0', port=port)

if __name__ == "__main__":
    run_server()
