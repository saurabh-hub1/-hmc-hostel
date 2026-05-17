# init_db.py
from database import init_database, get_db_path
import sqlite3
import hashlib
import os

def setup_database():
    """Setup database from scratch"""
    db_path = get_db_path()
    print(f"📁 Database path: {db_path}")
    
    # Delete existing database if it exists (for fresh start)
    if os.path.exists(db_path):
        confirm = input(f"🗑️ Database already exists at {db_path}. Delete and recreate? (y/n): ")
        if confirm.lower() == 'y':
            os.remove(db_path)
            print("🗑️ Old database deleted")
        else:
            print("❌ Setup cancelled")
            return
    
    # Create fresh database
    init_database()
    print("✅ Fresh database created")

def check_database():
    """Check if database exists and has admin user"""
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        print("   Run: python init_db.py")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check admin table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='admin'")
    if not cursor.fetchone():
        print("❌ Admin table not found")
        return False
    
    # Check admin user
    cursor.execute("SELECT username FROM admin WHERE username='admin'")
    admin = cursor.fetchone()
    
    if admin:
        print("✅ Admin user found")
        conn.close()
        return True
    else:
        print("❌ Admin user not found")
        conn.close()
        return False

def add_admin_user():
    """Force add admin user to database"""
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        print("   Run: python init_db.py first")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Ensure admin table exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT,
            email TEXT
        )
    ''')
    
    # Add admin user
    hashed = hashlib.sha256("admin123".encode()).hexdigest()
    cursor.execute("INSERT OR IGNORE INTO admin (username, password, full_name, email) VALUES (?, ?, ?, ?)", 
                   ('admin', hashed, 'Administrator', 'admin@diat.ac.in'))
    
    conn.commit()
    conn.close()
    print("✅ Admin user added/verified")

def show_admin_users():
    """Show all admin users in database"""
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT admin_id, username, full_name, email FROM admin")
    admins = cursor.fetchall()
    
    if admins:
        print("\n👑 Admin Users:")
        for admin in admins:
            print(f"   ID: {admin[0]}, Username: {admin[1]}, Name: {admin[2]}, Email: {admin[3]}")
    else:
        print("❌ No admin users found")
    
    conn.close()

if __name__ == "__main__":
    print("="*50)
    print("🚀 HMC Hostel Database Setup Tool")
    print("="*50)
    print("\nOptions:")
    print("1. Fresh Database Setup (Delete existing)")
    print("2. Add/Verify Admin User Only")
    print("3. Show Admin Users")
    print("4. Check Database Status")
    
    choice = input("\nEnter choice (1/2/3/4): ").strip()
    
    if choice == '1':
        setup_database()
        print("\n📝 Login Credentials:")
        print("   Username: admin")
        print("   Password: admin123")
    elif choice == '2':
        add_admin_user()
    elif choice == '3':
        show_admin_users()
    elif choice == '4':
        if check_database():
            print("✅ Database is ready!")
            show_admin_users()
    else:
        print("❌ Invalid choice")
    
    print("\n" + "="*50)