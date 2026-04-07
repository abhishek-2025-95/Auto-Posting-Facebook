#!/usr/bin/env python3
"""
Windows Task Scheduler compatible automation starter
This script can be run by Windows Task Scheduler to start the automation system
"""

import os
import sys
import time
import subprocess
from datetime import datetime

def start_automation():
    """Start the automation system"""
    print(f"Starting automation at {datetime.now()}")
    print("="*50)
    
    # Change to the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    try:
        # Run the main automation script
        result = subprocess.run([sys.executable, "main.py"], 
                              capture_output=False, 
                              text=True)
        
        if result.returncode == 0:
            print("Automation completed successfully")
        else:
            print(f"Automation failed with return code: {result.returncode}")
            
    except Exception as e:
        print(f"Error starting automation: {e}")
        return False
    
    return True

if __name__ == "__main__":
    start_automation()


