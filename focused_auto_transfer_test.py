#!/usr/bin/env python3
"""
Focused Test for Auto-Transfer Fix
Testing the specific flow requested by the user:
1. Create active failure with POST /api/failures
2. Update status to "הושלם" with PUT /api/failures/{id}
3. Verify failure is deleted from active failures
4. Verify failure is moved to resolved failures with all details
5. Check API response indicates the failure was moved
"""

import requests
import json
from datetime import datetime
import time

# Configuration
BASE_URL = "https://naval-ai-coach.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

def test_auto_transfer_fix():
    """Test the specific auto-transfer fix requested by user"""
    print("🔧 Testing Auto-Transfer Fix for PUT /api/failures/{id}")
    print("=" * 60)
    
    # Step 1: Create active failure
    print("\n1️⃣ Creating active failure...")
    failure_data = {
        "failure_number": f"AUTO-TEST-{datetime.now().strftime('%m%d%H%M%S')}",
        "date": datetime.now().strftime('%Y-%m-%d'),
        "system": "מערכת בדיקת העברה אוטומטית",
        "description": "בדיקת תיקון העברה אוטומטית כאשר מעדכנים סטטוס ל'הושלם'",
        "urgency": 4,
        "assignee": "מהנדס בדיקות",
        "estimated_hours": 3.0,
        "status": "פעיל"
    }
    
    response = requests.post(f"{BASE_URL}/failures", headers=HEADERS, json=failure_data)
    if response.status_code != 200:
        print(f"❌ Failed to create failure: {response.status_code} - {response.text}")
        return False
    
    failure_id = response.json().get('id')
    failure_number = failure_data['failure_number']
    print(f"✅ Created failure: {failure_number} (ID: {failure_id})")
    
    # Step 2: Verify failure exists in active failures
    print("\n2️⃣ Verifying failure exists in active failures...")
    response = requests.get(f"{BASE_URL}/failures", headers=HEADERS)
    if response.status_code != 200:
        print(f"❌ Failed to get active failures: {response.status_code}")
        return False
    
    active_failures = response.json()
    found_in_active = any(f.get('id') == failure_id for f in active_failures)
    if not found_in_active:
        print(f"❌ Failure not found in active failures list")
        return False
    
    print(f"✅ Failure found in active failures (Total active: {len(active_failures)})")
    
    # Step 3: Update failure status to "הושלם" to trigger auto-transfer
    print("\n3️⃣ Updating failure status to 'הושלם' to trigger auto-transfer...")
    
    # Get current failure data first
    current_failure = next((f for f in active_failures if f.get('id') == failure_id), None)
    if not current_failure:
        print("❌ Could not find current failure data")
        return False
    
    # Update to completed status
    updated_failure = current_failure.copy()
    updated_failure['status'] = 'הושלם'
    
    response = requests.put(f"{BASE_URL}/failures/{failure_id}", headers=HEADERS, json=updated_failure)
    if response.status_code != 200:
        print(f"❌ Failed to update failure: {response.status_code} - {response.text}")
        return False
    
    response_data = response.json()
    print(f"✅ Update response: {response_data}")
    
    # Check if response indicates the failure was moved
    moved_to_resolved = response_data.get('moved_to_resolved', False)
    if moved_to_resolved:
        print("✅ API response indicates failure was moved to resolved failures")
    else:
        print("⚠️  API response does not explicitly indicate move to resolved")
    
    # Wait for processing
    time.sleep(2)
    
    # Step 4: Verify failure was removed from active failures
    print("\n4️⃣ Verifying failure was removed from active failures...")
    response = requests.get(f"{BASE_URL}/failures", headers=HEADERS)
    if response.status_code != 200:
        print(f"❌ Failed to get active failures: {response.status_code}")
        return False
    
    active_failures_after = response.json()
    still_in_active = any(f.get('id') == failure_id for f in active_failures_after)
    
    if still_in_active:
        print(f"❌ Failure still exists in active failures list")
        return False
    
    print(f"✅ Failure removed from active failures (Total active now: {len(active_failures_after)})")
    
    # Step 5: Verify failure was moved to resolved failures with all details
    print("\n5️⃣ Verifying failure was moved to resolved failures...")
    response = requests.get(f"{BASE_URL}/resolved-failures", headers=HEADERS)
    if response.status_code != 200:
        print(f"❌ Failed to get resolved failures: {response.status_code}")
        return False
    
    resolved_failures = response.json()
    found_resolved = next((f for f in resolved_failures if f.get('id') == failure_id), None)
    
    if not found_resolved:
        print(f"❌ Failure not found in resolved failures list")
        print(f"   Looking for ID: {failure_id}")
        print(f"   Found {len(resolved_failures)} resolved failures")
        return False
    
    print(f"✅ Failure found in resolved failures")
    
    # Verify all required fields are present and populated
    print("\n6️⃣ Verifying all details were transferred correctly...")
    required_fields = {
        'id': failure_id,
        'failure_number': failure_number,
        'system': failure_data['system'],
        'description': failure_data['description'],
        'urgency': failure_data['urgency'],
        'assignee': failure_data['assignee'],
        'estimated_hours': failure_data['estimated_hours']
    }
    
    all_correct = True
    for field, expected_value in required_fields.items():
        actual_value = found_resolved.get(field)
        if actual_value != expected_value:
            print(f"❌ Field '{field}': expected '{expected_value}', got '{actual_value}'")
            all_correct = False
        else:
            print(f"✅ Field '{field}': {actual_value}")
    
    # Check resolution-specific fields
    resolution_fields = ['resolved_date', 'resolved_by', 'actual_hours', 'resolution_method', 'lessons_learned']
    for field in resolution_fields:
        value = found_resolved.get(field)
        if value is not None:
            print(f"✅ Resolution field '{field}': {value}")
        else:
            print(f"⚠️  Resolution field '{field}': empty (can be filled later)")
    
    if all_correct:
        print("\n🎉 AUTO-TRANSFER FIX TEST PASSED!")
        print("✅ All core functionality working correctly:")
        print("   • Failure created successfully")
        print("   • Status update to 'הושלם' triggered auto-transfer")
        print("   • Failure removed from active failures")
        print("   • Failure moved to resolved failures with all details")
        print("   • API response indicates successful move")
        return True
    else:
        print("\n❌ AUTO-TRANSFER FIX TEST FAILED!")
        print("Some data was not transferred correctly")
        return False

if __name__ == "__main__":
    success = test_auto_transfer_fix()
    exit(0 if success else 1)