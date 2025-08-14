#!/usr/bin/env python3
"""
Test all completion statuses that should trigger auto-transfer:
- "הושלם"
- "נסגר" 
- "טופל"
"""

import requests
import json
from datetime import datetime
import time

# Configuration
BASE_URL = "https://fleet-mentor.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

def test_completion_status(status_name):
    """Test auto-transfer for a specific completion status"""
    print(f"\n🔧 Testing auto-transfer for status: '{status_name}'")
    print("-" * 50)
    
    # Create active failure
    failure_data = {
        "failure_number": f"STATUS-{status_name}-{datetime.now().strftime('%H%M%S')}",
        "date": datetime.now().strftime('%Y-%m-%d'),
        "system": f"מערכת בדיקת סטטוס {status_name}",
        "description": f"בדיקת העברה אוטומטית עבור סטטוס '{status_name}'",
        "urgency": 3,
        "assignee": "טכנאי בדיקות",
        "estimated_hours": 2.0,
        "status": "פעיל"
    }
    
    response = requests.post(f"{BASE_URL}/failures", headers=HEADERS, json=failure_data)
    if response.status_code != 200:
        print(f"❌ Failed to create failure: {response.status_code}")
        return False
    
    failure_id = response.json().get('id')
    print(f"✅ Created failure: {failure_data['failure_number']} (ID: {failure_id})")
    
    # Get current failure data
    response = requests.get(f"{BASE_URL}/failures", headers=HEADERS)
    if response.status_code != 200:
        print(f"❌ Failed to get active failures: {response.status_code}")
        return False
    
    active_failures = response.json()
    current_failure = next((f for f in active_failures if f.get('id') == failure_id), None)
    if not current_failure:
        print("❌ Could not find current failure data")
        return False
    
    # Update to completion status
    updated_failure = current_failure.copy()
    updated_failure['status'] = status_name
    
    response = requests.put(f"{BASE_URL}/failures/{failure_id}", headers=HEADERS, json=updated_failure)
    if response.status_code != 200:
        print(f"❌ Failed to update failure: {response.status_code}")
        return False
    
    response_data = response.json()
    moved_to_resolved = response_data.get('moved_to_resolved', False)
    
    if moved_to_resolved:
        print(f"✅ Status '{status_name}' triggered auto-transfer")
    else:
        print(f"❌ Status '{status_name}' did not trigger auto-transfer")
        return False
    
    # Wait for processing
    time.sleep(1)
    
    # Verify removal from active and presence in resolved
    response = requests.get(f"{BASE_URL}/failures", headers=HEADERS)
    active_failures_after = response.json()
    still_in_active = any(f.get('id') == failure_id for f in active_failures_after)
    
    response = requests.get(f"{BASE_URL}/resolved-failures", headers=HEADERS)
    resolved_failures = response.json()
    found_in_resolved = any(f.get('id') == failure_id for f in resolved_failures)
    
    if still_in_active:
        print(f"❌ Failure still in active failures")
        return False
    
    if not found_in_resolved:
        print(f"❌ Failure not found in resolved failures")
        return False
    
    print(f"✅ Failure successfully moved from active to resolved")
    return True

def main():
    """Test all completion statuses"""
    print("🚀 Testing All Completion Statuses for Auto-Transfer")
    print("=" * 60)
    
    completion_statuses = ["הושלם", "נסגר", "טופל"]
    results = {}
    
    for status in completion_statuses:
        results[status] = test_completion_status(status)
    
    print("\n" + "=" * 60)
    print("📊 COMPLETION STATUS TEST RESULTS")
    print("=" * 60)
    
    all_passed = True
    for status, passed in results.items():
        status_icon = "✅" if passed else "❌"
        print(f"{status_icon} Status '{status}': {'PASSED' if passed else 'FAILED'}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 ALL COMPLETION STATUSES WORKING CORRECTLY!")
        print("✅ Auto-transfer triggers for: הושלם, נסגר, טופל")
    else:
        print("\n❌ SOME COMPLETION STATUSES FAILED!")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)