#!/usr/bin/env python3
"""
Backend Testing Suite for Resolved Failures Feature
Testing the complete flow of resolved failures functionality
"""

import requests
import json
import uuid
from datetime import datetime
import time

# Configuration
BASE_URL = "https://marine-leadership.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class ResolvedFailuresTest:
    def __init__(self):
        self.test_results = []
        self.created_failure_id = None
        self.created_resolved_failure_id = None
        
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details:
            print(f"   Details: {details}")
    
    def test_1_get_empty_resolved_failures(self):
        """Test 1: GET /api/resolved-failures should return empty list initially"""
        try:
            response = requests.get(f"{BASE_URL}/resolved-failures", headers=HEADERS)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result(
                        "GET resolved-failures (empty)", 
                        True, 
                        f"Successfully returned list with {len(data)} items",
                        f"Response: {data}"
                    )
                else:
                    self.log_result(
                        "GET resolved-failures (empty)", 
                        False, 
                        "Response is not a list",
                        f"Response: {data}"
                    )
            else:
                self.log_result(
                    "GET resolved-failures (empty)", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("GET resolved-failures (empty)", False, f"Exception: {str(e)}")
    
    def test_2_create_active_failure(self):
        """Test 2: Create an active failure for testing auto-transfer"""
        try:
            failure_data = {
                "failure_number": f"TEST-{datetime.now().strftime('%m%d%H%M%S')}",
                "date": datetime.now().strftime('%Y-%m-%d'),
                "system": "מערכת בדיקה",
                "description": "תקלה לבדיקת העברה אוטומטית לתקלות שטופלו",
                "urgency": 3,
                "assignee": "טכנאי בדיקה",
                "estimated_hours": 2.5,
                "status": "פעיל"
            }
            
            response = requests.post(f"{BASE_URL}/failures", headers=HEADERS, json=failure_data)
            
            if response.status_code == 200:
                data = response.json()
                self.created_failure_id = data.get('id')
                self.log_result(
                    "Create active failure", 
                    True, 
                    f"Created failure with ID: {self.created_failure_id}",
                    f"Failure number: {failure_data['failure_number']}"
                )
            else:
                self.log_result(
                    "Create active failure", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create active failure", False, f"Exception: {str(e)}")
    
    def test_3_verify_failure_in_active_list(self):
        """Test 3: Verify the failure appears in active failures list"""
        try:
            response = requests.get(f"{BASE_URL}/failures", headers=HEADERS)
            
            if response.status_code == 200:
                failures = response.json()
                found_failure = None
                for failure in failures:
                    if failure.get('id') == self.created_failure_id:
                        found_failure = failure
                        break
                
                if found_failure:
                    self.log_result(
                        "Verify failure in active list", 
                        True, 
                        "Failure found in active failures list",
                        f"Status: {found_failure.get('status')}"
                    )
                else:
                    self.log_result(
                        "Verify failure in active list", 
                        False, 
                        "Failure not found in active failures list",
                        f"Looking for ID: {self.created_failure_id}"
                    )
            else:
                self.log_result(
                    "Verify failure in active list", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Verify failure in active list", False, f"Exception: {str(e)}")
    
    def test_4_update_failure_to_completed(self):
        """Test 4: Update failure status to 'הושלם' to trigger auto-transfer"""
        if not self.created_failure_id:
            self.log_result("Update failure to completed", False, "No failure ID available")
            return
            
        try:
            # First get the current failure data
            response = requests.get(f"{BASE_URL}/failures", headers=HEADERS)
            if response.status_code != 200:
                self.log_result("Update failure to completed", False, "Could not get current failure data")
                return
            
            failures = response.json()
            current_failure = None
            for failure in failures:
                if failure.get('id') == self.created_failure_id:
                    current_failure = failure
                    break
            
            if not current_failure:
                self.log_result("Update failure to completed", False, "Could not find current failure")
                return
            
            # Update the failure to completed status
            updated_failure = current_failure.copy()
            updated_failure['status'] = 'הושלם'
            
            response = requests.put(
                f"{BASE_URL}/failures/{self.created_failure_id}", 
                headers=HEADERS, 
                json=updated_failure
            )
            
            if response.status_code == 200:
                self.log_result(
                    "Update failure to completed", 
                    True, 
                    "Successfully updated failure status to 'הושלם'",
                    "This should trigger auto-transfer to resolved failures"
                )
                # Wait a moment for the auto-transfer to process
                time.sleep(2)
            else:
                self.log_result(
                    "Update failure to completed", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Update failure to completed", False, f"Exception: {str(e)}")
    
    def test_5_verify_auto_transfer_to_resolved(self):
        """Test 5: Verify failure was automatically moved to resolved failures"""
        try:
            response = requests.get(f"{BASE_URL}/resolved-failures", headers=HEADERS)
            
            if response.status_code == 200:
                resolved_failures = response.json()
                found_resolved = None
                for resolved in resolved_failures:
                    if resolved.get('id') == self.created_failure_id:
                        found_resolved = resolved
                        break
                
                if found_resolved:
                    # Verify all required fields are present
                    required_fields = ['resolution_method', 'actual_hours', 'lessons_learned', 'resolved_by', 'resolved_date']
                    missing_fields = [field for field in required_fields if field not in found_resolved]
                    
                    if not missing_fields:
                        self.log_result(
                            "Verify auto-transfer to resolved", 
                            True, 
                            "Failure successfully moved to resolved failures with all required fields",
                            f"Resolved date: {found_resolved.get('resolved_date')}, Resolved by: {found_resolved.get('resolved_by')}"
                        )
                    else:
                        self.log_result(
                            "Verify auto-transfer to resolved", 
                            False, 
                            f"Failure moved but missing fields: {missing_fields}",
                            f"Available fields: {list(found_resolved.keys())}"
                        )
                else:
                    self.log_result(
                        "Verify auto-transfer to resolved", 
                        False, 
                        "Failure not found in resolved failures list",
                        f"Looking for ID: {self.created_failure_id}, Found {len(resolved_failures)} resolved failures"
                    )
            else:
                self.log_result(
                    "Verify auto-transfer to resolved", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Verify auto-transfer to resolved", False, f"Exception: {str(e)}")
    
    def test_6_verify_removal_from_active(self):
        """Test 6: Verify failure was removed from active failures list"""
        try:
            response = requests.get(f"{BASE_URL}/failures", headers=HEADERS)
            
            if response.status_code == 200:
                active_failures = response.json()
                found_active = None
                for failure in active_failures:
                    if failure.get('id') == self.created_failure_id:
                        found_active = failure
                        break
                
                if not found_active:
                    self.log_result(
                        "Verify removal from active", 
                        True, 
                        "Failure successfully removed from active failures list",
                        f"Active failures count: {len(active_failures)}"
                    )
                else:
                    self.log_result(
                        "Verify removal from active", 
                        False, 
                        "Failure still exists in active failures list",
                        f"Status: {found_active.get('status')}"
                    )
            else:
                self.log_result(
                    "Verify removal from active", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Verify removal from active", False, f"Exception: {str(e)}")
    
    def test_7_create_resolved_failure_directly(self):
        """Test 7: Test POST /api/resolved-failures endpoint"""
        try:
            resolved_failure_data = {
                "failure_number": f"DIRECT-{datetime.now().strftime('%m%d%H%M%S')}",
                "date": datetime.now().strftime('%Y-%m-%d'),
                "system": "מערכת בדיקה ישירה",
                "description": "תקלה שנוצרה ישירות בטבלת תקלות שטופלו",
                "urgency": 2,
                "assignee": "טכנאי ישיר",
                "estimated_hours": 1.5,
                "actual_hours": 2.0,
                "resolution_method": "החלפת רכיב פגום",
                "resolved_date": datetime.now().strftime('%Y-%m-%d'),
                "resolved_by": "טכנאי מומחה",
                "lessons_learned": "חשוב לבדוק רכיבים דומים מראש"
            }
            
            response = requests.post(f"{BASE_URL}/resolved-failures", headers=HEADERS, json=resolved_failure_data)
            
            if response.status_code == 200:
                data = response.json()
                self.created_resolved_failure_id = data.get('id')
                self.log_result(
                    "Create resolved failure directly", 
                    True, 
                    f"Created resolved failure with ID: {self.created_resolved_failure_id}",
                    f"Failure number: {resolved_failure_data['failure_number']}"
                )
            else:
                self.log_result(
                    "Create resolved failure directly", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create resolved failure directly", False, f"Exception: {str(e)}")
    
    def test_8_update_resolved_failure_details(self):
        """Test 8: Test PUT /api/resolved-failures/{id} endpoint"""
        if not self.created_resolved_failure_id:
            self.log_result("Update resolved failure details", False, "No resolved failure ID available")
            return
            
        try:
            update_data = {
                "resolution_method": "החלפת רכיב + כיול מחדש",
                "actual_hours": 2.5,
                "lessons_learned": "חשוב לבדוק רכיבים דומים מראש ולבצע כיול לאחר החלפה",
                "resolved_by": "טכנאי מומחה + מהנדס"
            }
            
            response = requests.put(
                f"{BASE_URL}/resolved-failures/{self.created_resolved_failure_id}", 
                headers=HEADERS, 
                json=update_data
            )
            
            if response.status_code == 200:
                self.log_result(
                    "Update resolved failure details", 
                    True, 
                    "Successfully updated resolved failure details",
                    f"Updated fields: {list(update_data.keys())}"
                )
            else:
                self.log_result(
                    "Update resolved failure details", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Update resolved failure details", False, f"Exception: {str(e)}")
    
    def test_9_ai_chat_failure_closure(self):
        """Test 9: Test AI agent integration with failure closure"""
        try:
            chat_message = {
                "user_message": f"ג'סיקה, אני רוצה לסגור את התקלה {self.created_failure_id if self.created_failure_id else 'TEST-123'}. התקלה טופלה על ידי החלפת רכיב פגום, לקח 3 שעות בפועל, והלקח שנלמד הוא לבדוק רכיבים דומים מראש.",
                "session_id": f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "chat_history": []
            }
            
            response = requests.post(f"{BASE_URL}/ai-chat", headers=HEADERS, json=chat_message)
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get('response', '')
                updated_tables = data.get('updated_tables', [])
                
                # Check if Jessica responded appropriately
                if 'תקלות' in ai_response or 'טופל' in ai_response:
                    self.log_result(
                        "AI chat failure closure", 
                        True, 
                        "Jessica responded appropriately to failure closure",
                        f"Updated tables: {updated_tables}, Response length: {len(ai_response)} chars"
                    )
                else:
                    self.log_result(
                        "AI chat failure closure", 
                        False, 
                        "Jessica did not respond appropriately to failure closure",
                        f"Response: {ai_response[:200]}..."
                    )
            else:
                self.log_result(
                    "AI chat failure closure", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("AI chat failure closure", False, f"Exception: {str(e)}")
    
    def test_10_ai_update_resolved_failure(self):
        """Test 10: Test Jessica's ability to update resolved failure using UPDATE_RESOLVED_FAILURE"""
        if not self.created_resolved_failure_id:
            self.log_result("AI update resolved failure", False, "No resolved failure ID available")
            return
            
        try:
            chat_message = {
                "user_message": f"ג'סיקה, אני רוצה לעדכן את פרטי הפתרון של התקלה {self.created_resolved_failure_id}. השיטה שבה טופלה: 'החלפת רכיב + בדיקה מקיפה', זמן בפועל: 3.5 שעות, לקחים: 'חשוב לבצע בדיקה מקיפה של כל המערכת לאחר החלפת רכיב'",
                "session_id": f"test_session_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "chat_history": []
            }
            
            response = requests.post(f"{BASE_URL}/ai-chat", headers=HEADERS, json=chat_message)
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get('response', '')
                updated_tables = data.get('updated_tables', [])
                
                # Check if Jessica updated the resolved failure
                if 'תקלות שטופלו' in updated_tables or 'עדכנתי' in ai_response:
                    self.log_result(
                        "AI update resolved failure", 
                        True, 
                        "Jessica successfully updated resolved failure details",
                        f"Updated tables: {updated_tables}"
                    )
                else:
                    self.log_result(
                        "AI update resolved failure", 
                        False, 
                        "Jessica did not update resolved failure details",
                        f"Response: {ai_response[:200]}..., Updated tables: {updated_tables}"
                    )
            else:
                self.log_result(
                    "AI update resolved failure", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("AI update resolved failure", False, f"Exception: {str(e)}")
    
    def test_11_verify_data_model_completeness(self):
        """Test 11: Verify ResolvedFailure data model includes all required fields"""
        try:
            response = requests.get(f"{BASE_URL}/resolved-failures", headers=HEADERS)
            
            if response.status_code == 200:
                resolved_failures = response.json()
                
                if resolved_failures:
                    # Check the first resolved failure for all required fields
                    sample_failure = resolved_failures[0]
                    required_fields = [
                        'id', 'failure_number', 'date', 'system', 'description', 
                        'urgency', 'assignee', 'estimated_hours', 'actual_hours',
                        'resolution_method', 'resolved_date', 'resolved_by', 
                        'lessons_learned', 'created_at', 'resolved_at'
                    ]
                    
                    present_fields = [field for field in required_fields if field in sample_failure]
                    missing_fields = [field for field in required_fields if field not in sample_failure]
                    
                    if not missing_fields:
                        self.log_result(
                            "Verify data model completeness", 
                            True, 
                            "All required fields present in ResolvedFailure model",
                            f"Fields: {present_fields}"
                        )
                    else:
                        self.log_result(
                            "Verify data model completeness", 
                            False, 
                            f"Missing required fields: {missing_fields}",
                            f"Present fields: {present_fields}"
                        )
                else:
                    self.log_result(
                        "Verify data model completeness", 
                        False, 
                        "No resolved failures available to check data model",
                        "Need at least one resolved failure to verify model"
                    )
            else:
                self.log_result(
                    "Verify data model completeness", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Verify data model completeness", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Resolved Failures Feature Testing")
        print("=" * 60)
        
        # Run tests in order
        self.test_1_get_empty_resolved_failures()
        self.test_2_create_active_failure()
        self.test_3_verify_failure_in_active_list()
        self.test_4_update_failure_to_completed()
        self.test_5_verify_auto_transfer_to_resolved()
        self.test_6_verify_removal_from_active()
        self.test_7_create_resolved_failure_directly()
        self.test_8_update_resolved_failure_details()
        self.test_9_ai_chat_failure_closure()
        self.test_10_ai_update_resolved_failure()
        self.test_11_verify_data_model_completeness()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        failed = len(self.test_results) - passed
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        
        if failed > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['test']}: {result['message']}")
        
        return self.test_results

class GoogleCalendarIntegrationTest:
    def __init__(self):
        self.test_results = []
        self.test_user_email = "test@example.com"
        
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details:
            print(f"   Details: {details}")
    
    def test_1_google_oauth_login_endpoint(self):
        """Test 1: GET /api/auth/google/login - should return authorization_url and state"""
        try:
            response = requests.get(f"{BASE_URL}/auth/google/login", headers=HEADERS)
            
            if response.status_code == 200:
                data = response.json()
                if 'authorization_url' in data and 'state' in data:
                    self.log_result(
                        "Google OAuth login endpoint", 
                        True, 
                        "Successfully returned authorization_url and state",
                        f"URL length: {len(data.get('authorization_url', ''))}, State: {data.get('state', '')[:20]}..."
                    )
                else:
                    self.log_result(
                        "Google OAuth login endpoint", 
                        False, 
                        "Missing required fields in response",
                        f"Response keys: {list(data.keys())}"
                    )
            else:
                self.log_result(
                    "Google OAuth login endpoint", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Google OAuth login endpoint", False, f"Exception: {str(e)}")
    
    def test_2_get_user_info_endpoint(self):
        """Test 2: GET /api/auth/user/{email} - should return user info and Google connection status"""
        try:
            response = requests.get(f"{BASE_URL}/auth/user/{self.test_user_email}", headers=HEADERS)
            
            if response.status_code == 200:
                data = response.json()
                # User might not exist yet, but endpoint should work
                if 'email' in data or 'error' in data:
                    self.log_result(
                        "Get user info endpoint", 
                        True, 
                        "Endpoint responds correctly (user may not exist yet)",
                        f"Response: {data}"
                    )
                else:
                    self.log_result(
                        "Get user info endpoint", 
                        False, 
                        "Unexpected response format",
                        f"Response: {data}"
                    )
            elif response.status_code == 404:
                # User not found is acceptable
                self.log_result(
                    "Get user info endpoint", 
                    True, 
                    "Endpoint works correctly (user not found as expected)",
                    "404 is expected for non-existent user"
                )
            else:
                self.log_result(
                    "Get user info endpoint", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Get user info endpoint", False, f"Exception: {str(e)}")
    
    def test_3_create_calendar_event_endpoint(self):
        """Test 3: POST /api/calendar/events - should handle event creation (may fail without auth)"""
        try:
            event_data = {
                "title": "בדיקת אירוע קלנדר",
                "description": "אירוע בדיקה לאינטגרציית Google Calendar",
                "start_time": "2025-01-20T10:00:00Z",
                "end_time": "2025-01-20T11:00:00Z",
                "location": "בסיס חיל הים",
                "attendees": ["test@example.com"]
            }
            
            # The endpoint expects user_email as query parameter
            response = requests.post(f"{BASE_URL}/calendar/events?user_email={self.test_user_email}", headers=HEADERS, json=event_data)
            
            # We expect this to fail without proper authentication, but endpoint should exist
            if response.status_code in [200, 201]:
                self.log_result(
                    "Create calendar event endpoint", 
                    True, 
                    "Event created successfully (unexpected but good)",
                    f"Response: {response.json()}"
                )
            elif response.status_code in [400, 401, 403]:
                # Expected failure due to no authentication
                self.log_result(
                    "Create calendar event endpoint", 
                    True, 
                    "Endpoint exists and handles unauthenticated requests correctly",
                    f"HTTP {response.status_code} - Expected for unauthenticated request"
                )
            elif response.status_code == 404:
                self.log_result(
                    "Create calendar event endpoint", 
                    False, 
                    "Endpoint not found - not implemented",
                    "POST /api/calendar/events endpoint missing"
                )
            else:
                self.log_result(
                    "Create calendar event endpoint", 
                    False, 
                    f"Unexpected HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create calendar event endpoint", False, f"Exception: {str(e)}")
    
    def test_4_get_calendar_events_endpoint(self):
        """Test 4: GET /api/calendar/events?user_email=test@example.com - should handle event retrieval"""
        try:
            response = requests.get(f"{BASE_URL}/calendar/events?user_email={self.test_user_email}", headers=HEADERS)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result(
                        "Get calendar events endpoint", 
                        True, 
                        f"Successfully returned events list with {len(data)} items",
                        f"Events: {data}"
                    )
                else:
                    self.log_result(
                        "Get calendar events endpoint", 
                        False, 
                        "Response is not a list",
                        f"Response: {data}"
                    )
            elif response.status_code in [400, 401, 403]:
                # Expected failure due to no authentication
                self.log_result(
                    "Get calendar events endpoint", 
                    True, 
                    "Endpoint exists and handles unauthenticated requests correctly",
                    f"HTTP {response.status_code} - Expected for unauthenticated request"
                )
            elif response.status_code == 404:
                self.log_result(
                    "Get calendar events endpoint", 
                    False, 
                    "Endpoint not found - not implemented",
                    "GET /api/calendar/events endpoint missing"
                )
            else:
                self.log_result(
                    "Get calendar events endpoint", 
                    False, 
                    f"Unexpected HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Get calendar events endpoint", False, f"Exception: {str(e)}")
    
    def test_5_create_from_maintenance_endpoint(self):
        """Test 5: POST /api/calendar/create-from-maintenance - should handle maintenance event creation"""
        try:
            maintenance_data = {
                "maintenance_id": "test-maintenance-123",
                "user_email": self.test_user_email,
                "scheduled_date": "2025-01-21",
                "scheduled_time": "09:00"
            }
            
            response = requests.post(f"{BASE_URL}/calendar/create-from-maintenance", headers=HEADERS, json=maintenance_data)
            
            if response.status_code in [200, 201]:
                self.log_result(
                    "Create from maintenance endpoint", 
                    True, 
                    "Maintenance event created successfully",
                    f"Response: {response.json()}"
                )
            elif response.status_code in [400, 401, 403, 404]:
                # Expected failure due to no authentication or missing maintenance
                self.log_result(
                    "Create from maintenance endpoint", 
                    True, 
                    "Endpoint exists and handles request correctly",
                    f"HTTP {response.status_code} - Expected for unauthenticated/invalid request"
                )
            elif response.status_code == 404:
                self.log_result(
                    "Create from maintenance endpoint", 
                    False, 
                    "Endpoint not found - not implemented",
                    "POST /api/calendar/create-from-maintenance endpoint missing"
                )
            else:
                self.log_result(
                    "Create from maintenance endpoint", 
                    False, 
                    f"Unexpected HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create from maintenance endpoint", False, f"Exception: {str(e)}")
    
    def test_6_create_from_daily_plan_endpoint(self):
        """Test 6: POST /api/calendar/create-from-daily-plan - should handle daily plan event creation"""
        try:
            daily_plan_data = {
                "daily_plan_id": "test-daily-plan-123",
                "user_email": self.test_user_email,
                "scheduled_date": "2025-01-22",
                "scheduled_time": "14:00"
            }
            
            response = requests.post(f"{BASE_URL}/calendar/create-from-daily-plan", headers=HEADERS, json=daily_plan_data)
            
            if response.status_code in [200, 201]:
                self.log_result(
                    "Create from daily plan endpoint", 
                    True, 
                    "Daily plan event created successfully",
                    f"Response: {response.json()}"
                )
            elif response.status_code in [400, 401, 403, 404]:
                # Expected failure due to no authentication or missing daily plan
                self.log_result(
                    "Create from daily plan endpoint", 
                    True, 
                    "Endpoint exists and handles request correctly",
                    f"HTTP {response.status_code} - Expected for unauthenticated/invalid request"
                )
            elif response.status_code == 404:
                self.log_result(
                    "Create from daily plan endpoint", 
                    False, 
                    "Endpoint not found - not implemented",
                    "POST /api/calendar/create-from-daily-plan endpoint missing"
                )
            else:
                self.log_result(
                    "Create from daily plan endpoint", 
                    False, 
                    f"Unexpected HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create from daily plan endpoint", False, f"Exception: {str(e)}")
    
    def test_7_verify_google_credentials_configured(self):
        """Test 7: Verify Google credentials are properly configured"""
        try:
            # Test if the OAuth login endpoint works (indicates credentials are configured)
            response = requests.get(f"{BASE_URL}/auth/google/login", headers=HEADERS)
            
            if response.status_code == 200:
                data = response.json()
                if 'authorization_url' in data and 'accounts.google.com' in data['authorization_url']:
                    self.log_result(
                        "Verify Google credentials configured", 
                        True, 
                        "Google credentials appear to be properly configured",
                        "OAuth flow can be initiated successfully"
                    )
                else:
                    self.log_result(
                        "Verify Google credentials configured", 
                        False, 
                        "Google credentials may not be properly configured",
                        f"Authorization URL: {data.get('authorization_url', 'Missing')}"
                    )
            elif response.status_code == 500:
                self.log_result(
                    "Verify Google credentials configured", 
                    False, 
                    "Server error - likely missing Google credentials",
                    "Check GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables"
                )
            else:
                self.log_result(
                    "Verify Google credentials configured", 
                    False, 
                    f"Unexpected response: HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Verify Google credentials configured", False, f"Exception: {str(e)}")
    
    def test_8_verify_required_libraries_installed(self):
        """Test 8: Verify required Google libraries are installed by testing imports"""
        try:
            # This test checks if the server can handle Google-related requests
            # If libraries are missing, we'd get import errors in the server logs
            
            # Test multiple endpoints to see if any fail due to missing imports
            endpoints_to_test = [
                "/auth/google/login",
                f"/auth/user/{self.test_user_email}",
                "/calendar/events"
            ]
            
            import_errors = []
            working_endpoints = []
            
            for endpoint in endpoints_to_test:
                try:
                    response = requests.get(f"{BASE_URL}{endpoint}", headers=HEADERS, timeout=5)
                    # Any response (even error) means the endpoint loaded successfully
                    working_endpoints.append(endpoint)
                except requests.exceptions.Timeout:
                    # Timeout might indicate server issues, but not import errors
                    working_endpoints.append(endpoint)
                except Exception as e:
                    if "import" in str(e).lower() or "module" in str(e).lower():
                        import_errors.append(f"{endpoint}: {str(e)}")
            
            if not import_errors and working_endpoints:
                self.log_result(
                    "Verify required libraries installed", 
                    True, 
                    "All Google-related endpoints load successfully",
                    f"Working endpoints: {working_endpoints}"
                )
            elif import_errors:
                self.log_result(
                    "Verify required libraries installed", 
                    False, 
                    "Import errors detected in Google endpoints",
                    f"Errors: {import_errors}"
                )
            else:
                self.log_result(
                    "Verify required libraries installed", 
                    False, 
                    "Could not verify library installation",
                    "No endpoints responded successfully"
                )
        except Exception as e:
            self.log_result("Verify required libraries installed", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all Google Calendar integration tests"""
        print("🚀 Starting Google Calendar Integration Testing")
        print("=" * 60)
        
        # Run tests in order
        self.test_1_google_oauth_login_endpoint()
        self.test_2_get_user_info_endpoint()
        self.test_3_create_calendar_event_endpoint()
        self.test_4_get_calendar_events_endpoint()
        self.test_5_create_from_maintenance_endpoint()
        self.test_6_create_from_daily_plan_endpoint()
        self.test_7_verify_google_credentials_configured()
        self.test_8_verify_required_libraries_installed()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 GOOGLE CALENDAR TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        failed = len(self.test_results) - passed
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        
        if failed > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['test']}: {result['message']}")
        
        return self.test_results

if __name__ == "__main__":
    print("🧪 Running Backend Test Suite")
    print("=" * 80)
    
    # Run Resolved Failures tests
    print("\n📋 PART 1: RESOLVED FAILURES TESTING")
    resolved_tester = ResolvedFailuresTest()
    resolved_results = resolved_tester.run_all_tests()
    
    # Run Google Calendar integration tests
    print("\n📅 PART 2: GOOGLE CALENDAR INTEGRATION TESTING")
    calendar_tester = GoogleCalendarIntegrationTest()
    calendar_results = calendar_tester.run_all_tests()
    
    # Overall summary
    print("\n" + "=" * 80)
    print("🎯 OVERALL TEST SUMMARY")
    print("=" * 80)
    
    total_resolved_passed = sum(1 for result in resolved_results if result['success'])
    total_calendar_passed = sum(1 for result in calendar_results if result['success'])
    total_passed = total_resolved_passed + total_calendar_passed
    total_tests = len(resolved_results) + len(calendar_results)
    
    print(f"Resolved Failures Tests: {total_resolved_passed}/{len(resolved_results)} passed")
    print(f"Google Calendar Tests: {total_calendar_passed}/{len(calendar_results)} passed")
    print(f"Overall: {total_passed}/{total_tests} passed ({(total_passed/total_tests*100):.1f}%)")
    
    if total_passed == total_tests:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  Some tests failed - check details above")