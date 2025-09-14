#!/usr/bin/env python3
"""
סקריפט להוספת נתוני דוגמה לטבלאות יהל
מבוסס על מבנה הנתונים המפורט במסמך yahel_tables_structure.md
"""

import sys
import os
sys.path.append('/app/backend')

from datetime import datetime, timedelta
import uuid
from pymongo import MongoClient

# הגדרת חיבור למונגו DB
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URL)
DB_NAME = os.environ.get('DB_NAME', 'yahel_department_db')
db = client[DB_NAME]

# טבלאות
active_failures_collection = db.active_failures
resolved_failures_collection = db.resolved_failures
pending_maintenance_collection = db.pending_maintenance
equipment_hours_collection = db.equipment_hours
daily_work_collection = db.daily_work
conversations_collection = db.conversations
dna_tracker_collection = db.dna_tracker
ninety_day_plan_collection = db.ninety_day_plan

def calculate_maintenance_dates(maintenance_data):
    """חישוב תאריכי אחזקה"""
    if maintenance_data.get('last_performed') and maintenance_data.get('frequency_days'):
        last_date = datetime.fromisoformat(maintenance_data['last_performed'])
        next_date = last_date + timedelta(days=maintenance_data['frequency_days'])
        days_until = (next_date - datetime.now()).days
        
        maintenance_data['next_due'] = next_date.isoformat()[:10]
        maintenance_data['days_until_due'] = days_until
        
        # קביעת סטטוס
        if days_until < 0:
            maintenance_data['status'] = 'מעוכב'
        elif days_until <= 7:
            maintenance_data['status'] = 'דחוף'
        elif days_until <= 30:
            maintenance_data['status'] = 'מתקרב'
        else:
            maintenance_data['status'] = 'בזמן'
    
    return maintenance_data

def calculate_service_hours(equipment_data):
    """חישוב שעות שירות לציוד"""
    current_hours = equipment_data.get('current_hours', 0)
    
    # חישוב שעות עד לטיפול הבא (לפי סוג הציוד)
    system_type = equipment_data.get('system_type', 'מנועים')
    
    service_intervals = {
        'מנועים': 250,
        'מכלולים': 500,
        'מערכות חשמל': 1000,
        'מערכות מיזוג': 300,
        'מערכות קירור': 200
    }
    
    interval = service_intervals.get(system_type, 250)
    hours_until_service = interval - (current_hours % interval)
    
    equipment_data['hours_until_service'] = hours_until_service
    equipment_data['next_service_hours'] = current_hours + hours_until_service
    
    # קביעת סטטוס
    if hours_until_service <= 50:
        equipment_data['service_status'] = 'דחוף'
    elif hours_until_service <= 100:
        equipment_data['service_status'] = 'מתקרב'
    else:
        equipment_data['service_status'] = 'תקין'
    
    return equipment_data

def clear_existing_data():
    """ניקוי נתונים קיימים"""
    print("🧹 מנקה נתונים קיימים...")
    
    collections = [
        active_failures_collection,
        resolved_failures_collection,
        pending_maintenance_collection,
        equipment_hours_collection,
        daily_work_collection,
        conversations_collection,
        dna_tracker_collection,
        ninety_day_plan_collection
    ]
    
    for collection in collections:
        collection.delete_many({})
    
    print("✅ ניקוי הושלם")

def populate_active_failures():
    """הוספת תקלות פעילות"""
    print("📋 מוסיף תקלות פעילות...")
    
    sample_failures = [
        {
            'id': str(uuid.uuid4()),
            'user_id': 'sample-user-001',
            'failure_number': 'F001',
            'date': (datetime.now() - timedelta(days=2)).isoformat()[:10],
            'system': 'מנוע ראשי',
            'description': 'רעש חריג במנוע בזמן הפעלה',
            'urgency': 4,
            'assignee': 'טכנאי דן',
            'estimated_hours': 3.0,
            'status': 'בטיפול',
            'created_at': (datetime.now() - timedelta(days=2)).isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'user_id': 'sample-user-001',
            'failure_number': 'F002',
            'date': (datetime.now() - timedelta(days=1)).isoformat()[:10],
            'system': 'מערכת קירור',
            'description': 'דליפת מים ממערכת הקירור הראשית',
            'urgency': 5,
            'assignee': 'טכנאי מור',
            'estimated_hours': 2.5,
            'status': 'פתוח',
            'created_at': (datetime.now() - timedelta(days=1)).isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'user_id': 'sample-user-001',
            'failure_number': 'F003',
            'date': datetime.now().isoformat()[:10],
            'system': 'מערכת חשמל',
            'description': 'בעיה בלוח החשמל הראשי - נתיכים נשרפים',
            'urgency': 3,
            'assignee': 'חשמלאי רון',
            'estimated_hours': 4.0,
            'status': 'פתוח',
            'created_at': datetime.now().isoformat()
        }
    ]
    
    active_failures_collection.insert_many(sample_failures)
    print(f"✅ הוספו {len(sample_failures)} תקלות פעילות")

