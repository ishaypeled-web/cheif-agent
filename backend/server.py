from fastapi import FastAPI, HTTPException, Request, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel, Field
from pymongo import MongoClient
from datetime import datetime, timedelta
import uuid
import os
import secrets
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage
import asyncio
import json

# Google Calendar imports
from google.auth.transport.requests import Request as GoogleRequest
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError
import google.auth.exceptions
from urllib.parse import urlencode

# Push Notifications imports
from webpush import WebPush, WebPushSubscription
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64
from pathlib import Path
import sqlite3
import aiohttp

# Google Sheets imports
import gspread
from google.oauth2.service_account import Credentials

# JWT Authentication imports
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="יהל Naval Department Management System")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'yahel_department_db')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
GOOGLE_SHEETS_CREDENTIALS = os.environ.get('GOOGLE_SHEETS_CREDENTIALS', '/app/backend/google_sheets_credentials.json')

# JWT Authentication settings
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-fallback-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

# Google Calendar setup
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'https://fleet-mentor.preview.emergentagent.com/api/auth/google/callback')

# Google OAuth 2.0 scopes for Calendar API
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# Collections - Department Management
active_failures_collection = db.active_failures
pending_maintenance_collection = db.pending_maintenance
equipment_hours_collection = db.equipment_hours
daily_work_collection = db.daily_work
resolved_failures_collection = db.resolved_failures  # NEW: Resolved failures

# Collections - Leadership Coaching
conversations_collection = db.conversations
dna_tracker_collection = db.dna_tracker
ninety_day_plan_collection = db.ninety_day_plan
ai_chat_history_collection = db.ai_chat_history

# Collections - Google Calendar Integration
users_collection = db.users  # Store user profiles and Google tokens
calendar_events_collection = db.calendar_events  # Optional: Store local copies of events

# Collections - Push Notifications
push_subscriptions_collection = db.push_subscriptions  # Store push notification subscriptions
notification_preferences_collection = db.notification_preferences  # Store user notification preferences
notification_history_collection = db.notification_history  # Store notification delivery history

# Collections - User Authentication & Sessions
authenticated_users_collection = db.authenticated_users  # Store user authentication data
user_sessions_collection = db.user_sessions  # Store active user sessions

# Pydantic Models - Department Management

class ActiveFailure(BaseModel):
    id: str = None
    failure_number: str
    date: str
    system: str  # מכלול
    description: str
    urgency: int  # 1-5 (5 = most urgent)
    assignee: str  # מבצע
    estimated_hours: float
    status: str = "פעיל"  # פעיל, בטיפול, הושלם
    created_at: str = None

class ResolvedFailure(BaseModel):
    id: str = None
    failure_number: str
    date: str
    system: str  # מכלול
    description: str
    urgency: int  # 1-5 (5 = most urgent)
    assignee: str  # מבצע
    estimated_hours: float
    actual_hours: float = None  # שעות בפועל
    resolution_method: str = ""  # איך טופל?
    resolved_date: str = None
    resolved_by: str = ""
    lessons_learned: str = ""  # לקחים שנלמדו
    created_at: str = None
    resolved_at: str = None

class PendingMaintenance(BaseModel):
    id: str = None
    maintenance_type: str
    system: str  # מכלול
    frequency_days: int  # תדירות בימים
    last_performed: str  # תאריך ביצוע אחרון
    next_due: str = None  # תאריך ביצוע הבא - מחושב אוטומטית
    days_until_due: int = None  # ימים עד ביצוע - מחושב
    status: str = "ממתין"  # ממתין, בביצוע, הושלם
    created_at: str = None

class EquipmentHours(BaseModel):
    id: str = None
    system: str  # מכלול
    system_type: str  # מנועים, תשלובות, גנרטורים, מדחסים
    current_hours: float
    next_service_hours: float = None  # שעות הטיפול הבא - מחושב
    hours_until_service: float = None  # שעות עד טיפול - מחושב
    alert_level: str = None  # ירוק, כתום, אדום
    last_service_date: str = None
    created_at: str = None

class DailyWorkPlan(BaseModel):
    id: str = None
    date: str
    task: str
    source: str  # תקלה, אחזקה, טיפול
    source_id: str  # ID של המשימה המקורית
    assignee: str
    estimated_hours: float
    status: str = "מתוכנן"  # מתוכנן, בביצוע, הושלם
    notes: str = ""
    created_at: str = None

# Pydantic Models - Leadership Coaching

class Conversation(BaseModel):
    id: str = None
    meeting_number: int
    date: str
    duration_minutes: int
    main_topics: List[str]
    insights: List[str]
    decisions: List[str]
    next_step: str
    yahel_energy_level: int  # 1-10
    created_at: str = None

class DNATracker(BaseModel):
    id: str = None
    component_name: str  # זהות ותפקיד, אינטרסים אותנטיים, יכולות ומומחיות, עקרונות פעולה, מדדי הצלחה
    current_definition: str
    clarity_level: int  # 1-10
    gaps_identified: List[str]
    development_plan: str
    last_updated: str = None
    created_at: str = None

class NinetyDayPlan(BaseModel):
    id: str = None
    week_number: int  # 1-12 (90 days / 7 days)
    goals: List[str]
    concrete_actions: List[str]
    success_metrics: List[str]
    status: str = "מתוכנן"  # מתוכנן, בביצוע, הושלם
    reflection: str = ""
    created_at: str = None

class ChatMessage(BaseModel):
    user_message: str
    session_id: Optional[str] = None
    chat_history: List[dict] = []
    user_id: Optional[str] = None  # Will be set by the endpoint

class ChatResponse(BaseModel):
    response: str
    updated_tables: List[str] = []

class ExportRequest(BaseModel):
    table_name: str
    sheet_title: Optional[str] = None

class ExportResponse(BaseModel):
    success: bool
    spreadsheet_id: Optional[str] = None
    spreadsheet_url: Optional[str] = None
    message: str

# User Authentication Models
class User(BaseModel):
    id: str = None
    email: str
    name: str
    google_id: Optional[str] = None
    created_at: str = None
    last_login: str = None
    is_active: bool = True

class UserSession(BaseModel):
    id: str = None
    user_id: str
    session_token: str
    created_at: str = None
    expires_at: str = None
    is_active: bool = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[str] = None
    recommendations: List[str] = []

# Google Calendar Integration Models
class UserProfile(BaseModel):
    id: str = None
    email: str
    name: str
    google_access_token: Optional[str] = None
    google_refresh_token: Optional[str] = None
    google_token_expires_at: Optional[datetime] = None
    created_at: str = None

class CalendarEvent(BaseModel):
    id: str = None
    google_event_id: Optional[str] = None
    title: str
    description: Optional[str] = ""
    start_time: datetime
    end_time: datetime
    location: Optional[str] = ""
    attendees: List[str] = []
    source_type: str = "manual"  # manual, maintenance, daily_plan, failure
    source_id: Optional[str] = None  # ID of the source item
    user_email: str
    created_at: str = None

class CalendarEventRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    start_time: str  # ISO format
    end_time: str    # ISO format  
    location: Optional[str] = ""
    attendees: List[str] = []

# Push Notifications Models
class PushSubscriptionData(BaseModel):
    endpoint: str = Field(..., description="Push service endpoint URL")
    keys: Dict[str, str] = Field(..., description="Encryption keys (p256dh and auth)")

class SubscribeRequest(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    subscription: PushSubscriptionData = Field(..., description="Push subscription object")

class NotificationRequest(BaseModel):
    user_id: str = Field(..., description="Target user identifier")
    title: str = Field(..., max_length=100, description="Notification title")
    body: str = Field(..., max_length=300, description="Notification body text")
    category: str = Field(default="general", description="Notification category")
    icon: Optional[str] = Field(None, description="Icon URL")
    badge: Optional[str] = Field(None, description="Badge icon URL")
    data: Optional[Dict] = Field(default_factory=dict, description="Custom data payload")
    urgent: bool = Field(default=False, description="Urgent notification flag")

class NotificationPreferences(BaseModel):
    user_id: str = Field(..., description="User identifier")
    categories: Dict[str, bool] = Field(default_factory=dict, description="Category enablement flags")
    quiet_hours_enabled: bool = Field(default=False, description="Enable quiet hours")
    quiet_hours_start: Optional[str] = Field(None, description="Quiet hours start time (HH:MM)")
    quiet_hours_end: Optional[str] = Field(None, description="Quiet hours end time (HH:MM)")
    language_code: str = Field(default="en", description="Preferred language")
    rtl_support: bool = Field(default=False, description="Enable RTL layout support")

# Helper functions

# Google Calendar Helper Functions
def create_google_oauth_flow():
    """Create Google OAuth flow"""
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [GOOGLE_REDIRECT_URI]
            }
        },
        scopes=GOOGLE_SCOPES
    )
    flow.redirect_uri = GOOGLE_REDIRECT_URI
    return flow

def get_user_by_email(email: str):
    """Get user from database by email"""
    return users_collection.find_one({"email": email})

def save_user_tokens(email: str, name: str, access_token: str, refresh_token: str = None, expires_at: datetime = None):
    """Save or update user Google tokens"""
    user_data = {
        "email": email,
        "name": name,
        "google_access_token": access_token,
        "google_refresh_token": refresh_token,
        "google_token_expires_at": expires_at,
        "updated_at": datetime.now().isoformat()
    }
    
    users_collection.update_one(
        {"email": email},
        {"$set": user_data, "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": datetime.now().isoformat()}},
        upsert=True
    )

def refresh_google_token(user_email: str):
    """Refresh Google access token using refresh token"""
    user = get_user_by_email(user_email)
    if not user or not user.get('google_refresh_token'):
        return False
    
    try:
        # Create credentials from stored tokens
        from google.oauth2.credentials import Credentials
        
        credentials = Credentials(
            token=user['google_access_token'],
            refresh_token=user['google_refresh_token'],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET
        )
        
        # Refresh the token
        credentials.refresh(GoogleRequest())
        
        # Save new tokens
        save_user_tokens(
            user['email'], 
            user['name'], 
            credentials.token,
            credentials.refresh_token,
            credentials.expiry
        )
        return True
    except Exception as e:
        print(f"Error refreshing token for {user_email}: {e}")
        return False

def get_google_calendar_service(user_email: str):
    """Get Google Calendar service for user"""
    user = get_user_by_email(user_email)
    if not user or not user.get('google_access_token'):
        return None
    
    try:
        from google.oauth2.credentials import Credentials
        
        credentials = Credentials(
            token=user['google_access_token'],
            refresh_token=user.get('google_refresh_token'),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET
        )
        
        # Check if token needs refresh
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(GoogleRequest())
            save_user_tokens(
                user['email'],
                user['name'],
                credentials.token,
                credentials.refresh_token,
                credentials.expiry
            )
        
        service = build('calendar', 'v3', credentials=credentials)
        return service
    except Exception as e:
        print(f"Error creating calendar service for {user_email}: {e}")
        return None

def calculate_maintenance_dates(maintenance: dict):
    """Calculate next due date and days until due"""
    if maintenance.get('last_performed'):
        last_date = datetime.fromisoformat(maintenance['last_performed'])
        next_date = last_date + timedelta(days=maintenance['frequency_days'])
        days_until = (next_date - datetime.now()).days
        
        maintenance['next_due'] = next_date.isoformat()[:10]
        maintenance['days_until_due'] = days_until
    
    return maintenance

# Push Notification Management Classes
class VAPIDKeyManager:
    def __init__(self, private_key_path: str = "vapid_private_key.pem", public_key_path: str = "vapid_public_key.pem"):
        self.private_key_path = private_key_path
        self.public_key_path = public_key_path
        self.ensure_keys_exist()
    
    def generate_vapid_keys(self):
        """Generate new VAPID key pair"""
        private_key = ec.generate_private_key(ec.SECP256R1())
        
        # Save private key
        with open(self.private_key_path, 'wb') as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Save public key
        public_key = private_key.public_key()
        with open(self.public_key_path, 'wb') as f:
            f.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))
        
        return self.get_application_server_key()
    
    def ensure_keys_exist(self):
        """Ensure VAPID keys exist, generate if missing"""
        if not Path(self.private_key_path).exists() or not Path(self.public_key_path).exists():
            self.generate_vapid_keys()
    
    def get_application_server_key(self):
        """Get base64url-encoded public key for client use"""
        with open(self.public_key_path, 'rb') as f:
            public_key_pem = f.read()
        
        public_key = serialization.load_pem_public_key(public_key_pem)
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )
        
        return base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')

