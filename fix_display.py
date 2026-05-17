# fix_display.py
import sqlite3
import json
import os

print("🔧 HMC Hostel - Database Fix Tool")
print("=" * 50)

# Check if database exists
db_file = 'hostel_booking.db'
if os.path.exists(db_file):
    print(f"✅ Database found: {db_file}")
else:
    print(f"❌ Database not found! Will create new.")

conn = sqlite3.connect(db_file)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("\n📊 Tables in database:")
for table in tables:
    count = conn.execute(f"SELECT COUNT(*) as count FROM {table[0]}").fetchone()['count']
    print(f"   - {table[0]}: {count} records")

# Check applications table
cursor.execute("SELECT COUNT(*) as count FROM applications")
count = cursor.fetchone()['count']
print(f"\n📝 Total applications: {count}")

if count > 0:
    # Show sample data
    cursor.execute("SELECT app_id, applicant_name, mobile, status FROM applications LIMIT 5")
    rows = cursor.fetchall()
    
    print("\n📋 Sample applications:")
    for row in rows:
        print(f"   ID: {row['app_id']} | {row['applicant_name']} | {row['mobile']} | {row['status']}")
    
    # Update any NULL values
    cursor.execute('''
        UPDATE applications 
        SET applicant_name = COALESCE(applicant_name, 'N/A'),
            mobile = COALESCE(mobile, 'N/A'),
            from_date = COALESCE(from_date, 'N/A'),
            to_date = COALESCE(to_date, 'N/A'),
            status = COALESCE(status, 'Pending')
    ''')
    conn.commit()
    print("\n✅ NULL values fixed")
    
else:
    print("\n❌ No applications found!")
    print("🔄 Inserting sample data from database.py...")
    
    # This will be handled by init_database() when app runs
    from database import add_sample_applications
    add_sample_applications(conn)
    print("✅ Sample data inserted!")

conn.close()
print("\n✅ Fix complete! Run 'python app.py' now.")