def populate_resolved_failures():
    """הוספת תקלות שטופלו"""
    print("📋 מוסיף תקלות שטופלו...")
    
    sample_resolved = [
        {
            'id': str(uuid.uuid4()),
            'user_id': 'sample-user-001',
            'failure_number': 'F000',
            'date': (datetime.now() - timedelta(days=10)).isoformat()[:10],
            'system': 'מנוע משני',
            'description': 'בעיה בהילוך במנוע המשני',
            'urgency': 3,
            'assignee': 'טכנאי דוד',
            'estimated_hours': 6.0,
            'actual_hours': 5.5,
            'resolution_method': 'החלפת גיר פגום והחלפת שמן',
            'resolved_date': (datetime.now() - timedelta(days=8)).isoformat()[:10],
            'resolved_by': 'טכנאי דוד',
            'lessons_learned': 'חשוב לבדוק איכות השמן בקביעות לפני החלפת חלקים',
            'created_at': (datetime.now() - timedelta(days=10)).isoformat(),
            'resolved_at': (datetime.now() - timedelta(days=8)).isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'user_id': 'sample-user-001',
            'failure_number': 'F999',
            'date': (datetime.now() - timedelta(days=15)).isoformat()[:10],
            'system': 'מערכת מיזוג',
            'description': 'מיזוג לא עובד באזור הפיקוד',
            'urgency': 2,
            'assignee': 'טכנאי איתי',
            'estimated_hours': 3.0,
            'actual_hours': 2.0,
            'resolution_method': 'ניקוי פילטרים וטעינת גז',
            'resolved_date': (datetime.now() - timedelta(days=14)).isoformat()[:10],
            'resolved_by': 'טכנאי איתי',
            'lessons_learned': 'יש לבצע ניקוי פילטרים מידי חודש במקום מידי חודשיים',
            'created_at': (datetime.now() - timedelta(days=15)).isoformat(),
            'resolved_at': (datetime.now() - timedelta(days=14)).isoformat()
        }
    ]
    
    resolved_failures_collection.insert_many(sample_resolved)
    print(f"✅ הוספו {len(sample_resolved)} תקלות שטופלו")

def populate_maintenance():
    """הוספת אחזקות ממתינות"""
    print("📋 מוסיף אחזקות ממתינות...")
    
    sample_maintenance = [
        {
            'id': str(uuid.uuid4()),
            'user_id': 'sample-user-001',
            'maintenance_type': 'בדיקה שבועית של מנוע ראשי',
            'system': 'מנוע ראשי',
            'frequency_days': 7,
            'last_performed': (datetime.now() - timedelta(days=5)).isoformat()[:10],
            'created_at': (datetime.now() - timedelta(days=20)).isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'user_id': 'sample-user-001',
            'maintenance_type': 'בחינה חודשית של מערכת הגנה',
            'system': 'מערכת הגנה',
            'frequency_days': 30,
            'last_performed': (datetime.now() - timedelta(days=28)).isoformat()[:10],
            'created_at': (datetime.now() - timedelta(days=50)).isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'user_id': 'sample-user-001',
            'maintenance_type': 'טיפול רבעוני במערכת קירור',
            'system': 'מערכת קירור',
            'frequency_days': 90,
            'last_performed': (datetime.now() - timedelta(days=85)).isoformat()[:10],
            'created_at': (datetime.now() - timedelta(days=100)).isoformat()
        }
    ]
    
    # חישוב תאריכים
    for maintenance in sample_maintenance:
        maintenance = calculate_maintenance_dates(maintenance)
    
    pending_maintenance_collection.insert_many(sample_maintenance)
    print(f"✅ הוספו {len(sample_maintenance)} אחזקות ממתינות")

