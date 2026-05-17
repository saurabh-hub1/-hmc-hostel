# database.py - Pure MongoDB Version (No PostgreSQL/SQLite)
import os
import json
import hashlib
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId

# ==================== MONGODB CONNECTION ====================

# 🔴 MongoDB Atlas connection string
ATLAS_CONNECTION_STRING = "mongodb+srv://hostel_admin:Hostel%40123@hosteladmin.jx75bvk.mongodb.net/?appName=hosteladmin"

# Pehle environment variable check karo (Render ke liye), nahi to Atlas use karo
MONGODB_URI = os.environ.get('MONGODB_URI')
if not MONGODB_URI:
    MONGODB_URI = ATLAS_CONNECTION_STRING
    print("⚠️ Using MongoDB Atlas (local development)")
else:
    print("✅ Using MongoDB Atlas (production - Render)")

# Connect to MongoDB
client = MongoClient(MONGODB_URI)
db = client['hostel_management']

# Collections (SQL tables ki jagah)
applications = db['applications']
rooms = db['rooms']
inventory = db['inventory']
inventory_logs = db['inventory_logs']
admin_collection = db['admin']
warden_collection = db['warden']

print("✅ MongoDB connected successfully!")

# ==================== HELPER FUNCTIONS ====================

def get_db_connection():
    """Return MongoDB client connection (for compatibility)"""
    return client

def format_datetime(dt):
    """Convert datetime to string format"""
    if dt and isinstance(dt, datetime):
        return dt.strftime('%Y-%m-%d %H:%M')
    return None

# ==================== DATABASE INITIALIZATION ====================

def init_database():
    """Initialize database with default data"""
    
    # Admin create karo
    if admin_collection.count_documents({}) == 0:
        hashed_password = hashlib.sha256("admin123".encode()).hexdigest()
        admin_collection.insert_one({
            'username': 'admin',
            'password': hashed_password,
            'full_name': 'Administrator',
            'email': 'admin@diat.ac.in',
            'created_at': datetime.now()
        })
        print("✅ Default admin user created")
    
    # Warden create karo
    if warden_collection.count_documents({}) == 0:
        hashed_password = hashlib.sha256("warden123".encode()).hexdigest()
        warden_collection.insert_one({
            'username': 'warden',
            'password': hashed_password,
            'full_name': 'Warden',
            'email': 'warden@diat.ac.in',
            'created_at': datetime.now()
        })
        print("✅ Default warden user created")
    
    # Inventory items create karo
    if inventory.count_documents({}) == 0:
        items = [
            {'name': 'Bed Sheet', 'stock': 100, 'unit': 'pieces', 'last_updated': datetime.now()},
            {'name': 'Pillow Cover', 'stock': 100, 'unit': 'pieces', 'last_updated': datetime.now()},
            {'name': 'Towel', 'stock': 50, 'unit': 'pieces', 'last_updated': datetime.now()},
            {'name': 'Blanket', 'stock': 30, 'unit': 'pieces', 'last_updated': datetime.now()}
        ]
        inventory.insert_many(items)
        print("✅ Inventory items created")
    
    # Rooms create karo (250 rooms)
    if rooms.count_documents({}) == 0:
        room_list = []
        floors = ['G', 'F', 'S', 'T']  # Ground, First, Second, Third
        for floor in floors:
            for i in range(1, 65):
                room_list.append({
                    'room_number': f"{floor}-{i:03d}",
                    'status': 'available',
                    'current_guest': None,
                    'current_application_id': None
                })
        rooms.insert_many(room_list)
        print(f"✅ {len(room_list)} rooms created")
    
    # Sample applications (optional - testing ke liye)
    if applications.count_documents({}) == 0:
        sample_apps = [
            {
                'applicant_name': 'Dr. Rajesh Kumar',
                'applicant_type': 'Serving DRDO',
                'mobile': '9876543210',
                'email': 'rajesh@drdo.in',
                'purpose': 'Research Meeting',
                'referred_by': 'Dr. Sharma',
                'remarks': 'Urgent',
                'guest_details': [
                    {'name': 'Dr. Rajesh Kumar', 'age_sex': '45/M', 'guest_type': 'Adult'},
                    {'name': 'Riya Kumar', 'age_sex': '10/F', 'guest_type': 'Child'}
                ],
                'from_date': '2026-05-15 10:00',
                'to_date': '2026-05-18 18:00',
                'rooms_required': 1,
                'status': 'Pending',
                'submitted_date': datetime.now(),
                'room_status': 'Booked'
            },
            {
                'applicant_name': 'Prof. Suresh Verma',
                'applicant_type': 'Retired DRDO',
                'mobile': '9876543211',
                'email': 'suresh@email.com',
                'purpose': 'Conference',
                'referred_by': 'Dr. Patil',
                'remarks': 'Guest lecture',
                'guest_details': [
                    {'name': 'Prof. Suresh Verma', 'age_sex': '55/M', 'guest_type': 'Adult'},
                    {'name': 'Mrs. Anjali Verma', 'age_sex': '50/F', 'guest_type': 'Adult'},
                    {'name': 'Master Arjun Verma', 'age_sex': '8/M', 'guest_type': 'Child'}
                ],
                'from_date': '2026-05-20 09:00',
                'to_date': '2026-05-22 17:00',
                'rooms_required': 2,
                'status': 'Approved',
                'submitted_date': datetime.now(),
                'room_status': 'Booked'
            }
        ]
        applications.insert_many(sample_apps)
        print("✅ Sample applications created")
    
    print("🎉 Database initialization complete!")