class PushNotificationService:
    def __init__(self):
        self.vapid_manager = VAPIDKeyManager()
        self.default_categories = {
            'urgent_failures': True,
            'maintenance_reminders': True,
            'jessica_updates': True,
            'system_status': False
        }
    
    def get_user_subscriptions(self, user_id: str):
        """Get active push subscriptions for user"""
        subscriptions = list(push_subscriptions_collection.find({
            "user_id": user_id,
            "is_active": True
        }))
        return subscriptions
    
    def get_user_preferences(self, user_id: str, category: str = None):
        """Get user notification preferences"""
        preferences = notification_preferences_collection.find_one({"user_id": user_id}, {"_id": 0})
        
        if not preferences:
            # Create default preferences
            default_prefs = {
                "user_id": user_id,
                "categories": self.default_categories.copy(),
                "quiet_hours_enabled": False,
                "language_code": "he",  # Default to Hebrew for Israeli naval system
                "rtl_support": True,
                "created_at": datetime.now().isoformat()
            }
            notification_preferences_collection.insert_one(default_prefs)
            preferences = default_prefs
        
        if category:
            return {
                'enabled': preferences.get('categories', {}).get(category, True),
                'rtl_support': preferences.get('rtl_support', True),
                'language_code': preferences.get('language_code', 'he')
            }
        
        return preferences
    
    def is_quiet_hours(self, user_id: str) -> bool:
        """Check if current time is within user's quiet hours"""
        preferences = self.get_user_preferences(user_id)
        
        if not preferences.get('quiet_hours_enabled'):
            return False
        
        # Implementation would check current time against quiet hours
        # For now, return False
        return False
    
    async def send_notification(self, user_id: str, title: str, body: str, 
                              category: str = "general", data: Dict = None, 
                              icon: str = None, badge: str = None):
        """Send push notification to user"""
        try:
            # Get user subscriptions
            subscriptions = self.get_user_subscriptions(user_id)
            
            if not subscriptions:
                return {"status": "no_subscriptions", "message": "User has no active subscriptions"}
            
            # Check user preferences
            preferences = self.get_user_preferences(user_id, category)
            if not preferences.get('enabled', True):
                return {"status": "skipped", "reason": "notifications disabled for category"}
            
            # Check quiet hours
            if self.is_quiet_hours(user_id):
                return {"status": "queued", "reason": "quiet hours active"}
            
            # Prepare notification data with Hebrew support
            is_hebrew = preferences.get('language_code', 'he') == 'he'
            notification_data = {
                "title": title,
                "body": body,
                "icon": icon or "/icons/notification-icon.png",
                "badge": badge or "/icons/badge-icon.png",
                "data": data or {},
                "category": category,
                "timestamp": datetime.utcnow().isoformat(),
                "rtl": preferences.get('rtl_support', True),
                "lang": preferences.get('language_code', 'he')
            }
            
            # Send to each subscription
            delivery_results = []
            for subscription in subscriptions:
                try:
                    # For now, we'll simulate delivery
                    # In a real implementation, this would use webpush library
                    delivery_results.append({"status": "delivered", "endpoint": subscription.get("endpoint", "unknown")})
                    
                    # Log notification
                    self.log_notification(user_id, title, body, category, "delivered")
                    
                except Exception as e:
                    delivery_results.append({"status": "failed", "error": str(e)})
                    self.log_notification(user_id, title, body, category, "failed", str(e))
            
            return {"status": "completed", "results": delivery_results}
            
        except Exception as e:
            print(f"Error sending notification: {e}")
            return {"status": "error", "message": str(e)}
    
    def log_notification(self, user_id: str, title: str, body: str, category: str, status: str, error_message: str = None):
        """Log notification delivery attempt"""
        log_entry = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "title": title,
            "body": body,
            "category": category,
            "status": status,
            "delivery_timestamp": datetime.now().isoformat(),
            "error_message": error_message
        }
        notification_history_collection.insert_one(log_entry)

# Initialize services
push_service = PushNotificationService()

# Authentication Functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_by_google_id(google_id: str):
    """Get user by Google ID"""
    user = authenticated_users_collection.find_one({"google_id": google_id}, {"_id": 0})
    return user

def create_user(email: str, name: str, google_id: str = None):
    """Create a new user in the system"""
    user_id = str(uuid.uuid4())
    user_data = {
        "id": user_id,
        "email": email,
        "name": name,
        "google_id": google_id,
        "created_at": datetime.now().isoformat(),
        "last_login": datetime.now().isoformat(),
        "is_active": True
    }
    
    authenticated_users_collection.insert_one(user_data)
    return user_data

