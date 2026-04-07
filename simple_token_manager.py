#!/usr/bin/env python3
"""
Simple Facebook Token Manager without Unicode characters
"""

import requests
import json
import os
from datetime import datetime, timedelta
from config import FACEBOOK_ACCESS_TOKEN, FACEBOOK_PAGE_ID

class SimpleTokenManager:
    def __init__(self):
        self.current_token = FACEBOOK_ACCESS_TOKEN
        self.page_id = FACEBOOK_PAGE_ID
        
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
    
    def monitor_token_health(self):
        """Monitor token health and alert if issues"""
        print("Monitoring token health...")
        
        # Validate token
        if not self.validate_token(self.current_token):
            print("CRITICAL: Token is invalid!")
            return False
        
        # Check expiry
        is_expired, message = self.check_token_expiry(self.current_token)
        if is_expired:
            print(f"WARNING: {message}")
            return False
        
        print(f"SUCCESS: Token healthy - {message}")
        return True

def test_simple_token_manager():
    """Test the simple token management system"""
    print("="*60)
    print("TESTING SIMPLE FACEBOOK TOKEN MANAGER")
    print("="*60)
    
    manager = SimpleTokenManager()
    
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
    print("SIMPLE TOKEN MANAGER TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_simple_token_manager()