# ==================== APPLICATION FUNCTIONS ====================

def insert_application(form_data, guest_list):
    """Insert new application"""
    app_data = {
        'applicant_name': form_data.get('applicant_name', ''),
        'designation': form_data.get('designation', ''),
        'applicant_type': form_data.get('applicant_type', ''),
        'mobile': form_data.get('mobile', ''),
        'email': form_data.get('email', ''),
        'purpose': form_data.get('purpose', ''),
        'referred_by': form_data.get('referred_by', ''),
        'remarks': form_data.get('remarks', ''),
        'guest_details': guest_list,
        'from_date': form_data.get('from_date', ''),
        'to_date': form_data.get('to_date', ''),
        'rooms_required': int(form_data.get('rooms_required', 1)),
        'messing_required': form_data.get('messing_required', 'No'),
        'billing_person': form_data.get('billing_person', ''),
        'signature': form_data.get('signature', ''),
        'status': 'Pending',
        'submitted_date': datetime.now(),
        'room_status': 'Booked',
        'allocated_room': None,
        'check_in_date': None,
        'check_out_date': None,
        'rejection_reason': None
    }
    
    result = applications.insert_one(app_data)
    return str(result.inserted_id)

def get_all_applications():
    """Get all applications with guest count"""
    all_apps = list(applications.find().sort('submitted_date', -1))
    
    result = []
    for app in all_apps:
        guest_count = len(app.get('guest_details', []))
        adult_count = len([g for g in app.get('guest_details', []) if g.get('guest_type') == 'Adult'])
        child_count = len([g for g in app.get('guest_details', []) if g.get('guest_type') == 'Child'])
        
        check_in = format_datetime(app.get('check_in_date'))
        check_out = format_datetime(app.get('check_out_date'))
        
        result.append({
            'app_id': str(app['_id']),
            'applicant_name': app.get('applicant_name', 'N/A'),
            'mobile': app.get('mobile', 'N/A'),
            'from_date': app.get('from_date', 'N/A'),
            'to_date': app.get('to_date', 'N/A'),
            'rooms_required': app.get('rooms_required', 1),
            'status': app.get('status', 'Pending'),
            'submitted_date': str(app.get('submitted_date', '')),
            'guest_count': guest_count,
            'adult_count': adult_count,
            'child_count': child_count,
            'room_status': app.get('room_status', 'Booked'),
            'check_in_date': check_in,
            'check_out_date': check_out,
            'allocated_room': app.get('allocated_room'),
            'rejection_reason': app.get('rejection_reason')
        })
    
    return result

def get_application_by_id(app_id):
    """Get single application by ID"""
    try:
        app = applications.find_one({'_id': ObjectId(app_id)})
        if app:
            app['_id'] = str(app['_id'])
            if app.get('check_in_date') and isinstance(app.get('check_in_date'), datetime):
                app['check_in_date_str'] = app['check_in_date'].strftime('%Y-%m-%d %H:%M')
            if app.get('check_out_date') and isinstance(app.get('check_out_date'), datetime):
                app['check_out_date_str'] = app['check_out_date'].strftime('%Y-%m-%d %H:%M')
            return app
        return None
    except:
        return None

def update_application_status(app_id, status, approved_by='Admin', rejection_reason=None):
    """Update application status"""
    update_data = {
        'status': status,
        'approved_by': approved_by,
        'approved_date': datetime.now()
    }
    if rejection_reason:
        update_data['rejection_reason'] = rejection_reason
    
    applications.update_one(
        {'_id': ObjectId(app_id)},
        {'$set': update_data}
    )

