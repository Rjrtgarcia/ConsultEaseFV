# ConsultEase

A comprehensive system for enhanced student-faculty interaction, featuring RFID-based authentication, real-time faculty availability, and streamlined consultation requests.

## Components

### Central System (Raspberry Pi)
- PyQt5 user interface for student interaction
- RFID-based authentication
- Real-time faculty availability display
- Consultation request management with improved UI
- Secure admin interface with automatic login account management
- Touch-optimized UI
- Smooth UI transitions and animations
- Integrated admin account creation and repair
- Real-time system monitoring and health checks
- Comprehensive audit logging for security compliance

### Faculty Desk Unit (ESP32)
- 2.4" TFT Display for consultation requests
- BLE-based presence detection (configurable always-available mode)
- MQTT communication with Central System
- Real-time status updates
- Improved reliability and error handling

## Requirements

### Central System
- Raspberry Pi 4 (Bookworm 64-bit)
- 10.1-inch touchscreen (1024x600 resolution)
- USB RFID IC Reader
- USB Keyboard
- Python 3.9+
- PostgreSQL database

### Faculty Desk Unit
- ESP32 microcontroller
- 2.4-inch TFT SPI Screen (ST7789)
- Arduino IDE 2.0+

## Installation

### Central System

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up PostgreSQL database:
```bash
# Create database and user
sudo -u postgres psql -c "CREATE DATABASE consultease;"
sudo -u postgres psql -c "CREATE USER piuser WITH PASSWORD 'password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE consultease TO piuser;"
```

3. Calibrate the touchscreen (if needed):
```bash
sudo chmod +x scripts/calibrate_touch.sh
sudo ./scripts/calibrate_touch.sh
```

4. Enable fullscreen mode (for deployment):
```bash
python scripts/enable_fullscreen.py
```

5. Run the application:
```bash
python central_system/main.py
```

## Admin Access

ConsultEase includes an enhanced admin account management system that ensures users can always gain admin access through multiple fallback mechanisms.

### Enhanced Admin Account Management

The system provides **multiple layers** of admin account management:

1. **Automatic Database Creation** - Creates default admin during database initialization
2. **First-Time Setup Dialog** - User-friendly account creation if no accounts exist
3. **Manual Login** - Traditional login with enhanced error handling
4. **Emergency Repair** - Automatic repair of corrupted accounts

### First-Time Setup Experience

When no admin accounts exist, the system automatically displays a **user-friendly setup dialog**:

#### Features:
- 🖥️ **Touch-Optimized Interface** - Designed for Raspberry Pi touchscreen
- 🔒 **Real-Time Password Validation** - Visual feedback on password requirements
- ✅ **Instant Verification** - Username uniqueness and strength checking
- 🎯 **Auto-Login** - Automatic login after successful account creation

#### Password Requirements:
- ✅ At least 8 characters long
- ✅ Contains uppercase letters (A-Z)
- ✅ Contains lowercase letters (a-z)
- ✅ Contains numbers (0-9)
- ✅ Contains special characters (!@#$%^&*)
- ✅ Passwords must match

### Accessing the Admin Dashboard

#### Option 1: First-Time Setup (No Admin Accounts)
1. **Start the application**
2. **Click "Admin Login"** button
3. **Follow the first-time setup dialog** (appears automatically)
4. **Create your admin account** with a secure password
5. **Automatically login** to the admin dashboard

#### Option 2: Existing Admin Account
1. **Start the application**
2. **Click "Admin Login"** button
3. **Enter your credentials**
4. **Access the admin dashboard**

#### Option 3: Default Admin (Fallback)
If automatic systems create a default admin:
```
Username: admin
Password: TempPass123!
```
**Note:** This password must be changed on first login for security.

### Admin Account Features

#### Multi-Layer Security:
- ✅ **Strong Password Requirements** - Enforced complexity rules
- ✅ **Secure Password Storage** - bcrypt hashing with salt
- ✅ **Account Validation** - Real-time username and password checking
- ✅ **Audit Logging** - Complete audit trail of all admin operations

#### User Experience:
- ✅ **Touch-Friendly Interface** - Optimized for touchscreen devices
- ✅ **Clear Visual Feedback** - Real-time validation indicators
- ✅ **Intuitive Setup Process** - Step-by-step guidance
- ✅ **Error Recovery** - Multiple fallback mechanisms

#### System Reliability:
- ✅ **Automatic Creation** - Admin accounts created automatically when needed
- ✅ **Self-Repair** - System fixes broken admin accounts during startup
- ✅ **Multiple Fallbacks** - Several methods ensure admin access is always possible
- ✅ **Zero Configuration** - Works out of the box without manual setup

### Faculty Desk Unit

1. Install the Arduino IDE and required libraries:
   - TFT_eSPI
   - NimBLE-Arduino
   - PubSubClient
   - ArduinoJson

2. Configure TFT_eSPI for your display

3. Update the configuration in `faculty_desk_unit/config.h`:
   - Set the faculty ID and name
   - Configure WiFi credentials
   - Set MQTT broker IP address
   - Configure BLE settings (including always-on option)

4. Upload the sketch to your ESP32

## Project Structure
```
consultease/
├── central_system/           # Raspberry Pi application
│   ├── models/               # Database models
│   ├── views/                # PyQt UI components
│   ├── controllers/          # Application logic
│   ├── services/             # External services (MQTT, RFID)
│   ├── resources/            # UI resources (icons, stylesheets)
│   └── utils/                # Utility functions
├── faculty_desk_unit/        # ESP32 firmware
│   ├── faculty_desk_unit.ino # Main firmware file
│   ├── config.h              # Configuration file
│   └── config_templates/     # Configuration templates
├── scripts/                  # Utility scripts
│   ├── calibrate_touch.sh    # Touchscreen calibration utility
│   ├── enable_fullscreen.py  # Enable fullscreen for deployment
│   ├── deploy_production.sh  # Production deployment script
│   └── start_consultease.sh  # Service startup script
└── docs/                     # Documentation
    ├── deployment_guide.md   # Comprehensive deployment guide
    ├── quick_start_guide.md  # Quick start instructions
    ├── user_manual.md        # User manual
```

## Touchscreen Features

ConsultEase includes several features to enhance usability on touchscreen devices:

- **Fullscreen mode**: Optimized for touchscreen deployment with full screen utilization
- **Touch calibration**: Tools to ensure accurate touch input recognition
- **Touch-friendly UI**: Larger buttons and input elements optimized for touch interaction

## Deployment

For a comprehensive deployment guide, see the [Deployment Guide](COMPREHENSIVE_DEPLOYMENT_GUIDE.md) file.