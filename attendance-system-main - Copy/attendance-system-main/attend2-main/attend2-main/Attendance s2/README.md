# Attendance Management System with Face Recognition

A comprehensive web-based attendance management system that utilizes face recognition technology to record attendance for students and employees without relying on external APIs.

## Features

### 🎓 Student Management
- **Photo Upload/Capture**: Students can enroll by uploading a photo or capturing their face directly through the web interface
- **Face Recognition**: Local face recognition using open-source libraries (no external APIs required)
- **Student Database**: Secure storage of student information and facial encodings

### 🔐 Authentication & Security
- **Role-based Access Control**: Separate access levels for Admin and Teachers
- **Email Verification**: Teachers require admin approval via email verification
- **Secure Login**: Password hashing and session management
- **Data Privacy**: Facial data stored securely with encryption

### 👨‍🏫 Admin Features
- **Teacher Verification**: Approve or reject teacher registration requests
- **Student Management**: Add, view, and manage enrolled students
- **System Oversight**: Monitor attendance statistics and system usage
- **Dashboard**: Comprehensive admin dashboard with real-time statistics

### 👩‍🏫 Teacher Features
- **Attendance Marking**: Use camera to mark student attendance via face recognition
- **Dashboard**: View daily attendance records and statistics
- **Student Access**: View enrolled students and their information

### 🎨 User Interface
- **Modern Design**: Clean, responsive UI with PT Sans typography
- **Real-time Feedback**: Clear notifications and status updates
- **Camera Integration**: Seamless camera access for photo capture
- **Animations**: Subtle transitions and feedback animations

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Face Recognition**: face_recognition library (dlib-based)
- **Frontend**: HTML5, CSS3, JavaScript
- **Camera**: WebRTC getUserMedia API
- **Email**: SMTP integration
- **Authentication**: bcrypt password hashing

## Installation

### Prerequisites
- Python 3.7 or higher
- Webcam/Camera access
- SMTP email account (for teacher verification)

### Setup Instructions

1. **Clone or Download the Project**
   ```bash
   cd "Attendance s2"
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   Edit the `.env` file with your email settings:
   ```env
   SECRET_KEY=your-secret-key-change-this-to-something-secure
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   EMAIL_ADDRESS=your-email@gmail.com
   EMAIL_PASSWORD=your-app-password
   ADMIN_EMAIL=admin@school.com
   ```

4. **Run the Application**
   ```bash
   python app.py
   ```

5. **Access the System**
   Open your browser and navigate to: `http://localhost:5000`

## Default Login Credentials

- **Admin Account**:
  - Username: `admin`
  - Password: `admin123`

## Usage Guide

### For Administrators

1. **Login** with admin credentials
2. **Manage Teachers**: 
   - Review teacher registration requests
   - Approve or reject verification requests via email notifications
3. **Enroll Students**:
   - Add new students with photo upload or camera capture
   - System automatically extracts facial features for recognition
4. **Monitor System**: View attendance statistics and system usage

### For Teachers

1. **Register** a new teacher account
2. **Wait for Approval**: Admin will receive email notification and approve access
3. **Login** after approval
4. **Mark Attendance**:
   - Start camera
   - Position student's face in frame
   - System automatically recognizes and marks attendance
5. **View Records**: Monitor daily attendance and student statistics

### For Students

1. **Enrollment**: Admin or teacher enrolls student with photo
2. **Attendance**: Simply position face in front of camera when teacher marks attendance
3. **Recognition**: System instantly recognizes and records attendance

## System Architecture

### Database Schema

- **students**: Student information and facial encodings
- **users**: Admin and teacher accounts with roles
- **attendance**: Daily attendance records
- **verification_requests**: Teacher approval workflow

### Security Features

- Password hashing with bcrypt
- Session-based authentication
- Role-based access control
- Secure facial data storage
- CSRF protection

### Face Recognition Process

1. **Enrollment**: Extract facial encoding from uploaded/captured photo
2. **Storage**: Store encoding as binary data in database
3. **Recognition**: Compare live camera feed with stored encodings
4. **Matching**: Use tolerance-based matching for accurate recognition
5. **Recording**: Log attendance with timestamp and teacher information

## API Endpoints

### Authentication
- `POST /login` - User login
- `POST /register` - Teacher registration
- `GET /logout` - User logout

### Student Management
- `GET /students` - List all students
- `POST /enroll` - Enroll new student
- `POST /delete_student/<id>` - Delete student (admin only)

### Attendance
- `GET /mark_attendance` - Attendance marking interface
- `POST /mark_attendance` - Process face recognition and mark attendance

### Admin Functions
- `GET /admin/dashboard` - Admin dashboard
- `POST /admin/approve/<id>` - Approve teacher verification
- `POST /admin/reject/<id>` - Reject teacher verification

## Configuration

### Email Settings
Configure SMTP settings in `.env` file for teacher verification emails:
- Gmail: Use app-specific passwords
- Outlook: Enable SMTP access
- Custom SMTP: Configure server and port

### Camera Settings
- Default resolution: 640x480
- Face detection tolerance: 0.6
- Supported formats: JPEG, PNG, GIF

### Security Settings
- Session timeout: Browser session
- Password requirements: Minimum 6 characters
- Face encoding: 128-dimensional vector

## Troubleshooting

### Common Issues

1. **Camera Access Denied**
   - Ensure browser has camera permissions
   - Check if camera is being used by another application

2. **Face Recognition Not Working**
   - Ensure good lighting conditions
   - Face should be clearly visible and centered
   - Remove sunglasses or face coverings

3. **Email Verification Not Sending**
   - Check SMTP settings in `.env` file
   - Verify email credentials and app passwords
   - Check spam/junk folders

4. **Installation Issues**
   - Install Visual Studio Build Tools for Windows
   - Use conda environment for easier dlib installation
   - Check Python version compatibility

### Performance Optimization

- Use SSD storage for faster database operations
- Ensure adequate RAM for face recognition processing
- Use modern browser with WebRTC support
- Optimize camera resolution based on hardware

## Development

### Project Structure
```
attendance-system/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env                  # Environment configuration
├── attendance.db         # SQLite database (auto-created)
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── admin_dashboard.html
│   ├── teacher_dashboard.html
│   ├── enroll.html
│   ├── mark_attendance.html
│   └── students.html
└── static/              # CSS and JavaScript files
    ├── style.css
    └── script.js
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open-source and available under the MIT License.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the configuration settings
3. Ensure all dependencies are properly installed
4. Verify camera and email permissions

## Future Enhancements

- Mobile app integration
- Advanced reporting and analytics
- Multi-camera support
- Cloud storage integration
- Bulk student import
- Attendance reports export
- Real-time notifications
- Advanced face recognition algorithms
