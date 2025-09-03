#!/usr/bin/env python3
"""
Email Configuration Test Script
This script tests if the email configuration is working properly.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
import os

# Import config
try:
    from config import *
    print("✅ Config imported successfully")
    print(f"📧 Email Address: {EMAIL_ADDRESS}")
    print(f"🏢 Admin Email: {ADMIN_EMAIL}")
    print(f"🌐 SMTP Server: {SMTP_SERVER}:{SMTP_PORT}")
except ImportError as e:
    print(f"❌ Failed to import config: {e}")
    sys.exit(1)

def test_email_connection():
    """Test basic SMTP connection"""
    print("\n🔍 Testing SMTP connection...")
    
    try:
        print(f"🔗 Connecting to {SMTP_SERVER}:{SMTP_PORT}...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        print("✅ Connection established")
        
        print("🔐 Starting TLS...")
        server.starttls()
        print("✅ TLS started successfully")
        
        print("🔑 Testing login...")
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        print("✅ Login successful")
        
        server.quit()
        print("✅ SMTP connection test passed!")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("💡 Check your email address and app password")
        return False
    except smtplib.SMTPConnectError as e:
        print(f"❌ Connection failed: {e}")
        print("💡 Check your internet connection and SMTP settings")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        return False

def send_test_email():
    """Send a test email"""
    print("\n📤 Sending test email...")
    
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = ADMIN_EMAIL
        msg['Subject'] = 'Test Email - Attendance System Configuration'
        
        # Plain text version
        text_body = """
        This is a test email from the Attendance Management System.
        
        If you receive this email, your email configuration is working correctly!
        
        Configuration Details:
        - SMTP Server: {}:{}
        - From Email: {}
        - To Email: {}
        
        Test completed successfully.
        """.format(SMTP_SERVER, SMTP_PORT, EMAIL_ADDRESS, ADMIN_EMAIL)
        
        # HTML version
        html_body = """
        <html>
        <body>
        <h2>✅ Email Configuration Test</h2>
        <p>This is a test email from the <strong>Attendance Management System</strong>.</p>
        <p>If you receive this email, your email configuration is working correctly!</p>
        
        <h3>Configuration Details:</h3>
        <ul>
        <li><strong>SMTP Server:</strong> {}:{}</li>
        <li><strong>From Email:</strong> {}</li>
        <li><strong>To Email:</strong> {}</li>
        </ul>
        
        <p style="color: green;"><strong>✅ Test completed successfully!</strong></p>
        </body>
        </html>
        """.format(SMTP_SERVER, SMTP_PORT, EMAIL_ADDRESS, ADMIN_EMAIL)
        
        text_part = MIMEText(text_body, 'plain')
        html_part = MIMEText(html_body, 'html')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        print(f"🔗 Connecting to {SMTP_SERVER}:{SMTP_PORT}...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        print("🔐 Starting TLS...")
        server.starttls()
        print("🔑 Logging in...")
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        print("📤 Sending test message...")
        server.send_message(msg)
        print("🔒 Closing connection...")
        server.quit()
        
        print(f"✅ Test email sent successfully!")
        print(f"📬 Email sent from: {EMAIL_ADDRESS}")
        print(f"📬 Email sent to: {ADMIN_EMAIL}")
        print(f"💡 Check your inbox at {ADMIN_EMAIL}")
        return True
        
    except Exception as e:
        print(f"❌ Test email sending failed: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        return False

def check_configuration():
    """Check if configuration looks valid"""
    print("\n🔍 Checking email configuration...")
    
    issues = []
    
    # Check if values are still default
    if EMAIL_ADDRESS == "your-email@gmail.com":
        issues.append("EMAIL_ADDRESS is still set to default value")
    
    if EMAIL_PASSWORD == "your-app-password":
        issues.append("EMAIL_PASSWORD is still set to default value")
    
    if ADMIN_EMAIL == "admin@example.com":
        issues.append("ADMIN_EMAIL is still set to default value")
    
    # Check email format
    if "@" not in EMAIL_ADDRESS:
        issues.append("EMAIL_ADDRESS doesn't appear to be a valid email")
    
    if "@" not in ADMIN_EMAIL:
        issues.append("ADMIN_EMAIL doesn't appear to be a valid email")
    
    # Check password length (app passwords are usually 16 characters)
    if len(EMAIL_PASSWORD) < 10:
        issues.append("EMAIL_PASSWORD seems too short (should be Gmail App Password)")
    
    if issues:
        print("❌ Configuration issues found:")
        for issue in issues:
            print(f"   • {issue}")
        return False
    else:
        print("✅ Configuration looks good!")
        return True

def main():
    print("🧪 Email Configuration Test")
    print("=" * 50)
    
    # Step 1: Check configuration
    config_ok = check_configuration()
    
    if not config_ok:
        print("\n❌ Please fix configuration issues before testing email")
        return
    
    # Step 2: Test SMTP connection
    connection_ok = test_email_connection()
    
    if not connection_ok:
        print("\n❌ SMTP connection failed. Cannot proceed with email test.")
        return
    
    # Step 3: Send test email
    print("\n" + "=" * 50)
    response = input("📧 Do you want to send a test email? (y/n): ").lower().strip()
    
    if response in ['y', 'yes']:
        email_ok = send_test_email()
        
        if email_ok:
            print("\n🎉 Email test completed successfully!")
            print("📬 Check your inbox for the test email")
        else:
            print("\n❌ Email test failed")
    else:
        print("📧 Test email skipped")
    
    print("\n" + "=" * 50)
    print("🏁 Test completed")

if __name__ == "__main__":
    main()