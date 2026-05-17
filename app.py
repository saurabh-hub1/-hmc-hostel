# app.py - Pure MongoDB Version (No PostgreSQL/SQLite)
import os
import sys
print(f"🐍 Python version: {sys.version}")

from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import json
from datetime import datetime
import threading
import csv

# 🔴 Import ObjectId for MongoDB compatibility
from bson.objectid import ObjectId

# 🔴 Force using MongoDB
USING_MONGODB = True

# 🔴 TRY TO IMPORT PANDAS, BUT HANDLE ERROR
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
    print("✅ Pandas available")
except ImportError:
    PANDAS_AVAILABLE = False
    print("⚠️ Pandas not available, using fallback")

app = Flask(__name__)
app.secret_key = 'hmc-hostel-secret-key-2026'

# 🔴 Get CSV file path
def get_csv_path():
    """Get CSV file path for exports"""
    if os.environ.get('RAILWAY_VOLUME_MOUNT_PATH'):
        db_dir = '/app/data'
        os.makedirs(db_dir, exist_ok=True)
        return os.path.join(db_dir, 'hostel_data.csv')
    elif os.environ.get('RENDER'):
        return '/tmp/hostel_data.csv'
    else:
        return os.path.join(os.getcwd(), 'hostel_data.csv')

# 🔴 Database initialization - SKIP for MongoDB
def ensure_database():
    """Ensure database - MongoDB handled in database.py"""
    print("📁 Using MongoDB Atlas - no local DB setup needed")
    return

# 🔴 Call this BEFORE importing database module
ensure_database()

# Now import database module
from database import *
import database

# ==================== HELPER FUNCTION ====================
def update_csv():
    """Auto update CSV file with latest database data from MongoDB"""
    try:
        filepath = get_csv_path()
        print(f"📁 CSV path: {filepath}")
        
        # Get all applications from MongoDB
        all_apps = list(applications.find().sort('submitted_date', -1))
        
        if PANDAS_AVAILABLE and all_apps:
            data = []
            for app in all_apps:
                app_dict = {
                    'app_id': str(app['_id']),
                    'applicant_name': app.get('applicant_name', ''),
                    'mobile': app.get('mobile', ''),
                    'email': app.get('email', ''),
                    'from_date': app.get('from_date', ''),
                    'to_date': app.get('to_date', ''),
                    'rooms_required': app.get('rooms_required', 1),
                    'status': app.get('status', 'Pending'),
                    'submitted_date': str(app.get('submitted_date', '')),
                    'guest_count': len(app.get('guest_details', [])),
                    'room_status': app.get('room_status', 'Booked'),
                    'allocated_room': app.get('allocated_room', ''),
                    'purpose': app.get('purpose', ''),
                    'applicant_type': app.get('applicant_type', '')
                }
                data.append(app_dict)
            
            if data:
                df = pd.DataFrame(data)
                df.to_csv(filepath, index=False)
            else:
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['app_id', 'applicant_name', 'mobile', 'email', 'status'])
            
            print(f"✅ CSV Auto-Updated! Total records: {len(data)}")
            return len(data)
        else:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['app_id', 'applicant_name', 'mobile', 'email', 'status'])
                for app in all_apps:
                    writer.writerow([
                        str(app['_id']),
                        app.get('applicant_name', ''),
                        app.get('mobile', ''),
                        app.get('email', ''),
                        app.get('status', 'Pending')
                    ])
            
            print(f"✅ CSV Auto-Updated! Total records: {len(all_apps)}")
            return len(all_apps)
            
    except Exception as e:
        print(f"⚠️ CSV update failed: {e}")
        return 0

def send_email_async(application, email_type='approval', rejection_reason=None):
    """Send email in background thread"""
    try:
        if email_type == 'approval':
            from email_service import send_approval_email
            send_approval_email(application)
        elif email_type == 'rejection':
            from email_service import send_rejection_email_with_reason
            send_rejection_email_with_reason(application, rejection_reason)
    except Exception as e:
        print(f"⚠️ Email error: {e}")

# ==================== INVENTORY MANAGEMENT ====================

INVENTORY_FILE = 'inventory_data.csv'
INVENTORY_LOG_FILE = 'inventory_log.csv'