def populate_equipment_hours():
    """הוספת שעות מכלולים"""
    print("📋 מוסיף שעות מכלולים...")
    
    sample_equipment = [
        {
            'id': str(uuid.uuid4()),
            'user_id': 'sample-user-001',
            'system': 'מנוע ראשי A',
            'system_type': 'מנועים',
            'current_hours': 1247.5,
            'last_service_date': (datetime.now() - timedelta(days=45)).isoformat()[:10],
            'created_at': datetime.now().isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'user_id': 'sample-user-001',
            'system': 'מנוע משני B',
            'system_type': 'מנועים',
            'current_hours': 892.0,
            'last_service_date': (datetime.now() - timedelta(days=30)).isoformat()[:10],
            'created_at': datetime.now().isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'user_id': 'sample-user-001',
            'system': 'גנרטור עזר',
            'system_type': 'מכלולים',
            'current_hours': 234.5,
            'last_service_date': (datetime.now() - timedelta(days=60)).isoformat()[:10],
            'created_at': datetime.now().isoformat()
        }
    ]
    
    # חישוב שעות שירות
    for equipment in sample_equipment:
        equipment = calculate_service_hours(equipment)
    
    equipment_hours_collection.insert_many(sample_equipment)
    print(f"✅ הוספו {len(sample_equipment)} מכלולים לשעות ציוד")

def populate_daily_work():
    """הוספת תכנון עבודה יומי"""
    print("📋 מוסיף תכנון עבודה יומי...")
    
    sample_work = [
        {
            'id': str(uuid.uuid4()),
            'user_id': 'sample-user-001',
            'date': datetime.now().isoformat()[:10],
            'task': 'בדיקת מנוע ראשי - רעש חריג',
            'source': 'תקלה',
            'source_id': 'F001',
            'assignee': 'טכנאי דן',
            'estimated_hours': 3.0,
            'status': 'מתוכנן',
            'notes': 'לוודא שמירת פרוטוקול בדיקה מפורט',
            'created_at': datetime.now().isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'user_id': 'sample-user-001',
            'date': (datetime.now() + timedelta(days=1)).isoformat()[:10],
            'task': 'אחזקה שבועית מנוע ראשי',
            'source': 'אחזקה',
            'source_id': '',
            'assignee': 'טכנאי מור',
            'estimated_hours': 2.0,
            'status': 'מתוכנן',
            'notes': 'כולל בדיקת שמן ופילטרים',
            'created_at': datetime.now().isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'user_id': 'sample-user-001',
            'date': (datetime.now() - timedelta(days=1)).isoformat()[:10],
            'task': 'תיקון מערכת קירור',
            'source': 'תקלה',
            'source_id': 'F002',
            'assignee': 'טכנאי איתי',
            'estimated_hours': 2.5,
            'status': 'הושלם',
            'notes': 'הושלם בהצלחה - בוצעה החלפת אטם',
            'created_at': (datetime.now() - timedelta(days=1)).isoformat()
        }
    ]
    
    daily_work_collection.insert_many(sample_work)
    print(f"✅ הוספו {len(sample_work)} משימות תכנון יומי")

def populate_conversations():
    """הוספת שיחות מעקב"""
    print("📋 מוסיף שיחות מעקב...")
    
    sample_conversations = [
        {
            'id': str(uuid.uuid4()),
            'user_id': 'sample-user-001',
            'meeting_number': 1,
            'date': (datetime.now() - timedelta(days=7)).isoformat()[:10],
            'participant': 'טכנאי דן',
            'topic': 'מעקב אחר התקדמות מקצועית',
            'insights': 'הטכנאי מראה יכולות טובות באבחון תקלות מכניות',
            'follow_up_plan': 'להכשיר אותו על מערכות חשמל',
            'created_at': (datetime.now() - timedelta(days=7)).isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'user_id': 'sample-user-001',
            'meeting_number': 2,
            'date': (datetime.now() - timedelta(days=3)).isoformat()[:10],
            'participant': 'טכנאי מור',
            'topic': 'דיון על יעדים אישיים ומקצועיים',
            'insights': 'מתעניין בהתמחות במערכות מיזוג ואוורור',
            'follow_up_plan': 'לתאם קורס מתקדם במערכות HVAC',
            'created_at': (datetime.now() - timedelta(days=3)).isoformat()
        }
    ]
    
    conversations_collection.insert_many(sample_conversations)
    print(f"✅ הוספו {len(sample_conversations)} שיחות מעקב")

