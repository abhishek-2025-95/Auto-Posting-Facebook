#!/usr/bin/env python3
"""
Test Facebook API connection
"""

import requests
from config import FACEBOOK_ACCESS_TOKEN, FACEBOOK_PAGE_ID

def test_facebook_connection():
    print("Testing Facebook API connection...")
    print(f"Page ID: {FACEBOOK_PAGE_ID}")
    print(f"Token (first 20 chars): {FACEBOOK_ACCESS_TOKEN[:20]}...")
    
    # Test 1: Get page info
    url = f"https://graph.facebook.com/v18.0/{FACEBOOK_PAGE_ID}"
    params = {
        'access_token': FACEBOOK_ACCESS_TOKEN,
        'fields': 'id,name'
    }
    
    try:
        response = requests.get(url, params=params)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: Connected to page '{data.get('name', 'Unknown')}'")
            return True
        else:
            print(f"FAILED: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    test_facebook_connection()



