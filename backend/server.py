from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime, timedelta
import uuid
import os
from typing import List, Optional

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

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# Collections
active_failures_collection = db.active_failures
pending_maintenance_collection = db.pending_maintenance
equipment_hours_collection = db.equipment_hours
daily_work_collection = db.daily_work

# Pydantic Models

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

# API Routes

@app.get("/")
async def root():
    return {"message": "יהל Naval Department Management System API", "status": "running"}

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

# Dashboard/Summary Routes
@app.get("/api/dashboard/summary")
async def get_dashboard_summary():
    # Get critical items summary
    urgent_failures = len(list(active_failures_collection.find({"urgency": {"$gte": 4}})))
    overdue_maintenance = len(list(pending_maintenance_collection.find({})))
    critical_equipment = len(list(equipment_hours_collection.find({})))
    today_tasks = len(list(daily_work_collection.find({"date": datetime.now().isoformat()[:10]})))
    
    return {
        "urgent_failures": urgent_failures,
        "overdue_maintenance": overdue_maintenance, 
        "critical_equipment": critical_equipment,
        "today_tasks": today_tasks,
        "last_updated": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)