def delete_application(app_id):
    """Delete application"""
    applications.delete_one({'_id': ObjectId(app_id)})

# ==================== WARDEN FUNCTIONS ====================

def verify_admin(username, password):
    """Verify admin credentials"""
    hashed = hashlib.sha256(password.encode()).hexdigest()
    admin = admin_collection.find_one({'username': username, 'password': hashed})
    return admin is not None

def verify_warden(username, password):
    """Verify warden credentials"""
    hashed = hashlib.sha256(password.encode()).hexdigest()
    warden = warden_collection.find_one({'username': username, 'password': hashed})
    return warden is not None

def get_pending_checkins():
    """Get approved applications waiting for check-in"""
    pending = list(applications.find({
        'status': 'Approved',
        '$or': [
            {'room_status': 'Booked'},
            {'room_status': None}
        ]
    }).sort('submitted_date', -1))
    
    result = []
    for app in pending:
        result.append({
            'app_id': str(app['_id']),
            '_id': str(app['_id']),
            'applicant_name': app.get('applicant_name', 'N/A'),
            'mobile': app.get('mobile', 'N/A'),
            'email': app.get('email', 'N/A'),
            'from_date': app.get('from_date', 'N/A'),
            'to_date': app.get('to_date', 'N/A'),
            'rooms_required': app.get('rooms_required', 1),
            'purpose': app.get('purpose', 'N/A'),
            'status': app.get('status', 'Approved'),
            'guest_count': len(app.get('guest_details', [])),
            'guest_details': app.get('guest_details', []),
            'room_status': app.get('room_status', 'Booked')
        })
    
    return result

def warden_check_in(app_id, room_number):
    """Warden check-in with room allocation"""
    # Update application
    applications.update_one(
        {'_id': ObjectId(app_id)},
        {'$set': {
            'check_in_date': datetime.now(),
            'room_status': 'Occupied',
            'allocated_room': room_number
        }}
    )
    
    # Update room status
    rooms.update_one(
        {'room_number': room_number},
        {'$set': {
            'status': 'occupied',
            'current_application_id': app_id
        }}
    )

def warden_check_out(app_id):
    """Warden check-out - guest leaves, room becomes vacant"""
    # Get application to find allocated room
    app = applications.find_one({'_id': ObjectId(app_id)})
    allocated_room = app.get('allocated_room')
    
    # Update application
    result = applications.update_one(
        {'_id': ObjectId(app_id), 'room_status': 'Occupied'},
        {'$set': {
            'check_out_date': datetime.now(),
            'room_status': 'Vacant'
        }}
    )
    
    # Update room status
    if allocated_room:
        rooms.update_one(
            {'room_number': allocated_room},
            {'$set': {
                'status': 'available',
                'current_application_id': None
            }}
        )
    
    return result.modified_count > 0

def get_warden_occupancy():
    """Get currently occupied rooms for warden"""
    occupied = list(applications.find({
        'room_status': 'Occupied'
    }).sort('check_in_date', -1))
    
    result = []
    for app in occupied:
        check_in = app.get('check_in_date')
        if check_in and isinstance(check_in, datetime):
            check_in_str = check_in.strftime('%Y-%m-%d %H:%M')
        else:
            check_in_str = None
        
        result.append({
            'app_id': str(app['_id']),
            '_id': str(app['_id']),
            'applicant_name': app.get('applicant_name', 'N/A'),
            'mobile': app.get('mobile', 'N/A'),
            'email': app.get('email', 'N/A'),
            'from_date': app.get('from_date', 'N/A'),
            'to_date': app.get('to_date', 'N/A'),
            'allocated_room': app.get('allocated_room', 'Not assigned'),
            'check_in_date': check_in_str,
            'guest_count': len(app.get('guest_details', []))
        })
    
    return result

def get_checked_in_applications():
    """Get all currently checked-in guests (for check-out list)"""
    checked_in = list(applications.find({
        'room_status': 'Occupied',
        'check_out_date': None
    }).sort('check_in_date', -1))
    
    result = []
    for app in checked_in:
        check_in = app.get('check_in_date')
        if check_in and isinstance(check_in, datetime):
            check_in_str = check_in.strftime('%Y-%m-%d %H:%M')
        else:
            check_in_str = None
        
        result.append({
            'app_id': str(app['_id']),
            'applicant_name': app.get('applicant_name', 'N/A'),
            'mobile': app.get('mobile', 'N/A'),
            'allocated_room': app.get('allocated_room', 'Not assigned'),
            'check_in_date': check_in_str,
            'from_date': app.get('from_date', 'N/A'),
            'to_date': app.get('to_date', 'N/A')
        })
    
    return result

