#!/usr/bin/env python3
"""
Test script for the history system functionality
"""

import requests
import json
import time
from datetime import datetime

def test_history_system():
    """Test the complete history system"""
    base_url = "http://127.0.0.1:5000"
    
    print("Testing History System")
    print("=" * 50)
    
    try:
        # Test 1: Check if history endpoint exists
        print("\n1. Testing history endpoint...")
        response = requests.get(f"{base_url}/history")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {len(data.get('sessions', []))} sessions")
            print(f"   Pagination: {data.get('pagination', {})}")
        else:
            print(f"   Error: {response.text}")
        
        # Test 2: Check history page
        print("\n2. Testing history page...")
        response = requests.get(f"{base_url}/history-page")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   History page loaded successfully")
        else:
            print(f"   Error loading history page")
        
        # Test 3: Test main page with navigation
        print("\n3. Testing main page navigation...")
        response = requests.get(f"{base_url}/")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200 and "Histórico" in response.text:
            print("   Navigation with history link found")
        else:
            print("   Navigation link might be missing")
        
        print("\n" + "=" * 50)
        print("History System Test Completed")
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the application")
        print("Please make sure the Flask app is running on http://127.0.0.1:5000")
    except Exception as e:
        print(f"Test error: {e}")

if __name__ == "__main__":
    test_history_system()