from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import cv2
import numpy as np
import base64
from PIL import Image
import io
import os
import bcrypt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import secrets
from dotenv import load_dotenv

load_dotenv()

# Initialize face recognizer with highly permissive parameters for better initial matching
face_recognizer = cv2.face.LBPHFaceRecognizer_create(
    radius=1,           # Smaller radius for finer detail
    neighbors=4,        # Fewer neighbors for more lenient matching
    grid_x=4,          # Smaller grid for less strict spatial matching
    grid_y=4,          # Smaller grid for less strict spatial matching
    threshold=500.0     # Much higher threshold for very permissive matching
)
face_recognizer_trained = False

# Initialize face cascade classifiers
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
face_cascade_alt = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml')

# Import config if it exists
try:
    from config import *
except ImportError:
    # Fallback to environment variables
    pass

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-this')

# Email configuration - Use config.py values if available, otherwise fallback to environment variables
try:
    # These should be imported from config.py
    SMTP_SERVER = SMTP_SERVER
    SMTP_PORT = SMTP_PORT
    EMAIL_ADDRESS = EMAIL_ADDRESS
    EMAIL_PASSWORD = EMAIL_PASSWORD
    ADMIN_EMAIL = ADMIN_EMAIL
except NameError:
    # Fallback to environment variables if config.py not loaded
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS', 'your-email@gmail.com')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', 'your-app-password')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@school.com')

def train_face_recognizer():
    """Train the face recognizer with all enrolled students"""
    global face_recognizer_trained
    
    print("Starting face recognizer training...")
    
    # Initialize the database if it doesn't exist
    init_db()
    
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, face_encoding, name FROM students WHERE face_encoding IS NOT NULL')
    students = cursor.fetchall()
    
    if not students:
        print("No enrolled students found with face encodings")
        face_recognizer_trained = False
        return
    
    print(f"Found {len(students)} enrolled students with face encodings")
    faces = []
    labels = []
    
    for student in students:
        if student[1] is not None:  # Check if face_encoding exists
            try:
                face_encoding = student[1]
                # If face_encoding is str, convert to bytes
                if isinstance(face_encoding, str):
                    face_encoding = face_encoding.encode('latin1')
                    
                # Decode the stored face image
                nparr = np.frombuffer(face_encoding, np.uint8)
                face = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
                
                if face is not None and face.shape == (128, 128):
                    # Apply exactly the same preprocessing as recognition
                    face_final = preprocess_face(face)
                    
                    faces.append(face_final)
                    labels.append(student[0])  # Use student ID as label
                    print(f"Processed face for student {student[2]} (ID: {student[0]})")
            except Exception as e:
                print(f"Error processing face for student {student[2]} (ID: {student[0]}): {e}")
                continue
    
    if len(faces) > 0:
        try:
            # Convert lists to numpy arrays
            faces_array = np.array(faces)
            labels_array = np.array(labels)
            
            print(f"Training face recognizer with {len(faces)} faces")
            print(f"Face array shape: {faces_array.shape}")
            print(f"Labels array shape: {labels_array.shape}")
            
            # Reset and retrain the recognizer
            face_recognizer.train(faces_array, labels_array)
            face_recognizer_trained = True
            print("Face recognizer training completed successfully")
            
            # Test the recognizer on training data
            for i, face in enumerate(faces):
                label, confidence = face_recognizer.predict(face)
                similarity = 1 - min(confidence / 100.0, 1.0)
                print(f"Test recognition - Expected: {labels[i]}, Got: {label}, Confidence: {confidence:.2f}, Similarity: {similarity:.2f}")
                
        except Exception as e:
            print(f"Error training face recognizer: {e}")
            face_recognizer_trained = False
    else:
        print("No valid faces found for training")
        face_recognizer_trained = False
    
    conn.close()
    return face_recognizer_trained

