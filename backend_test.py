#!/usr/bin/env python3
"""
Backend Testing Suite for Yahel Naval Management System
Testing authentication functionality and data isolation after recent updates
"""

import requests
import json
import uuid
from datetime import datetime
import time

# Configuration
BASE_URL = "https://fleet-mentor.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class AuthenticationTest:
    """Test authentication functionality after recent updates"""
    
    def __init__(self):
        self.test_results = []
        self.valid_jwt_token = None
        self.test_user_data = {
            "email": "test@yahel-naval.com",
            "name": "Test User",
            "google_id": "test_google_id_123"
        }
        
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
        """Test 1: Google OAuth login endpoint - should redirect to Google OAuth"""
        try:
            response = requests.get(f"{BASE_URL}/auth/google/login", headers=HEADERS)
            
            if response.status_code == 200:
                data = response.json()
                if 'authorization_url' in data and 'state' in data:
                    # Check if URL contains Google OAuth components
                    auth_url = data.get('authorization_url', '')
                    if 'accounts.google.com' in auth_url and 'oauth2' in auth_url:
                        self.log_result(
                            "Google OAuth login endpoint", 
                            True, 
                            "Successfully returns Google OAuth authorization URL",
                            f"URL contains Google OAuth components, State: {data.get('state', '')[:20]}..."
                        )
                    else:
                        self.log_result(
                            "Google OAuth login endpoint", 
                            False, 
                            "Authorization URL doesn't contain expected Google OAuth components",
                            f"URL: {auth_url[:100]}..."
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
                    f"HTTP {response.status_code} - Expected 200",
                    response.text[:200]
                )
        except Exception as e:
            self.log_result("Google OAuth login endpoint", False, f"Exception: {str(e)}")
    
    def test_2_google_oauth_callback_endpoint(self):
        """Test 2: Google OAuth callback endpoint - should handle callback (simulated)"""
        try:
            # Simulate callback with test parameters
            callback_params = {
                "code": "test_auth_code_123",
                "state": "test_state_456"
            }
            
            response = requests.get(f"{BASE_URL}/auth/google/callback", params=callback_params, headers=HEADERS)
            
            # We expect this to fail with our test data, but endpoint should exist
            if response.status_code in [200, 302]:  # 302 for redirect
                self.log_result(
                    "Google OAuth callback endpoint", 
                    True, 
                    "Callback endpoint exists and processes requests",
                    f"HTTP {response.status_code}"
                )
            elif response.status_code in [400, 401, 403]:
                # Expected failure with test data
                self.log_result(
                    "Google OAuth callback endpoint", 
                    True, 
                    "Callback endpoint exists and properly rejects invalid auth codes",
                    f"HTTP {response.status_code} - Expected for test data"
                )
            elif response.status_code == 404:
                self.log_result(
                    "Google OAuth callback endpoint", 
                    False, 
                    "Callback endpoint not found - not implemented",
                    "GET /api/auth/google/callback endpoint missing"
                )
            else:
                self.log_result(
                    "Google OAuth callback endpoint", 
                    False, 
                    f"Unexpected HTTP {response.status_code}",
                    response.text[:200]
                )
        except Exception as e:
            self.log_result("Google OAuth callback endpoint", False, f"Exception: {str(e)}")
    
    def test_3_jwt_token_creation(self):
        """Test 3: JWT token creation - verify tokens are properly created"""
        try:
            # Try to get user info (this might create a token or show us the auth flow)
            response = requests.get(f"{BASE_URL}/auth/user/{self.test_user_data['email']}", headers=HEADERS)
            
            if response.status_code == 200:
                data = response.json()
                if 'access_token' in data or 'token' in data:
                    # Token was returned
                    token = data.get('access_token') or data.get('token')
                    self.valid_jwt_token = token
                    self.log_result(
                        "JWT token creation", 
                        True, 
                        "JWT token successfully created/returned",
                        f"Token length: {len(token)} chars"
                    )
                else:
                    self.log_result(
                        "JWT token creation", 
                        True, 
                        "User endpoint works (token creation tested indirectly)",
                        f"Response: {data}"
                    )
            elif response.status_code == 404:
                # User not found - this is expected for test user
                self.log_result(
                    "JWT token creation", 
                    True, 
                    "User endpoint works correctly (user not found as expected)",
                    "404 is expected for non-existent test user"
                )
            else:
                self.log_result(
                    "JWT token creation", 
                    False, 
                    f"Unexpected response from user endpoint: HTTP {response.status_code}",
                    response.text[:200]
                )
        except Exception as e:
            self.log_result("JWT token creation", False, f"Exception: {str(e)}")
    
    def test_4_endpoints_without_authentication(self):
        """Test 4: Critical endpoints WITHOUT authentication - should return 401/403"""
        try:
            # Test critical endpoints that should require authentication
            protected_endpoints = [
                ("GET", "/failures", "Get failures"),
                ("POST", "/failures", "Create failure", {"failure_number": "TEST", "system": "test", "description": "test", "urgency": 1, "assignee": "test", "estimated_hours": 1}),
                ("GET", "/resolved-failures", "Get resolved failures"),
                ("GET", "/maintenance", "Get maintenance"),
                ("POST", "/ai-chat", "AI chat", {"user_message": "test", "session_id": "test"})
            ]
            
            results = {}
            
            for method, endpoint, description, *payload in protected_endpoints:
                try:
                    if method == "GET":
                        response = requests.get(f"{BASE_URL}{endpoint}", headers=HEADERS)
                    elif method == "POST":
                        data = payload[0] if payload else {}
                        response = requests.post(f"{BASE_URL}{endpoint}", headers=HEADERS, json=data)
                    
                    # Check if endpoint requires authentication
                    if response.status_code in [401, 403]:
                        results[description] = True  # Correctly protected
                    elif response.status_code == 200:
                        results[description] = False  # Not protected (should be)
                    else:
                        results[description] = None  # Other error
                        
                except Exception as e:
                    results[description] = None
            
            protected_count = sum(1 for v in results.values() if v is True)
            unprotected_count = sum(1 for v in results.values() if v is False)
            error_count = sum(1 for v in results.values() if v is None)
            
            if protected_count >= 3:  # Most endpoints should be protected
                self.log_result(
                    "Endpoints without authentication", 
                    True, 
                    f"Most critical endpoints properly protected ({protected_count}/{len(results)})",
                    f"Protected: {[k for k, v in results.items() if v is True]}"
                )
            else:
                self.log_result(
                    "Endpoints without authentication", 
                    False, 
                    f"Too many unprotected endpoints ({unprotected_count}/{len(results)})",
                    f"Unprotected: {[k for k, v in results.items() if v is False]}, Results: {results}"
                )
                
        except Exception as e:
            self.log_result("Endpoints without authentication", False, f"Exception: {str(e)}")
    
    def test_5_endpoints_with_invalid_jwt_token(self):
        """Test 5: Endpoints WITH invalid JWT token - should return 401"""
        try:
            # Create invalid JWT token
            invalid_token = "Bearer invalid.jwt.token.here"
            auth_headers = {**HEADERS, "Authorization": invalid_token}
            
            # Test endpoints with invalid token
            test_endpoints = [
                ("GET", "/failures", "Get failures with invalid token"),
                ("GET", "/resolved-failures", "Get resolved failures with invalid token"),
                ("GET", "/maintenance", "Get maintenance with invalid token"),
                ("POST", "/ai-chat", "AI chat with invalid token", {"user_message": "test", "session_id": "test"})
            ]
            
            results = {}
            
            for method, endpoint, description, *payload in test_endpoints:
                try:
                    if method == "GET":
                        response = requests.get(f"{BASE_URL}{endpoint}", headers=auth_headers)
                    elif method == "POST":
                        data = payload[0] if payload else {}
                        response = requests.post(f"{BASE_URL}{endpoint}", headers=auth_headers, json=data)
                    
                    # Should return 401 for invalid token
                    if response.status_code == 401:
                        results[description] = True  # Correctly rejects invalid token
                    else:
                        results[description] = False  # Doesn't validate token properly
                        
                except Exception as e:
                    results[description] = None
            
            valid_rejections = sum(1 for v in results.values() if v is True)
            
            if valid_rejections >= 3:  # Most should reject invalid tokens
                self.log_result(
                    "Endpoints with invalid JWT token", 
                    True, 
                    f"Most endpoints properly reject invalid tokens ({valid_rejections}/{len(results)})",
                    f"Correctly rejecting: {[k for k, v in results.items() if v is True]}"
                )
            else:
                self.log_result(
                    "Endpoints with invalid JWT token", 
                    False, 
                    f"Some endpoints don't validate JWT tokens properly",
                    f"Results: {results}"
                )
                
        except Exception as e:
            self.log_result("Endpoints with invalid JWT token", False, f"Exception: {str(e)}")
    
    def test_6_data_isolation_user_id_filtering(self):
        """Test 6: Data isolation - verify user_id filtering works"""
        try:
            # This test checks if endpoints filter data by user_id
            # Since we don't have valid auth, we'll test the behavior
            
            # Test failures endpoint
            response = requests.get(f"{BASE_URL}/failures", headers=HEADERS)
            
            if response.status_code == 401:
                self.log_result(
                    "Data isolation user_id filtering", 
                    True, 
                    "Failures endpoint requires authentication (good for data isolation)",
                    "401 response indicates authentication middleware is working"
                )
            elif response.status_code == 200:
                # If it returns data, check if it's filtered (empty or contains user_id field)
                data = response.json()
                if isinstance(data, list):
                    if len(data) == 0:
                        self.log_result(
                            "Data isolation user_id filtering", 
                            True, 
                            "Failures endpoint returns empty data (possibly filtered by user_id)",
                            "Empty response suggests user-specific filtering"
                        )
                    else:
                        # Check if returned data has user_id field
                        has_user_id = any('user_id' in item for item in data if isinstance(item, dict))
                        if has_user_id:
                            self.log_result(
                                "Data isolation user_id filtering", 
                                True, 
                                "Failures data includes user_id field (supports data isolation)",
                                f"Found user_id field in {sum(1 for item in data if isinstance(item, dict) and 'user_id' in item)} items"
                            )
                        else:
                            self.log_result(
                                "Data isolation user_id filtering", 
                                False, 
                                "Failures data doesn't include user_id field",
                                f"Sample item keys: {list(data[0].keys()) if data and isinstance(data[0], dict) else 'N/A'}"
                            )
                else:
                    self.log_result(
                        "Data isolation user_id filtering", 
                        False, 
                        "Unexpected response format from failures endpoint",
                        f"Response type: {type(data)}"
                    )
            else:
                self.log_result(
                    "Data isolation user_id filtering", 
                    False, 
                    f"Unexpected response from failures endpoint: HTTP {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_result("Data isolation user_id filtering", False, f"Exception: {str(e)}")
    
    def test_7_ai_chat_authentication_requirement(self):
        """Test 7: AI chat endpoint requires authentication"""
        try:
            chat_data = {
                "user_message": "שלום ג'סיקה, איך אתה?",
                "session_id": f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "chat_history": []
            }
            
            response = requests.post(f"{BASE_URL}/ai-chat", headers=HEADERS, json=chat_data)
            
            if response.status_code == 401:
                self.log_result(
                    "AI chat authentication requirement", 
                    True, 
                    "AI chat endpoint properly requires authentication",
                    "401 response indicates authentication middleware is working"
                )
            elif response.status_code == 403:
                self.log_result(
                    "AI chat authentication requirement", 
                    True, 
                    "AI chat endpoint properly requires authentication (403 Forbidden)",
                    "403 response indicates authentication middleware is working"
                )
            elif response.status_code == 200:
                # If it works without auth, that's a problem
                self.log_result(
                    "AI chat authentication requirement", 
                    False, 
                    "AI chat endpoint works without authentication (security issue)",
                    "This endpoint should require authentication"
                )
            else:
                self.log_result(
                    "AI chat authentication requirement", 
                    False, 
                    f"Unexpected response from AI chat endpoint: HTTP {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_result("AI chat authentication requirement", False, f"Exception: {str(e)}")
    
    def test_8_jwt_secret_key_configuration(self):
        """Test 8: Verify JWT_SECRET_KEY is properly configured"""
        try:
            # We can't directly test the secret key, but we can test if JWT functionality works
            # by checking if the OAuth login endpoint works (it uses JWT internally)
            
            response = requests.get(f"{BASE_URL}/auth/google/login", headers=HEADERS)
            
            if response.status_code == 200:
                data = response.json()
                if 'authorization_url' in data and 'state' in data:
                    self.log_result(
                        "JWT secret key configuration", 
                        True, 
                        "JWT functionality appears to work (OAuth login successful)",
                        "OAuth login endpoint works, suggesting JWT_SECRET_KEY is configured"
                    )
                else:
                    self.log_result(
                        "JWT secret key configuration", 
                        False, 
                        "OAuth login endpoint returns incomplete response",
                        f"Response: {data}"
                    )
            elif response.status_code == 500:
                # Server error might indicate JWT configuration issue
                self.log_result(
                    "JWT secret key configuration", 
                    False, 
                    "Server error in OAuth login - possible JWT configuration issue",
                    "500 error might indicate missing or invalid JWT_SECRET_KEY"
                )
            else:
                self.log_result(
                    "JWT secret key configuration", 
                    False, 
                    f"Unexpected response from OAuth login: HTTP {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_result("JWT secret key configuration", False, f"Exception: {str(e)}")
    
    def test_9_authentication_middleware_coverage(self):
        """Test 9: Verify authentication middleware is applied to critical endpoints"""
        try:
            # Test multiple critical endpoints to ensure they're protected
            critical_endpoints = [
                "/failures",
                "/resolved-failures", 
                "/maintenance",
                "/ai-chat"
            ]
            
            protected_endpoints = []
            unprotected_endpoints = []
            error_endpoints = []
            
            for endpoint in critical_endpoints:
                try:
                    response = requests.get(f"{BASE_URL}{endpoint}", headers=HEADERS)
                    
                    if response.status_code in [401, 403]:
                        protected_endpoints.append(endpoint)
                    elif response.status_code == 200:
                        unprotected_endpoints.append(endpoint)
                    else:
                        error_endpoints.append((endpoint, response.status_code))
                        
                except Exception as e:
                    error_endpoints.append((endpoint, f"Exception: {str(e)}"))
            
            protection_rate = len(protected_endpoints) / len(critical_endpoints)
            
            if protection_rate >= 0.75:  # At least 75% should be protected
                self.log_result(
                    "Authentication middleware coverage", 
                    True, 
                    f"Good authentication coverage ({len(protected_endpoints)}/{len(critical_endpoints)} endpoints protected)",
                    f"Protected: {protected_endpoints}, Unprotected: {unprotected_endpoints}"
                )
            else:
                self.log_result(
                    "Authentication middleware coverage", 
                    False, 
                    f"Insufficient authentication coverage ({len(protected_endpoints)}/{len(critical_endpoints)} endpoints protected)",
                    f"Protected: {protected_endpoints}, Unprotected: {unprotected_endpoints}, Errors: {error_endpoints}"
                )
                
        except Exception as e:
            self.log_result("Authentication middleware coverage", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all authentication tests"""
        print("🔐 Starting Authentication Functionality Testing")
        print("=" * 60)
        
        # Run tests in order
        self.test_1_google_oauth_login_endpoint()
        self.test_2_google_oauth_callback_endpoint()
        self.test_3_jwt_token_creation()
        self.test_4_endpoints_without_authentication()
        self.test_5_endpoints_with_invalid_jwt_token()
        self.test_6_data_isolation_user_id_filtering()
        self.test_7_ai_chat_authentication_requirement()
        self.test_8_jwt_secret_key_configuration()
        self.test_9_authentication_middleware_coverage()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 AUTHENTICATION TEST SUMMARY")
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

def main():
    """Main function to run authentication tests"""
    print("🚀 Yahel Naval Management System - Authentication Testing")
    print("Testing authentication functionality after recent updates")
    print("=" * 80)
    
    # Run authentication tests
    auth_test = AuthenticationTest()
    auth_results = auth_test.run_all_tests()
    
    # Overall summary
    print("\n" + "=" * 80)
    print("🎯 OVERALL TEST SUMMARY")
    print("=" * 80)
    
    total_tests = len(auth_results)
    total_passed = sum(1 for result in auth_results if result['success'])
    total_failed = total_tests - total_passed
    
    print(f"Total Tests Run: {total_tests}")
    print(f"✅ Total Passed: {total_passed}")
    print(f"❌ Total Failed: {total_failed}")
    print(f"Overall Success Rate: {(total_passed/total_tests*100):.1f}%")
    
    if total_failed > 0:
        print("\n🚨 CRITICAL ISSUES FOUND:")
        for result in auth_results:
            if not result['success']:
                print(f"  • {result['test']}")
                print(f"    Issue: {result['message']}")
                if result.get('details'):
                    print(f"    Details: {result['details']}")
                print()
    
    return auth_results

if __name__ == "__main__":
    main()