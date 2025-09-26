#!/usr/bin/env python3
"""
Chrome launcher script for browser automation
"""
import subprocess
import sys
import os
import time
import requests
import platform

def find_chrome_executable():
    """Find Chrome executable based on the platform"""
    system = platform.system().lower()
    
    if system == "windows":
        possible_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.environ.get('USERNAME', '')),
        ]
    elif system == "darwin":  # macOS
        possible_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/usr/bin/google-chrome",
        ]
    else:  # Linux
        possible_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
        ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None

def is_chrome_running():
    """Check if Chrome is already running with remote debugging"""
    try:
        response = requests.get("http://localhost:9222/json/version", timeout=2)
        return response.status_code == 200
    except:
        return False

def start_chrome():
    """Start Chrome with remote debugging enabled"""
    if is_chrome_running():
        print("✅ Chrome is already running with remote debugging on port 9222")
        return True
    
    chrome_path = find_chrome_executable()
    if not chrome_path:
        print("❌ Chrome executable not found. Please install Google Chrome.")
        return False
    
    print(f"🚀 Starting Chrome from: {chrome_path}")
    
    # Create temp directory for Chrome user data
    temp_dir = os.path.join(os.getcwd(), "chrome_temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Chrome arguments
    chrome_args = [
        chrome_path,
        "--remote-debugging-port=9222",
        "--disable-web-security",
        "--disable-extensions",
        "--disable-plugins",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        f"--user-data-dir={temp_dir}",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--start-maximized"
    ]
    
    try:
        # Start Chrome process
        process = subprocess.Popen(
            chrome_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0
        )
        
        # Wait for Chrome to start
        print("⏳ Waiting for Chrome to start...")
        for i in range(10):
            time.sleep(1)
            if is_chrome_running():
                print(f"✅ Chrome started successfully! Remote debugging available at http://localhost:9222")
                return True
            print(f"   Waiting... ({i+1}/10)")
        
        print("❌ Chrome failed to start with remote debugging")
        return False
        
    except Exception as e:
        print(f"❌ Error starting Chrome: {e}")
        return False

def main():
    """Main function"""
    print("🔧 Chrome Browser Automation Setup")
    print("=" * 40)
    
    if start_chrome():
        print("\n🎉 Chrome is ready for automation!")
        print("📋 You can now run your automation scripts.")
        print("🌐 Chrome DevTools: http://localhost:9222")
        print("\n💡 Keep this terminal open while running automation.")
        
        # Keep script running
        try:
            print("\n⏸️  Press Ctrl+C to stop Chrome...")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")
    else:
        print("\n❌ Failed to start Chrome. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()