def init_inventory_file():
    """Initialize inventory CSV file if not exists"""
    if not os.path.exists(INVENTORY_FILE):
        items = [
            (1, 'Bed Sheet', 200, 'pcs'),
            (2, 'Pillow Cover', 200, 'pcs'),
            (3, 'Bath Towel', 200, 'pcs'),
            (4, 'Face Towel', 200, 'pcs'),
            (5, 'Blanket', 200, 'pcs')
        ]
        with open(INVENTORY_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'stock', 'unit', 'last_updated', 'last_updated_by'])
            for item in items:
                writer.writerow([item[0], item[1], item[2], item[3], datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'system'])

def get_inventory():
    """Get current inventory data"""
    init_inventory_file()
    inventory = []
    with open(INVENTORY_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            inventory.append({
                'id': int(row['id']),
                'name': row['name'],
                'stock': int(row['stock']),
                'unit': row['unit'],
                'last_updated': row['last_updated'],
                'last_updated_by': row['last_updated_by']
            })
    return inventory

def log_inventory_transaction(item_id, item_name, action, quantity, old_stock, new_stock, performed_by):
    """Log inventory transaction for history"""
    file_exists = os.path.exists(INVENTORY_LOG_FILE)
    with open(INVENTORY_LOG_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['id', 'item_id', 'item_name', 'action', 'quantity', 'old_stock', 'new_stock', 'performed_by', 'timestamp'])
        writer.writerow([
            str(int(datetime.now().timestamp())),
            item_id, item_name, action, quantity, old_stock, new_stock, performed_by,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ])

def update_inventory_stock(item_id, action, quantity, performed_by):
    """Update inventory stock"""
    inventory = get_inventory()
    new_inventory = []
    old_stock = 0
    
    for item in inventory:
        if item['id'] == item_id:
            old_stock = item['stock']
            if action == 'add':
                new_stock = old_stock + quantity
            elif action == 'use':
                new_stock = old_stock - quantity
            elif action == 'damage':
                new_stock = old_stock - quantity
            else:
                return False, "Invalid action"
            
            if new_stock < 0:
                return False, f"Insufficient stock! Current stock: {old_stock}"
            
            item['stock'] = new_stock
            item['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            item['last_updated_by'] = performed_by
            new_inventory.append(item)
            
            # Log transaction
            log_inventory_transaction(item_id, item['name'], action, quantity, old_stock, new_stock, performed_by)
        else:
            new_inventory.append(item)
    
    # Write back to CSV
    with open(INVENTORY_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'name', 'stock', 'unit', 'last_updated', 'last_updated_by'])
        for item in new_inventory:
            writer.writerow([item['id'], item['name'], item['stock'], item['unit'], item['last_updated'], item['last_updated_by']])
    
    return True, f"Stock updated successfully! New stock: {new_stock}"

# ==================== MAIN ROUTES ====================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/student-form')
def student_form():
    return render_template('student_form.html', today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/submit-application', methods=['POST'])
def submit_application():
    try:
        form_data = request.form.to_dict()
        
        if form_data.get('applicant_type') == 'Others':
            other_text = request.form.get('other_applicant_type', '')
            if other_text:
                form_data['applicant_type'] = f"Others - {other_text}"
        
        total_guests = int(request.form.get('total_guests', 0))
        if total_guests > 4:
            total_guests = 4
        
        guest_list = []
        for i in range(1, total_guests + 1):
            name = request.form.get(f'guest_name_{i}')
            if name and name.strip():
                guest = {
                    'name': name,
                    'age_sex': request.form.get(f'guest_age_sex_{i}', ''),
                    'guest_type': request.form.get(f'guest_type_{i}', 'Adult'),
                    'nationality': request.form.get(f'guest_nationality_{i}', ''),
                    'aadhaar': request.form.get(f'guest_aadhaar_{i}', ''),
                    'contact': request.form.get(f'guest_contact_{i}', '')
                }
                guest_list.append(guest)
        
        app_id = insert_application(form_data, guest_list)
        update_csv()
        
        flash(f'✅ Application submitted successfully! Application ID: {app_id}', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        flash(f'❌ Error submitting application: {str(e)}', 'error')
        return redirect(url_for('student_form'))

# ==================== ADMIN ROUTES ====================

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if verify_admin(username, password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('✅ Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('❌ Invalid username or password!', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin-dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('admin_login'))
    
    applications = get_all_applications()
    
    print(f"\n{'='*50}")
    print(f"📊 Admin Dashboard - Found {len(applications)} applications")
    for app_data in applications:
        print(f"   ID: {app_data['app_id']} | Name: {app_data['applicant_name']} | Status: {app_data['status']} | Room: {app_data.get('room_status', 'Booked')}")
    print(f"{'='*50}\n")
    
    total = len(applications)
    pending = len([a for a in applications if a['status'] == 'Pending'])
    approved = len([a for a in applications if a['status'] == 'Approved'])
    rejected = len([a for a in applications if a['status'] == 'Rejected'])
    room_stats = get_room_status_count()
    
    return render_template('admin_dashboard.html', 
                         applications=applications,
                         total=total,
                         pending=pending,
                         approved=approved,
                         rejected=rejected,
                         room_stats=room_stats)

@app.route('/view-application/<app_id>')
def view_application(app_id):
    if not session.get('admin_logged_in') and not session.get('warden_logged_in'):
        flash('Please login first!', 'error')
        if session.get('admin_logged_in'):
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('warden_dashboard'))
    
    application = get_application_by_id(app_id)
    if not application:
        flash('Application not found!', 'error')
        if session.get('admin_logged_in'):
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('warden_dashboard'))
    
    guest_details = []
    if application.get('guest_details'):
        try:
            if isinstance(application['guest_details'], str):
                guest_details = json.loads(application['guest_details'])
            else:
                guest_details = application['guest_details']
        except:
            guest_details = []
    
    return render_template('view_application.html', 
                         application=application,
                         guest_details=guest_details)

@app.route('/approve-application/<app_id>')
def approve_application(app_id):
    if not session.get('admin_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('admin_login'))
    
    update_application_status(app_id, 'Approved', session['admin_username'])
    
    application = get_application_by_id(app_id)
    if application and application.get('email'):
        try:
            email_thread = threading.Thread(target=send_email_async, args=(application, 'approval'))
            email_thread.start()
        except:
            pass
    
    update_csv()
    flash(f'✅ Application #{app_id} approved successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/reject-application/<app_id>', methods=['GET', 'POST'])
def reject_application(app_id):
    if not session.get('admin_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        reason = request.form.get('rejection_reason', 'No reason provided')
        
        update_application_status(app_id, 'Rejected', session['admin_username'], reason)
        
        application = get_application_by_id(app_id)
        if application and application.get('email'):
            try:
                email_thread = threading.Thread(target=send_email_async, args=(application, 'rejection', reason))
                email_thread.start()
            except:
                pass
        
        update_csv()
        flash(f'⚠️ Application #{app_id} rejected! Email sent with reason.', 'info')
        return redirect(url_for('admin_dashboard'))
    
    application = get_application_by_id(app_id)
    return render_template('reject_reason.html', application=application)

@app.route('/delete-application/<app_id>')
def delete_application_route(app_id):
    if not session.get('admin_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('admin_login'))
    
    delete_application(app_id)
    update_csv()
    flash(f'🗑️ Application #{app_id} deleted!', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin-logout')
def admin_logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

# ==================== WARDEN ROUTES ====================

@app.route('/warden-login', methods=['GET', 'POST'])
def warden_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if verify_warden(username, password):
            session['warden_logged_in'] = True
            session['warden_username'] = username
            flash('✅ Warden login successful!', 'success')
            return redirect(url_for('warden_dashboard'))
        else:
            flash('❌ Invalid username or password!', 'error')
    
    return render_template('warden_login.html')

@app.route('/warden-dashboard')
def warden_dashboard():
    if not session.get('warden_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('warden_login'))
    
    pending_checkins = get_pending_checkins()
    
    return render_template('warden_dashboard.html', applications=pending_checkins)

@app.route('/warden-check-in/<app_id>', methods=['GET', 'POST'])
def warden_check_in_route(app_id):
    if not session.get('warden_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('warden_login'))
    
    if request.method == 'POST':
        room_number = request.form.get('room_number')
        
        from database import warden_check_in as db_warden_check_in
        db_warden_check_in(app_id, room_number)
        
        update_csv()
        
        flash(f'✅ Guest checked in successfully! Room {room_number} allocated.', 'success')
        return redirect(url_for('warden_dashboard'))
    
    application = get_application_by_id(app_id)
    return render_template('warden_check_in.html', application=application)

@app.route('/warden-current-occupancy')
def warden_current_occupancy():
    if not session.get('warden_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('warden_login'))
    
    occupied_rooms = get_warden_occupancy()
    room_stats = get_room_status_count()
    applications = get_all_applications()
    return render_template('warden_occupancy.html', 
                         occupied_rooms=occupied_rooms,
                         room_stats=room_stats,
                         applications=applications)

@app.route('/warden-check-out/<app_id>', methods=['GET', 'POST'])
def warden_check_out_route(app_id):
    if not session.get('warden_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('warden_login'))
    
    from database import warden_check_out
    warden_check_out(app_id)
    
    update_csv()
    
    flash(f'✅ Guest checked out successfully! Room is now VACANT.', 'success')
    return redirect(url_for('warden_current_occupancy'))

@app.route('/warden-logout')
def warden_logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

# ==================== INVENTORY ROUTES ====================

@app.route('/inventory')
def inventory_page():
    """Inventory management page"""
    if not session.get('warden_logged_in') and not session.get('admin_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('index'))
    
    inventory = get_inventory()
    total_stock = sum(item['stock'] for item in inventory)
    
    # Calculate active guests from MongoDB
    try:
        active_guests = applications.count_documents({'room_status': 'Occupied'})
    except:
        active_guests = 0
    
    return render_template('inventory.html', 
                         inventory=inventory, 
                         total_stock=total_stock,
                         active_guests=active_guests)

@app.route('/inventory/update', methods=['POST'])
def inventory_update():
    """Update inventory stock"""
    if not session.get('warden_logged_in') and not session.get('admin_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('index'))
    
    item_id = int(request.form.get('item_id'))
    action = request.form.get('action')
    quantity = int(request.form.get('quantity', 1))
    performed_by = session.get('warden_username') or session.get('admin_username')
    
    success, message = update_inventory_stock(item_id, action, quantity, performed_by)
    
    if success:
        flash(f'✅ {message}', 'success')
    else:
        flash(f'❌ {message}', 'error')
    
    return redirect(url_for('inventory_page'))

@app.route('/inventory/export')
def inventory_export():
    """Export inventory data to CSV"""
    if not session.get('warden_logged_in') and not session.get('admin_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('index'))
    
    import pandas as pd
    inventory = get_inventory()
    
    df = pd.DataFrame(inventory)
    
    filepath = os.path.join(os.getcwd(), 'inventory_export.csv')
    df.to_csv(filepath, index=False)
    
    return send_file(filepath, as_attachment=True, download_name='inventory_export.csv')

@app.route('/inventory/history')
def inventory_history():
    """View inventory transaction history"""
    if not session.get('warden_logged_in') and not session.get('admin_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('index'))
    
    history = []
    if os.path.exists(INVENTORY_LOG_FILE):
        with open(INVENTORY_LOG_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            history = list(reader)
    
    return render_template('inventory_history.html', history=history)

# ==================== CHECK-IN / CHECK-OUT ROUTES (Admin) ====================

@app.route('/check-in/<app_id>')
def check_in(app_id):
    if not session.get('admin_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('admin_login'))
    
    success, message = check_in_application(app_id, session['admin_username'])
    if success:
        update_csv()
        flash(f'🚪 {message} Room is now OCCUPIED.', 'success')
    else:
        flash(f'❌ {message}', 'error')
    return redirect(url_for('admin_dashboard'))

@app.route('/check-out/<app_id>')
def check_out(app_id):
    if not session.get('admin_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('admin_login'))
    
    success, message = check_out_application(app_id)
    if success:
        update_csv()
        flash(f'🚪 {message} Room is now VACANT.', 'success')
    else:
        flash(f'❌ {message}', 'error')
    return redirect(url_for('admin_dashboard'))

@app.route('/current-occupancy')
def current_occupancy():
    if not session.get('admin_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('admin_login'))
    
    occupied_rooms = get_current_occupancy()
    room_stats = get_room_status_count()
    applications = get_all_applications()
    
    return render_template('current_occupancy.html', 
                         occupied_rooms=occupied_rooms,
                         room_stats=room_stats,
                         applications=applications)

# ==================== EXPORT ROUTES ====================

@app.route('/export-csv')
def export_csv():
    try:
        filepath = get_csv_path()
        update_csv()
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>CSV Export - HMC Hostel</title>
            <style>
                body {{ font-family: Arial; text-align: center; padding: 50px; background: #f5f6fa; }}
                .success {{ background: #d4edda; color: #155724; padding: 20px; border-radius: 10px; }}
                .btn {{ background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="success">
                <h2>✅ CSV Export Successful!</h2>
                <p><strong>File:</strong> {filepath}</p>
                <a href="/download-csv" class="btn" style="background: #27ae60;">📥 Download CSV</a>
            </div>
            <a href="/admin-dashboard" class="btn">← Back to Dashboard</a>
            <a href="/" class="btn" style="background: #27ae60;">🏠 Home</a>
        </body>
        </html>
        """
    except Exception as e:
        return f"<h2>❌ CSV Export Failed</h2><p>Error: {str(e)}</p>"

@app.route('/download-csv')
def download_csv():
    try:
        filepath = get_csv_path()
        update_csv()
        return send_file(filepath, as_attachment=True, download_name='hostel_data.csv')
    except Exception as e:
        return f"Error: {e}"

@app.route('/force-export')
def force_export():
    try:
        filepath = get_csv_path()
        update_csv()
        return f"""
        <h2>✅ Force CSV Export Successful!</h2>
        <p>File: {filepath}</p>
        <a href="/download-csv" class="btn">📥 Download CSV</a>
        <a href="/admin-dashboard" class="btn">← Back to Dashboard</a>
        """
    except Exception as e:
        return f"<h2>❌ Error: {str(e)}</h2>"

@app.route('/simple-export')
def simple_export():
    try:
        filepath = get_csv_path()
        update_csv()
        return f"""
        <h2>✅ Simple CSV Export Successful!</h2>
        <p>File: {filepath}</p>
        <a href="/download-csv" class="btn">📥 Download CSV</a>
        <a href="/admin-dashboard" class="btn">← Back to Dashboard</a>
        """
    except Exception as e:
        return f"<h2>❌ Error: {str(e)}</h2>"

@app.route('/download-simple-csv')
def download_simple_csv():
    try:
        filepath = get_csv_path()
        update_csv()
        return send_file(filepath, as_attachment=True, download_name='hostel_data_simple.csv')
    except Exception as e:
        return f"Error: {e}"

# ==================== BULK DATA ADD ====================

@app.route('/add-bulk-data')
def add_bulk_data():
    if not session.get('admin_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('admin_login'))
    
    try:
        import random
        
        names = ['Dr. Rajesh Kumar', 'Prof. Suresh Verma', 'Ms. Priya Singh', 'Dr. Anjali Sharma']
        types = ['Serving DRDO', 'Retired DRDO', 'Other Govt Emp.', 'Others']
        purposes = ['Research Meeting', 'Conference', 'Training Program', 'Workshop', 'Seminar']
        
        count = 0
        for i in range(10):
            status = 'Approved' if i < 5 else ('Pending' if i < 8 else 'Rejected')
            
            app_data = {
                'applicant_name': random.choice(names),
                'applicant_type': random.choice(types),
                'mobile': f'98{random.randint(10000000, 99999999)}',
                'email': f'user{i}@drdo.in',
                'purpose': random.choice(purposes),
                'from_date': f'{random.randint(1,28)}-05-2026 10:00',
                'to_date': f'{random.randint(1,28)}-05-2026 17:00',
                'rooms_required': random.choice([1, 2, 3]),
                'messing_required': random.choice(['Yes', 'No']),
                'status': status,
                'submitted_date': datetime.now(),
                'guest_details': []
            }
            
            applications.insert_one(app_data)
            count += 1
        
        update_csv()
        flash(f'✅ Added {count} sample applications!', 'success')
        
    except Exception as e:
        flash(f'❌ Error: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))

# ==================== RUN SERVER ====================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("🚀 HMC Hostel Booking System Starting...")
    print(f"📍 URL: http://127.0.0.1:{port}")
    print("👑 Admin: admin / admin123")
    print("🛡️ Warden: warden / warden123")
    print("🍃 Using MongoDB Atlas (data persists forever!)")
    print("="*50)
    app.run(debug=True, host='127.0.0.1', port=port)