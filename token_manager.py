#!/usr/bin/env python3
"""
Facebook Access Token Manager for Automated Systems
Handles token refresh, validation, and automatic renewal
"""

import requests
import json
import os
from datetime import datetime, timedelta
from config import FACEBOOK_ACCESS_TOKEN, FACEBOOK_PAGE_ID

class FacebookTokenManager:
    def __init__(self):
        self.token_file = "facebook_token.json"
        self.current_token = FACEBOOK_ACCESS_TOKEN
        self.page_id = FACEBOOK_PAGE_ID
        self.app_id = None
        self.app_secret = None
        self.long_lived_token = None
        
    def load_token_data(self):
        """Load token data from file"""
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data
            except:
                return {}
        return {}
    
    def save_token_data(self, data):
        """Save token data to file"""
        with open(self.token_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def validate_token(self, token):
        """Validate if token is still active"""
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
    
    def get_token_info(self, token):
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
                print(f"ERROR: Token info error - Status: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"ERROR: Token info error: {e}")
            return None
    
    def check_token_expiry(self, token):
        """Check if token is close to expiry"""
        token_info = self.get_token_info(token)
        
        if not token_info or not token_info['is_valid']:
            return True, "Token is invalid"
        
        expires_at = token_info.get('expires_at', 0)
        
        if expires_at == 0:
            return False, "Token never expires (permanent)"
        
        # Convert Unix timestamp to datetime
        expiry_date = datetime.fromtimestamp(expires_at)
        current_date = datetime.now()
        
        # Check if token expires within 7 days
        days_until_expiry = (expiry_date - current_date).days
        
        if days_until_expiry <= 7:
            return True, f"Token expires in {days_until_expiry} days"
        
        return False, f"Token expires in {days_until_expiry} days"
    
    def extend_token(self, short_lived_token):
        """Extend short-lived token to long-lived token"""
        try:
            # First, get a long-lived user token
            url = "https://graph.facebook.com/v21.0/oauth/access_token"
            params = {
                'grant_type': 'fb_exchange_token',
                'client_id': self.app_id,
                'client_secret': self.app_secret,
                'fb_exchange_token': short_lived_token
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                long_lived_token = data.get('access_token')
                expires_in = data.get('expires_in', 0)
                
                if long_lived_token:
                    print(f"✅ Extended token - Expires in {expires_in} seconds")
                    return long_lived_token, expires_in
                else:
                    print("❌ No long-lived token received")
                    return None, 0
            else:
                print(f"❌ Token extension failed - Status: {response.status_code}")
                return None, 0
                
        except Exception as e:
            print(f"❌ Token extension error: {e}")
            return None, 0
    
    def get_page_access_token(self, user_token):
        """Get page access token from user token"""
        try:
            url = f"https://graph.facebook.com/v21.0/{self.page_id}"
            params = {
                'fields': 'access_token',
                'access_token': user_token
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                page_token = data.get('access_token')
                
                if page_token:
                    print("✅ Page access token obtained")
                    return page_token
                else:
                    print("❌ No page access token received")
                    return None
            else:
                print(f"❌ Page token error - Status: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Page token error: {e}")
            return None
    
    def refresh_token_automatically(self):
        """Automatically refresh token if needed"""
        print("🔄 Checking token status...")
        
        # Load existing token data
        token_data = self.load_token_data()
        
        # Check if current token is valid
        if self.validate_token(self.current_token):
            print("✅ Current token is valid")
            
            # Check expiry
            is_expired, message = self.check_token_expiry(self.current_token)
            if not is_expired:
                print(f"✅ {message}")
                return self.current_token
            else:
                print(f"⚠️ {message}")
        else:
            print("❌ Current token is invalid")
        
        # Try to refresh token
        print("🔄 Attempting to refresh token...")
        
        # Check if we have stored refresh data
        if 'refresh_token' in token_data:
            refresh_token = token_data['refresh_token']
            print("🔄 Using stored refresh token...")
            
            # Try to get new token using refresh token
            new_token = self.refresh_with_stored_token(refresh_token)
            if new_token:
                return new_token
        
        # If no refresh token or it failed, prompt for manual refresh
        print("❌ Automatic refresh failed")
        print("🔧 Manual intervention required:")
        print("1. Go to Facebook Developers Console")
        print("2. Generate new Page Access Token")
        print("3. Update FACEBOOK_ACCESS_TOKEN in config.py")
        print("4. Restart the automation system")
        
        return None
    
    def refresh_with_stored_token(self, refresh_token):
        """Refresh token using stored refresh token"""
        try:
            # This would depend on your specific Facebook app setup
            # For now, return None to indicate manual refresh needed
            print("⚠️ Stored refresh token method not implemented")
            print("💡 Consider implementing OAuth flow for automatic refresh")
            return None
            
        except Exception as e:
            print(f"❌ Refresh error: {e}")
            return None
    
    def setup_automatic_refresh(self):
        """Setup automatic token refresh system"""
        print("🔧 Setting up automatic token refresh...")
        
        # Check if we have the necessary credentials
        if not self.app_id or not self.app_secret:
            print("⚠️ App ID and Secret not configured")
            print("💡 Add APP_ID and APP_SECRET to config.py for automatic refresh")
            return False
        
        # Validate current token
        if not self.validate_token(self.current_token):
            print("❌ Current token is invalid")
            return False
        
        # Check expiry
        is_expired, message = self.check_token_expiry(self.current_token)
        if is_expired:
            print(f"⚠️ {message}")
            print("🔄 Attempting automatic refresh...")
            
            # Try to extend token
            long_lived_token, expires_in = self.extend_token(self.current_token)
            if long_lived_token:
                # Get page access token
                page_token = self.get_page_access_token(long_lived_token)
                if page_token:
                    # Save new token
                    token_data = {
                        'access_token': page_token,
                        'expires_at': datetime.now() + timedelta(seconds=expires_in),
                        'last_updated': datetime.now().isoformat()
                    }
                    self.save_token_data(token_data)
                    
                    print("✅ Token automatically refreshed!")
                    return page_token
        
        print("✅ Token is valid and not expiring soon")
        return self.current_token
    
    def monitor_token_health(self):
        """Monitor token health and alert if issues"""
        print("🔍 Monitoring token health...")
        
        # Validate token
        if not self.validate_token(self.current_token):
            print("❌ CRITICAL: Token is invalid!")
            return False
        
        # Check expiry
        is_expired, message = self.check_token_expiry(self.current_token)
        if is_expired:
            print(f"⚠️ WARNING: {message}")
            return False
        
        print(f"✅ Token healthy: {message}")
        return True

def test_token_manager():
    """Test the token management system"""
    print("="*60)
    print("TESTING FACEBOOK TOKEN MANAGER")
    print("="*60)
    
    manager = FacebookTokenManager()
    
    # Test 1: Validate current token
    print("\n1. Validating current token...")
    is_valid = manager.validate_token(manager.current_token)
    print(f"   Token valid: {is_valid}")
    
    # Test 2: Get token info
    print("\n2. Getting token information...")
    token_info = manager.get_token_info(manager.current_token)
    if token_info:
        print(f"   Valid: {token_info['is_valid']}")
        print(f"   Type: {token_info['type']}")
        print(f"   Scopes: {token_info['scopes']}")
    
    # Test 3: Check expiry
    print("\n3. Checking token expiry...")
    is_expired, message = manager.check_token_expiry(manager.current_token)
    print(f"   Expired: {is_expired}")
    print(f"   Message: {message}")
    
    # Test 4: Monitor health
    print("\n4. Monitoring token health...")
    is_healthy = manager.monitor_token_health()
    print(f"   Healthy: {is_healthy}")
    
    print("\n" + "="*60)
    print("TOKEN MANAGER TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_token_manager()