def create_user_session(user_id: str, session_token: str):
    """Create a user session"""
    session_data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "session_token": session_token,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).isoformat(),
        "is_active": True
    }
    
    user_sessions_collection.insert_one(session_data)
    return session_data

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get the current authenticated user"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not credentials:
        raise credentials_exception
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        
        if email is None or user_id is None:
            raise credentials_exception
            
        token_data = TokenData(email=email, user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    # Check if user exists and is active
    user = authenticated_users_collection.find_one({"id": user_id, "is_active": True}, {"_id": 0})
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get the current user if authenticated, None otherwise"""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

def calculate_service_hours(equipment: dict):
    """Calculate next service hours and alert level based on system type"""
    system_type = equipment['system_type'].lower()
    current_hours = equipment['current_hours']
    
    # Service intervals by system type
    intervals = {
        'מנועים': [250, 500, 1500, 3000, 6000],
        'תשלובות': [500, 1000, 6000], 
        'גנרטורים': [400, 2000, 6000, 18000],
        'מדחסים': [200, 600, 6000]
    }
    
    # Find next service interval
    service_intervals = intervals.get(system_type, [500, 1000, 5000])
    next_service = None
    
    for interval in service_intervals:
        if current_hours < interval:
            next_service = interval
            break
    
    if not next_service:
        next_service = service_intervals[-1] + service_intervals[-1]  # Add another full cycle
    
    hours_until = next_service - current_hours
    
    # Alert levels
    if hours_until <= 10:
        alert_level = "אדום"
    elif hours_until <= 50:
        alert_level = "כתום"
    else:
        alert_level = "ירוק"
    
    equipment['next_service_hours'] = next_service
    equipment['hours_until_service'] = hours_until
    equipment['alert_level'] = alert_level
    
    return equipment

def get_department_summary(user_id: str):
    """Get summary of all department data for AI analysis"""
    try:
        failures = list(active_failures_collection.find({"user_id": user_id}, {"_id": 0}))
        maintenance = list(pending_maintenance_collection.find({"user_id": user_id}, {"_id": 0}))
        equipment = list(equipment_hours_collection.find({"user_id": user_id}, {"_id": 0}))
        daily_work = list(daily_work_collection.find({"user_id": user_id}, {"_id": 0}))
        
        # Recalculate dynamic fields
        for item in maintenance:
            item = calculate_maintenance_dates(item)
        for item in equipment:
            item = calculate_service_hours(item)
            
        return {
            "failures": failures,
            "maintenance": maintenance,
            "equipment": equipment,
            "daily_work": daily_work,
            "summary": {
                "urgent_failures": len([f for f in failures if f.get('urgency', 0) >= 4]),
                "overdue_maintenance": len([m for m in maintenance if m.get('days_until_due', 999) <= 0]),
                "critical_equipment": len([e for e in equipment if e.get('alert_level') == 'אדום']),
                "today_tasks": len([w for w in daily_work if w.get('date') == datetime.now().isoformat()[:10]])
            }
        }
    except Exception as e:
        print(f"Error getting department summary: {e}")
        return {}

def get_leadership_context(user_id: str):
    """Get leadership coaching context"""
    try:
        conversations = list(conversations_collection.find({"user_id": user_id}, {"_id": 0}).sort("meeting_number", -1).limit(5))
        dna_items = list(dna_tracker_collection.find({"user_id": user_id}, {"_id": 0}))
        plan_items = list(ninety_day_plan_collection.find({"user_id": user_id}, {"_id": 0}).sort("week_number", 1))
        
        return {
            "recent_conversations": conversations,
            "dna_tracker": dna_items,
            "ninety_day_plan": plan_items
        }
    except Exception as e:
        print(f"Error getting leadership context: {e}")
        return {}

async def move_failure_to_resolved(failure_data: dict, resolution_info: dict = None):
    """Move completed failure to resolved failures table"""
    try:
        # Create resolved failure record
        resolved_failure = {
            'id': failure_data['id'],
            'user_id': failure_data.get('user_id'),  # Maintain user_id
            'failure_number': failure_data['failure_number'],
            'date': failure_data['date'],
            'system': failure_data['system'],
            'description': failure_data['description'],
            'urgency': failure_data['urgency'],
            'assignee': failure_data['assignee'],
            'estimated_hours': failure_data['estimated_hours'],
            'actual_hours': resolution_info.get('actual_hours') if resolution_info else failure_data['estimated_hours'],
            'resolution_method': resolution_info.get('resolution_method', '') if resolution_info else '',
            'resolved_date': datetime.now().isoformat()[:10],
            'resolved_by': resolution_info.get('resolved_by', failure_data['assignee']) if resolution_info else failure_data['assignee'],
            'lessons_learned': resolution_info.get('lessons_learned', '') if resolution_info else '',
            'created_at': failure_data['created_at'],
            'resolved_at': datetime.now().isoformat()
        }
        
        # Insert into resolved failures
        resolved_failures_collection.insert_one(resolved_failure)
        
        # Remove from active failures (filter by user_id)
        active_failures_collection.delete_one({'id': failure_data['id'], 'user_id': failure_data.get('user_id')})
        
        print(f"Moved failure {failure_data['failure_number']} to resolved failures")
        return True
        
    except Exception as e:
        print(f"Error moving failure to resolved: {e}")
        return False

# AI Agent Functions

# AI Agent Functions with Database Operations

def parse_ai_actions(ai_response: str):
    """Parse AI response for database actions"""
    actions = []
    
    # Look for action patterns in AI response
    import re
    
    # ADD patterns
    add_failure_pattern = r'\[ADD_FAILURE:(.*?)\]'
    add_maintenance_pattern = r'\[ADD_MAINTENANCE:(.*?)\]'
    add_equipment_pattern = r'\[ADD_EQUIPMENT:(.*?)\]'
    add_daily_work_pattern = r'\[ADD_DAILY_WORK:(.*?)\]'
    add_conversation_pattern = r'\[ADD_CONVERSATION:(.*?)\]'
    add_dna_item_pattern = r'\[ADD_DNA_ITEM:(.*?)\]'
    add_90day_plan_pattern = r'\[ADD_90DAY_PLAN:(.*?)\]'
    
    # UPDATE patterns - NEW!
    update_failure_pattern = r'\[UPDATE_FAILURE:(.*?)\]'
    update_maintenance_pattern = r'\[UPDATE_MAINTENANCE:(.*?)\]'
    update_equipment_pattern = r'\[UPDATE_EQUIPMENT:(.*?)\]'
    update_daily_work_pattern = r'\[UPDATE_DAILY_WORK:(.*?)\]'
    update_conversation_pattern = r'\[UPDATE_CONVERSATION:(.*?)\]'
    update_dna_item_pattern = r'\[UPDATE_DNA_ITEM:(.*?)\]'
    update_90day_plan_pattern = r'\[UPDATE_90DAY_PLAN:(.*?)\]'
    
    # DELETE patterns - NEW!
    delete_failure_pattern = r'\[DELETE_FAILURE:(.*?)\]'
    delete_maintenance_pattern = r'\[DELETE_MAINTENANCE:(.*?)\]'
    delete_equipment_pattern = r'\[DELETE_EQUIPMENT:(.*?)\]'
    delete_daily_work_pattern = r'\[DELETE_DAILY_WORK:(.*?)\]'
    
    # RESOLVED FAILURE patterns - NEW!
    update_resolved_failure_pattern = r'\[UPDATE_RESOLVED_FAILURE:(.*?)\]'
    
    patterns = [
        # ADD patterns
        (add_failure_pattern, 'add_failure'),
        (add_maintenance_pattern, 'add_maintenance'),
        (add_equipment_pattern, 'add_equipment'),
        (add_daily_work_pattern, 'add_daily_work'),
        (add_conversation_pattern, 'add_conversation'),
        (add_dna_item_pattern, 'add_dna_item'),
        (add_90day_plan_pattern, 'add_90day_plan'),
        
        # UPDATE patterns
        (update_failure_pattern, 'update_failure'),
        (update_maintenance_pattern, 'update_maintenance'),
        (update_equipment_pattern, 'update_equipment'),
        (update_daily_work_pattern, 'update_daily_work'),
        (update_conversation_pattern, 'update_conversation'),
        (update_dna_item_pattern, 'update_dna_item'),
        (update_90day_plan_pattern, 'update_90day_plan'),
        
        # DELETE patterns
        (delete_failure_pattern, 'delete_failure'),
        (delete_maintenance_pattern, 'delete_maintenance'),
        (delete_equipment_pattern, 'delete_equipment'),
        (delete_daily_work_pattern, 'delete_daily_work'),
        
        # RESOLVED FAILURE patterns
        (update_resolved_failure_pattern, 'update_resolved_failure'),
    ]
    
    for pattern, action_type in patterns:
        for match in re.finditer(pattern, ai_response, re.DOTALL):
            try:
                action_data = match.group(1).strip()
                # Parse the parameters
                params = {}
                for param in action_data.split(','):
                    if '=' in param:
                        key, value = param.strip().split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        # Handle list parameters
                        if key in ['main_topics', 'insights', 'decisions', 'gaps_identified', 'goals', 'concrete_actions', 'success_metrics']:
                            if ',' in value:
                                params[key] = [item.strip() for item in value.split(',')]
                            else:
                                params[key] = [value]
                        elif key in ['duration_minutes', 'yahel_energy_level', 'clarity_level', 'week_number', 'frequency_days', 'urgency']:
                            params[key] = int(value) if value.isdigit() else 1
                        elif key in ['estimated_hours', 'current_hours']:
                            params[key] = float(value) if value.replace('.', '').isdigit() else 0.0
                        else:
                            params[key] = value
                
                actions.append((action_type, params))
            except Exception as e:
                print(f"Error parsing action {action_type}: {e}")
    
    return actions

async def execute_ai_actions(actions, user_id: str):
    """Execute database actions from AI"""
    updated_tables = []
    
    for action_type, params in actions:
        try:
            if action_type == 'add_failure':
                # Create failure
                failure_data = {
                    'id': str(uuid.uuid4()),
                    'user_id': user_id,  # Add user_id
                    'failure_number': params.get('failure_number', f'F{datetime.now().strftime("%m%d%H%M")}'),
                    'date': params.get('date', datetime.now().isoformat()[:10]),
                    'system': params.get('system', ''),
                    'description': params.get('description', ''),
                    'urgency': int(params.get('urgency', 3)),
                    'assignee': params.get('assignee', ''),
                    'estimated_hours': float(params.get('estimated_hours', 2)),
                    'status': 'פעיל',
                    'created_at': datetime.now().isoformat()
                }
                active_failures_collection.insert_one(failure_data)
                updated_tables.append('תקלות פעילות')
                
            elif action_type == 'update_failure':
                # Update existing failure
                failure_id = params.get('id') or params.get('failure_number')
                if not failure_id:
                    print("Error: No ID provided for failure update")
                    continue
                    
                # Get current failure data before update
                query = {'id': failure_id} if failure_id.startswith('F') == False else {'failure_number': failure_id}
                current_failure = active_failures_collection.find_one(query)
                
                if not current_failure:
                    print(f"Failure {failure_id} not found for update")
                    continue
                
                update_data = {}
                if 'status' in params:
                    update_data['status'] = params['status']
                if 'urgency' in params:
                    update_data['urgency'] = int(params['urgency'])
                if 'assignee' in params:
                    update_data['assignee'] = params['assignee']
                if 'description' in params:
                    update_data['description'] = params['description']
                if 'estimated_hours' in params:
                    update_data['estimated_hours'] = float(params['estimated_hours'])
                
                # Check if failure is being resolved
                if update_data.get('status') in ['הושלם', 'נסגר', 'טופל']:
                    # Get resolution details if provided
                    resolution_info = {
                        'actual_hours': params.get('actual_hours'),
                        'resolution_method': params.get('resolution_method', ''),
                        'resolved_by': params.get('resolved_by', current_failure['assignee']),
                        'lessons_learned': params.get('lessons_learned', '')
                    }
                    
                    # Move to resolved failures
                    moved = await move_failure_to_resolved(current_failure, resolution_info)
                    if moved:
                        updated_tables.append('תקלות פעילות')
                        updated_tables.append('תקלות שטופלו')
                        print(f"Moved resolved failure {failure_id} to resolved table")
                        
                        # Store the failure number for Jessica to ask about resolution
                        # This will trigger Jessica to ask follow-up questions
                        if not resolution_info.get('resolution_method'):
                            # Store in session that we need to ask about this failure
                            resolved_failure_info = {
                                'failure_number': current_failure['failure_number'],
                                'system': current_failure['system'],
                                'description': current_failure['description'],
                                'needs_resolution_details': True
                            }
                            # Store in a way Jessica can access it
                            print(f"Need to ask about resolution for {current_failure['failure_number']}")
                else:
                    # Regular update
                    result = active_failures_collection.update_one(query, {'$set': update_data})
                    
                    if result.matched_count > 0:
                        updated_tables.append('תקלות פעילות')
                        print(f"Updated failure {failure_id}: {update_data}")
                    else:
                        print(f"Failure {failure_id} not found for update")
                    
            elif action_type == 'delete_failure':
                # Delete failure
                failure_id = params.get('id') or params.get('failure_number')
                if not failure_id:
                    print("Error: No ID provided for failure deletion")
                    continue
                    
                query = {'id': failure_id} if failure_id.startswith('F') == False else {'failure_number': failure_id}
                result = active_failures_collection.delete_one(query)
                
                if result.deleted_count > 0:
                    updated_tables.append('תקלות פעילות')
                    print(f"Deleted failure {failure_id}")
                else:
                    print(f"Failure {failure_id} not found for deletion")
                
            elif action_type == 'add_maintenance':
                # Create maintenance
                maintenance_data = {
                    'id': str(uuid.uuid4()),
                    'maintenance_type': params.get('maintenance_type', ''),
                    'system': params.get('system', ''),
                    'frequency_days': int(params.get('frequency_days', 30)),
                    'last_performed': params.get('last_performed', datetime.now().isoformat()[:10]),
                    'status': 'ממתין',
                    'created_at': datetime.now().isoformat()
                }
                maintenance_data = calculate_maintenance_dates(maintenance_data)
                pending_maintenance_collection.insert_one(maintenance_data)
                updated_tables.append('אחזקות ממתינות')
                
            elif action_type == 'update_maintenance':
                # Update maintenance
                maintenance_id = params.get('id')
                if not maintenance_id:
                    print("Error: No ID provided for maintenance update")
                    continue
                    
                update_data = {}
                if 'status' in params:
                    update_data['status'] = params['status']
                if 'last_performed' in params:
                    update_data['last_performed'] = params['last_performed']
                if 'frequency_days' in params:
                    update_data['frequency_days'] = int(params['frequency_days'])
                
                # Recalculate dates if needed
                if 'last_performed' in update_data or 'frequency_days' in update_data:
                    update_data = calculate_maintenance_dates(update_data)
                
                result = pending_maintenance_collection.update_one({'id': maintenance_id}, {'$set': update_data})
                if result.matched_count > 0:
                    updated_tables.append('אחזקות ממתינות')
                    print(f"Updated maintenance {maintenance_id}")
                else:
                    print(f"Maintenance {maintenance_id} not found for update")
                
            elif action_type == 'add_equipment':
                # Create equipment
                equipment_data = {
                    'id': str(uuid.uuid4()),
                    'system': params.get('system', ''),
                    'system_type': params.get('system_type', 'מנועים'),
                    'current_hours': float(params.get('current_hours', 0)),
                    'last_service_date': params.get('last_service_date', ''),
                    'created_at': datetime.now().isoformat()
                }
                equipment_data = calculate_service_hours(equipment_data)
                equipment_hours_collection.insert_one(equipment_data)
                updated_tables.append('שעות מכלולים')
                
            elif action_type == 'update_equipment':
                # Update equipment
                equipment_id = params.get('id')
                if not equipment_id:
                    print("Error: No ID provided for equipment update")
                    continue
                    
                update_data = {}
                if 'current_hours' in params:
                    update_data['current_hours'] = float(params['current_hours'])
                if 'last_service_date' in params:
                    update_data['last_service_date'] = params['last_service_date']
                
                # Recalculate service hours
                if update_data:
                    existing_equipment = equipment_hours_collection.find_one({'id': equipment_id})
                    if existing_equipment:
                        existing_equipment.update(update_data)
                        update_data = calculate_service_hours(existing_equipment)
                
                result = equipment_hours_collection.update_one({'id': equipment_id}, {'$set': update_data})
                if result.matched_count > 0:
                    updated_tables.append('שעות מכלולים')
                    print(f"Updated equipment {equipment_id}")
                else:
                    print(f"Equipment {equipment_id} not found for update")
                
            elif action_type == 'add_daily_work':
                # Create daily work
                work_data = {
                    'id': str(uuid.uuid4()),
                    'date': params.get('date', datetime.now().isoformat()[:10]),
                    'task': params.get('task', ''),
                    'source': params.get('source', 'אחר'),
                    'source_id': params.get('source_id', ''),
                    'assignee': params.get('assignee', ''),
                    'estimated_hours': float(params.get('estimated_hours', 2)),
                    'status': 'מתוכנן',
                    'notes': params.get('notes', ''),
                    'created_at': datetime.now().isoformat()
                }
                daily_work_collection.insert_one(work_data)
                updated_tables.append('תכנון יומי')
                
            elif action_type == 'update_daily_work':
                # Update daily work
                work_id = params.get('id')
                if not work_id:
                    print("Error: No ID provided for daily work update")
                    continue
                    
                update_data = {}
                if 'status' in params:
                    update_data['status'] = params['status']
                if 'notes' in params:
                    update_data['notes'] = params['notes']
                if 'assignee' in params:
                    update_data['assignee'] = params['assignee']
                
                result = daily_work_collection.update_one({'id': work_id}, {'$set': update_data})
                if result.matched_count > 0:
                    updated_tables.append('תכנון יומי')
                    print(f"Updated daily work {work_id}")
                else:
                    print(f"Daily work {work_id} not found for update")
                
            elif action_type == 'add_conversation':
                # Create leadership conversation
                conversation_data = {
                    'id': str(uuid.uuid4()),
                    'meeting_number': int(params.get('meeting_number', 1)),
                    'date': params.get('date', datetime.now().isoformat()[:10]),
                    'duration_minutes': int(params.get('duration_minutes', 30)),
                    'main_topics': params.get('main_topics', []),
                    'insights': params.get('insights', []),
                    'decisions': params.get('decisions', []),
                    'next_step': params.get('next_step', ''),
                    'yahel_energy_level': int(params.get('yahel_energy_level', 5)),
                    'created_at': datetime.now().isoformat()
                }
                conversations_collection.insert_one(conversation_data)
                updated_tables.append('מעקב שיחות')
                
            elif action_type == 'add_dna_item':
                # Create or update DNA tracker item
                dna_data = {
                    'id': str(uuid.uuid4()),
                    'component_name': params.get('component_name', ''),
                    'current_definition': params.get('current_definition', ''),
                    'clarity_level': int(params.get('clarity_level', 5)),
                    'gaps_identified': params.get('gaps_identified', []),
                    'development_plan': params.get('development_plan', ''),
                    'last_updated': datetime.now().isoformat()[:10],
                    'created_at': datetime.now().isoformat()
                }
                
                # Check if DNA component already exists
                existing = dna_tracker_collection.find_one({'component_name': dna_data['component_name']})
                if existing:
                    # Update existing
                    dna_tracker_collection.update_one(
                        {'component_name': dna_data['component_name']},
                        {'$set': dna_data}
                    )
                else:
                    # Create new
                    dna_tracker_collection.insert_one(dna_data)
                
                updated_tables.append('DNA Tracker')
                
            elif action_type == 'add_90day_plan':
                # Create 90-day plan item
                plan_data = {
                    'id': str(uuid.uuid4()),
                    'week_number': int(params.get('week_number', 1)),
                    'goals': params.get('goals', []),
                    'concrete_actions': params.get('concrete_actions', []),
                    'success_metrics': params.get('success_metrics', []),
                    'status': params.get('status', 'מתוכנן'),
                    'reflection': params.get('reflection', ''),
                    'created_at': datetime.now().isoformat()
                }
                
                # Check if week already exists
                existing = ninety_day_plan_collection.find_one({'week_number': plan_data['week_number']})
                if existing:
                    # Update existing
                    ninety_day_plan_collection.update_one(
                        {'week_number': plan_data['week_number']},
                        {'$set': plan_data}
                    )
                else:
                    # Create new
                    ninety_day_plan_collection.insert_one(plan_data)
                
                updated_tables.append('תכנית 90 יום')
                
            elif action_type == 'update_resolved_failure':
                # Update resolved failure details
                failure_id = params.get('id') or params.get('failure_number')
                if not failure_id:
                    print("Error: No ID provided for resolved failure update")
                    continue
                
                update_data = {}
                if 'resolution_method' in params:
                    update_data['resolution_method'] = params['resolution_method']
                if 'actual_hours' in params:
                    update_data['actual_hours'] = float(params['actual_hours'])
                if 'lessons_learned' in params:
                    update_data['lessons_learned'] = params['lessons_learned']
                if 'resolved_by' in params:
                    update_data['resolved_by'] = params['resolved_by']
                
                query = {'id': failure_id} if failure_id.startswith('F') == False else {'failure_number': failure_id}
                result = resolved_failures_collection.update_one(query, {'$set': update_data})
                
                if result.matched_count > 0:
                    updated_tables.append('תקלות שטופלו')
                    print(f"Updated resolved failure {failure_id}: {update_data}")
                else:
                    print(f"Resolved failure {failure_id} not found for update")
                
        except Exception as e:
            print(f"Error executing action {action_type}: {e}")
    
    return updated_tables

async def create_yahel_ai_agent(user_message: str, session_id: str = None, chat_history: List[dict] = None, current_user: dict = None) -> ChatResponse:
    """Create AI agent for Yahel with department and leadership context"""
    try:
        user_id = current_user['id'] if current_user else None
        
        # Get all context
        dept_data = get_department_summary(user_id) if user_id else {}
        leadership_data = get_leadership_context(user_id) if user_id else {}
        
        # Build conversation history context
        conversation_context = ""
        if chat_history and len(chat_history) > 1:
            conversation_context = "\n\n📝 **היסטוריית השיחה הנוכחית:**\n"
            for msg in chat_history[-6:]:  # Last 6 messages for context
                if msg.get('type') == 'user':
                    conversation_context += f"יהל: {msg.get('content', '')}\n"
                elif msg.get('type') == 'ai':
                    conversation_context += f"ג'סיקה: {msg.get('content', '')[:200]}...\n"
        
        # Get user's preferred name from chat history or ask for it
        user_name = None
        if chat_history:
            # Look for stored name in previous conversations
            for msg in chat_history:
                if msg.get('role') == 'assistant' and 'אני אקרא לך:' in msg.get('content', ''):
                    import re
                    match = re.search(r'אני אקרא לך:\s*([^\s,.\n]+)', msg.get('content', ''))
                    if match:
                        user_name = match.group(1)
                        break
        
        # If no name found in history and this is the first interaction, ask for name
        if not user_name and (not chat_history or len(chat_history) == 0):
            system_message = f"""
אתה ג'סיקה - האייג'נט AI של מערכת ניהול המחלקה הצבאית. 
אתה מתמחה בניהול מחלקה וליווי מנהיגותי.

🎯 **משימה ראשונה חשובה:**
שאל את המשתמש: "איך אתה רוצה שאני אקרא לך?" 
אל תמציא שמות ואל תקרא לו בשום שם עד שהוא יגיד לך במפורש.

אחרי שתקבל את השם, השב: "נחמד להכיר אותך! אני אקרא לך: [השם שהמשתמש נתן]"
מכיון ועד זה, זכור את השם הזה לכל השיחות הבאות והשתמש בו.

**🚫 חובה - אל תמציא מידע:**
- אם חסר לך מידע ספציפי - אמור במפורש "אין לי מידע על זה" או "לא מצאתי פרטים" 
- אם אתה לא בטוח - אמור "אני לא בטוח" ובקש הבהרה
- אם צריך מידע נוסף - שאל שאלות ברורות ומפורטות

השב בעברית בצורה חמה ומקצועית.
"""
        else:
            # Use the stored name or default behavior
            display_name = user_name if user_name else "המשתמש"
            system_message = f"""
אתה ג'סיקה - האייג'נט AI של {display_name}, מנהל מחלקה בחיל הים הישראלי. 
אתה משלב שלושה תפקידים מרכזיים:

1. **מערכת ניהול מחלקה מתקדמת** 
2. **סוכנת ליווי מנהיגותי** המיישמת עקרונות המארג הקוונטי
3. **מאמן אישי** לפיתוח מנהיגות צבאית-אישית

🧬 **עקרונות המארג הקוונטי שאתה מיישם:**
- **עקרון אי-ההשוואה™**: עזור ל{display_name} לבנות זהות מנהיגותית ייחודית
- **נאמנות ל-DNA™**: כל החלטה עקבית עם הזהות והערכים של {display_name}
- **זמן קוונטי ומהירות אקספוננציאלית™**: תוצאות פי 10, לא פלוס 10%
- **בריאה עצמית אוטונומית™**: {display_name} מפתח בעצמו את היכולות הנדרשות

**🚫 חובה - אל תמציא מידע:**
- אם חסר לך מידע ספציפי (מספרי תקלה, שמות, זמנים, תאריכים) - אמור במפורש "אין לי מידע על זה" או "לא מצאתי פרטים על זה במערכת"
- אם לא בטוח במידע - אמור "אני לא בטוח בפרט הזה" ובקש הבהרה מ{display_name}
- אם צריך להזין ערך ואין לך מידע - השאר ריק או תזין "לא צוין"
- כשמבקש מ{display_name} מידע חסר - שאל שאלות ברורות ומפורטות: "איזה תאריך?", "איזה טכנאי?", "כמה זמן בדיוק?"

📊 **נתוני המחלקה הנוכחיים:**
{json.dumps(dept_data, ensure_ascii=False, indent=2)}

🎯 **נתוני הליווי המנהיגותי:**
{json.dumps(leadership_data, ensure_ascii=False, indent=2)}

{conversation_context}

💪 **יכולות עדכון טבלאות מלא:**
אתה יכול להוסיף, לעדכן ולמחוק פריטים בכל הטבלאות. השתמש בפורמטים הבאים:

**הוספת פריטים חדשים:**
[ADD_FAILURE: failure_number="F003", system="מערכת קירור", description="תיאור התקלה", urgency="4", assignee="טכנאי דן", estimated_hours="3"]
[ADD_MAINTENANCE: maintenance_type="בדיקה שבועית", system="מנוע ראשי", frequency_days="7", last_performed="2025-08-14"]
[ADD_EQUIPMENT: system="מנוע חדש", system_type="מנועים", current_hours="0", last_service_date="2025-08-14"]
[ADD_DAILY_WORK: date="2025-08-15", task="ביצוע בדיקה", source="תקלה", assignee="טכנאי מור", estimated_hours="2", notes="דחוף"]

**עדכון פריטים קיימים:**
[UPDATE_FAILURE: id="F004", status="הושלם"]
[UPDATE_FAILURE: failure_number="F004", status="נסגר", resolution_method="החלפת רכיב פגום", actual_hours="3.5", resolved_by="טכנאי רונן"]
[UPDATE_MAINTENANCE: id="maintenance_id", status="הושלם", last_performed="2025-08-14"]
[UPDATE_EQUIPMENT: id="equipment_id", current_hours="250"]
[UPDATE_DAILY_WORK: id="work_id", status="הושלם", notes="בוצע בהצלחה"]

**עדכון תקלות שטופלו:**
[UPDATE_RESOLVED_FAILURE: failure_number="F004", resolution_method="החלפת רכיב פגום", actual_hours="3.5", lessons_learned="חשוב לבדוק רכיבים דומים"]

**מחיקת פריטים:**
[DELETE_FAILURE: failure_number="F004"]
[DELETE_MAINTENANCE: id="maintenance_id"]
[DELETE_EQUIPMENT: id="equipment_id"]
[DELETE_DAILY_WORK: id="work_id"]

**טבלאות ליווי מנהיגותי:**
[ADD_CONVERSATION: meeting_number="5", date="2025-08-14", duration_minutes="45", main_topics="פיתוח מנהיגות,תכנון קריירה", insights="{display_name} מראה התקדמות בביטחון עצמי", decisions="להתמקד בפיתוח כישורי תקשורת", next_step="תרגול מתן פידבק לצוות", energy_level="8"]

[ADD_DNA_ITEM: component_name="זהות ותפקיד", current_definition="צ'יף מנוסה עם חזון לשיפור המחלקה", clarity_level="7", gaps_identified="צריך להגדיר טוב יותר את הסגנון המנהיגותי הייחודי", development_plan="שיחות עומק על ערכים אישיים ומקצועיים"]

[ADD_90DAY_PLAN: week_number="3", goals="שיפור תקשורת עם הצוות,הטמעת תהליכי עבודה חדשים", concrete_actions="פגישות יחיד עם כל חבר צוות,הכנת מדריך נהלים", success_metrics="שביעות רצון צוות מעל 85%,הפחתת זמן טיפול בתקלות ב-20%", status="מתוכנן"]

**⚡ חשוב מאוד:**
- כדי לסגור תקלה: [UPDATE_FAILURE: failure_number="F004", status="הושלם"]
- כדי לסמן משימה כהושלמה: [UPDATE_DAILY_WORK: id="work_id", status="הושלם"]
- כדי לעדכן ציוד: [UPDATE_EQUIPMENT: id="equipment_id", current_hours="250"]
- תמיד הקפד על הפורמט המדויק - id או failure_number נדרש לעדכונים!

**🚫 חובה - אל תמציא מידע:**
- אם חסר לך מידע ספציפי (מספרי תקלה, שמות, זמנים, תאריכים) - השתמש בביטויים: "אין לי מידע על זה", "לא מצאתי פרטים על זה במערכת", "לא נרשם במערכת"
- אם לא בטוח במידע - תמיד אמור "אני לא בטוח בפרט הזה" ובקש הבהרה
- אם צריך להזין ערך ואין לך מידע - השאר ריק או תזין "לא צוין"
- כשצריך פרטים חסרים - שאל שאלות ספציפיות: "איזה תאריך בדיוק?", "איזה טכנאי בדיוק טיפל?", "כמה זמן לקח בדיוק?"

🎯 **התפקידים שלך:**

**כמנהל מחלקה:**
1. נתח את מצב המחלקה והמלץ על עדיפויות
2. זהה patterns ובעיות חוזרות
3. הצע פתרונות מעשיים ליעילות
4. הוסף/עדכן פריטים בטבלאות כשצריך

**כמלווה מנהיגותית:**
1. **השתמש בהיסטוריית השיחה** לרצף טבעי - זכור מה דיברנו קודם
2. שאל שאלות זיקוק אינטרסים מותאמות למצב של המשתמש
3. אתגר את המשתמש לחשוב אקספוננציאלית
4. עזור לו לבנות DNA מנהיגותי חדש
5. **תמיד עדכן את טבלת השיחות אחרי אינטראקציה משמעותית!**

**🔍 כמנהל תקלות מתקדם:**
1. **כשמבקשים לסגור תקלה** - תמיד בצע קודם את הסגירה
2. ביטויים שמחייבים סגירה מיידית:
   - "סגרי את התקלה [מספר]"
   - "התקלה [מספר] טופלה"
   - "סיימנו עם התקלה [מספר]"
   
3. **זרימת עבודה:**
   א) תמיד בצע: [UPDATE_FAILURE: failure_number="F123", status="נסגר"]
   ב) תמיד שאל את השאלות:
      - "כמה זמן זה לקח?"
      - "מי טיפל בתקלה?"  
      - "האם צריך לעשות משהו בעתיד כדי שזה לא יחזור על עצמו?"
   ג) **כל תשובה שכוללת "זמן:" ו"מי:" ו"מניעה:"** - תמיד בצע UPDATE_RESOLVED_FAILURE