def populate_dna_tracker():
    """הוספת DNA מנהיגותי"""
    print("📋 מוסיף DNA מנהיגותי...")
    
    sample_dna = [
        {
            'id': str(uuid.uuid4()),
            'user_id': 'sample-user-001',
            'component_name': 'זהות ותפקיד',
            'self_assessment': 4,
            'target_score': 5,
            'action_plan': 'לפתח סגנון מנהיגות אישי וייחודי המבוסס על ערכי הצוות',
            'mentor_notes': 'מראה פוטנציאל מנהיגותי גבוה, צריך לעבוד על ביטחון עצמי',
            'last_updated': (datetime.now() - timedelta(days=5)).isoformat()[:10],
            'created_at': (datetime.now() - timedelta(days=30)).isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'user_id': 'sample-user-001',
            'component_name': 'תקשורת ומתן משוב',
            'self_assessment': 3,
            'target_score': 5,
            'action_plan': 'להשתתף בקורס תקשורת יעילה ולתרגל מתן משוב בונה',
            'mentor_notes': 'מתקשה לתת משוב קשה, חשוב לפתח כישורי תקשורת אסרטיבית',
            'last_updated': (datetime.now() - timedelta(days=2)).isoformat()[:10],
            'created_at': (datetime.now() - timedelta(days=25)).isoformat()
        }
    ]
    
    dna_tracker_collection.insert_many(sample_dna)
    print(f"✅ הוספו {len(sample_dna)} רכיבי DNA מנהיגותי")

def populate_ninety_day_plan():
    """הוספת תכנית 90 יום"""
    print("📋 מוסיף תכנית 90 יום...")
    
    sample_plan = [
        {
            'id': str(uuid.uuid4()),
            'user_id': 'sample-user-001',
            'week_number': 1,
            'goals': 'הכרת הצוות והבנת התהליכים הנוכחיים',
            'planned_activities': 'פגישות יחיד עם כל חבר צוות, סיור במתקנים',
            'required_resources': 'זמן לפגישות, גישה למסמכי תהליכים',
            'success_indicators': 'השלמת פגישות עם כל הצוות, מיפוי תהליכי עבודה',
            'status': 'הושלם',
            'created_at': (datetime.now() - timedelta(days=60)).isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'user_id': 'sample-user-001',
            'week_number': 2,
            'goals': 'זיהוי נקודות שיפור וחולשות במערכת',
            'planned_activities': 'ניתוח נתוני תקלות, סקר שביעות רצון צוות',
            'required_resources': 'נתונים היסטוריים, כלי סקר',
            'success_indicators': 'דו"ח ניתוח מלא, רשימת שיפורים מורשרית לפי עדיפות',
            'status': 'בביצוע',
            'created_at': (datetime.now() - timedelta(days=53)).isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'user_id': 'sample-user-001',
            'week_number': 3,
            'goals': 'הטמעת שיפורים ראשוניים',
            'planned_activities': 'יישום שיפורי תהליכים, הכשרת צוות',
            'required_resources': 'תקציב לכלים חדשים, זמן הכשרה',
            'success_indicators': 'הפחתת זמן טיפול בתקלות ב-15%',
            'status': 'מתוכנן',
            'created_at': (datetime.now() - timedelta(days=46)).isoformat()
        }
    ]
    
    ninety_day_plan_collection.insert_many(sample_plan)
    print(f"✅ הוספו {len(sample_plan)} שבועות לתכנית 90 יום")

def main():
    """פונקציה ראשית"""
    print("🚀 מתחיל בהוספת נתוני דוגמה למערכת יהל")
    print("=" * 50)
    
    try:
        # בדיקת חיבור למונגו
        client.admin.command('ping')
        print("✅ חיבור למונגו DB תקין")
        
        # ניקוי נתונים קיימים אוטומטית
        print("🧹 מנקה נתונים קיימים...")
        clear_existing_data()
        
        # הוספת נתוני דוגמה
        populate_active_failures()
        populate_resolved_failures()
        populate_maintenance()
        populate_equipment_hours()
        populate_daily_work()
        populate_conversations()
        populate_dna_tracker()
        populate_ninety_day_plan()
        
        print("\n" + "=" * 50)
        print("🎉 הוספת נתוני הדוגמה הושלמה בהצלחה!")
        print("=" * 50)
        
        # סיכום
        print("\n📊 סיכום נתונים שנוספו:")
        print(f"• תקלות פעילות: {active_failures_collection.count_documents({})}")
        print(f"• תקלות שטופלו: {resolved_failures_collection.count_documents({})}")
        print(f"• אחזקות ממתינות: {pending_maintenance_collection.count_documents({})}")
        print(f"• ציוד ושעות: {equipment_hours_collection.count_documents({})}")
        print(f"• תכנון יומי: {daily_work_collection.count_documents({})}")
        print(f"• שיחות מעקב: {conversations_collection.count_documents({})}")
        print(f"• DNA מנהיגותי: {dna_tracker_collection.count_documents({})}")
        print(f"• תכנית 90 יום: {ninety_day_plan_collection.count_documents({})}")
        
    except Exception as e:
        print(f"❌ שגיאה: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()