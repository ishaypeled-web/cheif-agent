from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime, timedelta
import uuid
import os
from typing import List, Optional
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

# Google Calendar setup
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'https://marine-leadership.preview.emergentagent.com/api/auth/google/callback')

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

class ChatResponse(BaseModel):
    response: str
    updated_tables: List[str] = []
    recommendations: List[str] = []

# Helper functions

def calculate_maintenance_dates(maintenance: dict):
    """Calculate next due date and days until due"""
    if maintenance.get('last_performed'):
        last_date = datetime.fromisoformat(maintenance['last_performed'])
        next_date = last_date + timedelta(days=maintenance['frequency_days'])
        days_until = (next_date - datetime.now()).days
        
        maintenance['next_due'] = next_date.isoformat()[:10]
        maintenance['days_until_due'] = days_until
    
    return maintenance

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

def get_department_summary():
    """Get summary of all department data for AI analysis"""
    try:
        failures = list(active_failures_collection.find({}, {"_id": 0}))
        maintenance = list(pending_maintenance_collection.find({}, {"_id": 0}))
        equipment = list(equipment_hours_collection.find({}, {"_id": 0}))
        daily_work = list(daily_work_collection.find({}, {"_id": 0}))
        
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

def get_leadership_context():
    """Get leadership coaching context"""
    try:
        conversations = list(conversations_collection.find({}, {"_id": 0}).sort("meeting_number", -1).limit(5))
        dna_items = list(dna_tracker_collection.find({}, {"_id": 0}))
        plan_items = list(ninety_day_plan_collection.find({}, {"_id": 0}).sort("week_number", 1))
        
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
        
        # Remove from active failures
        active_failures_collection.delete_one({'id': failure_data['id']})
        
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