**⚠️ חובה לזכור:** כל הודעה עם הפרטים "זמן:", "מי:", "מניעה:" היא תשובה לשאלות שלך!

**⚡ דוגמה מלאה:**
משתמש: "ג'סיקה, סגרי את התקלה F123"
אתה: [UPDATE_FAILURE: failure_number="F123", status="נסגר"]
       "התקלה F123 נסגרה. כמה זמן זה לקח? מי טיפל בתקלה? האם צריך לעשות משהו בעתיד כדי שזה לא יחזור על עצמו?"
משתמש: "זמן: 2 שעות, מי: טכנאי יוסי, מניעה: החלפת חלק"
אתה: [UPDATE_RESOLVED_FAILURE: failure_number="F123", actual_hours="2", resolved_by="טכנאי יוסי", lessons_learned="החלפת חלק"]
      "תודה! עדכנתי את פרטי הפתרון של התקלה F123."

🔥 **שאלות זיקוק אינטרסים מומלצות:**
- "מה באמת מניע אותך במעבר לתפקיד החדש?"
- "איזה חלום או חזון יש לך לגבי המחלקה?"
- "מה התחום שאתה הכי אוהב לפתור בעבודה?"
- "איך אתה רואה את עצמך כמנהיג בעוד שנתיים?"
- "מה המורכבות הכי גדולה שאתה מתמודד איתה עכשיו?"

