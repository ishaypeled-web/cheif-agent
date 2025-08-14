#!/usr/bin/env python3
"""
Debug script to test the auto-transfer functionality
"""

import requests
import json
from datetime import datetime
import time

BASE_URL = "https://fleet-mentor.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

def debug_auto_transfer():
    print("🔍 Debugging Auto-Transfer Functionality")
    print("=" * 50)
    
    # 1. Create a new failure
    failure_data = {
        "failure_number": f"DEBUG-{datetime.now().strftime('%m%d%H%M%S')}",
        "date": datetime.now().strftime('%Y-%m-%d'),
        "system": "מערכת דיבוג",
        "description": "תקלה לבדיקת העברה אוטומטית - דיבוג",
        "urgency": 4,
        "assignee": "טכנאי דיבוג",
        "estimated_hours": 1.0,
        "status": "פעיל"
    }
    
    print("1. Creating new failure...")
    response = requests.post(f"{BASE_URL}/failures", headers=HEADERS, json=failure_data)
    if response.status_code != 200:
        print(f"❌ Failed to create failure: {response.status_code}")
        return
    
    failure_id = response.json().get('id')
    failure_number = failure_data['failure_number']
    print(f"✅ Created failure: {failure_number} (ID: {failure_id})")
    
    # 2. Get the current failure data
    print("\n2. Getting current failure data...")
    response = requests.get(f"{BASE_URL}/failures", headers=HEADERS)
    if response.status_code != 200:
        print(f"❌ Failed to get failures: {response.status_code}")
        return
    
    failures = response.json()
    current_failure = None
    for failure in failures:
        if failure.get('id') == failure_id:
            current_failure = failure
            break
    
    if not current_failure:
        print(f"❌ Could not find failure {failure_id}")
        return
    
    print(f"✅ Found failure: {json.dumps(current_failure, indent=2, ensure_ascii=False)}")
    
    # 3. Update failure to completed status using the exact same data structure
    print("\n3. Updating failure to 'הושלם' status...")
    updated_failure = current_failure.copy()
    updated_failure['status'] = 'הושלם'
    
    print(f"Sending update: {json.dumps(updated_failure, indent=2, ensure_ascii=False)}")
    
    response = requests.put(f"{BASE_URL}/failures/{failure_id}", headers=HEADERS, json=updated_failure)
    print(f"Update response status: {response.status_code}")
    print(f"Update response: {response.text}")
    
    if response.status_code != 200:
        print(f"❌ Failed to update failure: {response.status_code}")
        return
    
    print("✅ Successfully updated failure status")
    
    # 4. Wait and check resolved failures
    print("\n4. Waiting 3 seconds for auto-transfer...")
    time.sleep(3)
    
    print("5. Checking resolved failures...")
    response = requests.get(f"{BASE_URL}/resolved-failures", headers=HEADERS)
    if response.status_code != 200:
        print(f"❌ Failed to get resolved failures: {response.status_code}")
        return
    
    resolved_failures = response.json()
    print(f"Found {len(resolved_failures)} resolved failures")
    
    found_resolved = None
    for resolved in resolved_failures:
        if resolved.get('id') == failure_id or resolved.get('failure_number') == failure_number:
            found_resolved = resolved
            break
    
    if found_resolved:
        print(f"✅ Found in resolved failures: {json.dumps(found_resolved, indent=2, ensure_ascii=False)}")
    else:
        print(f"❌ NOT found in resolved failures")
        print("Available resolved failures:")
        for rf in resolved_failures:
            print(f"  - {rf.get('failure_number')} (ID: {rf.get('id')})")
    
    # 6. Check if still in active failures
    print("\n6. Checking if still in active failures...")
    response = requests.get(f"{BASE_URL}/failures", headers=HEADERS)
    if response.status_code != 200:
        print(f"❌ Failed to get active failures: {response.status_code}")
        return
    
    active_failures = response.json()
    found_active = None
    for failure in active_failures:
        if failure.get('id') == failure_id:
            found_active = failure
            break
    
    if found_active:
        print(f"❌ Still in active failures: {json.dumps(found_active, indent=2, ensure_ascii=False)}")
    else:
        print("✅ Removed from active failures")

if __name__ == "__main__":
    debug_auto_transfer()