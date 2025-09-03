// Global variables
let currentStream = null;
let isProcessing = false;

// Dark mode functionality
class ThemeManager {
    constructor() {
        this.init();
    }

    init() {
        // Get saved theme or default to light
        const savedTheme = localStorage.getItem('theme') || 'light';
        this.setTheme(savedTheme);
        
        // Set up toggle button
        const toggleButton = document.getElementById('themeToggle');
        if (toggleButton) {
            toggleButton.addEventListener('click', () => this.toggleTheme());
        }
    }

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        
        // Update icon
        const icon = document.getElementById('themeIcon');
        if (icon) {
            icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
        
        // Update toggle button title
        const toggleButton = document.getElementById('themeToggle');
        if (toggleButton) {
            toggleButton.title = theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';
        }
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
        
        // Show notification
        showNotification(`Switched to ${newTheme} mode`, 'success');
    }

    getCurrentTheme() {
        return document.documentElement.getAttribute('data-theme') || 'light';
    }
}

// Initialize theme manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
});

// Utility functions
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-triangle' : 'info-circle'}"></i>
        ${message}
        <button class="alert-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    const flashContainer = document.querySelector('.flash-messages') || createFlashContainer();
    flashContainer.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

function createFlashContainer() {
    const container = document.createElement('div');
    container.className = 'flash-messages';
    document.querySelector('.main-content').prepend(container);
    return container;
}

// Camera functions
async function initializeCamera(videoElement, constraints = {}) {
    try {
        const defaultConstraints = {
            video: {
                width: { ideal: 640 },
                height: { ideal: 480 },
                facingMode: 'user'
            }
        };
        
        const finalConstraints = { ...defaultConstraints, ...constraints };
        currentStream = await navigator.mediaDevices.getUserMedia(finalConstraints);
        videoElement.srcObject = currentStream;
        
        return true;
    } catch (error) {
        console.error('Camera initialization failed:', error);
        showNotification('Failed to access camera: ' + error.message, 'error');
        return false;
    }
}

function stopCamera() {
    if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
        currentStream = null;
    }
}

function captureImageFromVideo(videoElement, canvasElement) {
    const context = canvasElement.getContext('2d');
    canvasElement.width = videoElement.videoWidth;
    canvasElement.height = videoElement.videoHeight;
    context.drawImage(videoElement, 0, 0);
    return canvasElement.toDataURL('image/jpeg', 0.8);
}

// Form validation
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validateForm(formElement) {
    const inputs = formElement.querySelectorAll('input[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('error');
            isValid = false;
        } else {
            input.classList.remove('error');
        }
        
        if (input.type === 'email' && input.value && !validateEmail(input.value)) {
            input.classList.add('error');
            isValid = false;
        }
    });
    
    return isValid;
}

// API functions
async function makeRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Request failed:', error);
        throw error;
    }
}

// Face recognition functions
function preprocessImage(imageData) {
    // Basic image preprocessing
    return imageData;
}

async function submitAttendance(imageData) {
    if (isProcessing) return;
    
    isProcessing = true;
    
    try {
        const response = await fetch('/mark_attendance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                image_data: imageData
            })
        });
        
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Attendance submission failed:', error);
        throw error;
    } finally {
        isProcessing = false;
    }
}

// UI Enhancement functions
function addLoadingState(element) {
    element.disabled = true;
    element.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
}

function removeLoadingState(element, originalText) {
    element.disabled = false;
    element.innerHTML = originalText;
}

function animateElement(element, animationClass, duration = 1000) {
    element.classList.add(animationClass);
    setTimeout(() => {
        element.classList.remove(animationClass);
    }, duration);
}

// Cool Animation Functions
function createRippleEffect(event) {
    const button = event.currentTarget;
    const ripple = document.createElement('span');
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;
    
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';
    ripple.classList.add('ripple');
    
    button.appendChild(ripple);
    
    setTimeout(() => {
        ripple.remove();
    }, 600);
}

