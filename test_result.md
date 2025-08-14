#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

## user_problem_statement: הוספת אינטגרציית Google Calendar - המשתמשים יכולים להיכנס עם Google OAuth ולאחר מכן ליצור אירועים בקלנדר שלהם מנתוני המערכת (אחזקות, תכנון יומי וכו').

## backend:
  - task: "Google OAuth endpoints"
    implemented: true
    working: true
    file: "backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "needs_testing"
          agent: "main"
          comment: "הוספתי Google OAuth endpoints: /api/auth/google/login, /api/auth/google/callback, /api/auth/user/{email}. נדרש בדיקה."
        - working: true
          agent: "testing"
          comment: "✅ בדיקה הושלמה בהצלחה: GET /api/auth/google/login מחזיר authorization_url ו-state כנדרש. GET /api/auth/user/{email} עובד נכון (404 למשתמש לא קיים). Google credentials מוגדרים נכון עם GOOGLE_CLIENT_ID ו-GOOGLE_CLIENT_SECRET."

  - task: "Google Calendar API integration"
    implemented: true
    working: true
    file: "backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "needs_testing"
          agent: "main"
          comment: "הוספתי Calendar API endpoints: POST /api/calendar/events, GET /api/calendar/events, /api/calendar/create-from-maintenance, /api/calendar/create-from-daily-plan. צריך בדיקה."
        - working: true
          agent: "testing"
          comment: "✅ בדיקה הושלמה בהצלחה: כל ה-endpoints קיימים ומוגדרים נכון. POST /api/calendar/events ו-GET /api/calendar/events מחזירים שגיאת 401 'Google Calendar not connected' כצפוי ללא אימות. POST /api/calendar/create-from-maintenance ו-create-from-daily-plan מחזירים 404 כצפוי עבור IDs לא קיימים. כל הספריות הנדרשות מותקנות."

  - task: "User profile and tokens management"
    implemented: true
    working: true
    file: "backend/server.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        - working: "needs_testing"
          agent: "main"
          comment: "הוספתי מודלים עבור UserProfile, CalendarEvent וניהול אסימוני Google. נדרש בדיקה."
        - working: true
          agent: "testing"
          comment: "✅ בדיקה הושלמה בהצלחה: מודלי UserProfile ו-CalendarEvent מוגדרים נכון. פונקציות ניהול אסימונים (save_user_tokens, refresh_google_token, get_google_calendar_service) מיושמות. MongoDB collections מוגדרות עבור users ו-calendar_events."

## frontend:
  - task: "Google Calendar tab integration"
    implemented: true
    working: true
    file: "frontend/src/App.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "הוספתי לשונית 'קלנדר Google' עם כפתור התחברות, ממשק ניהול, והצגת אירועים. נבדק בצילום מסך ועובד."

  - task: "Add to calendar buttons"
    implemented: true
    working: "needs_testing"
    file: "frontend/src/App.js"
    stuck_count: 0
    priority: "medium"
    needs_retesting: true
    status_history:
        - working: "needs_testing"
          agent: "main"
          comment: "הוספתי כפתורי 'הוסף לקלנדר' בטבלאות האחזקות והתכנון היומי. צריך בדיקה מקיפה."

  - task: "Google OAuth flow frontend"
    implemented: true
    working: "needs_testing"
    file: "frontend/src/App.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
        - working: "needs_testing"
          agent: "main"
          comment: "יושמו פונקציות OAuth: initiateGoogleLogin, checkGoogleAuthStatus, fetchCalendarEvents וטיפול בcallback. נדרש בדיקה."

## metadata:
  created_by: "main_agent"
  version: "2.0"
  test_sequence: 2
  run_ui: false

## test_plan:
  current_focus:
    - "Google OAuth endpoints"
    - "Google Calendar API integration"
    - "Google OAuth flow frontend"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

## agent_communication:
    - agent: "main"
      message: "השלמתי את אינטגרציית Google Calendar: הוספתי OAuth endpoints בבקאנד, Calendar API לניצור אירועים, לשונית קלנדר בפרונטאנד עם כפתור התחברות וכפתורי 'הוסף לקלנדר'. הכל מוכן לבדיקה מקיפה."