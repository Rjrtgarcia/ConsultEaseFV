# ConsultEase Comprehensive Deployment Guide

## Overview
This guide provides complete instructions for deploying the ConsultEase system on a Raspberry Pi production environment.

## 🚀 SYSTEM IMPROVEMENTS SUMMARY

### Phase 1: Critical Security & Stability ✅
- Enhanced admin authentication with secure password hashing
- Comprehensive input validation and SQL injection prevention
- Secure session management and audit logging
- Database connection resilience and error handling

### Phase 2: Performance & Reliability ✅
- Asynchronous MQTT service for improved responsiveness
- Connection pooling and caching mechanisms
- UI performance optimizations and memory management
- Enhanced error handling and recovery procedures

### Phase 3: Code Quality & UX ✅
- Consistent UI styling and accessibility features
- Enhanced user feedback systems and loading states
- Code refactoring and standardized error handling
- Comprehensive accessibility support (WCAG 2.1 AA)

### Phase 4: System Integration ✅
- System coordinator for service lifecycle management
- Enhanced MQTT message routing and processing
- Database manager with advanced connection pooling
- Comprehensive system health monitoring

## 📋 PREREQUISITES

### Hardware Requirements
- Raspberry Pi 4 (4GB RAM recommended)
- 32GB+ microSD card (Class 10 or better)
- 10.1" touchscreen display
- USB RFID reader
- USB Keyboard
- Stable internet connection
- 5 nRF51822 BLE beacons (for faculty presence detection)
- 5 ESP32 development boards (for faculty desk units)

### Software Requirements
- Raspberry Pi OS (Bookworm 64-bit)
- Python 3.9+
- PostgreSQL 13+
- Mosquitto MQTT broker
- Git

## 🔧 INSTALLATION STEPS

### Step 1: System Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv git postgresql mosquitto mosquitto-clients

# Install PyQt5 dependencies
sudo apt install -y python3-pyqt5 python3-pyqt5.qtcore python3-pyqt5.qtgui python3-pyqt5.qtwidgets

# Install system monitoring tools
sudo apt install -y htop iotop nethogs
```

### Step 2: Database Setup
```bash
# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres createdb consultease
sudo -u postgres createuser consultease_user
sudo -u postgres psql -c "ALTER USER consultease_user WITH PASSWORD 'secure_db_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE consultease TO consultease_user;"
```

### Step 3: MQTT Broker Configuration
```bash
# Create MQTT configuration
sudo tee /etc/mosquitto/conf.d/consultease.conf << EOF
listener 1883
allow_anonymous false
password_file /etc/mosquitto/passwd
EOF

# Create MQTT user
sudo mosquitto_passwd -c /etc/mosquitto/passwd consultease_user
# Enter password: consultease_secure_password

# Restart mosquitto
sudo systemctl restart mosquitto
sudo systemctl enable mosquitto
```

### Step 4: ConsultEase Installation
```bash
# Clone repository
cd /home/pi
git clone https://github.com/your-repo/ConsultEase.git
cd ConsultEase

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Set permissions
chmod +x scripts/*.sh
```

### Step 5: Configuration
```bash
# Create configuration file
cp central_system/config_template.json central_system/config.json

# Edit configuration (update database and MQTT settings)
nano central_system/config.json
```

Example configuration:
```json
{
    "database": {
        "type": "postgresql",
        "host": "localhost",
        "port": 5432,
        "name": "consultease",
        "user": "consultease_user",
        "password": "secure_db_password",
        "pool_size": 5,
        "max_overflow": 10
    },
    "mqtt": {
        "broker_host": "localhost",
        "broker_port": 1883,
        "username": "consultease_user",
        "password": "consultease_secure_password"
    },
    "ui": {
        "fullscreen": true,
        "theme": "default"
    }
}
```

### Step 6: Database Initialization
```bash
# Initialize database
source venv/bin/activate
python3 -c "from central_system.models.base import init_db; init_db()"
```

### Step 7: Service Installation
```bash
# Copy service file
sudo cp scripts/consultease.service /etc/systemd/system/

# Update service file with correct paths
sudo sed -i "s|/home/pi/ConsultEase|$(pwd)|g" /etc/systemd/system/consultease.service

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable consultease
```

### Step 8: Touchscreen Configuration
```bash
# Make calibration script executable
chmod +x scripts/calibrate_touch.sh

# Run calibration
./scripts/calibrate_touch.sh
```

### Step 9: Enable Fullscreen Mode
```bash
# Enable fullscreen for deployment
python scripts/enable_fullscreen.py
```

### Step 10: Start the Service
```bash
# Start ConsultEase service
sudo systemctl start consultease

# Check status
sudo systemctl status consultease
```

## 🔍 SYSTEM VERIFICATION

### Health Check Commands
```bash
# Check system services
sudo systemctl status postgresql mosquitto consultease

# Check logs
sudo journalctl -u consultease -f
```

## 📱 FACULTY DESK UNIT SETUP

### Step 1: Prepare Arduino IDE
1. Install Arduino IDE 2.0+
2. Add ESP32 board support via Boards Manager
3. Install required libraries:
   - TFT_eSPI
   - NimBLE-Arduino
   - PubSubClient
   - ArduinoJson

### Step 2: Configure TFT_eSPI
1. Edit User_Setup.h in TFT_eSPI library folder
2. Enable ST7789 display and set correct pins

### Step 3: Configure Faculty Desk Unit
1. Open faculty_desk_unit/faculty_desk_unit.ino in Arduino IDE
2. Copy config_production_template.h to config.h
3. Edit config.h to set:
   - WiFi credentials
   - MQTT broker IP address (Raspberry Pi IP)
   - Faculty ID and name
   - BLE settings

### Step 4: Upload Firmware
1. Connect ESP32 to computer
2. Select correct board and port in Arduino IDE
3. Upload firmware
4. Verify operation (display should show startup screen)

## 🔒 SECURITY RECOMMENDATIONS

### Access Control
1. Change default passwords for all accounts
2. Use strong passwords for admin accounts
3. Restrict physical access to the central system

### Network Security
1. Use a dedicated WiFi network for the system
2. Enable WPA2/WPA3 encryption on WiFi
3. Consider using a VPN for remote access

### Database Security
1. Regular backups of the database
2. Keep PostgreSQL updated with security patches

## 🛠️ TROUBLESHOOTING

### Common Issues

#### Service Fails to Start
- Check logs: `sudo journalctl -u consultease -f`
- Verify database connection in config.json
- Check file permissions

#### Touchscreen Issues
- Run calibration script: `./scripts/calibrate_touch.sh`
- Verify touchscreen is detected: `xinput list`

#### MQTT Connection Problems
- Check MQTT broker status: `sudo systemctl status mosquitto`
- Verify network connectivity
- Check credentials in config.json

#### Faculty Desk Unit Not Connecting
- Verify WiFi credentials in config.h
- Check MQTT broker IP address
- Restart ESP32 and check serial output

## 🔄 MAINTENANCE

### Regular Updates
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Update ConsultEase
cd /home/pi/ConsultEase
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart consultease
```

### Database Maintenance
```bash
# Backup database
sudo -u postgres pg_dump consultease > consultease_backup_$(date +%Y%m%d).sql

# Restore database (if needed)
sudo -u postgres psql consultease < consultease_backup_YYYYMMDD.sql
```

## 📞 SUPPORT

For additional assistance, refer to the documentation in the docs/ directory:
- User manual
- Quick start guide