📋 **דוגמאות למתי לעדכן טבלאות:**
- המשתמש מספר על שיחה או מפגש → עדכן טבלת שיחות
- מזהה gap בכישורים → עדכן DNA Tracker
- קובע יעדים או תכניות → עדכן תכנית 90 יום
- מזכיר תקלה/משימה → עדכן טבלאות מחלקה

🎯 **המטרה הסופית:** 
המשתמש יהיה לא רק צ'יף טוב, אלא יחולל מהפכה באופן ניהול מחלקות בחיל הים.
תמיד חשוב אקספוננציאלית - איך להגיע לפי 10 שיפור במקום פלוס 10%.

**חשוב: השתמש בהיסטוריית השיחה כדי לתת תגובות רצופות וטבעיות. אל תחזור על מידע שכבר נאמר.**

השב בעברית, בצורה ישירה ומעשית, כמי שמכיר את המשתמש באופן אישי ויודע את ההיסטוריה שלכם.

📊 **נתוני המחלקה הנוכחיים:**
{json.dumps(dept_data, ensure_ascii=False, indent=2)}

🎯 **נתוני הליווי המנהיגותי:**
{json.dumps(leadership_data, ensure_ascii=False, indent=2)}

{conversation_context}
        """
        
        # Create session ID if not provided
        if not session_id:
            session_id = f"yahel_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize chat with OpenAI
        if not OPENAI_API_KEY:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
            
        chat = LlmChat(
            api_key=OPENAI_API_KEY,
            session_id=session_id,
            system_message=system_message
        ).with_model("openai", "gpt-4o-mini")
        
        # Send message
        user_msg = UserMessage(text=user_message)
        response = await chat.send_message(user_msg)
        
        # Parse and execute any database actions
        actions = parse_ai_actions(response)
        updated_tables = []
        
        if actions and user_id:
            updated_tables = await execute_ai_actions(actions, user_id)
            # Remove action tags from response
            import re
            clean_response = re.sub(r'\[ADD_\w+:.*?\]', '', response, flags=re.DOTALL)
            clean_response = re.sub(r'\[UPDATE_\w+:.*?\]', '', clean_response, flags=re.DOTALL)
            clean_response = re.sub(r'\[DELETE_\w+:.*?\]', '', clean_response, flags=re.DOTALL)
            response = clean_response.strip()
            
            # Add confirmation of actions taken
            if updated_tables:
                action_summary = f"\n\n✅ עדכנתי: {', '.join(updated_tables)}"
                response += action_summary
        
        # Store chat history in database
        chat_record = {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "user_id": user_id,  # Add user_id
            "user_message": user_message,
            "ai_response": response,
            "timestamp": datetime.now().isoformat(),
            "department_context": dept_data.get("summary", {}),
            "leadership_context": len(leadership_data.get("recent_conversations", [])),
            "updated_tables": updated_tables,
            "chat_history_length": len(chat_history) if chat_history else 0
        }
        ai_chat_history_collection.insert_one(chat_record)
        
        return ChatResponse(
            response=response,
            updated_tables=updated_tables,
            recommendations=[]
        )
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error in AI agent: {error_msg}")
        
        # Return a friendly error message instead of crashing
        if "AuthenticationError" in error_msg or "API key" in error_msg:
            return ChatResponse(
                response="מצטער, יש בעיה זמנית בחיבור למערכת הAI. אנא נסה שוב מאוחר יותר.",
                success=False,
                updated_tables=[]
            )
        else:
            return ChatResponse(
                response="מצטער, אירעה שגיאה. אנא נסה שוב או פנה למנהל המערכת.",
                success=False,
                updated_tables=[]
            )

# API Routes

@app.get("/")
async def root():
    return {"message": "יהל Naval Department Management System API", "status": "running"}

# AI Chat Route
@app.get("/api/ai-chat/history/{session_id}")
async def get_session_chat_history(session_id: str, current_user = Depends(get_current_user)):
    """Get chat history for specific session"""
    try:
        chat_records = list(ai_chat_history_collection.find(
            {"session_id": session_id, "user_id": current_user['id']}, 
            {"_id": 0}
        ).sort("timestamp", 1))
        
        # Convert to chat format
        history = []
        for record in chat_records:
            # Add user message
            history.append({
                "role": "user",
                "content": record["user_message"]
            })
            # Add assistant message
            history.append({
                "role": "assistant", 
                "content": record["ai_response"]
            })
        
        return {"history": history}
    except Exception as e:
        return {"history": []}

@app.delete("/api/ai-chat/history/{session_id}")
async def clear_session_chat_history(session_id: str, current_user = Depends(get_current_user)):
    """Clear chat history for specific session"""
    try:
        result = ai_chat_history_collection.delete_many({"session_id": session_id, "user_id": current_user['id']})
        return {"message": f"Cleared {result.deleted_count} chat records"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing chat history: {str(e)}")

@app.post("/api/ai-chat")
async def ai_chat(message: ChatMessage, current_user = Depends(get_current_user)):
    # Add user context to the message
    message.user_id = current_user['id']
    response = await create_yahel_ai_agent(
        message.user_message, 
        message.session_id, 
        message.chat_history,
        current_user
    )
    return response

# Active Failures Routes
@app.post("/api/failures")
async def create_failure(failure: ActiveFailure, current_user = Depends(get_current_user)):
    failure_dict = failure.dict()
    failure_dict['id'] = str(uuid.uuid4())
    failure_dict['user_id'] = current_user['id']  # Associate with authenticated user
    failure_dict['created_at'] = datetime.now().isoformat()
    
    result = active_failures_collection.insert_one(failure_dict)
    return {"id": failure_dict['id'], "message": "Failure created successfully"}

@app.get("/api/failures")
async def get_failures(current_user = Depends(get_current_user)):
    failures = list(active_failures_collection.find({"user_id": current_user['id']}, {"_id": 0}))
    # Sort by urgency (highest first) then by date
    failures.sort(key=lambda x: (-x['urgency'], x['date']))
    return failures

@app.put("/api/failures/{failure_id}")
async def update_failure(failure_id: str, failure: ActiveFailure, current_user = Depends(get_current_user)):
    # Get current failure data before update (filter by user)
    current_failure = active_failures_collection.find_one({"id": failure_id, "user_id": current_user['id']})
    if not current_failure:
        raise HTTPException(status_code=404, detail="Failure not found")
    
    failure_dict = failure.dict()
    failure_dict['user_id'] = current_user['id']  # Ensure user_id is maintained
    
    # Check if status is being changed to completed
    if failure_dict.get('status') in ['הושלם', 'נסגר', 'טופל']:
        # Move to resolved failures instead of updating
        resolution_info = {
            'actual_hours': failure_dict.get('estimated_hours', current_failure.get('estimated_hours')),
            'resolution_method': '',  # Empty for now, Jessica can fill this later
            'resolved_by': failure_dict.get('assignee', current_failure.get('assignee')),
            'lessons_learned': ''
        }
        
        moved = await move_failure_to_resolved(current_failure, resolution_info)
        if moved:
            return {"message": "Failure completed and moved to resolved failures", "moved_to_resolved": True}
        else:
            # If move failed, fall back to regular update
            result = active_failures_collection.update_one(
                {"id": failure_id, "user_id": current_user['id']}, 
                {"$set": failure_dict}
            )
    else:
        # Regular update for non-completed status
        result = active_failures_collection.update_one(
            {"id": failure_id, "user_id": current_user['id']}, 
            {"$set": failure_dict}
        )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Failure not found")
    return {"message": "Failure updated successfully"}

@app.delete("/api/failures/{failure_id}")
async def delete_failure(failure_id: str, current_user = Depends(get_current_user)):
    result = active_failures_collection.delete_one({"id": failure_id, "user_id": current_user['id']})
    result = active_failures_collection.delete_one({"id": failure_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Failure not found")
    return {"message": "Failure deleted successfully"}

# Resolved Failures Routes
@app.get("/api/resolved-failures")
async def get_resolved_failures(current_user = Depends(get_current_user)):
    resolved_failures = list(resolved_failures_collection.find({"user_id": current_user['id']}, {"_id": 0}).sort("resolved_date", -1))
    return resolved_failures

@app.post("/api/resolved-failures")
async def create_resolved_failure(resolved_failure: ResolvedFailure, current_user = Depends(get_current_user)):
    resolved_failure_dict = resolved_failure.dict()
    resolved_failure_dict['id'] = str(uuid.uuid4())
    resolved_failure_dict['user_id'] = current_user['id']
    resolved_failure_dict['resolved_at'] = datetime.now().isoformat()
    
    result = resolved_failures_collection.insert_one(resolved_failure_dict)
    return {"id": resolved_failure_dict['id'], "message": "Resolved failure created successfully"}

@app.put("/api/resolved-failures/{failure_id}")
async def update_resolved_failure(failure_id: str, updates: dict, current_user = Depends(get_current_user)):
    """Update resolution details for a resolved failure"""
    try:
        # Find the resolved failure (filter by user)
        query = {'id': failure_id, 'user_id': current_user['id']} if not failure_id.startswith('F') else {'failure_number': failure_id, 'user_id': current_user['id']}
        
        update_data = {}
        if 'resolution_method' in updates:
            update_data['resolution_method'] = updates['resolution_method']
        if 'actual_hours' in updates:
            update_data['actual_hours'] = float(updates['actual_hours'])
        if 'lessons_learned' in updates:
            update_data['lessons_learned'] = updates['lessons_learned']
        if 'resolved_by' in updates:
            update_data['resolved_by'] = updates['resolved_by']
        
        result = resolved_failures_collection.update_one(query, {'$set': update_data})
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Resolved failure not found")
        
        return {"message": "Resolved failure updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating resolved failure: {str(e)}")

@app.get("/api/resolved-failures/{failure_id}")
async def get_resolved_failure(failure_id: str, current_user = Depends(get_current_user)):
    """Get specific resolved failure"""
    query = {'id': failure_id, 'user_id': current_user['id']} if not failure_id.startswith('F') else {'failure_number': failure_id, 'user_id': current_user['id']}
    resolved_failure = resolved_failures_collection.find_one(query, {"_id": 0})
    
    if not resolved_failure:
        raise HTTPException(status_code=404, detail="Resolved failure not found")
    
    return resolved_failure

@app.delete("/api/resolved-failures/{failure_id}")
async def delete_resolved_failure(failure_id: str, current_user = Depends(get_current_user)):
    """Delete specific resolved failure"""
    try:
        query = {'id': failure_id, 'user_id': current_user['id']} if not failure_id.startswith('F') else {'failure_number': failure_id, 'user_id': current_user['id']}
        result = resolved_failures_collection.delete_one(query)
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Resolved failure not found")
        
        return {"message": "Resolved failure deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting resolved failure: {str(e)}")

# Pending Maintenance Routes
@app.post("/api/maintenance")
async def create_maintenance(maintenance: PendingMaintenance, current_user = Depends(get_current_user)):
    maintenance_dict = maintenance.dict()
    maintenance_dict['id'] = str(uuid.uuid4())
    maintenance_dict['user_id'] = current_user['id']
    maintenance_dict['created_at'] = datetime.now().isoformat()
    
    # Calculate dates
    maintenance_dict = calculate_maintenance_dates(maintenance_dict)
    
    result = pending_maintenance_collection.insert_one(maintenance_dict)
    return {"id": maintenance_dict['id'], "message": "Maintenance created successfully"}

@app.get("/api/maintenance")
async def get_maintenance(current_user = Depends(get_current_user)):
    maintenance_items = list(pending_maintenance_collection.find({"user_id": current_user['id']}, {"_id": 0}))
    # Recalculate dates for each item
    for item in maintenance_items:
        item = calculate_maintenance_dates(item)
    # Sort by days until due
    maintenance_items.sort(key=lambda x: x.get('days_until_due', 999))
    return maintenance_items

@app.put("/api/maintenance/{maintenance_id}")
async def update_maintenance(maintenance_id: str, maintenance: PendingMaintenance, current_user = Depends(get_current_user)):
    maintenance_dict = maintenance.dict()
    maintenance_dict['user_id'] = current_user['id']  # Ensure user_id is set
    maintenance_dict = calculate_maintenance_dates(maintenance_dict)
    
    result = pending_maintenance_collection.update_one(
        {"id": maintenance_id, "user_id": current_user['id']}, 
        {"$set": maintenance_dict}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Maintenance not found")
    return {"message": "Maintenance updated successfully"}

@app.delete("/api/maintenance/{maintenance_id}")
async def delete_maintenance(maintenance_id: str, current_user = Depends(get_current_user)):
    result = pending_maintenance_collection.delete_one({"id": maintenance_id, "user_id": current_user['id']})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Maintenance not found")
    return {"message": "Maintenance deleted successfully"}

# Equipment Hours Routes
@app.post("/api/equipment")
async def create_equipment(equipment: EquipmentHours, current_user = Depends(get_current_user)):
    equipment_dict = equipment.dict()
    equipment_dict['id'] = str(uuid.uuid4())
    equipment_dict['user_id'] = current_user['id']
    equipment_dict['created_at'] = datetime.now().isoformat()
    
    # Calculate service hours
    equipment_dict = calculate_service_hours(equipment_dict)
    
    result = equipment_hours_collection.insert_one(equipment_dict)
    return {"id": equipment_dict['id'], "message": "Equipment created successfully"}

@app.get("/api/equipment")
async def get_equipment(current_user = Depends(get_current_user)):
    equipment_items = list(equipment_hours_collection.find({"user_id": current_user['id']}, {"_id": 0}))
    # Recalculate service hours for each item
    for item in equipment_items:
        item = calculate_service_hours(item)
    # Sort by alert level priority and hours until service
    priority = {"אדום": 1, "כתום": 2, "ירוק": 3}
    equipment_items.sort(key=lambda x: (priority.get(x.get('alert_level', 'ירוק'), 3), x.get('hours_until_service', 999)))
    return equipment_items

@app.put("/api/equipment/{equipment_id}")
async def update_equipment(equipment_id: str, equipment: EquipmentHours, current_user = Depends(get_current_user)):
    equipment_dict = equipment.dict()
    equipment_dict['user_id'] = current_user['id']
    equipment_dict = calculate_service_hours(equipment_dict)
    
    result = equipment_hours_collection.update_one(
        {"id": equipment_id, "user_id": current_user['id']}, 
        {"$set": equipment_dict}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return {"message": "Equipment updated successfully"}

@app.delete("/api/equipment/{equipment_id}")
async def delete_equipment(equipment_id: str, current_user = Depends(get_current_user)):
    result = equipment_hours_collection.delete_one({"id": equipment_id, "user_id": current_user['id']})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return {"message": "Equipment deleted successfully"}

# Daily Work Plan Routes
@app.post("/api/daily-work")
async def create_daily_work(work: DailyWorkPlan, current_user = Depends(get_current_user)):
    work_dict = work.dict()
    work_dict['id'] = str(uuid.uuid4())
    work_dict['user_id'] = current_user['id']
    work_dict['created_at'] = datetime.now().isoformat()
    
    result = daily_work_collection.insert_one(work_dict)
    return {"id": work_dict['id'], "message": "Daily work created successfully"}

@app.get("/api/daily-work")
async def get_daily_work(date: Optional[str] = None, current_user = Depends(get_current_user)):
    query = {"user_id": current_user['id']}
    if date:
        query['date'] = date
    
    work_items = list(daily_work_collection.find(query, {"_id": 0}))
    # Sort by date and assignee
    work_items.sort(key=lambda x: (x['date'], x['assignee']))
    return work_items

@app.get("/api/daily-work/today")
async def get_today_work(current_user = Depends(get_current_user)):
    today = datetime.now().isoformat()[:10]
    return await get_daily_work(today, current_user)

@app.put("/api/daily-work/{work_id}")
async def update_daily_work(work_id: str, work: DailyWorkPlan, current_user = Depends(get_current_user)):
    work_dict = work.dict()
    work_dict['user_id'] = current_user['id']
    result = daily_work_collection.update_one(
        {"id": work_id, "user_id": current_user['id']}, 
        {"$set": work_dict}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Work item not found")
    return {"message": "Daily work updated successfully"}

@app.delete("/api/daily-work/{work_id}")
async def delete_daily_work(work_id: str, current_user = Depends(get_current_user)):
    result = daily_work_collection.delete_one({"id": work_id, "user_id": current_user['id']})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Work item not found")
    return {"message": "Daily work deleted successfully"}

# Leadership Coaching Routes

@app.post("/api/conversations")
async def create_conversation(conversation: Conversation, current_user = Depends(get_current_user)):
    conversation_dict = conversation.dict()
    conversation_dict['id'] = str(uuid.uuid4())
    conversation_dict['user_id'] = current_user['id']
    conversation_dict['created_at'] = datetime.now().isoformat()
    
    result = conversations_collection.insert_one(conversation_dict)
    return {"id": conversation_dict['id'], "message": "Conversation created successfully"}

@app.get("/api/conversations")
async def get_conversations(current_user = Depends(get_current_user)):
    conversations = list(conversations_collection.find({"user_id": current_user['id']}, {"_id": 0}).sort("meeting_number", -1))
    return conversations

@app.put("/api/conversations/{conversation_id}")
async def update_conversation(conversation_id: str, conversation: Conversation, current_user = Depends(get_current_user)):
    conversation_dict = conversation.dict()
    conversation_dict['user_id'] = current_user['id']
    
    result = conversations_collection.update_one(
        {"id": conversation_id, "user_id": current_user['id']}, 
        {"$set": conversation_dict}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation updated successfully"}

@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, current_user = Depends(get_current_user)):
    result = conversations_collection.delete_one({"id": conversation_id, "user_id": current_user['id']})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation deleted successfully"}

@app.post("/api/dna-tracker")
async def create_dna_item(dna: DNATracker, current_user = Depends(get_current_user)):
    dna_dict = dna.dict()
    dna_dict['id'] = str(uuid.uuid4())
    dna_dict['user_id'] = current_user['id']
    dna_dict['created_at'] = datetime.now().isoformat()
    dna_dict['last_updated'] = datetime.now().isoformat()[:10]
    
    # Check if component already exists for this user
    existing = dna_tracker_collection.find_one({'component_name': dna_dict['component_name'], 'user_id': current_user['id']})
    if existing:
        # Update existing
        result = dna_tracker_collection.update_one(
            {'component_name': dna_dict['component_name'], 'user_id': current_user['id']},
            {'$set': dna_dict}
        )
        return {"id": existing['id'], "message": "DNA component updated successfully"}
    else:
        # Create new
        result = dna_tracker_collection.insert_one(dna_dict)
        return {"id": dna_dict['id'], "message": "DNA component created successfully"}

@app.get("/api/dna-tracker")
async def get_dna_tracker(current_user = Depends(get_current_user)):
    dna_items = list(dna_tracker_collection.find({"user_id": current_user['id']}, {"_id": 0}))
    return dna_items

@app.put("/api/dna-tracker/{dna_id}")
async def update_dna_item(dna_id: str, dna: DNATracker, current_user = Depends(get_current_user)):
    dna_dict = dna.dict()
    dna_dict['user_id'] = current_user['id']
    dna_dict['last_updated'] = datetime.now().isoformat()[:10]
    
    result = dna_tracker_collection.update_one(
        {"id": dna_id, "user_id": current_user['id']}, 
        {"$set": dna_dict}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="DNA item not found")
    return {"message": "DNA item updated successfully"}

@app.delete("/api/dna-tracker/{dna_id}")
async def delete_dna_item(dna_id: str, current_user = Depends(get_current_user)):
    result = dna_tracker_collection.delete_one({"id": dna_id, "user_id": current_user['id']})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="DNA item not found")
    return {"message": "DNA item deleted successfully"}

@app.post("/api/ninety-day-plan")
async def create_plan_item(plan: NinetyDayPlan, current_user = Depends(get_current_user)):
    plan_dict = plan.dict()
    plan_dict['id'] = str(uuid.uuid4())
    plan_dict['user_id'] = current_user['id']
    plan_dict['created_at'] = datetime.now().isoformat()
    
    # Check if week already exists
    existing = ninety_day_plan_collection.find_one({'week_number': plan_dict['week_number'], 'user_id': current_user['id']})
    if existing:
        # Update existing
        result = ninety_day_plan_collection.update_one(
            {'week_number': plan_dict['week_number'], 'user_id': current_user['id']},
            {'$set': plan_dict}
        )
        return {"id": existing['id'], "message": f"Week {plan_dict['week_number']} plan updated successfully"}
    else:
        # Create new
        result = ninety_day_plan_collection.insert_one(plan_dict)
        return {"id": plan_dict['id'], "message": f"Week {plan_dict['week_number']} plan created successfully"}

@app.get("/api/ninety-day-plan")
async def get_ninety_day_plan(current_user = Depends(get_current_user)):
    plan_items = list(ninety_day_plan_collection.find({"user_id": current_user['id']}, {"_id": 0}).sort("week_number", 1))
    return plan_items

@app.put("/api/ninety-day-plan/{plan_id}")
async def update_plan_item(plan_id: str, plan: NinetyDayPlan, current_user = Depends(get_current_user)):
    plan_dict = plan.dict()
    plan_dict['user_id'] = current_user['id']
    result = ninety_day_plan_collection.update_one(
        {"id": plan_id, "user_id": current_user['id']}, 
        {"$set": plan_dict}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Plan item not found")
    return {"message": "Plan item updated successfully"}

@app.delete("/api/ninety-day-plan/{plan_id}")
async def delete_plan_item(plan_id: str, current_user = Depends(get_current_user)):
    result = ninety_day_plan_collection.delete_one({"id": plan_id, "user_id": current_user['id']})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Plan item not found")
    return {"message": "Plan item deleted successfully"}

# Advanced AI Routes for Leadership Coaching

@app.get("/api/leadership-summary")
async def get_leadership_summary():
    """Get comprehensive leadership coaching summary"""
    try:
        # Get recent conversations
        recent_conversations = list(conversations_collection.find({}, {"_id": 0}).sort("meeting_number", -1).limit(3))
        
        # Get DNA progress
        dna_items = list(dna_tracker_collection.find({}, {"_id": 0}))
        avg_clarity = sum(item.get('clarity_level', 0) for item in dna_items) / len(dna_items) if dna_items else 0
        
        # Get 90-day plan progress
        plan_items = list(ninety_day_plan_collection.find({}, {"_id": 0}))
        completed_weeks = len([item for item in plan_items if item.get('status') == 'הושלם'])
        total_weeks = len(plan_items)
        
        # Calculate energy trend from recent conversations
        energy_levels = [conv.get('yahel_energy_level', 5) for conv in recent_conversations]
        avg_energy = sum(energy_levels) / len(energy_levels) if energy_levels else 5
        
        return {
            "recent_conversations_count": len(recent_conversations),
            "avg_energy_level": round(avg_energy, 1),
            "dna_clarity_average": round(avg_clarity, 1),
            "dna_components_defined": len(dna_items),
            "plan_completion_rate": round((completed_weeks / total_weeks * 100), 1) if total_weeks > 0 else 0,
            "total_weeks_planned": total_weeks,
            "weeks_completed": completed_weeks,
            "last_conversation": recent_conversations[0] if recent_conversations else None,
            "next_actions_needed": len([item for item in dna_items if item.get('clarity_level', 0) < 7])
        }
        
    except Exception as e:
        print(f"Error getting leadership summary: {e}")
        return {"error": "Could not generate leadership summary"}

@app.post("/api/ai-coaching-session")
async def ai_coaching_session(session_data: dict):
    """Process AI coaching session and auto-update leadership tables"""
    try:
        user_message = session_data.get('message', '')
        session_type = session_data.get('type', 'general')  # general, reflection, planning
        
        # Call the main AI agent
        response = await create_yahel_ai_agent(user_message)
        
        # If this was a coaching session, automatically create conversation record
        if session_type == 'coaching' and response.updated_tables:
            conversation_data = {
                'id': str(uuid.uuid4()),
                'meeting_number': len(list(conversations_collection.find())) + 1,
                'date': datetime.now().isoformat()[:10],
                'duration_minutes': 30,  # Default
                'main_topics': ['AI coaching session'],
                'insights': ['Processed via AI agent'],
                'decisions': [],
                'next_step': 'Continue regular coaching sessions',
                'yahel_energy_level': 7,  # Default
                'created_at': datetime.now().isoformat()
            }
            
            conversations_collection.insert_one(conversation_data)
            response.updated_tables.append('מעקב שיחות')
        
        return response
        
    except Exception as e:
        print(f"Error in coaching session: {e}")
        raise HTTPException(status_code=500, detail="Error processing coaching session")

# Dashboard/Summary Routes
@app.get("/api/dashboard/summary")
async def get_dashboard_summary():
    dept_summary = get_department_summary()
    return dept_summary.get("summary", {})

@app.get("/api/chat-history")
async def get_chat_history(limit: int = 10):
    chat_history = list(ai_chat_history_collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit))
    return chat_history

# Google Calendar OAuth Routes
@app.get("/api/auth/google/login")
async def google_login():
    """Initiate Google OAuth flow with simpler redirect"""
    try:
        client_id = os.environ.get('GOOGLE_CLIENT_ID')
        redirect_uri = os.environ.get('GOOGLE_REDIRECT_URI')
        
        # Create the Google OAuth URL manually to avoid library issues
        scope = "https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/calendar"
        state = secrets.token_urlsafe(32)
        
        oauth_url = (
            f"https://accounts.google.com/o/oauth2/auth"
            f"?response_type=code"
            f"&client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&scope={scope}"
            f"&state={state}"
            f"&access_type=offline"
            f"&include_granted_scopes=true"
            f"&prompt=consent"
        )
        
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=oauth_url, status_code=302)
        
    except Exception as e:
        print(f"Error in google_login: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating OAuth flow: {str(e)}")

@app.get("/api/auth/google/callback")
async def google_callback(request: Request, code: str = None, state: str = None, error: str = None):
    """Handle Google OAuth callback and create authenticated user session"""
    try:
        if error:
            raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
            
        if not code:
            raise HTTPException(status_code=400, detail="No authorization code received")
        
        # Exchange code for token using direct HTTP requests to avoid HTTPS issues
        import httpx
        
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": os.environ.get('GOOGLE_CLIENT_ID'),
            "client_secret": os.environ.get('GOOGLE_CLIENT_SECRET'),
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": os.environ.get('GOOGLE_REDIRECT_URI')
        }
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=token_data)
            token_response.raise_for_status()
            tokens = token_response.json()
        
        # Get user info
        access_token = tokens.get("access_token")
        user_info_url = f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={access_token}"
        
        async with httpx.AsyncClient() as client:
            user_response = await client.get(user_info_url)
            user_response.raise_for_status()
            user_info = user_response.json()
        
        # Check if user exists in our authentication system
        google_id = user_info.get('id')
        user = get_user_by_google_id(google_id)
        
        if not user:
            # Create new user
            user = create_user(
                email=user_info['email'],
                name=user_info.get('name', ''),
                google_id=google_id
            )
        else:
            # Update last login
            authenticated_users_collection.update_one(
                {"id": user["id"]},
                {"$set": {"last_login": datetime.now().isoformat()}}
            )
        
        # Create JWT access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        jwt_token = create_access_token(
            data={"sub": user["email"], "user_id": user["id"]},
            expires_delta=access_token_expires
        )
        
        # Create session in database
        create_user_session(user["id"], jwt_token)
        
        # Save Google Calendar tokens for existing functionality
        save_user_tokens(
            user_info['email'],
            user_info.get('name', ''),
            access_token,
            tokens.get('refresh_token'),
            None  # We'll handle expiry differently
        )
        
        # Redirect to frontend with authentication token
        frontend_url = "https://fleet-mentor.preview.emergentagent.com"
        redirect_url = f"{frontend_url}?google_auth=success&token={jwt_token}&email={user['email']}&name={user['name']}"
        
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        print(f"OAuth callback error: {e}")
        # Redirect to frontend with error
        frontend_url = "https://fleet-mentor.preview.emergentagent.com"
        redirect_url = f"{frontend_url}?google_auth=error&message={str(e)}"
        return RedirectResponse(url=redirect_url)

@app.get("/api/auth/google/user")
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current authenticated user information"""
    return {
        "user_id": current_user["id"],
        "email": current_user["email"], 
        "name": current_user.get("name", ""),
        "authenticated": True
    }

