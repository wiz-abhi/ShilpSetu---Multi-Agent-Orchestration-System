"""
Script to start the complete system (API + Web Interface)
"""

import subprocess
import sys
import time
import requests
import threading
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'fastapi', 'uvicorn', 'streamlit', 'google-generativeai', 
        'google-cloud-storage', 'pillow', 'moviepy'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Install them with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def check_config():
    """Check if configuration is properly set up"""
    try:
        from config.settings import Config
        Config.validate_config()
        print("✅ Configuration validated")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {str(e)}")
        print("Please check your .env file and ensure all required variables are set")
        return False

def start_api_server(port=8000):
    """Start the API server"""
    print(f"🚀 Starting API server on port {port}...")
    
    try:
        import uvicorn
        from api.workflow_api import app
        
        # Run in a separate thread
        def run_server():
            uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        for i in range(30):  # Wait up to 30 seconds
            try:
                response = requests.get(f"http://localhost:{port}/api/health", timeout=1)
                if response.status_code == 200:
                    print(f"✅ API server started successfully on http://localhost:{port}")
                    return True
            except:
                time.sleep(1)
        
        print("❌ API server failed to start")
        return False
        
    except Exception as e:
        print(f"❌ Failed to start API server: {str(e)}")
        return False

def start_web_interface(api_port=8000, web_port=8501):
    """Start the Streamlit web interface"""
    print(f"🌐 Starting web interface on port {web_port}...")
    
    try:
        # Set environment variable for API URL
        import os
        os.environ['API_BASE_URL'] = f"http://localhost:{api_port}"
        
        # Start Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "web_interface/app.py",
            "--server.port", str(web_port),
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ])
        
    except Exception as e:
        print(f"❌ Failed to start web interface: {str(e)}")

def main():
    """Main function to start the complete system"""
    print("🎨 Artisan Marketplace Multi-Agent System")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check configuration
    if not check_config():
        sys.exit(1)
    
    # Start API server
    api_port = 8000
    if not start_api_server(api_port):
        sys.exit(1)
    
    # Start web interface
    web_port = 8501
    print(f"🌐 Starting web interface...")
    print(f"📱 Web interface will be available at: http://localhost:{web_port}")
    print(f"🔗 API documentation available at: http://localhost:{api_port}/docs")
    print("\n🎉 System started successfully!")
    print("Press Ctrl+C to stop the system")
    
    try:
        start_web_interface(api_port, web_port)
    except KeyboardInterrupt:
        print("\n👋 System stopped by user")
    except Exception as e:
        print(f"❌ System error: {str(e)}")

if __name__ == "__main__":
    main()
