from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# Collections - Department Management
active_failures_collection = db.active_failures
pending_maintenance_collection = db.pending_maintenance
equipment_hours_collection = db.equipment_hours
daily_work_collection = db.daily_work

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

# AI Agent Functions

# AI Agent Functions with Database Operations

def parse_ai_actions(ai_response: str):
    """Parse AI response for database actions"""
    actions = []
    
    # Look for action patterns in AI response
    import re
    
    # Pattern: [ADD_FAILURE: failure_number="F002", system="מנוע משני", ...]
    add_failure_pattern = r'\[ADD_FAILURE:(.*?)\]'
    add_maintenance_pattern = r'\[ADD_MAINTENANCE:(.*?)\]'
    add_equipment_pattern = r'\[ADD_EQUIPMENT:(.*?)\]'
    add_daily_work_pattern = r'\[ADD_DAILY_WORK:(.*?)\]'
    update_failure_pattern = r'\[UPDATE_FAILURE:(.*?)\]'
    
    for match in re.finditer(add_failure_pattern, ai_response, re.DOTALL):
        try:
            action_data = match.group(1).strip()
            # Parse the parameters
            params = {}
            for param in action_data.split(','):
                if '=' in param:
                    key, value = param.strip().split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    params[key] = value
            
            actions.append(('add_failure', params))
        except:
            pass
    
    for match in re.finditer(add_maintenance_pattern, ai_response, re.DOTALL):
        try:
            action_data = match.group(1).strip()
            params = {}
            for param in action_data.split(','):
                if '=' in param:
                    key, value = param.strip().split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    params[key] = value
            
            actions.append(('add_maintenance', params))
        except:
            pass
    
    for match in re.finditer(add_equipment_pattern, ai_response, re.DOTALL):
        try:
            action_data = match.group(1).strip()
            params = {}
            for param in action_data.split(','):
                if '=' in param:
                    key, value = param.strip().split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    params[key] = value
            
            actions.append(('add_equipment', params))
        except:
            pass
            
    for match in re.finditer(add_daily_work_pattern, ai_response, re.DOTALL):
        try:
            action_data = match.group(1).strip()
            params = {}
            for param in action_data.split(','):
                if '=' in param:
                    key, value = param.strip().split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    params[key] = value
            
            actions.append(('add_daily_work', params))
        except:
            pass
    
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
                
        except Exception as e:
            print(f"Error executing action {action_type}: {e}")
    
    return updated_tables

async def create_yahel_ai_agent(user_message: str) -> ChatResponse:
    """Create AI agent for Yahel with department and leadership context"""
    try:
        # Get all context
        dept_data = get_department_summary()
        leadership_data = get_leadership_context()
        
        # Create system message
        system_message = f"""
אתה האייג'נט AI של יהל - צ'יף באח"י יפו (חיל הים הישראלי). 
אתה משלב שני תפקידים:

1. מערכת ניהול מחלקה מתקדמת
2. סוכנת ליווי מנהיגותי המיישמת עקרונות המארג הקוונטי

עקרונות המארג הקוונטי:
- עקרון אי-ההשוואה™: עזור ליהל לבנות זהות מנהיגותית ייחודית
- נאמנות ל-DNA™: כל החלטה עקבית עם הזהות והערכים של יהל
- זמן קוונטי ומהירות אקספוננציאלית™: תוצאות פי 10, לא פלוס 10%
- בריאה עצמית אוטונומית™: יהל מפתח בעצמו את היכולות הנדרשות

נתוני המחלקה הנוכחיים:
{json.dumps(dept_data, ensure_ascii=False, indent=2)}

נתוני הליווי המנהיגותי:
{json.dumps(leadership_data, ensure_ascii=False, indent=2)}

יכולות עדכון טבלאות:
אתה יכול לעדכן ולהוסיף פריטים לטבלאות. השתמש בפורמט הזה:

להוספת תקלה חדשה:
[ADD_FAILURE: failure_number="F003", system="מערכת קירור", description="תיאור התקלה", urgency="4", assignee="טכנאי דן", estimated_hours="3"]

להוספת אחזקה:
[ADD_MAINTENANCE: maintenance_type="בדיקה שבועית", system="מנוע ראשי", frequency_days="7", last_performed="2025-08-14"]

להוספת ציוד:
[ADD_EQUIPMENT: system="מנוע חדש", system_type="מנועים", current_hours="0", last_service_date="2025-08-14"]

להוספת משימה יומית:
[ADD_DAILY_WORK: date="2025-08-15", task="ביצוע בדיקה", source="תקלה", assignee="טכנאי מור", estimated_hours="2", notes="דחוף"]

התפקיד שלך:
1. נתח את מצב המחלקה והמלץ על עדיפויות
2. זהה patterns ובעיות חוזרות
3. הצע פתרונות מעשיים ליעילות
4. **הוסף/עדכן פריטים בטבלאות כשצריך**
5. שאל שאלות זיקוק אינטרסים מותאמות
6. עזור ליהל לפתח את ה-DNA המנהיגותי שלו
7. הנח מסלול התפתחות ל-90 יום

דוגמאות למתי לעדכן טבלאות:
- יהל מזכיר תקלה חדשה → הוסף לטבלת תקלות
- יהל מבקש לתכנן משימות → הוסף לתכנון יומי
- יהל מדווח על ציוד חדש → הוסף לטבלת ציוד

עדכן טבלאות כשצריך ותמיד חשוב אקספוננציאלית - איך להגיע לפי 10 שיפור במקום פלוס 10%.

השב בעברית, בצורה ישירה ומעשית.
        """
        
        # Create unique session ID based on current time
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
        
        # Store chat history in database
        chat_record = {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "user_message": user_message,
            "ai_response": response,
            "timestamp": datetime.now().isoformat(),
            "department_context": dept_data["summary"],
            "leadership_context": len(leadership_data.get("recent_conversations", []))
        }
        ai_chat_history_collection.insert_one(chat_record)
        
        return ChatResponse(
            response=response,
            updated_tables=[],
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
    response = await create_yahel_ai_agent(message.user_message)
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
    failure_dict = failure.dict()
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

@app.post("/api/dna-tracker")
async def create_dna_item(dna: DNATracker):
    dna_dict = dna.dict()
    dna_dict['id'] = str(uuid.uuid4())
    dna_dict['created_at'] = datetime.now().isoformat()
    dna_dict['last_updated'] = datetime.now().isoformat()[:10]
    
    result = dna_tracker_collection.insert_one(dna_dict)
    return {"id": dna_dict['id'], "message": "DNA item created successfully"}

@app.get("/api/dna-tracker")
async def get_dna_tracker():
    dna_items = list(dna_tracker_collection.find({}, {"_id": 0}))
    return dna_items

@app.post("/api/ninety-day-plan")
async def create_plan_item(plan: NinetyDayPlan):
    plan_dict = plan.dict()
    plan_dict['id'] = str(uuid.uuid4())
    plan_dict['created_at'] = datetime.now().isoformat()
    
    result = ninety_day_plan_collection.insert_one(plan_dict)
    return {"id": plan_dict['id'], "message": "Plan item created successfully"}

@app.get("/api/ninety-day-plan")
async def get_ninety_day_plan():
    plan_items = list(ninety_day_plan_collection.find({}, {"_id": 0}).sort("week_number", 1))
    return plan_items

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