@app.post("/api/auth/logout")
async def logout_user(current_user = Depends(get_current_user)):
    """Logout current user by invalidating their session"""
    try:
        # Remove user session from database if we're tracking them
        # For now, just return success - frontend will remove token from localStorage
        return {
            "message": "Logout successful",
            "logged_out": True
        }
    except Exception as e:
        print(f"Logout error: {e}")
        return {
            "message": "Logout completed", 
            "logged_out": True
        }

@app.get("/api/summary")
async def get_dashboard_summary(current_user = Depends(get_current_user)):
    """Get dashboard summary data"""
    try:
        # Get counts for each table
        failures_count = active_failures_collection.count_documents({"user_id": current_user['id']})
        resolved_count = resolved_failures_collection.count_documents({"user_id": current_user['id']})
        maintenance_count = pending_maintenance_collection.count_documents({"user_id": current_user['id']})
        equipment_count = equipment_hours_collection.count_documents({"user_id": current_user['id']})
        
        # Get urgent items
        urgent_failures = list(active_failures_collection.find(
            {"user_id": current_user['id'], "urgency": {"$gte": 4}}, 
            {"_id": 0}
        ).limit(5))
        
        return {
            "counts": {
                "active_failures": failures_count,
                "resolved_failures": resolved_count,
                "pending_maintenance": maintenance_count,
                "equipment_items": equipment_count
            },
            "urgent_items": urgent_failures,
            "user": {
                "name": current_user.get("name", ""),
                "email": current_user.get("email", "")
            }
        }
    except Exception as e:
        print(f"Error getting summary: {e}")
        return {
            "counts": {
                "active_failures": 0,
                "resolved_failures": 0,
                "pending_maintenance": 0,
                "equipment_items": 0
            },
            "urgent_items": [],
            "user": {
                "name": current_user.get("name", "משתמש"),
                "email": current_user.get("email", "")
            }
        }