function showSuccessAnimation(element) {
    const checkmark = document.createElement('div');
    checkmark.innerHTML = `
        <svg class="success-checkmark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
            <circle class="success-checkmark__circle" cx="26" cy="26" r="25" fill="none"/>
            <path class="success-checkmark__check" fill="none" d="m14.1 27.2l7.1 7.2 16.7-16.8"/>
        </svg>
    `;
    
    element.appendChild(checkmark);
    
    setTimeout(() => {
        checkmark.remove();
    }, 2000);
}

function typeWriter(element, text, speed = 50) {
    element.innerHTML = '';
    let i = 0;
    
    function type() {
        if (i < text.length) {
            element.innerHTML += text.charAt(i);
            i++;
            setTimeout(type, speed);
        }
    }
    
    type();
}

function createFloatingNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `floating-notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-triangle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Add to notification container
    let container = document.querySelector('.notification-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'notification-container';
        document.body.appendChild(container);
    }
    
    container.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Auto remove
    setTimeout(() => {
        notification.classList.add('hide');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, duration);
}

function createProgressBar(container, progress = 0) {
    const progressBar = document.createElement('div');
    progressBar.className = 'progress-bar';
    progressBar.innerHTML = `<div class="progress-fill" style="width: ${progress}%"></div>`;
    
    container.appendChild(progressBar);
    return progressBar;
}

function updateProgress(progressBar, newProgress) {
    const fill = progressBar.querySelector('.progress-fill');
    fill.style.width = newProgress + '%';
}

function createLoadingOverlay(message = 'Loading...') {
    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.innerHTML = `
        <div class="loading-content">
            <div class="loading-spinner"></div>
            <p>${message}</p>
        </div>
    `;
    
    document.body.appendChild(overlay);
    return overlay;
}

function removeLoadingOverlay() {
    const overlay = document.querySelector('.loading-overlay');
    if (overlay) {
        overlay.classList.add('fade-out');
        setTimeout(() => {
            overlay.remove();
        }, 300);
    }
}

// Face Recognition Animation
function startFaceRecognitionAnimation(videoContainer) {
    const overlay = document.createElement('div');
    overlay.className = 'face-scan-overlay';
    overlay.innerHTML = '<div class="face-scan-line"></div>';
    
    videoContainer.style.position = 'relative';
    videoContainer.appendChild(overlay);
    
    return overlay;
}

function stopFaceRecognitionAnimation(videoContainer) {
    const overlay = videoContainer.querySelector('.face-scan-overlay');
    if (overlay) {
        overlay.remove();
    }
}

// Particle Effect for Success
function createParticleExplosion(x, y) {
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];
    
    for (let i = 0; i < 15; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.cssText = `
            position: fixed;
            width: 6px;
            height: 6px;
            background: ${colors[Math.floor(Math.random() * colors.length)]};
            border-radius: 50%;
            left: ${x}px;
            top: ${y}px;
            pointer-events: none;
            z-index: 9999;
        `;
        
        document.body.appendChild(particle);
        
        const angle = (Math.PI * 2 * i) / 15;
        const velocity = 100 + Math.random() * 100;
        const vx = Math.cos(angle) * velocity;
        const vy = Math.sin(angle) * velocity;
        
        let posX = x;
        let posY = y;
        let opacity = 1;
        
        const animate = () => {
            posX += vx * 0.02;
            posY += vy * 0.02 + 2; // gravity
            opacity -= 0.02;
            
            particle.style.left = posX + 'px';
            particle.style.top = posY + 'px';
            particle.style.opacity = opacity;
            
            if (opacity > 0) {
                requestAnimationFrame(animate);
            } else {
                particle.remove();
            }
        };
        
        requestAnimationFrame(animate);
    }
}

// Event listeners for common elements
document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide flash messages
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.parentElement) {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 300);
            }
        }, 5000);
    });
    
    // Form validation on submit
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(form)) {
                e.preventDefault();
                showNotification('Please fill in all required fields correctly.', 'error');
            }
        });
    });
    
    // Enhanced button interactions
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            animateElement(this, 'pulse');
        });
    });
    
    // Cleanup camera on page unload
    window.addEventListener('beforeunload', function() {
        stopCamera();
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Escape key to close modals
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal[style*="flex"]');
            modals.forEach(modal => {
                modal.style.display = 'none';
            });
        }
        
        // Ctrl+Enter to submit forms
        if (e.ctrlKey && e.key === 'Enter') {
            const activeForm = document.querySelector('form:focus-within');
            if (activeForm) {
                activeForm.submit();
            }
        }
    });
});

// Attendance marking specific functions
function initializeAttendanceMarking() {
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const startBtn = document.getElementById('start-camera');
    const captureBtn = document.getElementById('capture-btn');
    const stopBtn = document.getElementById('stop-camera');
    
    if (!video || !canvas) return;
    
    startBtn?.addEventListener('click', async function() {
        const success = await initializeCamera(video);
        if (success) {
            startBtn.style.display = 'none';
            captureBtn.style.display = 'inline-block';
            stopBtn.style.display = 'inline-block';
        }
    });
    
    captureBtn?.addEventListener('click', async function() {
        if (isProcessing) return;
        
        const originalText = captureBtn.innerHTML;
        addLoadingState(captureBtn);
        
        try {
            const imageData = captureImageFromVideo(video, canvas);
            const result = await submitAttendance(imageData);
            
            if (result.success) {
                showNotification(result.message, 'success');
                updateAttendanceCount();
            } else {
                showNotification(result.message, 'error');
            }
        } catch (error) {
            showNotification('Failed to process attendance: ' + error.message, 'error');
        } finally {
            removeLoadingState(captureBtn, originalText);
        }
    });
    
    stopBtn?.addEventListener('click', function() {
        stopCamera();
        startBtn.style.display = 'inline-block';
        captureBtn.style.display = 'none';
        stopBtn.style.display = 'none';
    });
}

function updateAttendanceCount() {
    const countElement = document.getElementById('attendance-count');
    if (countElement) {
        const currentCount = parseInt(countElement.textContent) || 0;
        countElement.textContent = currentCount + 1;
        animateElement(countElement, 'pulse');
    }
}

// Student enrollment specific functions
function initializeStudentEnrollment() {
    const photoInput = document.getElementById('photo');
    const previewSection = document.getElementById('photo-preview');
    const previewImage = document.getElementById('preview-image');
    
    photoInput?.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                previewImage.src = e.target.result;
                previewSection.style.display = 'block';
                animateElement(previewSection, 'fadeIn');
            };
            reader.readAsDataURL(file);
        }
    });
}

// Dashboard specific functions
function initializeDashboard() {
    // Real-time clock update
    function updateClock() {
        const clockElement = document.getElementById('current-time');
        if (clockElement) {
            const now = new Date();
            clockElement.textContent = now.toLocaleTimeString();
        }
    }
    
    setInterval(updateClock, 1000);
    updateClock();
    
    // Auto-refresh dashboard data every 5 minutes
    setInterval(function() {
        if (document.querySelector('.dashboard-container')) {
            location.reload();
        }
    }, 300000);
}

// Initialize page-specific functionality
function initializePage() {
    const currentPage = window.location.pathname;
    
    switch (currentPage) {
        case '/mark_attendance':
            initializeAttendanceMarking();
            break;
        case '/enroll':
            initializeStudentEnrollment();
            break;
        case '/dashboard':
        case '/admin/dashboard':
        case '/teacher/dashboard':
            initializeDashboard();
            break;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initializePage);

// Export functions for global use
window.AttendanceSystem = {
    showNotification,
    initializeCamera,
    stopCamera,
    validateForm,
    makeRequest
};
