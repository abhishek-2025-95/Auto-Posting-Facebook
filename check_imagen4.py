#!/usr/bin/env python3
"""
Quick Imagen 4 Status Check
"""

from content_generator import generate_image_with_imagen4
from datetime import datetime

def check_imagen4_status():
    """Check if Imagen 4 is working"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Testing Imagen 4 status...")
    
    try:
        test_prompt = "A simple test image of a red circle on white background"
        result = generate_image_with_imagen4(test_prompt)
        
        if result and "Error" not in str(result):
            print("SUCCESS: Imagen 4 is working!")
            print(f"Generated image: {result}")
            return True
        else:
            print("Imagen 4 not working yet")
            print(f"Error: {result}")
            return False
            
    except Exception as e:
        print(f"Imagen 4 error: {e}")
        return False

if __name__ == "__main__":
    check_imagen4_status()
