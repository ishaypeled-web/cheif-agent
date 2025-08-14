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

if __name__ == "__main__":
    tester = ResolvedFailuresTest()
    results = tester.run_all_tests()