def get_room_status_count():
    """Get room occupancy statistics"""
    TOTAL_ROOMS = 250
    
    # Occupied rooms count
    occupied = applications.count_documents({'room_status': 'Occupied'})
    
    # Booked rooms count (approved but not checked in)
    booked = applications.count_documents({
        'status': 'Approved',
        '$or': [
            {'room_status': 'Booked'},
            {'room_status': None}
        ]
    })
    
    vacant = TOTAL_ROOMS - occupied - booked
    
    return {'occupied': occupied, 'booked': booked, 'vacant': vacant}

# ==================== CHECK-IN / CHECK-OUT FUNCTIONS ====================

def check_in_application(app_id, admin_name):
    """Admin check-in function"""
    app = applications.find_one({'_id': ObjectId(app_id)})
    if app and app.get('room_status') == 'Occupied':
        return False, "Already checked in!"
    
    applications.update_one(
        {'_id': ObjectId(app_id)},
        {'$set': {
            'check_in_date': datetime.now(),
            'room_status': 'Occupied'
        }}
    )
    return True, "Checked in successfully!"

def check_out_application(app_id):
    """Admin check-out function"""
    app = applications.find_one({'_id': ObjectId(app_id)})
    if app and app.get('room_status') == 'Vacant':
        return False, "Already checked out!"
    
    applications.update_one(
        {'_id': ObjectId(app_id)},
        {'$set': {
            'check_out_date': datetime.now(),
            'room_status': 'Vacant'
        }}
    )
    return True, "Checked out successfully!"

def get_current_occupancy():
    """Get current occupancy for admin with proper app_id"""
    occupied = list(applications.find({
        'room_status': 'Occupied',
        'check_out_date': None
    }).sort('check_in_date', -1))
    
    result = []
    for app in occupied:
        check_in = app.get('check_in_date')
        if check_in and isinstance(check_in, datetime):
            check_in_str = check_in.strftime('%Y-%m-%d %H:%M')
        else:
            check_in_str = None
        
        result.append({
            'app_id': str(app['_id']),
            'applicant_name': app.get('applicant_name', 'N/A'),
            'mobile': app.get('mobile', 'N/A'),
            'email': app.get('email', 'N/A'),
            'from_date': app.get('from_date', 'N/A'),
            'to_date': app.get('to_date', 'N/A'),
            'rooms_required': app.get('rooms_required', 1),
            'guest_count': len(app.get('guest_details', [])),
            'guest_details': app.get('guest_details', []),
            'room_status': app.get('room_status', 'Occupied'),
            'check_in_date': check_in_str,
            'check_out_date': app.get('check_out_date'),
            'allocated_room': app.get('allocated_room', 'Not assigned'),
            'status': app.get('status', 'Approved')
        })
    
    return result

# ==================== INVENTORY FUNCTIONS ====================

def get_all_inventory():
    """Get all inventory items"""
    items = list(inventory.find())
    for item in items:
        item['_id'] = str(item['_id'])
    return items

def update_inventory(item_id, action, quantity):
    """Update inventory stock"""
    try:
        item_id_int = int(item_id) if isinstance(item_id, str) and item_id.isdigit() else item_id
    except:
        item_id_int = item_id
    
    if action == 'add':
        inventory.update_one(
            {'_id': item_id_int},
            {'$inc': {'stock': quantity}, '$set': {'last_updated': datetime.now()}}
        )
    elif action == 'use':
        inventory.update_one(
            {'_id': item_id_int},
            {'$inc': {'stock': -quantity}, '$set': {'last_updated': datetime.now()}}
        )
    elif action == 'damage':
        inventory.update_one(
            {'_id': item_id_int},
            {'$inc': {'stock': -quantity}, '$set': {'last_updated': datetime.now()}}
        )
    
    inventory_logs.insert_one({
        'item_id': item_id_int,
        'action': action,
        'quantity': quantity,
        'timestamp': datetime.now()
    })

def get_total_stock():
    """Get total stock of all items"""
    items = list(inventory.find())
    total = sum(item.get('stock', 0) for item in items)
    return total

# ==================== INITIALIZE ON IMPORT ====================

print("🔄 Initializing MongoDB database...")
try:
    init_database()
    print("✅ Database initialized successfully!")
except Exception as e:
    print(f"⚠️ Database init error: {e}")