def preprocess_face(image):
    """Apply simple but effective preprocessing to face images for both enrollment and recognition."""
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # 1. Basic size normalization
    gray = cv2.resize(gray, (128, 128))
    
    # 2. Simple noise reduction with Gaussian blur
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    
    # 3. Basic histogram equalization for contrast
    gray = cv2.equalizeHist(gray)
    
    # 4. Ensure proper type and range
    gray = np.uint8(gray)
    
    return gray

def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    # Students table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            student_id TEXT UNIQUE NOT NULL,
            email TEXT,
            face_encoding BLOB,  -- Stores PNG image data of preprocessed face
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Users table (admin and teachers)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('admin', 'teacher')),
            is_verified BOOLEAN DEFAULT FALSE,
            verification_token TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Attendance records
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            date DATE NOT NULL,
            time TIME NOT NULL,
            status TEXT DEFAULT 'present',
            marked_by INTEGER,
            FOREIGN KEY (student_id) REFERENCES students (id),
            FOREIGN KEY (marked_by) REFERENCES users (id)
        )
    ''')
    
    # Verification requests
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verification_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            token TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create default admin user if doesn't exist
    cursor.execute('SELECT * FROM users WHERE role = "admin"')
    if not cursor.fetchone():
        admin_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, role, is_verified)
            VALUES (?, ?, ?, ?, ?)
        ''', ('admin', ADMIN_EMAIL, admin_password.decode('utf-8'), 'admin', True))
    
    conn.commit()
    conn.close()

