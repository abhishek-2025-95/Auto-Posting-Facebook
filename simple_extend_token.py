#!/usr/bin/env python3
"""
Simple Facebook Token Extender
Extends tokens using Facebook's built-in token extension
"""

import requests
import json
from datetime import datetime, timedelta
from config import FACEBOOK_ACCESS_TOKEN, FACEBOOK_PAGE_ID

def extend_token_simple():
    """
    Simple token extension using Facebook's token extension endpoint
    """
    print("="*60)
    print("SIMPLE FACEBOOK TOKEN EXTENSION")
    print("="*60)
    
    try:
        # Use Facebook's token extension endpoint
        url = "https://graph.facebook.com/v21.0/oauth/access_token"
        params = {
            'grant_type': 'fb_exchange_token',
            'client_id': 'your_app_id',  # This will be replaced
            'client_secret': 'your_app_secret',  # This will be replaced
            'fb_exchange_token': FACEBOOK_ACCESS_TOKEN
        }
        
        print(f"Current token: {FACEBOOK_ACCESS_TOKEN[:20]}...")
        print(f"Page ID: {FACEBOOK_PAGE_ID}")
        
        # Get app credentials from user
        app_id = input("\nEnter your Facebook App ID: ").strip()
        app_secret = input("Enter your Facebook App Secret: ").strip()
        
        if not app_id or not app_secret:
            print("ERROR: App ID and Secret are required for token extension")
            return None
        
        # Update params with real credentials
        params['client_id'] = app_id
        params['client_secret'] = app_secret
        
        print("\nExtending token...")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            long_lived_token = data.get('access_token')
            expires_in = data.get('expires_in', 0)
            
            if long_lived_token:
                print(f"SUCCESS: Long-lived token obtained!")
                print(f"Expires in: {expires_in} seconds ({expires_in/86400:.1f} days)")
                
                # Get page access token
                print("\nGetting page access token...")
                page_token = get_page_token(long_lived_token, FACEBOOK_PAGE_ID)
                
                if page_token:
                    print(f"SUCCESS: Page access token obtained!")
                    
                    # Validate new token
                    print("\nValidating new token...")
                    if validate_token(page_token):
                        print("SUCCESS: New token is valid!")
                        
                        # Save token info
                        token_info = {
                            'access_token': page_token,
                            'expires_in': expires_in,
                            'expires_at': datetime.now() + timedelta(seconds=expires_in),
                            'created_at': datetime.now().isoformat(),
                            'token_type': 'long_lived_page_token'
                        }
                        
                        with open('extended_token.json', 'w', encoding='utf-8') as f:
                            json.dump(token_info, f, indent=2, ensure_ascii=False)
                        
                        print("\n" + "="*60)
                        print("TOKEN EXTENSION SUCCESSFUL!")
                        print("="*60)
                        print(f"New long-lived token: {page_token}")
                        print(f"Valid for: {expires_in/86400:.1f} days")
                        print(f"Expires at: {token_info['expires_at']}")
                        
                        return page_token
                    else:
                        print("ERROR: New token validation failed")
                        return None
                else:
                    print("ERROR: Failed to get page access token")
                    return None
            else:
                print("ERROR: No long-lived token received")
                return None
        else:
            print(f"ERROR: Token extension failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"ERROR: Token extension error: {e}")
        return None

def get_page_token(user_token, page_id):
    """Get page access token from user token"""
    try:
        url = f"https://graph.facebook.com/v21.0/{page_id}"
        params = {
            'fields': 'access_token',
            'access_token': user_token
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            page_token = data.get('access_token')
            return page_token
        else:
            print(f"ERROR: Page token request failed - Status: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"ERROR: Page token error: {e}")
        return None

def validate_token(token):
    """Validate if token is working"""
    try:
        url = f"https://graph.facebook.com/v21.0/me"
        params = {
            'access_token': token,
            'fields': 'id,name'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: Token valid - Page: {data.get('name', 'Unknown')}")
            return True
        else:
            print(f"ERROR: Token invalid - Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"ERROR: Token validation error: {e}")
        return False

def main():
    """Main function"""
    print("FACEBOOK TOKEN EXTENDER")
    print("Extending your current token to long-lived (60 days)")
    print("="*60)
    
    if not FACEBOOK_ACCESS_TOKEN or FACEBOOK_ACCESS_TOKEN == "YOUR_FACEBOOK_ACCESS_TOKEN_HERE":
        print("ERROR: No Facebook access token found in config.py")
        return
    
    new_token = extend_token_simple()
    
    if new_token:
        print("\n" + "="*60)
        print("NEXT STEPS:")
        print("="*60)
        print("1. Update FACEBOOK_ACCESS_TOKEN in config.py:")
        print(f"   FACEBOOK_ACCESS_TOKEN = \"{new_token}\"")
        print("\n2. Test the new token:")
        print("   python simple_token_manager.py")
        print("\n3. Restart your automation system")
        print("   python monetization_optimized_schedule.py")
    else:
        print("\n" + "="*60)
        print("TOKEN EXTENSION FAILED")
        print("="*60)
        print("Manual steps required:")
        print("1. Go to Facebook Graph API Explorer")
        print("2. Generate new Page Access Token")
        print("3. Update FACEBOOK_ACCESS_TOKEN in config.py")

if __name__ == "__main__":
    main()


