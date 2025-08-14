#!/usr/bin/env python3
"""
Review Request Test - Jessica's Updated Workflow
Testing the exact scenario requested in the Hebrew review
"""

import requests
import json
import uuid
from datetime import datetime
import time

# Configuration
BASE_URL = "https://22c70d5c-67fd-4150-9b2e-94e1cc9b4876.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class ReviewRequestTest:
    """Test the exact scenario from the Hebrew review request"""
    
    def __init__(self):
        self.test_results = []
        self.failure_number = "F997"
        self.session_id = f"review_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
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
    
    def test_1_create_failure_f997(self):
        """Step 1: צור תקלה F997"""
        try:
            failure_data = {
                "failure_number": self.failure_number,
                "date": datetime.now().strftime('%Y-%m-%d'),
                "system": "מערכת בדיקה",
                "description": "תקלה לבדיקת ג'סיקה המעודכנת",
                "urgency": 3,
                "assignee": "טכנאי דני",
                "estimated_hours": 1.0,
                "status": "פעיל"
            }
            
            response = requests.post(f"{BASE_URL}/failures", headers=HEADERS, json=failure_data)
            
            if response.status_code == 200:
                data = response.json()
                self.created_failure_id = data.get('id')
                self.log_result(
                    "צור תקלה F997", 
                    True, 
                    f"נוצרה תקלה {self.failure_number} בהצלחה",
                    f"ID: {self.created_failure_id}"
                )
            else:
                self.log_result(
                    "צור תקלה F997", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("צור תקלה F997", False, f"Exception: {str(e)}")
    
    def test_2_send_close_message(self):
        """Step 2: שלח: "ג'סיקה, סגרי את התקלה F997 - היא טופלה" """
        try:
            chat_message = {
                "user_message": "ג'סיקה, סגרי את התקלה F997 - היא טופלה",
                "session_id": self.session_id,
                "chat_history": []
            }
            
            response = requests.post(f"{BASE_URL}/ai-chat", headers=HEADERS, json=chat_message)
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get('response', '')
                updated_tables = data.get('updated_tables', [])
                
                print(f"\n🤖 Jessica's Response:")
                print(f"   {ai_response}")
                print(f"   Updated Tables: {updated_tables}")
                
                # Check if Jessica performed UPDATE_FAILURE automatically
                failure_updated = 'תקלות פעילות' in updated_tables or 'תקלות שטופלו' in updated_tables
                
                # Check if Jessica asks the 3 required questions
                required_questions = [
                    "כמה זמן זה לקח",
                    "מי טיפל בתקלה", 
                    "האם צריך לעשות משהו בעתיד כדי שזה לא יחזור על עצמו"
                ]
                
                questions_found = sum(1 for q in required_questions if q in ai_response)
                
                if failure_updated and questions_found >= 2:
                    self.log_result(
                        "ג'סיקה מבצעת UPDATE_FAILURE ושואלת שאלות", 
                        True, 
                        f"ג'סיקה עדכנה את התקלה ושאלה {questions_found}/3 שאלות נדרשות",
                        f"טבלאות מעודכנות: {updated_tables}"
                    )
                elif failure_updated:
                    self.log_result(
                        "ג'סיקה מבצעת UPDATE_FAILURE ושואלת שאלות", 
                        False, 
                        f"ג'סיקה עדכנה את התקלה אבל שאלה רק {questions_found}/3 שאלות",
                        f"תגובה: {ai_response[:300]}..."
                    )
                else:
                    self.log_result(
                        "ג'סיקה מבצעת UPDATE_FAILURE ושואלת שאלות", 
                        False, 
                        "ג'סיקה לא עדכנה את התקלה אוטומטית",
                        f"טבלאות מעודכנות: {updated_tables}"
                    )
            else:
                self.log_result(
                    "ג'סיקה מבצעת UPDATE_FAILURE ושואלת שאלות", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("ג'סיקה מבצעת UPDATE_FAILURE ושואלת שאלות", False, f"Exception: {str(e)}")
    
    def test_3_provide_answers(self):
        """Step 3: ענה: "זמן: 1 שעה, מי: טכנאי דני, מניעה: בדיקה יומית" """
        try:
            chat_message = {
                "user_message": "זמן: 1 שעה, מי: טכנאי דני, מניעה: בדיקה יומית",
                "session_id": self.session_id,
                "chat_history": [
                    {"type": "user", "content": "ג'סיקה, סגרי את התקלה F997 - היא טופלה"},
                    {"type": "ai", "content": "התקלה F997 נסגרה. כמה זמן זה לקח? מי טיפל בתקלה? האם צריך לעשות משהו בעתיד כדי שזה לא יחזור על עצמו?"}
                ]
            }
            
            response = requests.post(f"{BASE_URL}/ai-chat", headers=HEADERS, json=chat_message)
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get('response', '')
                updated_tables = data.get('updated_tables', [])
                
                print(f"\n🤖 Jessica's Response to Answers:")
                print(f"   {ai_response}")
                print(f"   Updated Tables: {updated_tables}")
                
                # Check if Jessica performed UPDATE_RESOLVED_FAILURE automatically
                resolved_updated = 'תקלות שטופלו' in updated_tables
                
                # Check if Jessica acknowledged the answers
                acknowledged = ('תודה' in ai_response or 'עדכנתי' in ai_response or 'פרטי הפתרון' in ai_response)
                
                if resolved_updated:
                    self.log_result(
                        "ג'סיקה מבצעת UPDATE_RESOLVED_FAILURE אוטומטית", 
                        True, 
                        "ג'סיקה עדכנה אוטומטית את פרטי הפתרון",
                        f"טבלאות מעודכנות: {updated_tables}"
                    )
                else:
                    self.log_result(
                        "ג'סיקה מבצעת UPDATE_RESOLVED_FAILURE אוטומטית", 
                        False, 
                        "ג'סיקה לא עדכנה אוטומטית את פרטי הפתרון",
                        f"תגובה: {ai_response[:300]}..."
                    )
            else:
                self.log_result(
                    "ג'סיקה מבצעת UPDATE_RESOLVED_FAILURE אוטומטית", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("ג'סיקה מבצעת UPDATE_RESOLVED_FAILURE אוטומטית", False, f"Exception: {str(e)}")
    
    def test_4_verify_complete_workflow(self):
        """Step 4: בדוק שהזרימה השלמה עבדה"""
        try:
            # Check that F997 is NOT in active failures
            active_response = requests.get(f"{BASE_URL}/failures", headers=HEADERS)
            active_found = False
            
            if active_response.status_code == 200:
                active_failures = active_response.json()
                for failure in active_failures:
                    if failure.get('failure_number') == self.failure_number:
                        active_found = True
                        break
            
            # Check that F997 IS in resolved failures with correct details
            resolved_response = requests.get(f"{BASE_URL}/resolved-failures", headers=HEADERS)
            resolved_found = False
            resolved_details = None
            
            if resolved_response.status_code == 200:
                resolved_failures = resolved_response.json()
                for failure in resolved_failures:
                    if failure.get('failure_number') == self.failure_number:
                        resolved_found = True
                        resolved_details = failure
                        break
            
            if not active_found and resolved_found:
                # Check if resolution details match the provided answers
                actual_hours = resolved_details.get('actual_hours')
                resolved_by = resolved_details.get('resolved_by', '')
                lessons_learned = resolved_details.get('lessons_learned', '')
                
                # Expected from the answers: "זמן: 1 שעה, מי: טכנאי דני, מניעה: בדיקה יומית"
                hours_correct = actual_hours == 1.0
                resolved_by_correct = 'דני' in resolved_by
                lessons_correct = 'בדיקה יומית' in lessons_learned
                
                details_score = sum([hours_correct, resolved_by_correct, lessons_correct])
                
                if details_score >= 2:
                    self.log_result(
                        "בדוק זרימה שלמה", 
                        True, 
                        f"הזרימה השלמה עבדה! F997 עבר לתקלות שטופלו עם {details_score}/3 פרטים נכונים",
                        f"שעות: {actual_hours}, מי טיפל: {resolved_by}, לקחים: {lessons_learned}"
                    )
                else:
                    self.log_result(
                        "בדוק זרימה שלמה", 
                        False, 
                        f"F997 עבר לתקלות שטופלו אבל חסרים פרטי פתרון ({details_score}/3 נכונים)",
                        f"שעות: {actual_hours}, מי טיפל: {resolved_by}, לקחים: {lessons_learned}"
                    )
            elif active_found and not resolved_found:
                self.log_result(
                    "בדוק זרימה שלמה", 
                    False, 
                    "F997 עדיין בתקלות פעילות, לא עבר לתקלות שטופלו",
                    "הזרימה לא הושלמה"
                )
            elif active_found and resolved_found:
                self.log_result(
                    "בדוק זרימה שלמה", 
                    False, 
                    "F997 קיים גם בתקלות פעילות וגם בתקלות שטופלו",
                    "כפילות - העברה לא הושלמה כראוי"
                )
            else:
                self.log_result(
                    "בדוק זרימה שלמה", 
                    False, 
                    "F997 לא נמצא בשום טבלה",
                    "התקלה אבדה במהלך התהליך"
                )
        except Exception as e:
            self.log_result("בדוק זרימה שלמה", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run the complete review request test"""
        print("🎯 בדיקה מהירה לוודא שג'סיקה עכשיו עובדת נכון עם ההוראות המעודכנות")
        print("=" * 80)
        
        print("\n📋 התהליך הנבדק:")
        print("1. צור תקלה F997")
        print("2. שלח: 'ג'סיקה, סגרי את התקלה F997 - היא טופלה'")
        print("3. ענה: 'זמן: 1 שעה, מי: טכנאי דני, מניעה: בדיקה יומית'")
        print("\n🎯 מה אני מצפה עכשיו:")
        print("- ג'סיקה תבצע UPDATE_FAILURE אוטומטית כשמבקשים לסגור")
        print("- תשאל את 3 השאלות")
        print("- תבצע UPDATE_RESOLVED_FAILURE אוטומטית אחרי התשובות")
        
        print("\n" + "=" * 80)
        
        # Run tests in order
        self.test_1_create_failure_f997()
        self.test_2_send_close_message()
        self.test_3_provide_answers()
        self.test_4_verify_complete_workflow()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 תוצאות הבדיקה")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        failed = len(self.test_results) - passed
        
        print(f"סה\"כ בדיקות: {len(self.test_results)}")
        print(f"✅ עברו: {passed}")
        print(f"❌ נכשלו: {failed}")
        print(f"אחוז הצלחה: {(passed/len(self.test_results)*100):.1f}%")
        
        if failed == 0:
            print("\n🎉 כל הבדיקות עברו! ג'סיקה עובדת נכון עם ההוראות המעודכנות!")
        else:
            print(f"\n⚠️  {failed} בדיקות נכשלו:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['test']}: {result['message']}")
        
        return self.test_results

if __name__ == "__main__":
    # Run the review request test
    review_test = ReviewRequestTest()
    results = review_test.run_all_tests()
    
    print("\n" + "=" * 80)
    print("🏁 סיכום סופי")
    print("=" * 80)
    
    total_passed = sum(1 for result in results if result['success'])
    total_tests = len(results)
    
    if total_passed == total_tests:
        print("✅ ג'סיקה עובדת מצוין עם ההוראות החדשות!")
        print("   - מבצעת UPDATE_FAILURE אוטומטית")
        print("   - שואלת את 3 השאלות הנדרשות")
        print("   - מבצעת UPDATE_RESOLVED_FAILURE אוטומטית")
    else:
        print(f"⚠️  נמצאו {total_tests - total_passed} בעיות שצריך לתקן")
        print("   בדוק את הפרטים למעלה")
    
    print("=" * 80)