@app.get("/api/auth/user/{email}")
async def get_user_info(email: str):
    """Get user information and Google auth status"""
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "email": user['email'],
        "name": user['name'],
        "google_connected": bool(user.get('google_access_token')),
        "created_at": user.get('created_at')
    }

# Google Calendar API Routes
@app.post("/api/calendar/events")
async def create_calendar_event(event_request: CalendarEventRequest, user_email: str):
    """Create a new calendar event"""
    try:
        service = get_google_calendar_service(user_email)
        if not service:
            raise HTTPException(status_code=401, detail="Google Calendar not connected")
        
        # Convert string datetimes to datetime objects
        start_dt = datetime.fromisoformat(event_request.start_time.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(event_request.end_time.replace('Z', '+00:00'))
        
        # Create Google Calendar event
        event_body = {
            'summary': event_request.title,
            'description': event_request.description,
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': 'Asia/Jerusalem',
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': 'Asia/Jerusalem',
            },
            'location': event_request.location,
            'attendees': [{'email': email} for email in event_request.attendees]
        }
        
        created_event = service.events().insert(calendarId='primary', body=event_body).execute()
        
        # Save to local database
        calendar_event = CalendarEvent(
            id=str(uuid.uuid4()),
            google_event_id=created_event['id'],
            title=event_request.title,
            description=event_request.description,
            start_time=start_dt,
            end_time=end_dt,
            location=event_request.location,
            attendees=event_request.attendees,
            source_type="manual",
            user_email=user_email,
            created_at=datetime.now().isoformat()
        )
        
        calendar_events_collection.insert_one(calendar_event.dict())
        
        return {
            "success": True,
            "event_id": created_event['id'],
            "event_url": created_event.get('htmlLink'),
            "message": "Event created successfully"
        }
        
    except Exception as e:
        print(f"Error creating calendar event: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating event: {str(e)}")

@app.get("/api/calendar/events")
async def get_calendar_events(user_email: str, limit: int = 50):
    """Get user's calendar events"""
    try:
        service = get_google_calendar_service(user_email)
        if not service:
            raise HTTPException(status_code=401, detail="Google Calendar not connected")
        
        # Get events from Google Calendar
        now = datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=limit,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Also get local events
        local_events = list(calendar_events_collection.find(
            {"user_email": user_email},
            {"_id": 0}
        ).sort("start_time", 1).limit(limit))
        
        return {
            "google_events": events,
            "local_events": local_events
        }
        
    except Exception as e:
        print(f"Error fetching calendar events: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching events: {str(e)}")

@app.post("/api/calendar/create-from-maintenance")
async def create_event_from_maintenance(maintenance_id: str, user_email: str):
    """Create calendar event from maintenance schedule"""
    try:
        # Get maintenance data
        maintenance = pending_maintenance_collection.find_one({"id": maintenance_id})
        if not maintenance:
            raise HTTPException(status_code=404, detail="Maintenance not found")
        
        # Calculate event time (next due date)
        maintenance_data = calculate_maintenance_dates(maintenance)
        if maintenance_data['days_until_due'] < 0:
            raise HTTPException(status_code=400, detail="Maintenance is overdue")
        
        # Create event
        start_time = datetime.fromisoformat(maintenance_data['next_due_date'])
        end_time = start_time + timedelta(hours=2)  # 2 hour duration
        
        event_request = CalendarEventRequest(
            title=f"אחזקה: {maintenance['component']} - {maintenance['maintenance_type']}",
            description=f"תיאור: {maintenance['description']}\nדחיפות: {maintenance['priority']}",
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            location="יחידה ימית"
        )
        
        return await create_calendar_event(event_request, user_email)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating event from maintenance: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating event: {str(e)}")

@app.post("/api/calendar/create-from-daily-plan")
async def create_event_from_daily_plan(work_id: str, user_email: str):
    """Create calendar event from daily work plan"""
    try:
        # Get work plan data
        work_plan = daily_work_collection.find_one({"id": work_id})
        if not work_plan:
            raise HTTPException(status_code=404, detail="Work plan not found")
        
        # Create event for today
        today = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)  # 8 AM
        end_time = today + timedelta(hours=int(work_plan.get('estimated_hours', 2)))
        
        event_request = CalendarEventRequest(
            title=f"משימה: {work_plan['task']}",
            description=f"תיאור: {work_plan['description']}\nדחיפות: {work_plan['priority']}\nמבצע: {work_plan['assigned_to']}",
            start_time=today.isoformat(),
            end_time=end_time.isoformat(),
            location="יחידה ימית"
        )
        
        return await create_calendar_event(event_request, user_email)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating event from daily plan: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating event: {str(e)}")