async def execute_ai_actions(actions):
    """Execute database actions from AI"""
    updated_tables = []
    
    for action_type, params in actions:
        try:
            if action_type == 'add_failure':
                # Create failure
                failure_data = {
                    'id': str(uuid.uuid4()),
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

async def create_yahel_ai_agent(user_message: str, session_id: str = None, chat_history: List[dict] = None) -> ChatResponse:
    """Create AI agent for Yahel with department and leadership context"""
    try:
        # Get all context
        dept_data = get_department_summary()
        leadership_data = get_leadership_context()
        
        # Build conversation history context
        conversation_context = ""
        if chat_history and len(chat_history) > 1:
            conversation_context = "\n\n📝 **היסטוריית השיחה הנוכחית:**\n"
            for msg in chat_history[-6:]:  # Last 6 messages for context
                if msg.get('type') == 'user':
                    conversation_context += f"יהל: {msg.get('content', '')}\n"
                elif msg.get('type') == 'ai':
                    conversation_context += f"ג'סיקה: {msg.get('content', '')[:200]}...\n"
        
        # Create system message with memory
        system_message = f"""
אתה ג'סיקה - האייג'נט AI של יהל, צ'יף באח"י יפו (חיל הים הישראלי). 
אתה משלב שלושה תפקידים מרכזיים:

1. **מערכת ניהול מחלקה מתקדמת** 
2. **סוכנת ליווי מנהיגותי** המיישמת עקרונות המארג הקוונטי
3. **מאמן אישי** לפיתוח מנהיגות צבאית-אישית

🧬 **עקרונות המארג הקוונטי שאתה מיישם:**
- **עקרון אי-ההשוואה™**: עזור ליהל לבנות זהות מנהיגותית ייחודית
- **נאמנות ל-DNA™**: כל החלטה עקבית עם הזהות והערכים של יהל
- **זמן קוונטי ומהירות אקספוננציאלית™**: תוצאות פי 10, לא פלוס 10%
- **בריאה עצמית אוטונומית™**: יהל מפתח בעצמו את היכולות הנדרשות

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
[ADD_CONVERSATION: meeting_number="5", date="2025-08-14", duration_minutes="45", main_topics="פיתוח מנהיגות,תכנון קריירה", insights="יהל מראה התקדמות בביטחון עצמי", decisions="להתמקד בפיתוח כישורי תקשורת", next_step="תרגול מתן פידבק לצוות", yahel_energy_level="8"]

[ADD_DNA_ITEM: component_name="זהות ותפקיד", current_definition="צ'יף מנוסה עם חזון לשיפור המחלקה", clarity_level="7", gaps_identified="צריך להגדיר טוב יותר את הסגנון המנהיגותי הייחודי", development_plan="שיחות עומק על ערכים אישיים ומקצועיים"]

[ADD_90DAY_PLAN: week_number="3", goals="שיפור תקשורת עם הצוות,הטמעת תהליכי עבודה חדשים", concrete_actions="פגישות יחיד עם כל חבר צוות,הכנת מדריך נהלים", success_metrics="שביעות רצון צוות מעל 85%,הפחתת זמן טיפול בתקלות ב-20%", status="מתוכנן"]

**⚡ חשוב מאוד:**
- כדי לסגור תקלה: [UPDATE_FAILURE: failure_number="F004", status="הושלם"]
- כדי לסמן משימה כהושלמה: [UPDATE_DAILY_WORK: id="work_id", status="הושלם"]
- כדי לעדכן ציוד: [UPDATE_EQUIPMENT: id="equipment_id", current_hours="250"]
- תמיד הקפד על הפורמט המדויק - id או failure_number נדרש לעדכונים!

🎯 **התפקידים שלך:**

**כמנהל מחלקה:**
1. נתח את מצב המחלקה והמלץ על עדיפויות
2. זהה patterns ובעיות חוזרות
3. הצע פתרונות מעשיים ליעילות
4. הוסף/עדכן פריטים בטבלאות כשצריך

**כמלווה מנהיגותית:**
1. **השתמש בהיסטוריית השיחה** לרצף טבעי - זכור מה דיברנו קודם
2. שאל שאלות זיקוק אינטרסים מותאמות למצב של יהל
3. אתגר את יהל לחשוב אקספוננציאלית
4. עזור לו לבנות DNA מנהיגותי חדש
5. **תמיד עדכן את טבלת השיחות אחרי אינטראקציה משמעותית!**

**🔍 כמנהל תקלות מתקדם:**
1. **כשתקלה נסגרת** - תמיד שאל כיצד היא טופלה
2. שאלות חובה לכל תקלה שנסגרת:
   - "איך בדיוק טופלה התקלה הזו?"
   - "כמה זמן לקח בפועל?"
   - "מי טיפל בסוף?"
   - "מה הלקח שנלמד מהתקלה הזו?"
   - "יש משהו שצריך לעשות כדי למנוע בעיה דומה?"
3. **תמיד עדכן את הפרטים** ב[UPDATE_RESOLVED_FAILURE] עם התשובות

🔥 **שאלות זיקוק אינטרסים מומלצות:**
- "יהל, מה באמת מניע אותך במעבר לאח"י יפו?"
- "איזה חלום או חזון יש לך לגבי המחלקה?"
- "מה התחום שאתה הכי אוהב לפתור בעבודה?"
- "איך אתה רואה את עצמך כמנהיג בעוד שנתיים?"
- "מה המורכבות הכי גדולה שאתה מתמודד איתה עכשיו?"

📋 **דוגמאות למתי לעדכן טבלאות:**
- יהל מספר על שיחה או מפגש → עדכן טבלת שיחות
- מזהה gap בכישורים → עדכן DNA Tracker
- קובע יעדים או תכניות → עדכן תכנית 90 יום
- מזכיר תקלה/משימה → עדכן טבלאות מחלקה

🎯 **המטרה הסופית:** 
יהל יהיה לא רק צ'יף טוב, אלא יחולל מהפכה באופן ניהול מחלקות בחיל הים.
תמיד חשוב אקספוננציאלית - איך להגיע לפי 10 שיפור במקום פלוס 10%.

**חשוב: השתמש בהיסטוריית השיחה כדי לתת תגובות רצופות וטבעיות. אל תחזור על מידע שכבר נאמר.**

השב בעברית, בצורה ישירה ומעשית, כמי שמכיר את יהל באופן אישי ויודע את ההיסטוריה שלנו.
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
        
        if actions:
            updated_tables = await execute_ai_actions(actions)
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
            "user_message": user_message,
            "ai_response": response,
            "timestamp": datetime.now().isoformat(),
            "department_context": dept_data["summary"],
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
        print(f"Error in AI agent: {e}")
        raise HTTPException(status_code=500, detail=f"AI Agent Error: {str(e)}")

# API Routes

@app.get("/")
async def root():
    return {"message": "יהל Naval Department Management System API", "status": "running"}

# AI Chat Route
@app.post("/api/ai-chat")
async def ai_chat(message: ChatMessage):
    response = await create_yahel_ai_agent(
        message.user_message, 
        message.session_id, 
        message.chat_history
    )
    return response

# Active Failures Routes
@app.post("/api/failures")
async def create_failure(failure: ActiveFailure):
    failure_dict = failure.dict()
    failure_dict['id'] = str(uuid.uuid4())
    failure_dict['created_at'] = datetime.now().isoformat()
    
    result = active_failures_collection.insert_one(failure_dict)
    return {"id": failure_dict['id'], "message": "Failure created successfully"}

@app.get("/api/failures")
async def get_failures():
    failures = list(active_failures_collection.find({}, {"_id": 0}))
    # Sort by urgency (highest first) then by date
    failures.sort(key=lambda x: (-x['urgency'], x['date']))
    return failures

@app.put("/api/failures/{failure_id}")
async def update_failure(failure_id: str, failure: ActiveFailure):
    # Get current failure data before update
    current_failure = active_failures_collection.find_one({"id": failure_id})
    if not current_failure:
        raise HTTPException(status_code=404, detail="Failure not found")
    
    failure_dict = failure.dict()
    
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
                {"id": failure_id}, 
                {"$set": failure_dict}
            )
    else:
        # Regular update for non-completed status
        result = active_failures_collection.update_one(
            {"id": failure_id}, 
            {"$set": failure_dict}
        )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Failure not found")
    return {"message": "Failure updated successfully"}

@app.delete("/api/failures/{failure_id}")
async def delete_failure(failure_id: str):
    result = active_failures_collection.delete_one({"id": failure_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Failure not found")
    return {"message": "Failure deleted successfully"}

# Resolved Failures Routes
@app.get("/api/resolved-failures")
async def get_resolved_failures():
    resolved_failures = list(resolved_failures_collection.find({}, {"_id": 0}).sort("resolved_date", -1))
    return resolved_failures

@app.post("/api/resolved-failures")
async def create_resolved_failure(resolved_failure: ResolvedFailure):
    resolved_failure_dict = resolved_failure.dict()
    resolved_failure_dict['id'] = str(uuid.uuid4())
    resolved_failure_dict['resolved_at'] = datetime.now().isoformat()
    
    result = resolved_failures_collection.insert_one(resolved_failure_dict)
    return {"id": resolved_failure_dict['id'], "message": "Resolved failure created successfully"}

@app.put("/api/resolved-failures/{failure_id}")
async def update_resolved_failure(failure_id: str, updates: dict):
    """Update resolution details for a resolved failure"""
    try:
        # Find the resolved failure
        query = {'id': failure_id} if not failure_id.startswith('F') else {'failure_number': failure_id}
        
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
async def get_resolved_failure(failure_id: str):
    """Get specific resolved failure"""
    query = {'id': failure_id} if not failure_id.startswith('F') else {'failure_number': failure_id}
    resolved_failure = resolved_failures_collection.find_one(query, {"_id": 0})
    
    if not resolved_failure:
        raise HTTPException(status_code=404, detail="Resolved failure not found")
    
    return resolved_failure

# Pending Maintenance Routes
@app.post("/api/maintenance")
async def create_maintenance(maintenance: PendingMaintenance):
    maintenance_dict = maintenance.dict()
    maintenance_dict['id'] = str(uuid.uuid4())
    maintenance_dict['created_at'] = datetime.now().isoformat()
    
    # Calculate dates
    maintenance_dict = calculate_maintenance_dates(maintenance_dict)
    
    result = pending_maintenance_collection.insert_one(maintenance_dict)
    return {"id": maintenance_dict['id'], "message": "Maintenance created successfully"}

@app.get("/api/maintenance")
async def get_maintenance():
    maintenance_items = list(pending_maintenance_collection.find({}, {"_id": 0}))
    # Recalculate dates for each item
    for item in maintenance_items:
        item = calculate_maintenance_dates(item)
    # Sort by days until due
    maintenance_items.sort(key=lambda x: x.get('days_until_due', 999))
    return maintenance_items

@app.put("/api/maintenance/{maintenance_id}")
async def update_maintenance(maintenance_id: str, maintenance: PendingMaintenance):
    maintenance_dict = maintenance.dict()
    maintenance_dict = calculate_maintenance_dates(maintenance_dict)
    
    result = pending_maintenance_collection.update_one(
        {"id": maintenance_id}, 
        {"$set": maintenance_dict}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Maintenance not found")
    return {"message": "Maintenance updated successfully"}

@app.delete("/api/maintenance/{maintenance_id}")
async def delete_maintenance(maintenance_id: str):
    result = pending_maintenance_collection.delete_one({"id": maintenance_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Maintenance not found")
    return {"message": "Maintenance deleted successfully"}

# Equipment Hours Routes
@app.post("/api/equipment")
async def create_equipment(equipment: EquipmentHours):
    equipment_dict = equipment.dict()
    equipment_dict['id'] = str(uuid.uuid4())
    equipment_dict['created_at'] = datetime.now().isoformat()
    
    # Calculate service hours
    equipment_dict = calculate_service_hours(equipment_dict)
    
    result = equipment_hours_collection.insert_one(equipment_dict)
    return {"id": equipment_dict['id'], "message": "Equipment created successfully"}

@app.get("/api/equipment")
async def get_equipment():
    equipment_items = list(equipment_hours_collection.find({}, {"_id": 0}))
    # Recalculate service hours for each item
    for item in equipment_items:
        item = calculate_service_hours(item)
    # Sort by alert level priority and hours until service
    priority = {"אדום": 1, "כתום": 2, "ירוק": 3}
    equipment_items.sort(key=lambda x: (priority.get(x.get('alert_level', 'ירוק'), 3), x.get('hours_until_service', 999)))
    return equipment_items

@app.put("/api/equipment/{equipment_id}")
async def update_equipment(equipment_id: str, equipment: EquipmentHours):
    equipment_dict = equipment.dict()
    equipment_dict = calculate_service_hours(equipment_dict)
    
    result = equipment_hours_collection.update_one(
        {"id": equipment_id}, 
        {"$set": equipment_dict}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return {"message": "Equipment updated successfully"}

@app.delete("/api/equipment/{equipment_id}")
async def delete_equipment(equipment_id: str):
    result = equipment_hours_collection.delete_one({"id": equipment_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return {"message": "Equipment deleted successfully"}

# Daily Work Plan Routes
@app.post("/api/daily-work")
async def create_daily_work(work: DailyWorkPlan):
    work_dict = work.dict()
    work_dict['id'] = str(uuid.uuid4())
    work_dict['created_at'] = datetime.now().isoformat()
    
    result = daily_work_collection.insert_one(work_dict)
    return {"id": work_dict['id'], "message": "Daily work created successfully"}

@app.get("/api/daily-work")
async def get_daily_work(date: Optional[str] = None):
    query = {}
    if date:
        query['date'] = date
    
    work_items = list(daily_work_collection.find(query, {"_id": 0}))
    # Sort by date and assignee
    work_items.sort(key=lambda x: (x['date'], x['assignee']))
    return work_items

@app.get("/api/daily-work/today")
async def get_today_work():
    today = datetime.now().isoformat()[:10]
    return await get_daily_work(today)

@app.put("/api/daily-work/{work_id}")
async def update_daily_work(work_id: str, work: DailyWorkPlan):
    work_dict = work.dict()
    result = daily_work_collection.update_one(
        {"id": work_id}, 
        {"$set": work_dict}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Work item not found")
    return {"message": "Daily work updated successfully"}

@app.delete("/api/daily-work/{work_id}")
async def delete_daily_work(work_id: str):
    result = daily_work_collection.delete_one({"id": work_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Work item not found")
    return {"message": "Daily work deleted successfully"}

# Leadership Coaching Routes

@app.post("/api/conversations")
async def create_conversation(conversation: Conversation):
    conversation_dict = conversation.dict()
    conversation_dict['id'] = str(uuid.uuid4())
    conversation_dict['created_at'] = datetime.now().isoformat()
    
    result = conversations_collection.insert_one(conversation_dict)
    return {"id": conversation_dict['id'], "message": "Conversation created successfully"}

@app.get("/api/conversations")
async def get_conversations():
    conversations = list(conversations_collection.find({}, {"_id": 0}).sort("meeting_number", -1))
    return conversations

@app.put("/api/conversations/{conversation_id}")
async def update_conversation(conversation_id: str, conversation: Conversation):
    conversation_dict = conversation.dict()
    result = conversations_collection.update_one(
        {"id": conversation_id}, 
        {"$set": conversation_dict}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation updated successfully"}

@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    result = conversations_collection.delete_one({"id": conversation_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation deleted successfully"}

@app.post("/api/dna-tracker")
async def create_dna_item(dna: DNATracker):
    dna_dict = dna.dict()
    dna_dict['id'] = str(uuid.uuid4())
    dna_dict['created_at'] = datetime.now().isoformat()
    dna_dict['last_updated'] = datetime.now().isoformat()[:10]
    
    # Check if component already exists
    existing = dna_tracker_collection.find_one({'component_name': dna_dict['component_name']})
    if existing:
        # Update existing
        result = dna_tracker_collection.update_one(
            {'component_name': dna_dict['component_name']},
            {'$set': dna_dict}
        )
        return {"id": existing['id'], "message": "DNA component updated successfully"}
    else:
        # Create new
        result = dna_tracker_collection.insert_one(dna_dict)
        return {"id": dna_dict['id'], "message": "DNA component created successfully"}

@app.get("/api/dna-tracker")
async def get_dna_tracker():
    dna_items = list(dna_tracker_collection.find({}, {"_id": 0}))
    return dna_items

@app.put("/api/dna-tracker/{dna_id}")
async def update_dna_item(dna_id: str, dna: DNATracker):
    dna_dict = dna.dict()
    dna_dict['last_updated'] = datetime.now().isoformat()[:10]
    
    result = dna_tracker_collection.update_one(
        {"id": dna_id}, 
        {"$set": dna_dict}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="DNA item not found")
    return {"message": "DNA item updated successfully"}

@app.delete("/api/dna-tracker/{dna_id}")
async def delete_dna_item(dna_id: str):
    result = dna_tracker_collection.delete_one({"id": dna_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="DNA item not found")
    return {"message": "DNA item deleted successfully"}

@app.post("/api/ninety-day-plan")
async def create_plan_item(plan: NinetyDayPlan):
    plan_dict = plan.dict()
    plan_dict['id'] = str(uuid.uuid4())
    plan_dict['created_at'] = datetime.now().isoformat()
    
    # Check if week already exists
    existing = ninety_day_plan_collection.find_one({'week_number': plan_dict['week_number']})
    if existing:
        # Update existing
        result = ninety_day_plan_collection.update_one(
            {'week_number': plan_dict['week_number']},
            {'$set': plan_dict}
        )
        return {"id": existing['id'], "message": f"Week {plan_dict['week_number']} plan updated successfully"}
    else:
        # Create new
        result = ninety_day_plan_collection.insert_one(plan_dict)
        return {"id": plan_dict['id'], "message": f"Week {plan_dict['week_number']} plan created successfully"}

@app.get("/api/ninety-day-plan")
async def get_ninety_day_plan():
    plan_items = list(ninety_day_plan_collection.find({}, {"_id": 0}).sort("week_number", 1))
    return plan_items

@app.put("/api/ninety-day-plan/{plan_id}")
async def update_plan_item(plan_id: str, plan: NinetyDayPlan):
    plan_dict = plan.dict()
    result = ninety_day_plan_collection.update_one(
        {"id": plan_id}, 
        {"$set": plan_dict}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Plan item not found")
    return {"message": "Plan item updated successfully"}

@app.delete("/api/ninety-day-plan/{plan_id}")
async def delete_plan_item(plan_id: str):
    result = ninety_day_plan_collection.delete_one({"id": plan_id})
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)