#!/usr/bin/env python3
"""
Facebook Token Extender
Extends short-lived tokens to long-lived tokens (60 days validity)
"""

import requests
import json
from datetime import datetime, timedelta
from config import FACEBOOK_ACCESS_TOKEN, FACEBOOK_PAGE_ID

def extend_facebook_token(short_lived_token, app_id=None, app_secret=None):
    """
    Extend a short-lived Facebook token to a long-lived token
    """
    print("="*60)
    print("EXTENDING FACEBOOK TOKEN TO LONG-LIVED")
    print("="*60)
    
    try:
        # Step 1: Get long-lived user token
        print("\n1. Extending user token to long-lived...")
        
        url = "https://graph.facebook.com/v21.0/oauth/access_token"
        params = {
            'grant_type': 'fb_exchange_token',
            'client_id': app_id,
            'client_secret': app_secret,
            'fb_exchange_token': short_lived_token
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            long_lived_token = data.get('access_token')
            expires_in = data.get('expires_in', 0)
            
            if long_lived_token:
                print(f"SUCCESS: Long-lived user token obtained")
                print(f"Expires in: {expires_in} seconds ({expires_in/86400:.1f} days)")
                
                # Step 2: Get page access token
                print("\n2. Getting page access token...")
                page_token = get_page_access_token(long_lived_token, FACEBOOK_PAGE_ID)
                
                if page_token:
                    print(f"SUCCESS: Page access token obtained")
                    
                    # Step 3: Validate the new token
                    print("\n3. Validating new token...")
                    if validate_token(page_token):
                        print("SUCCESS: New token is valid and ready to use!")
                        
                        # Step 4: Save token info
                        token_info = {
                            'access_token': page_token,
                            'expires_in': expires_in,
                            'expires_at': datetime.now() + timedelta(seconds=expires_in),
                            'created_at': datetime.now().isoformat(),
                            'token_type': 'long_lived_page_token'
                        }
                        
                        with open('extended_token.json', 'w', encoding='utf-8') as f:
                            json.dump(token_info, f, indent=2, ensure_ascii=False)
                        
                        print(f"\nTOKEN EXTENSION COMPLETE!")
                        print(f"New token: {page_token}")
                        print(f"Expires: {token_info['expires_at']}")
                        print(f"Valid for: {expires_in/86400:.1f} days")
                        
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

def get_page_access_token(user_token, page_id):
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

def get_token_info(token):
    """Get detailed token information"""
    try:
        url = f"https://graph.facebook.com/v21.0/debug_token"
        params = {
            'input_token': token,
            'access_token': token
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            token_data = data.get('data', {})
            
            return {
                'is_valid': token_data.get('is_valid', False),
                'expires_at': token_data.get('expires_at', 0),
                'scopes': token_data.get('scopes', []),
                'app_id': token_data.get('app_id', ''),
                'user_id': token_data.get('user_id', ''),
                'type': token_data.get('type', '')
            }
        else:
            print(f"ERROR: Token info request failed - Status: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"ERROR: Token info error: {e}")
        return None

def main():
    """Main function to extend token"""
    print("FACEBOOK TOKEN EXTENDER")
    print("Extending short-lived token to long-lived token (60 days)")
    print("="*60)
    
    # Check if we have the current token
    if not FACEBOOK_ACCESS_TOKEN or FACEBOOK_ACCESS_TOKEN == "YOUR_FACEBOOK_ACCESS_TOKEN_HERE":
        print("ERROR: No Facebook access token found in config.py")
        print("Please set FACEBOOK_ACCESS_TOKEN in config.py first")
        return
    
    print(f"Current token: {FACEBOOK_ACCESS_TOKEN[:20]}...")
    print(f"Page ID: {FACEBOOK_PAGE_ID}")
    
    # Check if we have app credentials
    app_id = input("\nEnter your Facebook App ID (or press Enter to skip): ").strip()
    app_secret = input("Enter your Facebook App Secret (or press Enter to skip): ").strip()
    
    if not app_id or not app_secret:
        print("\nWARNING: No App ID/Secret provided")
        print("You can still try to extend the token, but it may not work without app credentials")
        print("Continuing with token extension...")
    
    # Try to extend the token
    new_token = extend_facebook_token(FACEBOOK_ACCESS_TOKEN, app_id, app_secret)
    
    if new_token:
        print("\n" + "="*60)
        print("TOKEN EXTENSION SUCCESSFUL!")
        print("="*60)
        print(f"New long-lived token: {new_token}")
        print(f"Valid for: 60 days")
        print("\nNext steps:")
        print("1. Update FACEBOOK_ACCESS_TOKEN in config.py with the new token")
        print("2. Test the new token with: python simple_token_manager.py")
        print("3. Restart your automation system")
    else:
        print("\n" + "="*60)
        print("TOKEN EXTENSION FAILED")
        print("="*60)
        print("Manual steps required:")
        print("1. Go to Facebook Graph API Explorer")
        print("2. Generate new Page Access Token")
        print("3. Update FACEBOOK_ACCESS_TOKEN in config.py")
        print("4. Test with: python simple_token_manager.py")

if __name__ == "__main__":
    main()


