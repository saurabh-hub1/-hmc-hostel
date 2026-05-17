# check_db.py
import sqlite3

print("🔍 HMC Hostel - Database Checker")
print("=" * 50)

conn = sqlite3.connect('hostel_booking.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("\n📊 DATABASE TABLES:")
for table in tables:
    table_name = table[0]
    count = conn.execute(f"SELECT COUNT(*) as count FROM {table_name}").fetchone()['count']
    print(f"   📁 {table_name}: {count} records")
    
    # Show schema
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    print(f"      Columns: {', '.join([col['name'] for col in columns])}")

# Detailed applications check
print("\n📝 APPLICATIONS DETAILS:")
cursor.execute("SELECT COUNT(*) as count FROM applications")
count = cursor.fetchone()['count']
print(f"   Total applications: {count}")

if count > 0:
    # Status wise count
    cursor.execute("SELECT status, COUNT(*) as count FROM applications GROUP BY status")
    status_counts = cursor.fetchall()
    print("\n   Status wise:")
    for row in status_counts:
        print(f"      {row['status']}: {row['count']}")
    
    # Sample data
    cursor.execute("SELECT app_id, applicant_name, mobile, status FROM applications LIMIT 5")
    samples = cursor.fetchall()
    print("\n   Sample records:")
    for row in samples:
        print(f"      #{row['app_id']}: {row['applicant_name']} | {row['mobile']} | {row['status']}")
else:
    print("\n   ❌ No applications found!")
    print("   Run 'python init_db.py' to add sample data.")

conn.close()
print("\n" + "=" * 50)