# Push Notifications API Endpoints
@app.get("/api/notifications/vapid-key")
async def get_vapid_public_key():
    """Get VAPID public key for client subscription"""
    try:
        return {
            "public_key": push_service.vapid_manager.get_application_server_key(),
            "subject": "mailto:admin@yahel-naval-system.com"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting VAPID key: {str(e)}")

@app.post("/api/notifications/subscribe")
async def subscribe_user(request: SubscribeRequest):
    """Subscribe user to push notifications"""
    try:
        # Store subscription in MongoDB
        subscription_data = {
            "id": str(uuid.uuid4()),
            "user_id": request.user_id,
            "subscription_json": json.dumps(request.subscription.dict()),
            "endpoint": request.subscription.endpoint,
            "p256dh_key": request.subscription.keys.get('p256dh'),
            "auth_key": request.subscription.keys.get('auth'),
            "created_at": datetime.now().isoformat(),
            "is_active": True
        }
        
        # Update if exists, insert if new
        push_subscriptions_collection.update_one(
            {"user_id": request.user_id, "endpoint": request.subscription.endpoint},
            {"$set": subscription_data},
            upsert=True
        )
        
        return {"status": "subscribed", "message": "User successfully subscribed to notifications"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Subscription failed: {str(e)}")

@app.post("/api/notifications/unsubscribe")
async def unsubscribe_user(user_id: str, endpoint: str):
    """Unsubscribe user from push notifications"""
    try:
        result = push_subscriptions_collection.update_one(
            {"user_id": user_id, "endpoint": endpoint},
            {"$set": {"is_active": False, "updated_at": datetime.now().isoformat()}}
        )
        
        if result.modified_count > 0:
            return {"status": "unsubscribed", "message": "User successfully unsubscribed"}
        else:
            return {"status": "not_found", "message": "Subscription not found"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unsubscription failed: {str(e)}")

@app.post("/api/notifications/send")
async def send_notification(request: NotificationRequest, background_tasks: BackgroundTasks):
    """Send push notification to user"""
    try:
        if request.urgent:
            # Send immediately for urgent notifications
            result = await push_service.send_notification(
                user_id=request.user_id,
                title=request.title,
                body=request.body,
                category=request.category,
                data=request.data,
                icon=request.icon,
                badge=request.badge
            )
            return result
        else:
            # Use background task for non-urgent notifications
            background_tasks.add_task(
                push_service.send_notification,
                request.user_id,
                request.title,
                request.body,
                request.category,
                request.data,
                request.icon,
                request.badge
            )
            return {"status": "queued", "message": "Notification queued for delivery"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send notification: {str(e)}")

@app.get("/api/notifications/preferences/{user_id}")
async def get_user_preferences(user_id: str):
    """Get user notification preferences"""
    try:
        preferences = push_service.get_user_preferences(user_id)
        return preferences
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve preferences: {str(e)}")

@app.put("/api/notifications/preferences/{user_id}")
async def update_user_preferences(user_id: str, preferences: NotificationPreferences):
    """Update user notification preferences"""
    try:
        # Validate user_id matches
        if preferences.user_id != user_id:
            raise HTTPException(status_code=400, detail="User ID mismatch")
        
        # Update preferences in MongoDB
        update_data = preferences.dict()
        update_data["updated_at"] = datetime.now().isoformat()
        
        notification_preferences_collection.update_one(
            {"user_id": user_id},
            {"$set": update_data},
            upsert=True
        )
        
        return {
            "status": "updated",
            "preferences": push_service.get_user_preferences(user_id),
            "message": "Preferences updated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update preferences: {str(e)}")

@app.get("/api/notifications/categories")
async def get_notification_categories():
    """Get available notification categories with descriptions"""
    return {
        "categories": {
            "urgent_failures": {
                "label": "Urgent Failures",
                "label_he": "כשלים דחופים",
                "description": "Critical system failures requiring immediate attention",
                "description_he": "כשלי מערכת קריטיים הדורשים טיפול מיידי",
                "default_enabled": True,
                "priority": "high"
            },
            "maintenance_reminders": {
                "label": "Maintenance Reminders", 
                "label_he": "תזכורות תחזוקה",
                "description": "Scheduled maintenance and update notifications",
                "description_he": "התראות על תחזוקה מתוכננת ועדכונים",
                "default_enabled": True,
                "priority": "medium"
            },
            "jessica_updates": {
                "label": "Jessica Updates",
                "label_he": "עדכוני ג'סיקה",
                "description": "Important messages and updates from Jessica AI assistant",
                "description_he": "הודעות חשובות ועדכונים מהעוזרת הדיגיטלית ג'סיקה",
                "default_enabled": True,
                "priority": "medium"
            },
            "system_status": {
                "label": "System Status",
                "label_he": "סטטוס מערכת", 
                "description": "General system status and performance updates",
                "description_he": "עדכוני סטטוס מערכת וביצועים כלליים",
                "default_enabled": False,
                "priority": "low"
            }
        }
    }

@app.get("/api/notifications/history/{user_id}")
async def get_notification_history(user_id: str, limit: int = 50):
    """Get user's notification history"""
    try:
        history = list(notification_history_collection.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("delivery_timestamp", -1).limit(limit))
        
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")

@app.post("/api/notifications/test")
async def send_test_notification(user_id: str, background_tasks: BackgroundTasks):
    """Send a test notification to user"""
    try:
        test_request = NotificationRequest(
            user_id=user_id,
            title="🧪 התראת בדיקה",
            body="זוהי התראת בדיקה ממערכת יהל. אם אתה רואה הודעה זו, ההתראות פועלות כראוי!",
            category="test",
            urgent=False,
            data={
                "url": "/",
                "type": "test_notification",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        result = await push_service.send_notification(
            user_id=test_request.user_id,
            title=test_request.title,
            body=test_request.body,
            category=test_request.category,
            data=test_request.data
        )
        
        return {"status": "sent", "result": result, "message": "Test notification sent"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send test notification: {str(e)}")

# Google Sheets Export Functionality
def get_sheets_service():
    """Initialize Google Sheets service with credentials"""
    try:
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        credentials = Credentials.from_service_account_file(
            GOOGLE_SHEETS_CREDENTIALS, 
            scopes=scopes
        )
        
        return gspread.authorize(credentials)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize Google Sheets service: {str(e)}")

def export_table_to_sheets(table_name: str, data: List[Dict], sheet_title: str = None):
    """Export table data to a new Google Sheet"""
    try:
        sheets_service = get_sheets_service()
        
        # Generate sheet title if not provided
        if not sheet_title:
            sheet_title = f"{table_name} Export - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Create new spreadsheet
        spreadsheet = sheets_service.create(sheet_title)
        worksheet = spreadsheet.sheet1
        
        if not data:
            # Just add headers if no data
            headers = ["No data available"]
            worksheet.update('A1', [headers])
        else:
            # Extract headers from first row
            headers = list(data[0].keys()) if data else []
            
            # Add headers
            if headers:
                worksheet.update('A1', [headers])
                
                # Add data rows
                data_rows = []
                for row in data:
                    row_values = [str(row.get(header, '')) for header in headers]
                    data_rows.append(row_values)
                
                if data_rows:
                    worksheet.update('A2', data_rows)
        
        # Make spreadsheet viewable by anyone with link
        spreadsheet.share('', perm_type='anyone', role='reader')
        
        return {
            "spreadsheet_id": spreadsheet.id,
            "spreadsheet_url": spreadsheet.url,
            "title": sheet_title
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export to Google Sheets: {str(e)}")

# Export Endpoints
@app.post("/api/export/failures", response_model=ExportResponse)
async def export_failures(request: ExportRequest):
    """Export failures data to Google Sheets"""
    try:
        failures = list(active_failures_collection.find({}, {"_id": 0}))
        result = export_table_to_sheets("failures", failures, request.sheet_title)
        
        return ExportResponse(
            success=True,
            spreadsheet_id=result["spreadsheet_id"],
            spreadsheet_url=result["spreadsheet_url"],
            message=f"Successfully exported {len(failures)} failures to Google Sheets"
        )
    except Exception as e:
        return ExportResponse(
            success=False,
            message=f"Failed to export failures: {str(e)}"
        )

@app.post("/api/export/resolved-failures", response_model=ExportResponse)
async def export_resolved_failures(request: ExportRequest):
    """Export resolved failures data to Google Sheets"""
    try:
        resolved_failures = list(resolved_failures_collection.find({}, {"_id": 0}))
        result = export_table_to_sheets("resolved-failures", resolved_failures, request.sheet_title)
        
        return ExportResponse(
            success=True,
            spreadsheet_id=result["spreadsheet_id"],
            spreadsheet_url=result["spreadsheet_url"],
            message=f"Successfully exported {len(resolved_failures)} resolved failures to Google Sheets"
        )
    except Exception as e:
        return ExportResponse(
            success=False,
            message=f"Failed to export resolved failures: {str(e)}"
        )

@app.post("/api/export/maintenance", response_model=ExportResponse)
async def export_maintenance(request: ExportRequest):
    """Export maintenance data to Google Sheets"""
    try:
        maintenance = list(pending_maintenance_collection.find({}, {"_id": 0}))
        result = export_table_to_sheets("maintenance", maintenance, request.sheet_title)
        
        return ExportResponse(
            success=True,
            spreadsheet_id=result["spreadsheet_id"],
            spreadsheet_url=result["spreadsheet_url"],
            message=f"Successfully exported {len(maintenance)} maintenance items to Google Sheets"
        )
    except Exception as e:
        return ExportResponse(
            success=False,
            message=f"Failed to export maintenance: {str(e)}"
        )

@app.post("/api/export/equipment", response_model=ExportResponse)
async def export_equipment(request: ExportRequest, current_user = Depends(get_current_user)):
    """Export equipment data to Google Sheets"""
    try:
        equipment = list(equipment_hours_collection.find({"user_id": current_user['id']}, {"_id": 0}))
        result = export_table_to_sheets("equipment", equipment, request.sheet_title)
        
        return ExportResponse(
            success=True,
            spreadsheet_id=result["spreadsheet_id"],
            spreadsheet_url=result["spreadsheet_url"],
            message=f"Successfully exported {len(equipment)} equipment items to Google Sheets"
        )
    except Exception as e:
        return ExportResponse(
            success=False,
            message=f"Failed to export equipment: {str(e)}"
        )

@app.post("/api/export/daily-work", response_model=ExportResponse)
async def export_daily_work(request: ExportRequest, current_user = Depends(get_current_user)):
    """Export daily work data to Google Sheets"""
    try:
        daily_work = list(daily_work_collection.find({"user_id": current_user['id']}, {"_id": 0}))
        result = export_table_to_sheets("daily-work", daily_work, request.sheet_title)
        
        return ExportResponse(
            success=True,
            spreadsheet_id=result["spreadsheet_id"],
            spreadsheet_url=result["spreadsheet_url"],
            message=f"Successfully exported {len(daily_work)} daily work items to Google Sheets"
        )
    except Exception as e:
        return ExportResponse(
            success=False,
            message=f"Failed to export daily work: {str(e)}"
        )

@app.post("/api/export/conversations", response_model=ExportResponse)
async def export_conversations(request: ExportRequest, current_user = Depends(get_current_user)):
    """Export conversations data to Google Sheets"""
    try:
        conversations = list(conversations_collection.find({"user_id": current_user['id']}, {"_id": 0}))
        result = export_table_to_sheets("conversations", conversations, request.sheet_title)
        
        return ExportResponse(
            success=True,
            spreadsheet_id=result["spreadsheet_id"],
            spreadsheet_url=result["spreadsheet_url"],
            message=f"Successfully exported {len(conversations)} conversations to Google Sheets"
        )
    except Exception as e:
        return ExportResponse(
            success=False,
            message=f"Failed to export conversations: {str(e)}"
        )

@app.post("/api/export/dna-tracker", response_model=ExportResponse)
async def export_dna_tracker(request: ExportRequest, current_user = Depends(get_current_user)):
    """Export DNA tracker data to Google Sheets"""
    try:
        dna_tracker = list(dna_tracker_collection.find({"user_id": current_user['id']}, {"_id": 0}))
        result = export_table_to_sheets("dna-tracker", dna_tracker, request.sheet_title)
        
        return ExportResponse(
            success=True,
            spreadsheet_id=result["spreadsheet_id"],
            spreadsheet_url=result["spreadsheet_url"],
            message=f"Successfully exported {len(dna_tracker)} DNA tracker items to Google Sheets"
        )
    except Exception as e:
        return ExportResponse(
            success=False,
            message=f"Failed to export DNA tracker: {str(e)}"
        )

@app.post("/api/export/ninety-day-plan", response_model=ExportResponse)
async def export_ninety_day_plan(request: ExportRequest, current_user = Depends(get_current_user)):
    """Export ninety day plan data to Google Sheets"""
    try:
        ninety_day_plan = list(ninety_day_plan_collection.find({"user_id": current_user['id']}, {"_id": 0}))
        result = export_table_to_sheets("ninety-day-plan", ninety_day_plan, request.sheet_title)
        
        return ExportResponse(
            success=True,
            spreadsheet_id=result["spreadsheet_id"],
            spreadsheet_url=result["spreadsheet_url"],
            message=f"Successfully exported {len(ninety_day_plan)} ninety day plan items to Google Sheets"
        )
    except Exception as e:
        return ExportResponse(
            success=False,
            message=f"Failed to export ninety day plan: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)