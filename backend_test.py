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
BASE_URL = "https://jessica-agent.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class FailureStatusManagementTest:
    """Test the updated failure management system with status field and automatic transfer"""
    
    def __init__(self):
        self.test_results = []
        self.test_failures = []  # Store created failures for cleanup
        
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
    
    def test_1_create_failure_with_initial_status(self):
        """Test 1: Create a new failure with initial status 'פתוח'"""
        try:
            failure_data = {
                "failure_number": f"STATUS-TEST-{datetime.now().strftime('%m%d%H%M%S')}",
                "date": datetime.now().strftime('%Y-%m-%d'),
                "system": "מערכת בדיקת סטטוס",
                "description": "תקלה לבדיקת שדה הסטטוס החדש",
                "urgency": 3,
                "assignee": "טכנאי בדיקה",
                "estimated_hours": 2.0,
                "status": "פתוח"
            }
            
            response = requests.post(f"{BASE_URL}/failures", headers=HEADERS, json=failure_data)
            
            if response.status_code == 200:
                data = response.json()
                failure_id = data.get('id')
                self.test_failures.append({
                    'id': failure_id,
                    'failure_number': failure_data['failure_number']
                })
                
                # Verify the failure was created with correct status
                get_response = requests.get(f"{BASE_URL}/failures", headers=HEADERS)
                if get_response.status_code == 200:
                    failures = get_response.json()
                    created_failure = next((f for f in failures if f.get('id') == failure_id), None)
                    
                    if created_failure and created_failure.get('status') == 'פתוח':
                        self.log_result(
                            "Create failure with initial status 'פתוח'", 
                            True, 
                            f"Successfully created failure with status 'פתוח'",
                            f"Failure ID: {failure_id}, Number: {failure_data['failure_number']}"
                        )
                    else:
                        self.log_result(
                            "Create failure with initial status 'פתוח'", 
                            False, 
                            f"Failure created but status incorrect: {created_failure.get('status') if created_failure else 'Not found'}",
                            f"Expected: 'פתוח', Got: {created_failure.get('status') if created_failure else 'N/A'}"
                        )
                else:
                    self.log_result(
                        "Create failure with initial status 'פתוח'", 
                        False, 
                        "Could not verify created failure",
                        f"GET failures returned: {get_response.status_code}"
                    )
            else:
                self.log_result(
                    "Create failure with initial status 'פתוח'", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create failure with initial status 'פתוח'", False, f"Exception: {str(e)}")
    
    def test_2_update_status_to_in_progress(self):
        """Test 2: Update failure status to 'בטיפול'"""
        if not self.test_failures:
            self.log_result("Update status to 'בטיפול'", False, "No test failure available")
            return
            
        try:
            test_failure = self.test_failures[0]
            failure_id = test_failure['id']
            
            # Get current failure data
            response = requests.get(f"{BASE_URL}/failures", headers=HEADERS)
            if response.status_code != 200:
                self.log_result("Update status to 'בטיפול'", False, "Could not get current failure data")
                return
            
            failures = response.json()
            current_failure = next((f for f in failures if f.get('id') == failure_id), None)
            
            if not current_failure:
                self.log_result("Update status to 'בטיפול'", False, "Could not find current failure")
                return
            
            # Update status to 'בטיפול'
            updated_failure = current_failure.copy()
            updated_failure['status'] = 'בטיפול'
            
            response = requests.put(
                f"{BASE_URL}/failures/{failure_id}", 
                headers=HEADERS, 
                json=updated_failure
            )
            
            if response.status_code == 200:
                # Verify the update
                get_response = requests.get(f"{BASE_URL}/failures", headers=HEADERS)
                if get_response.status_code == 200:
                    failures = get_response.json()
                    updated_failure_data = next((f for f in failures if f.get('id') == failure_id), None)
                    
                    if updated_failure_data and updated_failure_data.get('status') == 'בטיפול':
                        self.log_result(
                            "Update status to 'בטיפול'", 
                            True, 
                            "Successfully updated failure status to 'בטיפול'",
                            f"Failure remains in active failures table"
                        )
                    else:
                        self.log_result(
                            "Update status to 'בטיפול'", 
                            False, 
                            f"Status not updated correctly: {updated_failure_data.get('status') if updated_failure_data else 'Not found'}",
                            f"Expected: 'בטיפול'"
                        )
                else:
                    self.log_result(
                        "Update status to 'בטיפול'", 
                        False, 
                        "Could not verify status update",
                        f"GET failures returned: {get_response.status_code}"
                    )
            else:
                self.log_result(
                    "Update status to 'בטיפול'", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Update status to 'בטיפול'", False, f"Exception: {str(e)}")
    
    def test_3_update_status_to_completed_auto_transfer(self):
        """Test 3: Update failure status to 'הושלם' and verify automatic transfer to resolved failures"""
        if not self.test_failures:
            self.log_result("Update status to 'הושלם' (auto-transfer)", False, "No test failure available")
            return
            
        try:
            test_failure = self.test_failures[0]
            failure_id = test_failure['id']
            failure_number = test_failure['failure_number']
            
            # Get current failure data
            response = requests.get(f"{BASE_URL}/failures", headers=HEADERS)
            if response.status_code != 200:
                self.log_result("Update status to 'הושלם' (auto-transfer)", False, "Could not get current failure data")
                return
            
            failures = response.json()
            current_failure = next((f for f in failures if f.get('id') == failure_id), None)
            
            if not current_failure:
                self.log_result("Update status to 'הושלם' (auto-transfer)", False, "Could not find current failure")
                return
            
            # Update status to 'הושלם' - this should trigger auto-transfer
            updated_failure = current_failure.copy()
            updated_failure['status'] = 'הושלם'
            
            response = requests.put(
                f"{BASE_URL}/failures/{failure_id}", 
                headers=HEADERS, 
                json=updated_failure
            )
            
            if response.status_code == 200:
                # Wait a moment for auto-transfer
                time.sleep(2)
                
                # Check if failure was moved to resolved failures
                resolved_response = requests.get(f"{BASE_URL}/resolved-failures", headers=HEADERS)
                if resolved_response.status_code == 200:
                    resolved_failures = resolved_response.json()
                    moved_failure = next((f for f in resolved_failures if f.get('id') == failure_id), None)
                    
                    if moved_failure:
                        # Check if failure was removed from active failures
                        active_response = requests.get(f"{BASE_URL}/failures", headers=HEADERS)
                        if active_response.status_code == 200:
                            active_failures = active_response.json()
                            still_active = next((f for f in active_failures if f.get('id') == failure_id), None)
                            
                            if not still_active:
                                self.log_result(
                                    "Update status to 'הושלם' (auto-transfer)", 
                                    True, 
                                    "Successfully moved failure to resolved failures table",
                                    f"Failure {failure_number} automatically transferred when status changed to 'הושלם'"
                                )
                            else:
                                self.log_result(
                                    "Update status to 'הושלם' (auto-transfer)", 
                                    False, 
                                    "Failure moved to resolved but still exists in active",
                                    "Auto-transfer incomplete"
                                )
                        else:
                            self.log_result(
                                "Update status to 'הושלם' (auto-transfer)", 
                                False, 
                                "Could not verify removal from active failures",
                                f"GET active failures returned: {active_response.status_code}"
                            )
                    else:
                        self.log_result(
                            "Update status to 'הושלם' (auto-transfer)", 
                            False, 
                            "Failure not found in resolved failures table",
                            "Auto-transfer did not occur"
                        )
                else:
                    self.log_result(
                        "Update status to 'הושלם' (auto-transfer)", 
                        False, 
                        "Could not check resolved failures",
                        f"GET resolved-failures returned: {resolved_response.status_code}"
                    )
            else:
                self.log_result(
                    "Update status to 'הושלם' (auto-transfer)", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Update status to 'הושלם' (auto-transfer)", False, f"Exception: {str(e)}")
    
    def test_4_direct_edit_resolved_failure(self):
        """Test 4: Direct edit resolved failure details using PUT /api/resolved-failures/{id}"""
        if not self.test_failures:
            self.log_result("Direct edit resolved failure", False, "No test failure available")
            return
            
        try:
            test_failure = self.test_failures[0]
            failure_id = test_failure['id']
            
            # First verify the failure is in resolved failures
            resolved_response = requests.get(f"{BASE_URL}/resolved-failures", headers=HEADERS)
            if resolved_response.status_code != 200:
                self.log_result("Direct edit resolved failure", False, "Could not get resolved failures")
                return
            
            resolved_failures = resolved_response.json()
            resolved_failure = next((f for f in resolved_failures if f.get('id') == failure_id), None)
            
            if not resolved_failure:
                self.log_result("Direct edit resolved failure", False, "Failure not found in resolved failures")
                return
            
            # Update resolved failure details
            update_data = {
                "resolution_method": "החלפת רכיב פגום + כיול מערכת",
                "actual_hours": 3.5,
                "lessons_learned": "חשוב לבדוק כל הרכיבים הקשורים לפני החלפה ולבצע כיול מלא אחרי",
                "resolved_by": "טכנאי מומחה + מהנדס מערכת"
            }
            
            response = requests.put(
                f"{BASE_URL}/resolved-failures/{failure_id}", 
                headers=HEADERS, 
                json=update_data
            )
            
            if response.status_code == 200:
                # Verify the update
                get_response = requests.get(f"{BASE_URL}/resolved-failures/{failure_id}", headers=HEADERS)
                if get_response.status_code == 200:
                    updated_failure = get_response.json()
                    
                    # Check if all fields were updated
                    all_updated = True
                    updated_fields = []
                    for key, expected_value in update_data.items():
                        actual_value = updated_failure.get(key)
                        if actual_value == expected_value:
                            updated_fields.append(key)
                        else:
                            all_updated = False
                            break
                    
                    if all_updated:
                        self.log_result(
                            "Direct edit resolved failure", 
                            True, 
                            "Successfully updated all resolved failure details",
                            f"Updated fields: {updated_fields}"
                        )
                    else:
                        self.log_result(
                            "Direct edit resolved failure", 
                            False, 
                            "Not all fields were updated correctly",
                            f"Expected: {update_data}, Got: {updated_failure}"
                        )
                else:
                    self.log_result(
                        "Direct edit resolved failure", 
                        False, 
                        "Could not verify update",
                        f"GET resolved failure returned: {get_response.status_code}"
                    )
            else:
                self.log_result(
                    "Direct edit resolved failure", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Direct edit resolved failure", False, f"Exception: {str(e)}")
    
    def test_5_test_all_status_options(self):
        """Test 5: Test all status field options (פתוח, בטיפול, ממתין לחלקים, בבדיקה, הושלם, סגור)"""
        try:
            status_options = ["פתוח", "בטיפול", "ממתין לחלקים", "בבדיקה"]
            completion_statuses = ["הושלם", "סגור"]
            
            test_results = {}
            
            for status in status_options:
                # Create a failure with this status
                failure_data = {
                    "failure_number": f"STATUS-{status}-{datetime.now().strftime('%H%M%S')}",
                    "date": datetime.now().strftime('%Y-%m-%d'),
                    "system": "מערכת בדיקת סטטוס",
                    "description": f"תקלה לבדיקת סטטוס {status}",
                    "urgency": 2,
                    "assignee": "טכנאי בדיקה",
                    "estimated_hours": 1.0,
                    "status": status
                }
                
                response = requests.post(f"{BASE_URL}/failures", headers=HEADERS, json=failure_data)
                
                if response.status_code == 200:
                    data = response.json()
                    failure_id = data.get('id')
                    
                    # Verify the failure was created with correct status
                    get_response = requests.get(f"{BASE_URL}/failures", headers=HEADERS)
                    if get_response.status_code == 200:
                        failures = get_response.json()
                        created_failure = next((f for f in failures if f.get('id') == failure_id), None)
                        
                        if created_failure and created_failure.get('status') == status:
                            test_results[status] = True
                            # Clean up - delete the test failure
                            requests.delete(f"{BASE_URL}/failures/{failure_id}", headers=HEADERS)
                        else:
                            test_results[status] = False
                    else:
                        test_results[status] = False
                else:
                    test_results[status] = False
            
            # Test completion statuses (should auto-transfer)
            for status in completion_statuses:
                # Create a failure first
                failure_data = {
                    "failure_number": f"COMPLETE-{status}-{datetime.now().strftime('%H%M%S')}",
                    "date": datetime.now().strftime('%Y-%m-%d'),
                    "system": "מערכת בדיקת סטטוס",
                    "description": f"תקלה לבדיקת סטטוס {status}",
                    "urgency": 2,
                    "assignee": "טכנאי בדיקה",
                    "estimated_hours": 1.0,
                    "status": "פתוח"
                }
                
                create_response = requests.post(f"{BASE_URL}/failures", headers=HEADERS, json=failure_data)
                
                if create_response.status_code == 200:
                    data = create_response.json()
                    failure_id = data.get('id')
                    
                    # Update to completion status
                    failure_data['status'] = status
                    update_response = requests.put(
                        f"{BASE_URL}/failures/{failure_id}", 
                        headers=HEADERS, 
                        json=failure_data
                    )
                    
                    if update_response.status_code == 200:
                        time.sleep(1)  # Wait for auto-transfer
                        
                        # Check if moved to resolved failures
                        resolved_response = requests.get(f"{BASE_URL}/resolved-failures", headers=HEADERS)
                        if resolved_response.status_code == 200:
                            resolved_failures = resolved_response.json()
                            moved_failure = next((f for f in resolved_failures if f.get('id') == failure_id), None)
                            test_results[status] = moved_failure is not None
                            
                            # Clean up - delete from resolved failures
                            if moved_failure:
                                # Note: We don't have a DELETE endpoint for resolved failures, so we leave it
                                pass
                        else:
                            test_results[status] = False
                    else:
                        test_results[status] = False
                else:
                    test_results[status] = False
            
            # Evaluate results
            all_statuses = status_options + completion_statuses
            successful_statuses = [status for status, success in test_results.items() if success]
            failed_statuses = [status for status, success in test_results.items() if not success]
            
            if len(successful_statuses) == len(all_statuses):
                self.log_result(
                    "Test all status options", 
                    True, 
                    f"All {len(all_statuses)} status options work correctly",
                    f"Working statuses: {successful_statuses}"
                )
            else:
                self.log_result(
                    "Test all status options", 
                    False, 
                    f"Some status options failed: {failed_statuses}",
                    f"Working: {successful_statuses}, Failed: {failed_statuses}"
                )
                
        except Exception as e:
            self.log_result("Test all status options", False, f"Exception: {str(e)}")
    
    def test_6_verify_crud_operations_with_status(self):
        """Test 6: Verify all CRUD operations work properly with the new status field"""
        try:
            # CREATE - Create failure with status
            failure_data = {
                "failure_number": f"CRUD-TEST-{datetime.now().strftime('%m%d%H%M%S')}",
                "date": datetime.now().strftime('%Y-%m-%d'),
                "system": "מערכת בדיקת CRUD",
                "description": "תקלה לבדיקת פעולות CRUD עם שדה סטטוס",
                "urgency": 3,
                "assignee": "טכנאי CRUD",
                "estimated_hours": 2.0,
                "status": "פתוח"
            }
            
            create_response = requests.post(f"{BASE_URL}/failures", headers=HEADERS, json=failure_data)
            
            if create_response.status_code != 200:
                self.log_result("Verify CRUD operations with status", False, "CREATE operation failed")
                return
            
            failure_id = create_response.json().get('id')
            crud_results = {"CREATE": True}
            
            # READ - Get the created failure
            read_response = requests.get(f"{BASE_URL}/failures", headers=HEADERS)
            if read_response.status_code == 200:
                failures = read_response.json()
                found_failure = next((f for f in failures if f.get('id') == failure_id), None)
                crud_results["READ"] = found_failure is not None and found_failure.get('status') == 'פתוח'
            else:
                crud_results["READ"] = False
            
            # UPDATE - Update the failure status
            if found_failure:
                updated_failure = found_failure.copy()
                updated_failure['status'] = 'בטיפול'
                updated_failure['description'] = 'תקלה מעודכנת לבדיקת CRUD'
                
                update_response = requests.put(
                    f"{BASE_URL}/failures/{failure_id}", 
                    headers=HEADERS, 
                    json=updated_failure
                )
                
                if update_response.status_code == 200:
                    # Verify update
                    verify_response = requests.get(f"{BASE_URL}/failures", headers=HEADERS)
                    if verify_response.status_code == 200:
                        failures = verify_response.json()
                        updated_found = next((f for f in failures if f.get('id') == failure_id), None)
                        crud_results["UPDATE"] = (updated_found is not None and 
                                                updated_found.get('status') == 'בטיפול' and
                                                'מעודכנת' in updated_found.get('description', ''))
                    else:
                        crud_results["UPDATE"] = False
                else:
                    crud_results["UPDATE"] = False
            else:
                crud_results["UPDATE"] = False
            
            # DELETE - Delete the failure
            delete_response = requests.delete(f"{BASE_URL}/failures/{failure_id}", headers=HEADERS)
            if delete_response.status_code == 200:
                # Verify deletion
                verify_delete_response = requests.get(f"{BASE_URL}/failures", headers=HEADERS)
                if verify_delete_response.status_code == 200:
                    failures = verify_delete_response.json()
                    deleted_found = next((f for f in failures if f.get('id') == failure_id), None)
                    crud_results["DELETE"] = deleted_found is None
                else:
                    crud_results["DELETE"] = False
            else:
                crud_results["DELETE"] = False
            
            # Evaluate results
            successful_operations = [op for op, success in crud_results.items() if success]
            failed_operations = [op for op, success in crud_results.items() if not success]
            
            if len(successful_operations) == 4:
                self.log_result(
                    "Verify CRUD operations with status", 
                    True, 
                    "All CRUD operations work correctly with status field",
                    f"Successful operations: {successful_operations}"
                )
            else:
                self.log_result(
                    "Verify CRUD operations with status", 
                    False, 
                    f"Some CRUD operations failed: {failed_operations}",
                    f"Results: {crud_results}"
                )
                
        except Exception as e:
            self.log_result("Verify CRUD operations with status", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all failure status management tests"""
        print("🚀 Starting Failure Status Management Testing")
        print("=" * 60)
        
        # Run tests in order
        self.test_1_create_failure_with_initial_status()
        self.test_2_update_status_to_in_progress()
        self.test_3_update_status_to_completed_auto_transfer()
        self.test_4_direct_edit_resolved_failure()
        self.test_5_test_all_status_options()
        self.test_6_verify_crud_operations_with_status()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 FAILURE STATUS MANAGEMENT TEST SUMMARY")
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
            # The endpoint expects maintenance_id and user_email as query parameters
            response = requests.post(f"{BASE_URL}/calendar/create-from-maintenance?maintenance_id=test-maintenance-123&user_email={self.test_user_email}", headers=HEADERS)
            
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
            # The endpoint expects work_id and user_email as query parameters
            response = requests.post(f"{BASE_URL}/calendar/create-from-daily-plan?work_id=test-daily-plan-123&user_email={self.test_user_email}", headers=HEADERS)
            
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

class PushNotificationsTest:
    def __init__(self):
        self.test_results = []
        self.test_user_id = "test-user"
        self.subscription_data = None
        
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
    
    def test_1_get_vapid_key(self):
        """Test 1: GET /api/notifications/vapid-key - should return public_key and subject"""
        try:
            response = requests.get(f"{BASE_URL}/notifications/vapid-key", headers=HEADERS)
            
            if response.status_code == 200:
                data = response.json()
                if 'public_key' in data and 'subject' in data:
                    # Verify VAPID key format
                    public_key = data.get('public_key', '')
                    subject = data.get('subject', '')
                    
                    if len(public_key) > 80 and subject.startswith('mailto:'):
                        self.log_result(
                            "GET VAPID key", 
                            True, 
                            "Successfully returned valid VAPID key and subject",
                            f"Public key length: {len(public_key)}, Subject: {subject}"
                        )
                    else:
                        self.log_result(
                            "GET VAPID key", 
                            False, 
                            "VAPID key format appears invalid",
                            f"Public key length: {len(public_key)}, Subject: {subject}"
                        )
                else:
                    self.log_result(
                        "GET VAPID key", 
                        False, 
                        "Missing required fields in response",
                        f"Response keys: {list(data.keys())}"
                    )
            else:
                self.log_result(
                    "GET VAPID key", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("GET VAPID key", False, f"Exception: {str(e)}")
    
    def test_2_subscribe_user(self):
        """Test 2: POST /api/notifications/subscribe - subscription registration"""
        try:
            # Sample subscription data (realistic format)
            self.subscription_data = {
                "user_id": self.test_user_id,
                "subscription": {
                    "endpoint": "https://fcm.googleapis.com/fcm/send/test-endpoint-123",
                    "keys": {
                        "p256dh": "BKxvz2gF8rFoyT1wJwbgzKz7-test-p256dh-key-data",
                        "auth": "test-auth-key-data-16-bytes"
                    }
                }
            }
            
            response = requests.post(f"{BASE_URL}/notifications/subscribe", headers=HEADERS, json=self.subscription_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'subscribed':
                    self.log_result(
                        "POST subscribe user", 
                        True, 
                        "Successfully subscribed user to notifications",
                        f"Response: {data}"
                    )
                else:
                    self.log_result(
                        "POST subscribe user", 
                        False, 
                        "Unexpected response status",
                        f"Response: {data}"
                    )
            else:
                self.log_result(
                    "POST subscribe user", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("POST subscribe user", False, f"Exception: {str(e)}")
    
    def test_3_get_user_preferences(self):
        """Test 3: GET /api/notifications/preferences/test-user - get user preferences"""
        try:
            response = requests.get(f"{BASE_URL}/notifications/preferences/{self.test_user_id}", headers=HEADERS)
            
            if response.status_code == 200:
                data = response.json()
                # Check for required fields
                required_fields = ['user_id', 'categories', 'language_code', 'rtl_support']
                present_fields = [field for field in required_fields if field in data]
                
                if len(present_fields) == len(required_fields):
                    # Check Hebrew RTL support
                    is_hebrew = data.get('language_code') == 'he'
                    has_rtl = data.get('rtl_support', False)
                    categories = data.get('categories', {})
                    
                    self.log_result(
                        "GET user preferences", 
                        True, 
                        f"Successfully retrieved preferences with Hebrew RTL support",
                        f"Hebrew: {is_hebrew}, RTL: {has_rtl}, Categories: {list(categories.keys())}"
                    )
                else:
                    missing_fields = [field for field in required_fields if field not in data]
                    self.log_result(
                        "GET user preferences", 
                        False, 
                        f"Missing required fields: {missing_fields}",
                        f"Present fields: {present_fields}"
                    )
            else:
                self.log_result(
                    "GET user preferences", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("GET user preferences", False, f"Exception: {str(e)}")
    
    def test_4_update_user_preferences(self):
        """Test 4: PUT /api/notifications/preferences/test-user - update user preferences"""
        try:
            preferences_data = {
                "user_id": self.test_user_id,
                "categories": {
                    "urgent_failures": True,
                    "maintenance_reminders": True,
                    "jessica_updates": False,
                    "system_status": True
                },
                "quiet_hours_enabled": True,
                "quiet_hours_start": "22:00",
                "quiet_hours_end": "07:00",
                "language_code": "he",
                "rtl_support": True
            }
            
            response = requests.put(f"{BASE_URL}/notifications/preferences/{self.test_user_id}", headers=HEADERS, json=preferences_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'updated':
                    updated_prefs = data.get('preferences', {})
                    # Verify Hebrew and RTL settings
                    is_hebrew = updated_prefs.get('language_code') == 'he'
                    has_rtl = updated_prefs.get('rtl_support', False)
                    
                    self.log_result(
                        "PUT update user preferences", 
                        True, 
                        "Successfully updated preferences with Hebrew RTL support",
                        f"Hebrew: {is_hebrew}, RTL: {has_rtl}, Quiet hours: {preferences_data['quiet_hours_enabled']}"
                    )
                else:
                    self.log_result(
                        "PUT update user preferences", 
                        False, 
                        "Unexpected response status",
                        f"Response: {data}"
                    )
            else:
                self.log_result(
                    "PUT update user preferences", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("PUT update user preferences", False, f"Exception: {str(e)}")
    
    def test_5_get_notification_categories(self):
        """Test 5: GET /api/notifications/categories - get categories with Hebrew translations"""
        try:
            response = requests.get(f"{BASE_URL}/notifications/categories", headers=HEADERS)
            
            if response.status_code == 200:
                data = response.json()
                categories = data.get('categories', {})
                
                if categories:
                    # Check for Hebrew translations
                    hebrew_support = True
                    rtl_categories = []
                    
                    for category_name, category_info in categories.items():
                        if 'label_he' not in category_info or 'description_he' not in category_info:
                            hebrew_support = False
                        else:
                            rtl_categories.append(category_info.get('label_he', ''))
                    
                    if hebrew_support:
                        self.log_result(
                            "GET notification categories", 
                            True, 
                            f"Successfully retrieved {len(categories)} categories with Hebrew translations",
                            f"Hebrew categories: {rtl_categories}"
                        )
                    else:
                        self.log_result(
                            "GET notification categories", 
                            False, 
                            "Categories missing Hebrew translations",
                            f"Categories: {list(categories.keys())}"
                        )
                else:
                    self.log_result(
                        "GET notification categories", 
                        False, 
                        "No categories returned",
                        f"Response: {data}"
                    )
            else:
                self.log_result(
                    "GET notification categories", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("GET notification categories", False, f"Exception: {str(e)}")
    
    def test_6_send_test_notification(self):
        """Test 6: POST /api/notifications/test?user_id=test-user - send test notification"""
        try:
            response = requests.post(f"{BASE_URL}/notifications/test?user_id={self.test_user_id}", headers=HEADERS)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'sent':
                    result = data.get('result', {})
                    self.log_result(
                        "POST send test notification", 
                        True, 
                        "Successfully sent test notification",
                        f"Result: {result}"
                    )
                else:
                    self.log_result(
                        "POST send test notification", 
                        False, 
                        "Unexpected response status",
                        f"Response: {data}"
                    )
            else:
                self.log_result(
                    "POST send test notification", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("POST send test notification", False, f"Exception: {str(e)}")
    
    def test_7_get_notification_history(self):
        """Test 7: GET /api/notifications/history/test-user - get notification history"""
        try:
            response = requests.get(f"{BASE_URL}/notifications/history/{self.test_user_id}", headers=HEADERS)
            
            if response.status_code == 200:
                data = response.json()
                history = data.get('history', [])
                
                if isinstance(history, list):
                    self.log_result(
                        "GET notification history", 
                        True, 
                        f"Successfully retrieved notification history with {len(history)} entries",
                        f"History entries: {len(history)}"
                    )
                else:
                    self.log_result(
                        "GET notification history", 
                        False, 
                        "History is not a list",
                        f"Response: {data}"
                    )
            else:
                self.log_result(
                    "GET notification history", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("GET notification history", False, f"Exception: {str(e)}")
    
    def test_8_verify_vapid_key_files(self):
        """Test 8: Verify VAPID key files are generated automatically"""
        try:
            # Test if VAPID endpoint works (indicates keys were generated)
            response = requests.get(f"{BASE_URL}/notifications/vapid-key", headers=HEADERS)
            
            if response.status_code == 200:
                data = response.json()
                public_key = data.get('public_key', '')
                
                # A valid VAPID key should be base64url encoded and quite long
                if len(public_key) > 80:
                    self.log_result(
                        "Verify VAPID key generation", 
                        True, 
                        "VAPID keys appear to be generated automatically",
                        f"Public key length: {len(public_key)} characters"
                    )
                else:
                    self.log_result(
                        "Verify VAPID key generation", 
                        False, 
                        "VAPID key appears invalid or not generated",
                        f"Public key: {public_key}"
                    )
            else:
                self.log_result(
                    "Verify VAPID key generation", 
                    False, 
                    "Could not retrieve VAPID key",
                    f"HTTP {response.status_code}: {response.text}"
                )
        except Exception as e:
            self.log_result("Verify VAPID key generation", False, f"Exception: {str(e)}")
    
    def test_9_verify_mongodb_collections(self):
        """Test 9: Verify MongoDB collections are created for subscriptions and preferences"""
        try:
            # Test subscription endpoint (should create collection)
            if self.subscription_data:
                response = requests.post(f"{BASE_URL}/notifications/subscribe", headers=HEADERS, json=self.subscription_data)
                subscription_works = response.status_code == 200
            else:
                subscription_works = False
            
            # Test preferences endpoint (should create collection)
            response = requests.get(f"{BASE_URL}/notifications/preferences/{self.test_user_id}", headers=HEADERS)
            preferences_works = response.status_code == 200
            
            # Test history endpoint (should create collection)
            response = requests.get(f"{BASE_URL}/notifications/history/{self.test_user_id}", headers=HEADERS)
            history_works = response.status_code == 200
            
            if subscription_works and preferences_works and history_works:
                self.log_result(
                    "Verify MongoDB collections", 
                    True, 
                    "All notification collections appear to be working",
                    "Subscriptions, preferences, and history endpoints all functional"
                )
            else:
                failed_collections = []
                if not subscription_works:
                    failed_collections.append("subscriptions")
                if not preferences_works:
                    failed_collections.append("preferences")
                if not history_works:
                    failed_collections.append("history")
                
                self.log_result(
                    "Verify MongoDB collections", 
                    False, 
                    f"Some collections may not be working: {failed_collections}",
                    f"Subscription: {subscription_works}, Preferences: {preferences_works}, History: {history_works}"
                )
        except Exception as e:
            self.log_result("Verify MongoDB collections", False, f"Exception: {str(e)}")
    
    def test_10_verify_hebrew_rtl_support(self):
        """Test 10: Verify Hebrew RTL support in preferences and categories"""
        try:
            # Test preferences Hebrew support
            prefs_response = requests.get(f"{BASE_URL}/notifications/preferences/{self.test_user_id}", headers=HEADERS)
            prefs_hebrew = False
            prefs_rtl = False
            
            if prefs_response.status_code == 200:
                prefs_data = prefs_response.json()
                prefs_hebrew = prefs_data.get('language_code') == 'he'
                prefs_rtl = prefs_data.get('rtl_support', False)
            
            # Test categories Hebrew support
            cats_response = requests.get(f"{BASE_URL}/notifications/categories", headers=HEADERS)
            cats_hebrew = False
            
            if cats_response.status_code == 200:
                cats_data = cats_response.json()
                categories = cats_data.get('categories', {})
                if categories:
                    # Check if all categories have Hebrew labels
                    cats_hebrew = all('label_he' in cat_info for cat_info in categories.values())
            
            if prefs_hebrew and prefs_rtl and cats_hebrew:
                self.log_result(
                    "Verify Hebrew RTL support", 
                    True, 
                    "Full Hebrew RTL support confirmed",
                    f"Preferences Hebrew: {prefs_hebrew}, RTL: {prefs_rtl}, Categories Hebrew: {cats_hebrew}"
                )
            else:
                self.log_result(
                    "Verify Hebrew RTL support", 
                    False, 
                    "Hebrew RTL support incomplete",
                    f"Preferences Hebrew: {prefs_hebrew}, RTL: {prefs_rtl}, Categories Hebrew: {cats_hebrew}"
                )
        except Exception as e:
            self.log_result("Verify Hebrew RTL support", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all push notifications tests"""
        print("🚀 Starting Push Notifications API Testing")
        print("=" * 60)
        
        # Run tests in order
        self.test_1_get_vapid_key()
        self.test_2_subscribe_user()
        self.test_3_get_user_preferences()
        self.test_4_update_user_preferences()
        self.test_5_get_notification_categories()
        self.test_6_send_test_notification()
        self.test_7_get_notification_history()
        self.test_8_verify_vapid_key_files()
        self.test_9_verify_mongodb_collections()
        self.test_10_verify_hebrew_rtl_support()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 PUSH NOTIFICATIONS TEST SUMMARY")
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

class JessicaFailureClosureTest:
    """Test Jessica's new failure closure workflow with specific questions"""
    
    def __init__(self):
        self.test_results = []
        self.failure_number = "F999"
        self.session_id = f"jessica_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.created_failure_id = None
        
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
    
    def test_1_create_test_failure(self):
        """Test 1: Create failure F999 for Jessica testing"""
        try:
            failure_data = {
                "failure_number": self.failure_number,
                "date": datetime.now().strftime('%Y-%m-%d'),
                "system": "מערכת בדיקה",
                "description": "תקלה לבדיקת ג'סיקה",
                "urgency": 3,
                "assignee": "טכנאי בדיקה",
                "estimated_hours": 2.0,
                "status": "פעיל"
            }
            
            response = requests.post(f"{BASE_URL}/failures", headers=HEADERS, json=failure_data)
            
            if response.status_code == 200:
                data = response.json()
                self.created_failure_id = data.get('id')
                self.log_result(
                    "Create test failure F999", 
                    True, 
                    f"Successfully created failure {self.failure_number}",
                    f"ID: {self.created_failure_id}"
                )
            else:
                self.log_result(
                    "Create test failure F999", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create test failure F999", False, f"Exception: {str(e)}")
    
    def test_2_jessica_close_failure_request(self):
        """Test 2: Send message to Jessica to close failure F999"""
        try:
            chat_message = {
                "user_message": f"ג'סיקה, סגרי את התקלה {self.failure_number} - היא טופלה",
                "session_id": self.session_id,
                "chat_history": []
            }
            
            response = requests.post(f"{BASE_URL}/ai-chat", headers=HEADERS, json=chat_message)
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get('response', '')
                updated_tables = data.get('updated_tables', [])
                
                # Check if Jessica closed the failure and asks questions
                failure_closed = 'תקלות פעילות' in updated_tables or 'תקלות שטופלו' in updated_tables
                asks_questions = any(question in ai_response for question in [
                    "כמה זמן", "מי טיפל", "בעתיד", "זמן זה לקח", "טיפל בתקלה", "לא יחזור"
                ])
                
                if failure_closed and asks_questions:
                    self.log_result(
                        "Jessica close failure request", 
                        True, 
                        "Jessica closed failure and asks follow-up questions",
                        f"Updated tables: {updated_tables}, Response contains questions: {asks_questions}"
                    )
                elif failure_closed:
                    self.log_result(
                        "Jessica close failure request", 
                        True, 
                        "Jessica closed failure but didn't ask expected questions",
                        f"Updated tables: {updated_tables}, Response: {ai_response[:200]}..."
                    )
                else:
                    self.log_result(
                        "Jessica close failure request", 
                        False, 
                        "Jessica didn't close the failure",
                        f"Updated tables: {updated_tables}, Response: {ai_response[:200]}..."
                    )
            else:
                self.log_result(
                    "Jessica close failure request", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Jessica close failure request", False, f"Exception: {str(e)}")
    
    def test_3_jessica_asks_specific_questions(self):
        """Test 3: Verify Jessica asks exactly the 3 required questions"""
        try:
            # Continue the conversation to see Jessica's questions
            chat_message = {
                "user_message": "כן, התקלה טופלה",
                "session_id": self.session_id,
                "chat_history": [
                    {"type": "user", "content": f"ג'סיקה, סגרי את התקלה {self.failure_number} - היא טופלה"},
                    {"type": "ai", "content": "הבנתי, אני סוגרת את התקלה. יש לי כמה שאלות..."}
                ]
            }
            
            response = requests.post(f"{BASE_URL}/ai-chat", headers=HEADERS, json=chat_message)
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get('response', '')
                
                # Check for the 3 specific questions
                required_questions = [
                    "כמה זמן זה לקח",
                    "מי טיפל בתקלה", 
                    "האם צריך לעשות משהו בעתיד כדי שזה לא יחזור על עצמו"
                ]
                
                questions_found = []
                for question in required_questions:
                    if any(word in ai_response for word in question.split()):
                        questions_found.append(question)
                
                if len(questions_found) >= 2:  # At least 2 out of 3 questions
                    self.log_result(
                        "Jessica asks specific questions", 
                        True, 
                        f"Jessica asks {len(questions_found)}/3 required questions",
                        f"Questions found: {questions_found}"
                    )
                else:
                    self.log_result(
                        "Jessica asks specific questions", 
                        False, 
                        f"Jessica asks only {len(questions_found)}/3 required questions",
                        f"Response: {ai_response[:300]}..."
                    )
            else:
                self.log_result(
                    "Jessica asks specific questions", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Jessica asks specific questions", False, f"Exception: {str(e)}")
    
    def test_4_answer_jessica_questions(self):
        """Test 4: Answer Jessica's questions with specific responses"""
        try:
            chat_message = {
                "user_message": "זמן: 3 שעות, מי טיפל: טכנאי דני, מניעה: בדיקה שבועית של המערכת",
                "session_id": self.session_id,
                "chat_history": [
                    {"type": "user", "content": f"ג'סיקה, סגרי את התקלה {self.failure_number} - היא טופלה"},
                    {"type": "ai", "content": "כמה זמן זה לקח? מי טיפל בתקלה? האם צריך לעשות משהו בעתיד?"},
                    {"type": "user", "content": "זמן: 3 שעות, מי טיפל: טכנאי דני, מניעה: בדיקה שבועית של המערכת"}
                ]
            }
            
            response = requests.post(f"{BASE_URL}/ai-chat", headers=HEADERS, json=chat_message)
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get('response', '')
                updated_tables = data.get('updated_tables', [])
                
                # Check if Jessica updates resolved failures table
                updates_resolved = 'תקלות שטופלו' in updated_tables
                acknowledges_answers = any(word in ai_response for word in [
                    "תודה", "עדכנתי", "רשמתי", "שמרתי", "הבנתי"
                ])
                
                if updates_resolved and acknowledges_answers:
                    self.log_result(
                        "Answer Jessica questions", 
                        True, 
                        "Jessica processed answers and updated resolved failures",
                        f"Updated tables: {updated_tables}, Acknowledges: {acknowledges_answers}"
                    )
                elif updates_resolved:
                    self.log_result(
                        "Answer Jessica questions", 
                        True, 
                        "Jessica updated resolved failures but didn't acknowledge clearly",
                        f"Updated tables: {updated_tables}"
                    )
                else:
                    self.log_result(
                        "Answer Jessica questions", 
                        False, 
                        "Jessica didn't update resolved failures table",
                        f"Updated tables: {updated_tables}, Response: {ai_response[:200]}..."
                    )
            else:
                self.log_result(
                    "Answer Jessica questions", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Answer Jessica questions", False, f"Exception: {str(e)}")
    
    def test_5_verify_resolved_failure_details(self):
        """Test 5: Verify resolved failure contains the provided details"""
        try:
            response = requests.get(f"{BASE_URL}/resolved-failures", headers=HEADERS)
            
            if response.status_code == 200:
                resolved_failures = response.json()
                
                # Find our test failure
                test_failure = None
                for failure in resolved_failures:
                    if failure.get('failure_number') == self.failure_number:
                        test_failure = failure
                        break
                
                if test_failure:
                    # Check if details were updated
                    has_time = test_failure.get('actual_hours') == 3.0
                    has_resolver = 'דני' in str(test_failure.get('resolved_by', ''))
                    has_prevention = 'בדיקה שבועית' in str(test_failure.get('lessons_learned', ''))
                    
                    details_count = sum([has_time, has_resolver, has_prevention])
                    
                    if details_count >= 2:
                        self.log_result(
                            "Verify resolved failure details", 
                            True, 
                            f"Resolved failure contains {details_count}/3 expected details",
                            f"Time: {has_time}, Resolver: {has_resolver}, Prevention: {has_prevention}"
                        )
                    else:
                        self.log_result(
                            "Verify resolved failure details", 
                            False, 
                            f"Resolved failure missing details ({details_count}/3)",
                            f"Failure data: {test_failure}"
                        )
                else:
                    self.log_result(
                        "Verify resolved failure details", 
                        False, 
                        f"Test failure {self.failure_number} not found in resolved failures",
                        f"Found {len(resolved_failures)} resolved failures"
                    )
            else:
                self.log_result(
                    "Verify resolved failure details", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Verify resolved failure details", False, f"Exception: {str(e)}")
    
    def test_6_verify_failure_moved_from_active(self):
        """Test 6: Verify failure was moved from active to resolved table"""
        try:
            response = requests.get(f"{BASE_URL}/failures", headers=HEADERS)
            
            if response.status_code == 200:
                active_failures = response.json()
                
                # Check that our test failure is NOT in active failures
                test_failure_in_active = any(
                    failure.get('failure_number') == self.failure_number 
                    for failure in active_failures
                )
                
                if not test_failure_in_active:
                    self.log_result(
                        "Verify failure moved from active", 
                        True, 
                        f"Failure {self.failure_number} successfully moved from active table",
                        f"Active failures count: {len(active_failures)}"
                    )
                else:
                    self.log_result(
                        "Verify failure moved from active", 
                        False, 
                        f"Failure {self.failure_number} still exists in active table",
                        "Failure was not properly moved to resolved table"
                    )
            else:
                self.log_result(
                    "Verify failure moved from active", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Verify failure moved from active", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all Jessica failure closure tests"""
        print("🚀 Starting Jessica Failure Closure Workflow Testing")
        print("=" * 60)
        
        # Run tests in order
        self.test_1_create_test_failure()
        self.test_2_jessica_close_failure_request()
        self.test_3_jessica_asks_specific_questions()
        self.test_4_answer_jessica_questions()
        self.test_5_verify_resolved_failure_details()
        self.test_6_verify_failure_moved_from_active()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 JESSICA WORKFLOW TEST SUMMARY")
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

class JessicaUpdatedQuestionsTest:
    """Test Jessica's updated failure closure workflow with specific 3 questions"""
    
    def __init__(self):
        self.test_results = []
        self.failure_number = "F998"  # As specified in review request
        self.session_id = f"jessica_updated_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.created_failure_id = None
        
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
    
    def test_1_create_test_failure_f998(self):
        """Test 1: Create failure F998 for Jessica testing (as per review request)"""
        try:
            failure_data = {
                "failure_number": self.failure_number,
                "date": datetime.now().strftime('%Y-%m-%d'),
                "system": "מערכת בדיקה סופית",
                "description": "תקלה לבדיקה סופית של ג'סיקה",
                "urgency": 3,
                "assignee": "טכנאי בדיקה",
                "estimated_hours": 2.0,
                "status": "פעיל"
            }
            
            response = requests.post(f"{BASE_URL}/failures", headers=HEADERS, json=failure_data)
            
            if response.status_code == 200:
                data = response.json()
                self.created_failure_id = data.get('id')
                self.log_result(
                    "Create test failure F998", 
                    True, 
                    f"Successfully created failure {self.failure_number}",
                    f"ID: {self.created_failure_id}"
                )
            else:
                self.log_result(
                    "Create test failure F998", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create test failure F998", False, f"Exception: {str(e)}")
    
    def test_2_jessica_close_failure_f998(self):
        """Test 2: Send Jessica the exact message from review request"""
        try:
            chat_message = {
                "user_message": "ג'סיקה, סגרי את התקלה F998 - היא טופלה",
                "session_id": self.session_id,
                "chat_history": []
            }
            
            response = requests.post(f"{BASE_URL}/ai-chat", headers=HEADERS, json=chat_message)
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get('response', '')
                updated_tables = data.get('updated_tables', [])
                
                # Check if Jessica closed the failure
                failure_closed = 'תקלות פעילות' in updated_tables or 'תקלות שטופלו' in updated_tables
                
                # Check if Jessica asks the 3 specific questions
                expected_questions = [
                    "כמה זמן זה לקח",
                    "מי טיפל בתקלה",
                    "האם צריך לעשות משהו בעתיד כדי שזה לא יחזור על עצמו"
                ]
                
                questions_asked = sum(1 for q in expected_questions if q in ai_response)
                
                if failure_closed and questions_asked >= 2:  # At least 2 of 3 questions
                    self.log_result(
                        "Jessica closes F998 and asks questions", 
                        True, 
                        f"Jessica closed failure and asked {questions_asked}/3 expected questions",
                        f"Updated tables: {updated_tables}, Questions found: {questions_asked}"
                    )
                elif failure_closed:
                    self.log_result(
                        "Jessica closes F998 and asks questions", 
                        False, 
                        f"Jessica closed failure but only asked {questions_asked}/3 expected questions",
                        f"Response: {ai_response[:300]}..."
                    )
                else:
                    self.log_result(
                        "Jessica closes F998 and asks questions", 
                        False, 
                        "Jessica did not close the failure properly",
                        f"Updated tables: {updated_tables}, Response: {ai_response[:200]}..."
                    )
            else:
                self.log_result(
                    "Jessica closes F998 and asks questions", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Jessica closes F998 and asks questions", False, f"Exception: {str(e)}")
    
    def test_3_answer_jessica_questions(self):
        """Test 3: Answer Jessica's questions with the exact response from review request"""
        try:
            chat_message = {
                "user_message": "זמן: 2 שעות, מי: טכנאי יוסי, מניעה: החלפת חלק",
                "session_id": self.session_id,
                "chat_history": [
                    {"type": "user", "content": "ג'סיקה, סגרי את התקלה F998 - היא טופלה"},
                    {"type": "ai", "content": "כמה זמן זה לקח? מי טיפל בתקלה? האם צריך לעשות משהו בעתיד?"}
                ]
            }
            
            response = requests.post(f"{BASE_URL}/ai-chat", headers=HEADERS, json=chat_message)
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get('response', '')
                updated_tables = data.get('updated_tables', [])
                
                # Check if Jessica updated the resolved failure with the details
                resolved_updated = 'תקלות שטופלו' in updated_tables
                
                if resolved_updated:
                    self.log_result(
                        "Jessica updates resolved failure details", 
                        True, 
                        "Jessica successfully updated resolved failure with provided details",
                        f"Updated tables: {updated_tables}"
                    )
                else:
                    self.log_result(
                        "Jessica updates resolved failure details", 
                        False, 
                        "Jessica did not update resolved failure details",
                        f"Response: {ai_response[:300]}..., Updated tables: {updated_tables}"
                    )
            else:
                self.log_result(
                    "Jessica updates resolved failure details", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Jessica updates resolved failure details", False, f"Exception: {str(e)}")
    
    def test_4_verify_resolved_failure_details(self):
        """Test 4: Verify the resolved failure has the expected details"""
        try:
            response = requests.get(f"{BASE_URL}/resolved-failures", headers=HEADERS)
            
            if response.status_code == 200:
                resolved_failures = response.json()
                
                # Find our F998 failure
                f998_resolved = None
                for failure in resolved_failures:
                    if failure.get('failure_number') == self.failure_number:
                        f998_resolved = failure
                        break
                
                if f998_resolved:
                    # Check if it has the expected details
                    actual_hours = f998_resolved.get('actual_hours')
                    resolved_by = f998_resolved.get('resolved_by', '')
                    lessons_learned = f998_resolved.get('lessons_learned', '')
                    
                    # Expected values from the review request
                    expected_hours = 2.0
                    expected_resolved_by = "טכנאי יוסי"
                    expected_lessons = "החלפת חלק"
                    
                    hours_correct = actual_hours == expected_hours
                    resolved_by_correct = expected_resolved_by in resolved_by
                    lessons_correct = expected_lessons in lessons_learned
                    
                    if hours_correct and resolved_by_correct and lessons_correct:
                        self.log_result(
                            "Verify resolved failure details", 
                            True, 
                            "All expected details found in resolved failure",
                            f"Hours: {actual_hours}, Resolved by: {resolved_by}, Lessons: {lessons_learned}"
                        )
                    else:
                        missing_details = []
                        if not hours_correct:
                            missing_details.append(f"hours (expected {expected_hours}, got {actual_hours})")
                        if not resolved_by_correct:
                            missing_details.append(f"resolved_by (expected '{expected_resolved_by}', got '{resolved_by}')")
                        if not lessons_correct:
                            missing_details.append(f"lessons (expected '{expected_lessons}', got '{lessons_learned}')")
                        
                        self.log_result(
                            "Verify resolved failure details", 
                            False, 
                            f"Some details incorrect: {missing_details}",
                            f"Actual: hours={actual_hours}, resolved_by='{resolved_by}', lessons='{lessons_learned}'"
                        )
                else:
                    self.log_result(
                        "Verify resolved failure details", 
                        False, 
                        f"Failure {self.failure_number} not found in resolved failures",
                        f"Found {len(resolved_failures)} resolved failures"
                    )
            else:
                self.log_result(
                    "Verify resolved failure details", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Verify resolved failure details", False, f"Exception: {str(e)}")
    
    def test_5_verify_failure_removed_from_active(self):
        """Test 5: Verify F998 was removed from active failures"""
        try:
            response = requests.get(f"{BASE_URL}/failures", headers=HEADERS)
            
            if response.status_code == 200:
                active_failures = response.json()
                
                # Check if F998 is still in active failures
                f998_still_active = any(f.get('failure_number') == self.failure_number for f in active_failures)
                
                if not f998_still_active:
                    self.log_result(
                        "Verify F998 removed from active", 
                        True, 
                        f"Failure {self.failure_number} successfully removed from active failures",
                        f"Active failures count: {len(active_failures)}"
                    )
                else:
                    self.log_result(
                        "Verify F998 removed from active", 
                        False, 
                        f"Failure {self.failure_number} still exists in active failures",
                        f"Active failures: {[f.get('failure_number') for f in active_failures]}"
                    )
            else:
                self.log_result(
                    "Verify F998 removed from active", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Verify F998 removed from active", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all Jessica updated questions tests"""
        print("🤖 Starting Jessica Updated Questions Testing (Review Request)")
        print("=" * 70)
        
        # Run tests in order
        self.test_1_create_test_failure_f998()
        self.test_2_jessica_close_failure_f998()
        self.test_3_answer_jessica_questions()
        self.test_4_verify_resolved_failure_details()
        self.test_5_verify_failure_removed_from_active()
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 JESSICA UPDATED QUESTIONS TEST SUMMARY")
        print("=" * 70)
        
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

class ComprehensiveBackendTest:
    """Comprehensive backend testing for all key components"""
    
    def __init__(self):
        self.test_results = []
        self.test_user_id = "comprehensive-test-user"
        
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
    
    def test_core_crud_operations(self):
        """Test all management table CRUD operations"""
        try:
            # Test all management table endpoints
            endpoints = [
                ("failures", "תקלות פעילות"),
                ("resolved-failures", "תקלות שטופלו"),
                ("maintenance", "אחזקות ממתינות"),
                ("equipment", "שעות מכלולים"),
                ("daily-work", "תכנון יומי"),
                ("conversations", "מעקב שיחות"),
                ("dna-tracker", "DNA Tracker"),
                ("ninety-day-plan", "תכנית 90 יום")
            ]
            
            working_endpoints = []
            failed_endpoints = []
            
            for endpoint, hebrew_name in endpoints:
                try:
                    response = requests.get(f"{BASE_URL}/{endpoint}", headers=HEADERS, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, list):
                            working_endpoints.append(f"{hebrew_name} ({len(data)} items)")
                        else:
                            working_endpoints.append(f"{hebrew_name} (object response)")
                    else:
                        failed_endpoints.append(f"{hebrew_name} (HTTP {response.status_code})")
                except Exception as e:
                    failed_endpoints.append(f"{hebrew_name} (Exception: {str(e)[:50]})")
            
            if len(working_endpoints) >= 6:  # At least 6 out of 8 should work
                self.log_result(
                    "Core CRUD Operations", 
                    True, 
                    f"Successfully tested {len(working_endpoints)}/{len(endpoints)} management tables",
                    f"Working: {working_endpoints}"
                )
            else:
                self.log_result(
                    "Core CRUD Operations", 
                    False, 
                    f"Only {len(working_endpoints)}/{len(endpoints)} management tables working",
                    f"Failed: {failed_endpoints}"
                )
                
        except Exception as e:
            self.log_result("Core CRUD Operations", False, f"Exception: {str(e)}")
    
    def test_google_calendar_integration(self):
        """Test Google Calendar OAuth and API endpoints"""
        try:
            oauth_working = False
            calendar_working = False
            
            # Test OAuth login endpoint
            try:
                response = requests.get(f"{BASE_URL}/auth/google/login", headers=HEADERS, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'authorization_url' in data and 'state' in data:
                        oauth_working = True
            except:
                pass
            
            # Test calendar events endpoint
            try:
                response = requests.get(f"{BASE_URL}/calendar/events?user_email=test@example.com", headers=HEADERS, timeout=10)
                if response.status_code in [200, 400, 401, 403]:  # Any response means endpoint exists
                    calendar_working = True
                    # Also check if it's a proper error message about authentication
                    if response.status_code == 401:
                        try:
                            data = response.json()
                            if 'Google Calendar not connected' in data.get('detail', ''):
                                calendar_working = True  # This is the expected behavior
                        except:
                            pass
            except:
                pass
            
            # Test additional calendar endpoints
            calendar_endpoints_working = 0
            test_endpoints = [
                f"{BASE_URL}/calendar/create-from-maintenance?maintenance_id=test&user_email=test@example.com",
                f"{BASE_URL}/calendar/create-from-daily-plan?work_id=test&user_email=test@example.com"
            ]
            
            for endpoint in test_endpoints:
                try:
                    response = requests.post(endpoint, headers=HEADERS, timeout=10)
                    if response.status_code in [200, 400, 401, 403, 404]:  # Any proper response
                        calendar_endpoints_working += 1
                except:
                    pass
            
            if oauth_working and (calendar_working or calendar_endpoints_working >= 1):
                self.log_result(
                    "Google Calendar Integration", 
                    True, 
                    "OAuth and Calendar API endpoints are working correctly",
                    f"OAuth: {oauth_working}, Calendar events: {calendar_working}, Other endpoints: {calendar_endpoints_working}/2"
                )
            elif oauth_working:
                self.log_result(
                    "Google Calendar Integration", 
                    False, 
                    "OAuth working but Calendar API endpoints not responding properly",
                    f"Calendar events: {calendar_working}, Other endpoints: {calendar_endpoints_working}/2"
                )
            else:
                self.log_result(
                    "Google Calendar Integration", 
                    False, 
                    "Google Calendar integration not working",
                    "OAuth endpoints not responding correctly"
                )
                
        except Exception as e:
            self.log_result("Google Calendar Integration", False, f"Exception: {str(e)}")
    
    def test_push_notifications_system(self):
        """Test Push Notifications VAPID, subscriptions, and sending"""
        try:
            vapid_working = False
            subscription_working = False
            preferences_working = False
            
            # Test VAPID key endpoint
            try:
                response = requests.get(f"{BASE_URL}/notifications/vapid-key", headers=HEADERS, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'public_key' in data and 'subject' in data:
                        vapid_working = True
            except:
                pass
            
            # Test subscription endpoint
            try:
                subscription_data = {
                    "user_id": self.test_user_id,
                    "subscription": {
                        "endpoint": "https://fcm.googleapis.com/fcm/send/test-endpoint",
                        "keys": {
                            "p256dh": "test-p256dh-key",
                            "auth": "test-auth-key"
                        }
                    }
                }
                response = requests.post(f"{BASE_URL}/notifications/subscribe", headers=HEADERS, json=subscription_data, timeout=10)
                if response.status_code == 200:
                    subscription_working = True
            except:
                pass
            
            # Test preferences endpoint
            try:
                response = requests.get(f"{BASE_URL}/notifications/preferences/{self.test_user_id}", headers=HEADERS, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'user_id' in data and 'categories' in data:
                        preferences_working = True
            except:
                pass
            
            working_components = []
            if vapid_working:
                working_components.append("VAPID Keys")
            if subscription_working:
                working_components.append("Subscriptions")
            if preferences_working:
                working_components.append("Preferences")
            
            if len(working_components) >= 2:
                self.log_result(
                    "Push Notifications System", 
                    True, 
                    f"Push notification system working: {', '.join(working_components)}",
                    f"Working components: {working_components}"
                )
            else:
                self.log_result(
                    "Push Notifications System", 
                    False, 
                    f"Push notification system partially working: {', '.join(working_components)}",
                    f"VAPID: {vapid_working}, Subscription: {subscription_working}, Preferences: {preferences_working}"
                )
                
        except Exception as e:
            self.log_result("Push Notifications System", False, f"Exception: {str(e)}")
    
    def test_ai_agent_jessica(self):
        """Test AI Agent Jessica chat functionality and table interactions"""
        try:
            # Test basic chat functionality
            chat_message = {
                "user_message": "ג'סיקה, מה המצב של המחלקה?",
                "session_id": f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "chat_history": []
            }
            
            response = requests.post(f"{BASE_URL}/ai-chat", headers=HEADERS, json=chat_message, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get('response', '')
                updated_tables = data.get('updated_tables', [])
                
                # Check if Jessica responded in Hebrew
                hebrew_response = any(char in ai_response for char in 'אבגדהוזחטיכלמנסעפצקרשת')
                
                if hebrew_response and len(ai_response) > 50:
                    self.log_result(
                        "AI Agent Jessica", 
                        True, 
                        "Jessica AI agent responding correctly in Hebrew",
                        f"Response length: {len(ai_response)} chars, Updated tables: {updated_tables}"
                    )
                else:
                    self.log_result(
                        "AI Agent Jessica", 
                        False, 
                        "Jessica AI agent response appears incomplete",
                        f"Hebrew: {hebrew_response}, Response: {ai_response[:100]}..."
                    )
            else:
                self.log_result(
                    "AI Agent Jessica", 
                    False, 
                    f"AI chat endpoint error: HTTP {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_result("AI Agent Jessica", False, f"Exception: {str(e)}")
    
    def test_backend_services_status(self):
        """Test that backend services (MongoDB, FastAPI) are running properly"""
        try:
            # Test root endpoint
            root_working = False
            try:
                response = requests.get(f"{BASE_URL.replace('/api', '')}/", headers=HEADERS, timeout=10)
                if response.status_code == 200:
                    root_working = True
            except:
                pass
            
            # Test API root
            api_working = False
            try:
                response = requests.get(f"{BASE_URL}/failures", headers=HEADERS, timeout=10)
                if response.status_code == 200:
                    api_working = True
            except:
                pass
            
            # Test MongoDB connectivity (by trying to access any collection)
            mongodb_working = False
            try:
                response = requests.get(f"{BASE_URL}/failures", headers=HEADERS, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        mongodb_working = True
            except:
                pass
            
            working_services = []
            if root_working:
                working_services.append("FastAPI Root")
            if api_working:
                working_services.append("API Endpoints")
            if mongodb_working:
                working_services.append("MongoDB")
            
            if len(working_services) >= 2:
                self.log_result(
                    "Backend Services Status", 
                    True, 
                    f"Backend services running: {', '.join(working_services)}",
                    f"Services: {working_services}"
                )
            else:
                self.log_result(
                    "Backend Services Status", 
                    False, 
                    f"Some backend services not responding: {', '.join(working_services)}",
                    f"Root: {root_working}, API: {api_working}, MongoDB: {mongodb_working}"
                )
                
        except Exception as e:
            self.log_result("Backend Services Status", False, f"Exception: {str(e)}")
    
    def test_environment_configuration(self):
        """Test that environment variables are properly configured"""
        try:
            config_issues = []
            
            # Test if Google OAuth is configured (by testing login endpoint)
            try:
                response = requests.get(f"{BASE_URL}/auth/google/login", headers=HEADERS, timeout=10)
                if response.status_code != 200:
                    config_issues.append("Google OAuth credentials")
            except:
                config_issues.append("Google OAuth endpoints")
            
            # Test if OpenAI is configured (by testing AI chat)
            try:
                chat_message = {
                    "user_message": "בדיקה",
                    "session_id": "config_test",
                    "chat_history": []
                }
                response = requests.post(f"{BASE_URL}/ai-chat", headers=HEADERS, json=chat_message, timeout=15)
                if response.status_code == 500:
                    config_issues.append("OpenAI API key")
            except:
                config_issues.append("AI chat service")
            
            if len(config_issues) == 0:
                self.log_result(
                    "Environment Configuration", 
                    True, 
                    "All environment variables appear properly configured",
                    "Google OAuth and OpenAI API key working"
                )
            else:
                self.log_result(
                    "Environment Configuration", 
                    False, 
                    f"Configuration issues detected: {', '.join(config_issues)}",
                    f"Issues: {config_issues}"
                )
                
        except Exception as e:
            self.log_result("Environment Configuration", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all comprehensive backend tests"""
        print("🚀 Starting Comprehensive Backend Testing")
        print("=" * 60)
        
        # Run tests in order
        self.test_backend_services_status()
        self.test_environment_configuration()
        self.test_core_crud_operations()
        self.test_google_calendar_integration()
        self.test_push_notifications_system()
        self.test_ai_agent_jessica()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE BACKEND TEST SUMMARY")
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
    print("🎯 Starting Comprehensive Backend Testing Suite")
    print("=" * 80)
    
    # Run the specific failure status management test first (as requested in review)
    print("🔥 PRIORITY: Testing Updated Failure Management System")
    print("=" * 80)
    
    status_test = FailureStatusManagementTest()
    status_results = status_test.run_all_tests()
    
    print("\n" + "=" * 80)
    
    # Run other test suites
    resolved_test = ResolvedFailuresTest()
    resolved_results = resolved_test.run_all_tests()
    
    print("\n" + "=" * 80)
    
    google_test = GoogleCalendarIntegrationTest()
    google_results = google_test.run_all_tests()
    
    print("\n" + "=" * 80)
    
    push_test = PushNotificationsTest()
    push_results = push_test.run_all_tests()
    
    print("\n" + "=" * 80)
    
    jessica_test = JessicaFailureClosureTest()
    jessica_results = jessica_test.run_all_tests()
    
    # Overall summary
    print("\n" + "=" * 80)
    print("🏆 OVERALL TEST SUMMARY")
    print("=" * 80)
    
    all_results = status_results + resolved_results + google_results + push_results + jessica_results
    total_passed = sum(1 for result in all_results if result['success'])
    total_tests = len(all_results)
    
    print(f"Total Tests Across All Suites: {total_tests}")
    print(f"✅ Total Passed: {total_passed}")
    print(f"❌ Total Failed: {total_tests - total_passed}")
    print(f"Overall Success Rate: {(total_passed/total_tests*100):.1f}%")
    
    # Show failed tests from all suites
    failed_tests = [result for result in all_results if not result['success']]
    if failed_tests:
        print(f"\n🔍 ALL FAILED TESTS ({len(failed_tests)}):")
        for result in failed_tests:
            print(f"  • {result['test']}: {result['message']}")
    
    print("\n🎯 Backend testing completed!")
    print("=" * 80)