def send_verification_email(teacher_email, teacher_name, token):
    """Send verification email to admin"""
    print(f"🔍 Attempting to send verification email for {teacher_name} ({teacher_email})")
    
    # Check if email is properly configured
    if EMAIL_ADDRESS == 'your-email@gmail.com' or EMAIL_PASSWORD == 'your-app-password':
        print("❌ Email not configured. Skipping email send.")
        return False
    
    try:
        print(f"📧 Creating verification email...")
        
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = ADMIN_EMAIL
        msg['Subject'] = f'Teacher Verification Request - {teacher_name}'
        
        # Plain text version
        text_body = f"""
        A new teacher has requested access to the Attendance Management System:
        
        Teacher Name: {teacher_name}
        Teacher Email: {teacher_email}
        
        To approve this request, click the link below:
        http://localhost:5000/admin/verify/{token}
        
        To reject this request, please log into the admin panel.
        """
        
        # HTML version
        html_body = f"""
        <html>
        <body>
        <h2>Teacher Verification Request</h2>
        <p>A new teacher has requested access to the Attendance Management System:</p>
        <ul>
        <li><strong>Teacher Name:</strong> {teacher_name}</li>
        <li><strong>Teacher Email:</strong> {teacher_email}</li>
        </ul>
        <p><a href="http://localhost:5000/admin/verify/{token}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Click here to approve</a></p>
        </body>
        </html>
        """
        
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
        print("📤 Sending message...")
        server.send_message(msg)
        print("🔒 Closing connection...")
        server.quit()
        
        print(f"✅ Verification email sent successfully!")
        print(f"📬 Email sent to: {ADMIN_EMAIL}")
        print(f"🔗 Verification link: http://localhost:5000/admin/verify/{token}")
        return True
        
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/3d-demo')
def demo_3d():
    return render_template('3d-demo.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
            if user[4] == 'admin' or user[5]:  # Admin or verified teacher
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['role'] = user[4]
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            elif user[4] == 'teacher' and not user[5]:
                print(f"🔍 Unverified teacher login detected: {user[1]} ({user[2]})")
                # Create verification request
                token = secrets.token_urlsafe(32)
                conn = sqlite3.connect('attendance.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO verification_requests (user_id, token)
                    VALUES (?, ?)
                ''', (user[0], token))
                conn.commit()
                conn.close()
                print(f"✅ Verification request created in database for user {user[0]}")
                
                # Send verification email
                print(f"📧 Attempting to send verification email...")
                email_sent = send_verification_email(user[2], user[1], token)
                print(f"📧 Email sending result: {email_sent}")
                
                if email_sent:
                    flash('Verification request sent to admin via email. Please wait for approval.', 'info')
                    print(f"✅ Flash message: Email sent successfully")
                else:
                    flash('Email sending failed. Please contact admin directly.', 'error')
                    print(f"❌ Flash message: Email sending failed")
                return redirect(url_for('login'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        
        if role not in ['teacher']:  # Only teachers can register
            flash('Invalid role!', 'error')
            return redirect(url_for('register'))
        
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash.decode('utf-8'), role))
            conn.commit()
            flash('Registration successful! Please login to request verification.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists!', 'error')
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session['role'] == 'admin':
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('teacher_dashboard'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    # Get pending verification requests
    cursor.execute('''
        SELECT vr.id, u.username, u.email, vr.created_at
        FROM verification_requests vr
        JOIN users u ON vr.user_id = u.id
        WHERE vr.status = 'pending'
        ORDER BY vr.created_at DESC
    ''')
    pending_requests = cursor.fetchall()
    
    # Show notification if there are pending requests
    if pending_requests:
        flash(f'You have {len(pending_requests)} pending teacher verification request(s)!', 'warning')
    
    # Get system statistics
    cursor.execute('SELECT COUNT(*) FROM students')
    total_students = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE role = "teacher" AND is_verified = 1')
    verified_teachers = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM attendance WHERE date = ?', (datetime.now().date(),))
    today_attendance = cursor.fetchone()[0]
    
    conn.close()
    
    return render_template('admin_dashboard.html', 
                         pending_requests=pending_requests,
                         total_students=total_students,
                         verified_teachers=verified_teachers,
                         today_attendance=today_attendance)

@app.route('/teacher/dashboard')
def teacher_dashboard():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    # Get today's attendance
    cursor.execute('''
        SELECT s.name, s.student_id, a.time, a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE a.date = ? AND a.marked_by = ?
        ORDER BY a.time DESC
    ''', (datetime.now().date(), session['user_id']))
    today_attendance = cursor.fetchall()
    
    # Get total students
    cursor.execute('SELECT COUNT(*) FROM students')
    total_students = cursor.fetchone()[0]
    
    conn.close()
    
    return render_template('teacher_dashboard.html', 
                         today_attendance=today_attendance,
                         total_students=total_students)

@app.route('/api/teacher/attendance-data')
def get_attendance_data():
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Get current timestamp to ensure fresh data
    current_time = datetime.now()
    
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    # Get today's attendance with fresh query - get ALL attendance for today, not just by current teacher
    cursor.execute('''
        SELECT s.name, s.student_id, a.time, a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE a.date = ?
        ORDER BY a.time DESC
    ''', (current_time.date(),))
    today_attendance = cursor.fetchall()
    
    # Log for debugging
    print(f"API: Found {len(today_attendance)} attendance records for today ({current_time.date()})")
    
    # Get total students with fresh query
    cursor.execute('SELECT COUNT(*) FROM students')
    total_students = cursor.fetchone()[0]
    print(f"API: Total students: {total_students}")
    
    # Format attendance records for JSON response
    attendance_records = []
    for record in today_attendance:
        attendance_records.append({
            'name': record[0],
            'student_id': record[1],
            'time': record[2],
            'status': record[3]
        })
    
    # Calculate attendance rate
    attendance_rate = 0
    if total_students > 0:
        attendance_rate = (len(today_attendance) / total_students) * 100
    
    print(f"API: Attendance rate: {attendance_rate}%")
    
    conn.close()
    
    # Set cache control headers to prevent caching
    response_data = {
        'total_students': total_students,
        'present_today': len(today_attendance),
        'attendance_rate': round(attendance_rate, 1),
        'attendance_records': attendance_records,
        'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S')  # Include timestamp for verification
    }
    
    print(f"API: Sending response: {response_data['present_today']} present, {response_data['attendance_rate']}% rate")
    
    response = jsonify(response_data)
    
    # Add cache control headers
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

@app.route('/admin/verify/<token>')
def verify_teacher(token):
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT vr.user_id FROM verification_requests vr
        WHERE vr.token = ? AND vr.status = 'pending'
    ''', (token,))
    request_data = cursor.fetchone()
    
    if request_data:
        user_id = request_data[0]
        # Update user verification status
        cursor.execute('UPDATE users SET is_verified = 1 WHERE id = ?', (user_id,))
        # Update request status
        cursor.execute('UPDATE verification_requests SET status = "approved" WHERE token = ?', (token,))
        conn.commit()
        flash('Teacher verified successfully!', 'success')
    else:
        flash('Invalid or expired verification token!', 'error')
    
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/students')
def students():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, student_id, email, created_at FROM students ORDER BY name')
    students = cursor.fetchall()
    conn.close()
    
    return render_template('students.html', students=students)

@app.route('/teachers')
def teachers():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.*, COALESCE(
            (SELECT COUNT(*) FROM attendance WHERE marked_by = u.id), 0
        ) as attendance_count
        FROM users u 
        WHERE u.role = 'teacher'
        ORDER BY u.username
    ''')
    teachers = cursor.fetchall()
    conn.close()
    
    return render_template('teachers.html', teachers=teachers)

@app.route('/admin/verify_teacher/<int:user_id>', methods=['POST'])
def verify_teacher_by_id(user_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE users SET is_verified = 1 WHERE id = ? AND role = "teacher"', (user_id,))
        if cursor.rowcount > 0:
            conn.commit()
            return jsonify({'success': True, 'message': 'Teacher verified successfully'})
        else:
            return jsonify({'success': False, 'message': 'Teacher not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

@app.route('/admin/revoke_teacher/<int:user_id>', methods=['POST'])
def revoke_teacher_access(user_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    if user_id == session['user_id']:
        return jsonify({'success': False, 'message': 'Cannot revoke your own access'}), 400
    
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE users SET is_verified = 0 WHERE id = ? AND role = "teacher"', (user_id,))
        if cursor.rowcount > 0:
            conn.commit()
            return jsonify({'success': True, 'message': 'Access revoked successfully'})
        else:
            return jsonify({'success': False, 'message': 'Teacher not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

@app.route('/admin/delete_teacher/<int:user_id>', methods=['POST'])
def delete_teacher(user_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    if user_id == session['user_id']:
        return jsonify({'success': False, 'message': 'Cannot delete your own account'}), 400
    
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    try:
        # First, delete related verification requests
        cursor.execute('DELETE FROM verification_requests WHERE user_id = ?', (user_id,))
        
        # Update attendance records to set marked_by to NULL
        cursor.execute('UPDATE attendance SET marked_by = NULL WHERE marked_by = ?', (user_id,))
        
        # Finally, delete the user
        cursor.execute('DELETE FROM users WHERE id = ? AND role = "teacher"', (user_id,))
        
        if cursor.rowcount > 0:
            conn.commit()
            return jsonify({'success': True, 'message': 'Teacher deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'Teacher not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

@app.route('/api/students/<int:student_id>')
def api_get_student(student_id: int):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id, name, student_id, email, created_at FROM students WHERE id = ?', (student_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({'success': False, 'message': 'Student not found'}), 404

        student = {
            'id': row[0],
            'name': row[1],
            'studentId': row[2],
            'email': row[3] or '',
            'createdAt': row[4]
        }

        # Attendance stats
        cursor.execute('SELECT COUNT(*) FROM attendance WHERE student_id = ?', (student_id,))
        total_attendance = cursor.fetchone()[0]

        cursor.execute("""
            SELECT 
                SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END),
                SUM(CASE WHEN status = 'absent' THEN 1 ELSE 0 END),
                SUM(CASE WHEN status = 'late' THEN 1 ELSE 0 END)
            FROM attendance WHERE student_id = ?
        """, (student_id,))
        counts = cursor.fetchone()
        present_count = counts[0] or 0
        absent_count = counts[1] or 0
        late_count = counts[2] or 0

        cursor.execute('''
            SELECT date, time, status FROM attendance 
            WHERE student_id = ?
            ORDER BY date DESC, time DESC
            LIMIT 1
        ''', (student_id,))
        last_row = cursor.fetchone()
        last_attendance = None
        if last_row:
            last_attendance = {
                'date': last_row[0],
                'time': last_row[1],
                'status': last_row[2]
            }

        return jsonify({
            'success': True,
            'student': student,
            'stats': {
                'total': total_attendance,
                'present': present_count,
                'absent': absent_count,
                'late': late_count,
                'last': last_attendance
            }
        })
    finally:
        conn.close()

@app.route('/enroll', methods=['GET', 'POST'])
def enroll_student():
    if request.method == 'POST':
        name = request.form['name']
        student_id = request.form['student_id']
        email = request.form.get('email', '')
        
        # Handle image upload
        if 'photo' in request.files and request.files['photo'].filename:
            photo = request.files['photo']
            image = Image.open(photo.stream)
            image_array = np.array(image)
            
            # Convert to OpenCV format and detect faces
            image_cv = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            
            # Try multiple face detection methods for better accuracy
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            face_cascade_alt = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml')
            
            # Detect faces with different parameters
            faces1 = face_cascade.detectMultiScale(image_cv, 1.1, 4, minSize=(30, 30))
            faces2 = face_cascade_alt.detectMultiScale(image_cv, 1.1, 4, minSize=(30, 30))
            
            # Combine results and remove duplicates
            faces = list(faces1) + list(faces2)
            if len(faces) > 1:
                # Remove overlapping faces
                final_faces = []
                for face in faces:
                    x, y, w, h = face
                    is_duplicate = False
                    for existing_face in final_faces:
                        ex, ey, ew, eh = existing_face
                        # Check if faces overlap significantly
                        if (x < ex + ew and x + w > ex and 
                            y < ey + eh and y + h > ey):
                            is_duplicate = True
                            break
                    if not is_duplicate:
                        final_faces.append(face)
                faces = final_faces
            
            if len(faces) > 0:
                # Extract the first face and create a robust encoding
                (x, y, w, h) = faces[0]
                face_roi = image_cv[y:y+h, x:x+w]
                
                # Resize to standard size (same as recognition)
                face_resized = cv2.resize(face_roi, (128, 128))
                
                # Convert to grayscale
                face_gray = cv2.cvtColor(face_resized, cv2.COLOR_BGR2GRAY)
                
                # Apply preprocessing pipeline
                face_final = preprocess_face(face_gray)
                
                # Store the preprocessed face image directly
                face_encoding_blob = cv2.imencode('.png', face_final)[1].tobytes()
                
                print(f"Face processed for enrollment - Size: {face_final.shape}")
                
                conn = sqlite3.connect('attendance.db')
                cursor = conn.cursor()
                try:
                    cursor.execute('''
                        INSERT INTO students (name, student_id, email, face_encoding)
                        VALUES (?, ?, ?, ?)
                    ''', (name, student_id, email, face_encoding_blob))
                    conn.commit()
                    # Retrain face recognizer with new data
                    train_face_recognizer()
                    flash('Student enrolled successfully!', 'success')
                    return redirect(url_for('students'))
                except sqlite3.IntegrityError:
                    flash('Student ID already exists!', 'error')
                finally:
                    conn.close()
            else:
                flash('No face detected in the image. Please try again.', 'error')
        else:
            flash('Please upload a photo!', 'error')
    
    return render_template('enroll.html')

@app.route('/daily_attendance_report')
def daily_attendance_report():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    # Get today's date in ISO format
    today = datetime.now().date().isoformat()
    
    # Get all attendance records for today with student details
    cursor.execute('''
        SELECT s.name, s.student_id, a.time, a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE a.date = ?
        ORDER BY a.time ASC
    ''', (today,))
    attendance_records = cursor.fetchall()
    
    # Get total number of students
    cursor.execute('SELECT COUNT(*) FROM students')
    total_students = cursor.fetchone()[0]
    
    # Get count of present students
    cursor.execute('''
        SELECT COUNT(DISTINCT student_id) 
        FROM attendance 
        WHERE date = ?
    ''', (today,))
    present_students = cursor.fetchone()[0]
    
    conn.close()
    
    return render_template('daily_report.html',
                         attendance_records=attendance_records,
                         total_students=total_students,
                         present_students=present_students,
                         date=today)

@app.route('/mark_attendance', methods=['GET', 'POST'])
def mark_attendance():
    # Handle GET request - render the attendance page
    if request.method == 'GET':
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return render_template('mark_attendance.html')
    
    # Handle POST request - process attendance
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    # Check Content-Type header
    content_type = request.headers.get('Content-Type', '')
    if not content_type.startswith('application/json'):
        print(f"Invalid Content-Type: {content_type}")
        return jsonify({
            'success': False, 
            'message': 'Content-Type must be application/json',
            'received': content_type
        }), 415
    
    # Step 1: Get image data from request
    try:
        print("Processing attendance request...")
        
        # Get and validate request data
        data = request.get_json()
        if not data:
            print("Error: No JSON data in request")
            return jsonify({'success': False, 'message': 'No JSON data provided'}), 400
            
        if 'image_data' not in data:
            print("Error: No image_data in request")
            return jsonify({'success': False, 'message': 'No image data provided'}), 400
        
        # Parse and validate image data
        image_data = data['image_data']
        if not image_data:
            print("Error: Empty image data")
            return jsonify({'success': False, 'message': 'Empty image data provided'}), 400
            
        if not isinstance(image_data, str):
            print(f"Error: Invalid image data type: {type(image_data)}")
            return jsonify({'success': False, 'message': 'Invalid image data type'}), 400
            
        if not image_data.startswith('data:image/jpeg;base64,'):
            print("Error: Invalid image data format - missing expected prefix")
            return jsonify({'success': False, 'message': 'Invalid image data format - must be base64 encoded JPEG'}), 400
            
        # Extract and decode base64 image data
        try:
            image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
        except Exception as e:
            print(f"Error decoding base64 data: {e}")
            return jsonify({'success': False, 'message': 'Invalid base64 encoding'}), 400
            
        # Open and process image
        try:
            image = Image.open(io.BytesIO(image_bytes))
            image_array = np.array(image)
            image_cv = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            print(f"Image processed successfully. Shape: {image_array.shape}")
        except Exception as e:
            print(f"Error processing image: {e}")
            return jsonify({'success': False, 'message': f'Failed to process image: {str(e)}'}), 400
            
    except Exception as e:
        print(f"Unexpected error in image processing: {e}")
        return jsonify({'success': False, 'message': f'Internal server error while processing image: {str(e)}'}), 500
    
    # Step 2: Detect faces
    try:
        # Detect faces with different parameters and scales
        face_detected = False
        faces = []
        
        # Try different detection parameters
        scale_factors = [1.1, 1.05]  # More precise scaling
        min_neighbors_list = [3, 4, 5]  # Different neighbor thresholds
        
        for scale_factor in scale_factors:
            for min_neighbors in min_neighbors_list:
                # Try both cascade classifiers
                faces1 = face_cascade.detectMultiScale(
                    image_cv, 
                    scaleFactor=scale_factor,
                    minNeighbors=min_neighbors,
                    minSize=(60, 60)  # Increased minimum face size
                )
                
                faces2 = face_cascade_alt.detectMultiScale(
                    image_cv,
                    scaleFactor=scale_factor,
                    minNeighbors=min_neighbors,
                    minSize=(60, 60)
                )
                
                current_faces = list(faces1) + list(faces2)
                if len(current_faces) > 0:
                    faces.extend(current_faces)
                    face_detected = True
                    print(f"Face detected with scale={scale_factor}, neighbors={min_neighbors}")
                    break
            if face_detected:
                break
        
        # Handle multiple faces by removing overlapping detections
        if len(faces) > 1:
            final_faces = []
            for face in faces:
                x, y, w, h = face
                is_duplicate = False
                for existing_face in final_faces:
                    ex, ey, ew, eh = existing_face
                    # Check for significant overlap (more than 50%)
                    intersection_width = min(x + w, ex + ew) - max(x, ex)
                    intersection_height = min(y + h, ey + eh) - max(y, ey)
                    if intersection_width > 0 and intersection_height > 0:
                        overlap_area = intersection_width * intersection_height
                        min_area = min(w * h, ew * eh)
                        if overlap_area > 0.5 * min_area:  # 50% overlap threshold
                            is_duplicate = True
                            break
                if not is_duplicate:
                    final_faces.append(face)
            faces = final_faces
            print(f"Found {len(faces)} unique faces after overlap removal")
        
        if not faces:
            return jsonify({'success': False, 'message': 'No face detected in the image'}), 400
            
        # Process first detected face
        x, y, w, h = faces[0]
        face_roi = image_cv[y:y+h, x:x+w]
        
        # Apply preprocessing steps
        try:
            # 1. Resize to standard size
            face_resized = cv2.resize(face_roi, (128, 128))
            
            # 2. Convert to grayscale and preprocess
            face_gray = cv2.cvtColor(face_resized, cv2.COLOR_BGR2GRAY)
            face_adjusted = preprocess_face(face_gray)
            
            print("Face preprocessing completed successfully")
            
        except Exception as e:
            print(f"Error during face preprocessing: {e}")
            return jsonify({'success': False, 'message': 'Error processing face image'}), 400
        
        # Check if face recognizer is trained
        if not face_recognizer_trained:
            train_face_recognizer()
            
        if not face_recognizer_trained:
            return jsonify({'success': False, 'message': 'Face recognition system is not ready'}), 503
            
        # Predict face using LBPH recognizer
        try:
            label, confidence = face_recognizer.predict(face_adjusted)
            print(f"Recognition result - Label: {label}, Confidence: {confidence}")
            
            # Convert confidence to similarity score (LBPH returns distance, lower is better)
            similarity_score = 1 - min(confidence / 100.0, 1.0)
            print(f"Calculated similarity score: {similarity_score}")
            
            # Use extremely permissive threshold for initial testing
            if similarity_score < 0.1:  # Very permissive matching for testing
                # Get the number of enrolled students and debugging info
                conn = sqlite3.connect('attendance.db')
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM students')
                student_count = cursor.fetchone()[0]
                print(f"Recognition debug - Similarity: {similarity_score:.2f}, Confidence: {confidence:.2f}")
                conn.close()
                
                return jsonify({
                    'success': False, 
                    'message': f'Face not recognized. Confidence too low: {similarity_score:.2f}. Total enrolled students: {student_count}'
                }), 400
                
        except Exception as e:
            print(f"Error during face recognition: {e}")
            return jsonify({'success': False, 'message': 'Error during face recognition'}), 500
            
        # Get student details and mark attendance
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT id, name, student_id FROM students WHERE id = ?', (label,))
            student = cursor.fetchone()
            
            if not student:
                return jsonify({'success': False, 'message': 'Student not found'}), 404
            
            # Check if already marked today using ISO format date
            current_date = datetime.now().date().isoformat()
            cursor.execute('''
                SELECT * FROM attendance 
                WHERE student_id = ? AND date = ?
            ''', (student[0], current_date))
            
            if cursor.fetchone():
                return jsonify({
                    'success': False, 
                    'message': f'{student[1]} already marked present today'
                }), 400
            
            # Convert date and time to strings for SQLite
            current_date = datetime.now().date().isoformat()
            current_time = datetime.now().time().strftime('%H:%M:%S')
            
            # Mark attendance
            cursor.execute('''
                INSERT INTO attendance (student_id, date, time, marked_by)
                VALUES (?, ?, ?, ?)
            ''', (student[0], current_date, current_time, session['user_id']))
            
            conn.commit()
            return jsonify({
                'success': True,
                'message': f'Attendance marked for {student[1]} ({student[2]})'
            })
            
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error processing face: {str(e)}'
        }), 500

@app.route('/reset_attendance', methods=['POST'])
def reset_attendance():
    """Reset today's attendance - allows re-marking attendance"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        reset_type = data.get('type', 'all')  # 'all' or 'student'
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        current_date = datetime.now().date().isoformat()
        
        if reset_type == 'all':
            # Clear all attendance for today
            cursor.execute('DELETE FROM attendance WHERE date = ?', (current_date,))
            deleted_count = cursor.rowcount
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': f'Cleared {deleted_count} attendance records for today. You can now mark attendance again.'
            })
            
        elif reset_type == 'student':
            # Clear attendance for specific student today
            student_name = data.get('student_name', '')
            if not student_name:
                return jsonify({'success': False, 'message': 'Student name required'}), 400
            
            # Find student by name
            cursor.execute('SELECT id, name FROM students WHERE name LIKE ?', (f'%{student_name}%',))
            student = cursor.fetchone()
            
            if not student:
                return jsonify({'success': False, 'message': f'Student "{student_name}" not found'}), 404
            
            # Delete attendance for this student today
            cursor.execute('DELETE FROM attendance WHERE student_id = ? AND date = ?', (student[0], current_date))
            deleted_count = cursor.rowcount
            conn.commit()
            
            if deleted_count > 0:
                return jsonify({
                    'success': True,
                    'message': f'Cleared attendance for {student[1]} today. You can now mark their attendance again.'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f'{student[1]} has no attendance record for today to clear.'
                })
        
        else:
            return jsonify({'success': False, 'message': 'Invalid reset type'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error resetting attendance: {str(e)}'}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/admin/approve/<int:request_id>', methods=['POST'])
def approve_teacher_request(request_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    try:
        # Get the verification request
        cursor.execute('''
            SELECT vr.user_id FROM verification_requests vr
            WHERE vr.id = ? AND vr.status = 'pending'
        ''', (request_id,))
        request_data = cursor.fetchone()
        
        if request_data:
            user_id = request_data[0]
            # Update user verification status
            cursor.execute('UPDATE users SET is_verified = 1 WHERE id = ?', (user_id,))
            # Update request status
            cursor.execute('UPDATE verification_requests SET status = "approved" WHERE id = ?', (request_id,))
            conn.commit()
            return jsonify({'success': True, 'message': 'Teacher approved successfully'})
        else:
            return jsonify({'success': False, 'message': 'Request not found or already processed'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

@app.route('/admin/reject/<int:request_id>', methods=['POST'])
def reject_teacher_request(request_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('UPDATE verification_requests SET status = "rejected" WHERE id = ? AND status = "pending"', (request_id,))
        if cursor.rowcount > 0:
            conn.commit()
            return jsonify({'success': True, 'message': 'Teacher request rejected'})
        else:
            return jsonify({'success': False, 'message': 'Request not found or already processed'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

@app.route('/delete_student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    try:
        # Delete attendance records first (foreign key constraint)
        cursor.execute('DELETE FROM attendance WHERE student_id = ?', (student_id,))
        # Delete student
        cursor.execute('DELETE FROM students WHERE id = ?', (student_id,))
        
        if cursor.rowcount > 0:
            conn.commit()
            return jsonify({'success': True, 'message': 'Student deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'Student not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    train_face_recognizer()  # Train the recognizer with existing data
    app.run(debug=True, host='0.0.0.0', port=5000)
