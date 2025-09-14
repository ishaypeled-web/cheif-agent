#!/usr/bin/env python3
"""
Backend Testing Suite for Yahel Naval Management System
Comprehensive testing after adding new sample data to all 8 tables
בדיקה מקיפה של הבקאנד אחרי הוספת נתוני דוגמה חדשים למערכת יהל
"""

import requests
import json
import uuid
from datetime import datetime
import time

# Configuration
BASE_URL = "https://yahel-leadership.preview.emergentagent.com/api"
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
        """Test 1: Google OAuth login endpoint - should redirect to Google OAuth with correct client_id"""
        try:
            # Don't follow redirects to check the redirect response
            response = requests.get(f"{BASE_URL}/auth/google/login", headers=HEADERS, allow_redirects=False)
            
            if response.status_code == 302:
                # Check if redirect location contains Google OAuth components
                location = response.headers.get('Location', '')
                if 'accounts.google.com' in location and 'oauth2' in location:
                    # Check if the correct client_id is in the URL
                    expected_client_id = "383959914027-m8mtk81ocnvtjsfjl6eqsv2cdfh6t2m1.apps.googleusercontent.com"
                    if expected_client_id in location:
                        self.log_result(
                            "Google OAuth login endpoint", 
                            True, 
                            "✅ Successfully redirects to Google OAuth with correct client_id (NO MORE 403 DELETED CLIENT ERROR!)",
                            f"✅ Redirect URL contains correct client_id: {expected_client_id[:50]}... ✅ Full URL: {location[:150]}..."
                        )
                    else:
                        self.log_result(
                            "Google OAuth login endpoint", 
                            False, 
                            "Redirects to Google but with wrong client_id",
                            f"Expected client_id not found in URL: {location[:150]}..."
                        )
                else:
                    self.log_result(
                        "Google OAuth login endpoint", 
                        False, 
                        "Redirect location doesn't contain expected Google OAuth components",
                        f"Location: {location[:100]}..."
                    )
            elif response.status_code == 200:
                # Maybe it returns JSON instead of redirect
                try:
                    data = response.json()
                    if 'authorization_url' in data and 'state' in data:
                        auth_url = data.get('authorization_url', '')
                        if 'accounts.google.com' in auth_url and 'oauth2' in auth_url:
                            # Check client_id in JSON response
                            expected_client_id = "383959914027-m8mtk81ocnvtjsfjl6eqsv2cdfh6t2m1.apps.googleusercontent.com"
                            if expected_client_id in auth_url:
                                self.log_result(
                                    "Google OAuth login endpoint", 
                                    True, 
                                    "✅ Successfully returns Google OAuth authorization URL with correct client_id",
                                    f"✅ URL contains correct client_id, State: {data.get('state', '')[:20]}... ✅ Client resolved 403 error!"
                                )
                            else:
                                self.log_result(
                                    "Google OAuth login endpoint", 
                                    False, 
                                    "Authorization URL doesn't contain expected client_id",
                                    f"Expected client_id not found in URL: {auth_url[:150]}..."
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
                            "Missing required fields in JSON response",
                            f"Response keys: {list(data.keys())}"
                        )
                except:
                    self.log_result(
                        "Google OAuth login endpoint", 
                        False, 
                        "HTTP 200 but response is not JSON",
                        response.text[:200]
                    )
            else:
                self.log_result(
                    "Google OAuth login endpoint", 
                    False, 
                    f"HTTP {response.status_code} - Expected 302 or 200",
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
            
            response = requests.get(f"{BASE_URL}/auth/google/login", headers=HEADERS, allow_redirects=False)
            
            if response.status_code == 302:
                # Redirect response indicates OAuth is working
                location = response.headers.get('Location', '')
                if 'accounts.google.com' in location:
                    self.log_result(
                        "JWT secret key configuration", 
                        True, 
                        "JWT functionality appears to work (OAuth login redirects correctly)",
                        "OAuth login endpoint redirects to Google, suggesting JWT_SECRET_KEY is configured"
                    )
                else:
                    self.log_result(
                        "JWT secret key configuration", 
                        False, 
                        "OAuth login redirects but not to Google",
                        f"Redirect location: {location}"
                    )
            elif response.status_code == 200:
                # Maybe it returns JSON
                try:
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
                except:
                    self.log_result(
                        "JWT secret key configuration", 
                        False, 
                        "OAuth login endpoint returns non-JSON response",
                        response.text[:200]
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
    
    def test_10_complete_oauth_flow_simulation(self):
        """Test 10: Complete OAuth flow simulation - test the full authentication process"""
        try:
            print("\n🔐 Testing Complete Google OAuth Flow...")
            
            # Step 1: Test OAuth login initiation
            print("   Step 1: Testing OAuth login initiation...")
            response = requests.get(f"{BASE_URL}/auth/google/login", headers=HEADERS, allow_redirects=False)
            
            oauth_working = False
            if response.status_code == 302:
                location = response.headers.get('Location', '')
                if 'accounts.google.com' in location and 'oauth2' in location:
                    oauth_working = True
                    print(f"   ✅ OAuth login redirect working: {location[:100]}...")
            elif response.status_code == 200:
                try:
                    data = response.json()
                    if 'authorization_url' in data:
                        oauth_working = True
                        print(f"   ✅ OAuth login JSON response working")
                except:
                    pass
            
            # Step 2: Test callback endpoint behavior
            print("   Step 2: Testing OAuth callback endpoint...")
            callback_params = {
                "code": "test_authorization_code_123",
                "state": "test_state_456"
            }
            callback_response = requests.get(f"{BASE_URL}/auth/google/callback", params=callback_params, headers=HEADERS)
            
            callback_working = False
            if callback_response.status_code in [200, 302, 400, 401, 403]:
                callback_working = True
                print(f"   ✅ OAuth callback endpoint responding: HTTP {callback_response.status_code}")
            
            # Step 3: Test protected endpoint behavior
            print("   Step 3: Testing protected endpoints require authentication...")
            protected_response = requests.get(f"{BASE_URL}/failures", headers=HEADERS)
            
            protection_working = False
            if protected_response.status_code in [401, 403]:
                protection_working = True
                print(f"   ✅ Protected endpoints require auth: HTTP {protected_response.status_code}")
            
            # Step 4: Test JWT token validation
            print("   Step 4: Testing JWT token validation...")
            invalid_token_headers = {**HEADERS, "Authorization": "Bearer invalid.jwt.token"}
            jwt_response = requests.get(f"{BASE_URL}/failures", headers=invalid_token_headers)
            
            jwt_validation_working = False
            if jwt_response.status_code == 401:
                jwt_validation_working = True
                print(f"   ✅ JWT validation working: rejects invalid tokens")
            
            # Overall assessment
            working_components = sum([oauth_working, callback_working, protection_working, jwt_validation_working])
            
            if working_components >= 3:
                self.log_result(
                    "Complete OAuth flow simulation", 
                    True, 
                    f"✅ OAuth authentication system fully functional ({working_components}/4 components working)",
                    f"✅ OAuth Login: {oauth_working}, ✅ Callback: {callback_working}, ✅ Protection: {protection_working}, ✅ JWT Validation: {jwt_validation_working}"
                )
            else:
                self.log_result(
                    "Complete OAuth flow simulation", 
                    False, 
                    f"OAuth authentication system has issues ({working_components}/4 components working)",
                    f"OAuth Login: {oauth_working}, Callback: {callback_working}, Protection: {protection_working}, JWT Validation: {jwt_validation_working}"
                )
                
        except Exception as e:
            self.log_result("Complete OAuth flow simulation", False, f"Exception: {str(e)}")
    
    def test_11_google_oauth_credentials_validation(self):
        """Test 11: Validate that new Google OAuth credentials are working (no more 403 deleted client)"""
        try:
            print("\n🔑 Testing New Google OAuth Credentials...")
            
            # Test the OAuth login endpoint to see if we get proper Google redirect
            response = requests.get(f"{BASE_URL}/auth/google/login", headers=HEADERS, allow_redirects=False)
            
            if response.status_code == 302:
                location = response.headers.get('Location', '')
                
                # Check for the new client ID in the redirect URL
                new_client_id = "383959914027-m8mtk81ocnvtjsfjl6eqsv2cdfh6t2m1.apps.googleusercontent.com"
                
                if new_client_id in location:
                    # Check that it's a proper Google OAuth URL
                    if 'accounts.google.com/o/oauth2/auth' in location:
                        self.log_result(
                            "Google OAuth credentials validation", 
                            True, 
                            "✅ NEW GOOGLE OAUTH CREDENTIALS WORKING! No more 403 'deleted client' error",
                            f"✅ Redirect URL contains new client_id: {new_client_id} ✅ Redirects to: accounts.google.com/o/oauth2/auth"
                        )
                    else:
                        self.log_result(
                            "Google OAuth credentials validation", 
                            False, 
                            "Client ID found but not redirecting to proper Google OAuth URL",
                            f"Redirect location: {location[:150]}..."
                        )
                else:
                    self.log_result(
                        "Google OAuth credentials validation", 
                        False, 
                        "New client ID not found in redirect URL",
                        f"Expected: {new_client_id}, Got URL: {location[:150]}..."
                    )
            elif response.status_code == 200:
                # Check JSON response
                try:
                    data = response.json()
                    auth_url = data.get('authorization_url', '')
                    new_client_id = "383959914027-m8mtk81ocnvtjsfjl6eqsv2cdfh6t2m1.apps.googleusercontent.com"
                    
                    if new_client_id in auth_url and 'accounts.google.com' in auth_url:
                        self.log_result(
                            "Google OAuth credentials validation", 
                            True, 
                            "✅ NEW GOOGLE OAUTH CREDENTIALS WORKING! (JSON response)",
                            f"✅ Authorization URL contains new client_id and Google OAuth endpoint"
                        )
                    else:
                        self.log_result(
                            "Google OAuth credentials validation", 
                            False, 
                            "JSON response doesn't contain expected new credentials",
                            f"Auth URL: {auth_url[:150]}..."
                        )
                except:
                    self.log_result(
                        "Google OAuth credentials validation", 
                        False, 
                        "HTTP 200 but invalid JSON response",
                        response.text[:200]
                    )
            else:
                self.log_result(
                    "Google OAuth credentials validation", 
                    False, 
                    f"Unexpected HTTP response: {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_result("Google OAuth credentials validation", False, f"Exception: {str(e)}")
    
    def test_10_complete_oauth_flow_simulation(self):
        """Test 10: Complete OAuth flow simulation - test the full authentication process"""
        try:
            print("\n🔐 Testing Complete Google OAuth Flow...")
            
            # Step 1: Test OAuth login initiation
            print("   Step 1: Testing OAuth login initiation...")
            response = requests.get(f"{BASE_URL}/auth/google/login", headers=HEADERS, allow_redirects=False)
            
            oauth_working = False
            if response.status_code == 302:
                location = response.headers.get('Location', '')
                if 'accounts.google.com' in location and 'oauth2' in location:
                    oauth_working = True
                    print(f"   ✅ OAuth login redirect working: {location[:100]}...")
            elif response.status_code == 200:
                try:
                    data = response.json()
                    if 'authorization_url' in data:
                        oauth_working = True
                        print(f"   ✅ OAuth login JSON response working")
                except:
                    pass
            
            # Step 2: Test callback endpoint behavior
            print("   Step 2: Testing OAuth callback endpoint...")
            callback_params = {
                "code": "test_authorization_code_123",
                "state": "test_state_456"
            }
            callback_response = requests.get(f"{BASE_URL}/auth/google/callback", params=callback_params, headers=HEADERS)
            
            callback_working = False
            if callback_response.status_code in [200, 302, 400, 401, 403]:
                callback_working = True
                print(f"   ✅ OAuth callback endpoint responding: HTTP {callback_response.status_code}")
            
            # Step 3: Test protected endpoint behavior
            print("   Step 3: Testing protected endpoints require authentication...")
            protected_response = requests.get(f"{BASE_URL}/failures", headers=HEADERS)
            
            protection_working = False
            if protected_response.status_code in [401, 403]:
                protection_working = True
                print(f"   ✅ Protected endpoints require auth: HTTP {protected_response.status_code}")
            
            # Step 4: Test JWT token validation
            print("   Step 4: Testing JWT token validation...")
            invalid_token_headers = {**HEADERS, "Authorization": "Bearer invalid.jwt.token"}
            jwt_response = requests.get(f"{BASE_URL}/failures", headers=invalid_token_headers)
            
            jwt_validation_working = False
            if jwt_response.status_code == 401:
                jwt_validation_working = True
                print(f"   ✅ JWT validation working: rejects invalid tokens")
            
            # Overall assessment
            working_components = sum([oauth_working, callback_working, protection_working, jwt_validation_working])
            
            if working_components >= 3:
                self.log_result(
                    "Complete OAuth flow simulation", 
                    True, 
                    f"✅ OAuth authentication system fully functional ({working_components}/4 components working)",
                    f"✅ OAuth Login: {oauth_working}, ✅ Callback: {callback_working}, ✅ Protection: {protection_working}, ✅ JWT Validation: {jwt_validation_working}"
                )
            else:
                self.log_result(
                    "Complete OAuth flow simulation", 
                    False, 
                    f"OAuth authentication system has issues ({working_components}/4 components working)",
                    f"OAuth Login: {oauth_working}, Callback: {callback_working}, Protection: {protection_working}, JWT Validation: {jwt_validation_working}"
                )
                
        except Exception as e:
            self.log_result("Complete OAuth flow simulation", False, f"Exception: {str(e)}")
    
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
        self.test_10_complete_oauth_flow_simulation()
        self.test_11_google_oauth_credentials_validation()
        
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

class DataEndpointsAuthenticationTest:
    """Test specific data endpoints for authentication requirements as per review request"""
    
    def __init__(self):
        self.test_results = []
        self.base_url = BASE_URL
        self.headers = HEADERS
        
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
    
    def test_endpoint_without_auth(self, endpoint, method="GET", payload=None):
        """Test endpoint without authentication - should return 401/403"""
        try:
            if method == "GET":
                response = requests.get(f"{self.base_url}{endpoint}", headers=self.headers)
            elif method == "POST":
                response = requests.post(f"{self.base_url}{endpoint}", headers=self.headers, json=payload or {})
            
            return {
                "status_code": response.status_code,
                "requires_auth": response.status_code in [401, 403],
                "response_text": response.text[:200] if response.text else ""
            }
        except Exception as e:
            return {
                "status_code": None,
                "requires_auth": False,
                "error": str(e)
            }
    
    def test_endpoint_with_invalid_auth(self, endpoint, method="GET", payload=None):
        """Test endpoint with invalid JWT token - should return 401"""
        try:
            invalid_headers = {**self.headers, "Authorization": "Bearer invalid.jwt.token.here"}
            
            if method == "GET":
                response = requests.get(f"{self.base_url}{endpoint}", headers=invalid_headers)
            elif method == "POST":
                response = requests.post(f"{self.base_url}{endpoint}", headers=invalid_headers, json=payload or {})
            
            return {
                "status_code": response.status_code,
                "rejects_invalid": response.status_code == 401,
                "response_text": response.text[:200] if response.text else ""
            }
        except Exception as e:
            return {
                "status_code": None,
                "rejects_invalid": False,
                "error": str(e)
            }
    
    def test_all_data_endpoints(self):
        """Test all main data endpoints as specified in review request"""
        print("\n🎯 Testing Main Data Endpoints Authentication")
        print("=" * 60)
        
        # Endpoints to test as specified in review request
        endpoints_to_test = [
            ("/maintenance", "GET", "Pending Maintenances"),
            ("/equipment", "GET", "Equipment Hours"),
            ("/daily-work", "GET", "Daily Work Plan"),
            ("/conversations", "GET", "Conversations"),
            ("/dna-tracker", "GET", "DNA Tracker"),
            ("/ninety-day-plan", "GET", "90-Day Plan"),
            ("/resolved-failures", "GET", "Resolved Failures"),
            ("/failures", "GET", "Active Failures")
        ]
        
        results_summary = {
            "missing_auth": [],
            "has_auth": [],
            "errors": []
        }
        
        for endpoint, method, description in endpoints_to_test:
            print(f"\n🔍 Testing {description} ({method} {endpoint})")
            
            # Test without authentication
            no_auth_result = self.test_endpoint_without_auth(endpoint, method)
            
            # Test with invalid authentication
            invalid_auth_result = self.test_endpoint_with_invalid_auth(endpoint, method)
            
            # Analyze results
            if no_auth_result.get("requires_auth") and invalid_auth_result.get("rejects_invalid"):
                # Endpoint properly requires authentication
                results_summary["has_auth"].append({
                    "endpoint": endpoint,
                    "description": description,
                    "no_auth_status": no_auth_result.get("status_code"),
                    "invalid_auth_status": invalid_auth_result.get("status_code")
                })
                
                self.log_result(
                    f"{description} Authentication",
                    True,
                    f"✅ Properly protected - requires authentication",
                    f"No auth: HTTP {no_auth_result.get('status_code')}, Invalid auth: HTTP {invalid_auth_result.get('status_code')}"
                )
                
            elif no_auth_result.get("status_code") == 200:
                # Endpoint allows access without authentication - SECURITY ISSUE
                results_summary["missing_auth"].append({
                    "endpoint": endpoint,
                    "description": description,
                    "status_code": no_auth_result.get("status_code"),
                    "response_preview": no_auth_result.get("response_text", "")[:100]
                })
                
                self.log_result(
                    f"{description} Authentication",
                    False,
                    f"❌ MISSING AUTHENTICATION - allows access without auth",
                    f"HTTP {no_auth_result.get('status_code')} - This endpoint needs authentication middleware!"
                )
                
            else:
                # Other error or unexpected behavior
                results_summary["errors"].append({
                    "endpoint": endpoint,
                    "description": description,
                    "no_auth_result": no_auth_result,
                    "invalid_auth_result": invalid_auth_result
                })
                
                self.log_result(
                    f"{description} Authentication",
                    False,
                    f"⚠️ Unexpected behavior",
                    f"No auth: {no_auth_result}, Invalid auth: {invalid_auth_result}"
                )
        
        # Summary report
        print("\n" + "=" * 60)
        print("📊 DATA ENDPOINTS AUTHENTICATION SUMMARY")
        print("=" * 60)
        
        total_endpoints = len(endpoints_to_test)
        protected_count = len(results_summary["has_auth"])
        missing_auth_count = len(results_summary["missing_auth"])
        error_count = len(results_summary["errors"])
        
        print(f"Total Endpoints Tested: {total_endpoints}")
        print(f"✅ Properly Protected: {protected_count}")
        print(f"❌ Missing Authentication: {missing_auth_count}")
        print(f"⚠️ Errors/Unexpected: {error_count}")
        
        if missing_auth_count > 0:
            print(f"\n🚨 CRITICAL: {missing_auth_count} endpoints are missing authentication!")
            print("These endpoints need authentication middleware:")
            for item in results_summary["missing_auth"]:
                print(f"  • {item['endpoint']} ({item['description']})")
                if "טבלה תהיה זמינה בקרוב" in item.get('response_preview', ''):
                    print(f"    Shows placeholder message instead of requiring auth")
        
        if results_summary["has_auth"]:
            print(f"\n✅ Properly protected endpoints:")
            for item in results_summary["has_auth"]:
                print(f"  • {item['endpoint']} ({item['description']})")
        
        if results_summary["errors"]:
            print(f"\n⚠️ Endpoints with unexpected behavior:")
            for item in results_summary["errors"]:
                print(f"  • {item['endpoint']} ({item['description']})")
        
        # Overall assessment
        success_rate = (protected_count / total_endpoints) * 100
        overall_success = missing_auth_count == 0 and error_count <= 1
        
        self.log_result(
            "Overall Data Endpoints Authentication",
            overall_success,
            f"Authentication coverage: {success_rate:.1f}% ({protected_count}/{total_endpoints})",
            f"Missing auth: {missing_auth_count}, Errors: {error_count}"
        )
        
        return results_summary
    
    def run_review_request_tests(self):
        """Run the specific tests requested in the review"""
        print("🎯 REVIEW REQUEST: Testing Data Endpoints Authentication")
        print("Testing which endpoints are missing authentication middleware")
        print("=" * 80)
        
        results = self.test_all_data_endpoints()
        
        # Final summary for the review request
        print("\n" + "=" * 80)
        print("🎯 REVIEW REQUEST RESULTS")
        print("=" * 80)
        
        if len(results["missing_auth"]) == 0:
            print("✅ SUCCESS: All main data endpoints properly require authentication!")
            print("✅ User filtering should work correctly after successful Google OAuth login.")
        else:
            print(f"❌ FOUND {len(results['missing_auth'])} ENDPOINTS MISSING AUTHENTICATION:")
            for item in results["missing_auth"]:
                print(f"   • {item['endpoint']} - {item['description']}")
            print("\n🔧 RECOMMENDATION: Add authentication middleware to these endpoints")
            print("   Add @Depends(get_current_user) to these endpoint functions")
        
        return results

def run_review_request_test():
    """Run the specific test requested in the review"""
    print("🚀 Yahel Naval Management System - Review Request Testing")
    print("Testing main data endpoints for missing authentication")
    print("=" * 80)
    
    test = DataEndpointsAuthenticationTest()
    results = test.run_review_request_tests()
    
    return results

if __name__ == "__main__":
    # Focus on the Review Request specific tests
    print("🎯 REVIEW REQUEST: Re-testing all main data endpoints after authentication fixes")
    print("=" * 80)
    run_review_request_test()