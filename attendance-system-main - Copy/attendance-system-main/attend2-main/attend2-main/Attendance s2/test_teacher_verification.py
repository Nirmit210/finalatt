#!/usr/bin/env python3
"""
Teacher Verification Email Test
This script tests the complete teacher verification flow.
"""

import sqlite3
import bcrypt
import secrets
from config import *
from app import send_verification_email

def create_test_teacher():
    """Create a test teacher account"""
    print("👨‍🏫 Creating test teacher account...")
    
    # Test teacher details
    username = "test_teacher"
    email = "test.teacher@example.com"
    password = "testpass123"
    
    # Hash password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    try:
        # Delete existing test teacher if exists
        cursor.execute('DELETE FROM users WHERE username = ?', (username,))
        
        # Create new test teacher (unverified by default)
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, role, is_verified)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, email, password_hash.decode('utf-8'), 'teacher', False))
        
        conn.commit()
        
        # Get the created user ID
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        user_id = cursor.fetchone()[0]
        
        print(f"✅ Test teacher created successfully!")
        print(f"   Username: {username}")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        print(f"   User ID: {user_id}")
        
        return user_id, username, email
        
    except sqlite3.IntegrityError as e:
        print(f"❌ Failed to create test teacher: {e}")
        return None, None, None
    finally:
        conn.close()

def test_verification_email_flow():
    """Test the complete verification email flow"""
    print("\n🧪 Testing Teacher Verification Email Flow")
    print("=" * 60)
    
    # Step 1: Create test teacher
    user_id, username, email = create_test_teacher()
    if not user_id:
        print("❌ Cannot proceed without test teacher")
        return
    
    # Step 2: Create verification request (simulating login attempt)
    print(f"\n🔐 Simulating login attempt by unverified teacher...")
    
    token = secrets.token_urlsafe(32)
    
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    try:
        # Create verification request
        cursor.execute('''
            INSERT OR REPLACE INTO verification_requests (user_id, token)
            VALUES (?, ?)
        ''', (user_id, token))
        conn.commit()
        print(f"✅ Verification request created with token: {token[:16]}...")
        
    except Exception as e:
        print(f"❌ Failed to create verification request: {e}")
        return
    finally:
        conn.close()
    
    # Step 3: Send verification email
    print(f"\n📧 Sending verification email...")
    email_sent = send_verification_email(email, username, token)
    
    if email_sent:
        print(f"✅ Verification email sent successfully!")
        print(f"📬 Email sent to admin: {ADMIN_EMAIL}")
        print(f"🔗 Verification link: http://localhost:5000/admin/verify/{token}")
    else:
        print(f"❌ Failed to send verification email")
    
    # Step 4: Show verification request in database
    print(f"\n🗄️ Checking verification request in database...")
    
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT vr.id, vr.token, vr.status, vr.created_at, u.username, u.email
        FROM verification_requests vr
        JOIN users u ON vr.user_id = u.id
        WHERE vr.user_id = ?
        ORDER BY vr.created_at DESC
        LIMIT 1
    ''', (user_id,))
    
    request = cursor.fetchone()
    conn.close()
    
    if request:
        print(f"✅ Verification request found in database:")
        print(f"   Request ID: {request[0]}")
        print(f"   Token: {request[1][:16]}...")
        print(f"   Status: {request[2]}")
        print(f"   Created: {request[3]}")
        print(f"   Teacher: {request[4]} ({request[5]})")
    else:
        print(f"❌ No verification request found in database")
    
    return email_sent

def test_admin_approval_link():
    """Test the admin approval link"""
    print(f"\n🔗 Testing admin approval functionality...")
    
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    # Get the latest pending verification request
    cursor.execute('''
        SELECT vr.token, u.username
        FROM verification_requests vr
        JOIN users u ON vr.user_id = u.id
        WHERE vr.status = 'pending'
        ORDER BY vr.created_at DESC
        LIMIT 1
    ''')
    
    request = cursor.fetchone()
    conn.close()
    
    if request:
        token, username = request
        approval_url = f"http://localhost:5000/admin/verify/{token}"
        print(f"✅ Admin approval link ready:")
        print(f"   Teacher: {username}")
        print(f"   Approval URL: {approval_url}")
        print(f"💡 Admin can click this link to approve the teacher")
    else:
        print(f"❌ No pending verification requests found")

def cleanup_test_data():
    """Clean up test data"""
    print(f"\n🧹 Cleaning up test data...")
    
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    try:
        # Delete test teacher and related verification requests
        cursor.execute('DELETE FROM verification_requests WHERE user_id IN (SELECT id FROM users WHERE username = ?)', ('test_teacher',))
        cursor.execute('DELETE FROM users WHERE username = ?', ('test_teacher',))
        conn.commit()
        print(f"✅ Test data cleaned up")
    except Exception as e:
        print(f"❌ Error cleaning up: {e}")
    finally:
        conn.close()

def main():
    print("🧪 Teacher Verification Email Test")
    print("=" * 60)
    
    # Test the complete flow
    email_sent = test_verification_email_flow()
    
    if email_sent:
        test_admin_approval_link()
        
        print(f"\n" + "=" * 60)
        print(f"🎉 Test completed successfully!")
        print(f"📧 Check the admin email ({ADMIN_EMAIL}) for the verification email")
        print(f"🔗 The email should contain a link to approve the teacher")
    else:
        print(f"\n❌ Email test failed")
    
    # Ask if user wants to clean up
    print(f"\n" + "=" * 60)
    response = input("🧹 Do you want to clean up test data? (y/n): ").lower().strip()
    
    if response in ['y', 'yes']:
        cleanup_test_data()
    else:
        print("📝 Test data left in database for manual inspection")
    
    print(f"\n🏁 Test completed")

if __name__ == "__main__":
    main()