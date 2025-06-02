# ConsultEase - Faculty Desk Unit

This is the firmware for the Faculty Desk Unit component of the ConsultEase system. This unit is installed at each faculty member's desk and shows consultation requests from students while automatically detecting the faculty's presence via MAC address-based BLE scanning.

## Faculty Desk Unit

### Hardware Requirements

The Faculty Desk Unit is built using:

1. ESP32 Development Board
2. ST7789 2.4" TFT Display (320x240)
3. BLE Beacon for faculty presence detection
4. Two physical buttons for consultation responses
   - Accept button (green): GPIO 12
   - Decline/Busy button (red): GPIO 14
5. Passive buzzer for sound notifications (optional)

### Wiring Instructions

#### TFT Display Connection
- VCC → 3.3V
- GND → GND
- SCL → GPIO 18 (SCK)
- SDA → GPIO 23 (MOSI)
- RES → GPIO 4
- DC → GPIO 2
- CS → GPIO 5
- BL → 3.3V

#### Button Connections
- Accept Button: 
  - One terminal → GPIO 12 
  - Other terminal → GND
- Decline Button: 
  - One terminal → GPIO 14
  - Other terminal → GND

#### Buzzer Connection (Optional)
- Positive terminal → GPIO 25
- Negative terminal → GND

### Consultation Response Functionality

The Faculty Desk Unit now includes physical button inputs to handle consultation requests:

1. **Accept Button (Green)**: 
   - Acknowledges and accepts a student's consultation request
   - Shows confirmation on screen
   - Sends acceptance message to central system
   - Updates student's request status to ACCEPTED

2. **Decline/Busy Button (Red)**:
   - Declines a student's consultation request
   - Shows "Busy" status on screen
   - Sends decline message to central system
   - Updates student's request status to DECLINED

When a consultation request is received:
- The screen will display the request details
- Visual and audible notifications alert the faculty
- The header will flash to indicate a pending request
- After 60 seconds without response, the request will timeout (configurable)

## Pin Connections

### Display Connections (SPI)
| TFT Display Pin | ESP32 Pin |
|-----------------|-----------|
| MOSI/SDA        | GPIO 23   |
| MISO            | GPIO 19   |
| SCK/CLK         | GPIO 18   |
| CS              | GPIO 5    |
| DC              | GPIO 21   |
| RST             | GPIO 22   |
| VCC             | 3.3V      |
| GND             | GND       |

## Software Dependencies

The following libraries need to be installed via the Arduino Library Manager:

- WiFi
- PubSubClient (by Nick O'Leary)
- BLEDevice
- BLEServer
- BLEUtils
- BLE2902
- SPI
- Adafruit_GFX
- Adafruit_ST7789
- time
- WiFiUdp (built-in ESP32 library)
- NTPClient (by Fabrice Weinberg) - For automatic time synchronization
- NimBLE-Arduino (for BLE beacon)

## Setup and Configuration

1. Install the required libraries in Arduino IDE
2. Open `faculty_desk_unit.ino` in Arduino IDE
3. Copy config_production_template.h to config.h
4. Update the configuration in `config.h`:
   - WiFi credentials (`WIFI_SSID` and `WIFI_PASSWORD`)
   - MQTT broker IP address (`MQTT_SERVER`)
   - Faculty ID and name (`FACULTY_ID` and `FACULTY_NAME`)
   - Faculty MAC addresses in the `FACULTY_MAC_ADDRESSES` array
   - NTP settings (optional - defaults to Philippines timezone)
5. Compile and upload to your ESP32

### NTP Time Synchronization Configuration

The faculty desk unit includes automatic internet time synchronization. Configure these settings in `config.h`:

```cpp
// NTP Time Synchronization Configuration
#define NTP_SERVER_1 "pool.ntp.org"
#define NTP_SERVER_2 "time.nist.gov"
#define NTP_SERVER_3 "time.google.com"
#define TIMEZONE_OFFSET_HOURS 8  // Philippines timezone UTC+8
#define NTP_SYNC_INTERVAL_HOURS 1  // Sync every 1 hour
#define NTP_RETRY_INTERVAL_MINUTES 5  // Retry every 5 minutes if failed
#define NTP_MAX_RETRY_ATTEMPTS 3  // Maximum retry attempts before giving up
```

**Features:**
- Automatic time synchronization on startup
- Periodic sync every 1-2 hours to maintain accuracy
- Multiple NTP server fallback for reliability
- Visual indicators for sync status (green dot = synced, orange dot = fallback)
- Graceful fallback to ESP32 internal clock if NTP fails

### BLE Beacon Detection Configuration

The faculty desk unit uses **passive scanning** to detect BLE beacons for faculty presence detection. No pairing or connection is required.

Configure BLE detection in `config.h`:

```cpp
// Replace with your actual beacon MAC address
#define FACULTY_BEACON_MAC "AA:BB:CC:DD:EE:FF"

// Adjust detection parameters if needed
#define BLE_RSSI_THRESHOLD -75  // Signal strength threshold (-75 dBm ≈ 5-10 meters)
#define BLE_SCAN_INTERVAL 5000  // Scan every 5 seconds
#define BLE_SCAN_DURATION 3     // Scan for 3 seconds each time
```

#### Detection Features:
- **No Pairing Required**: Uses passive BLE scanning
- **Automatic Detection**: Scans every 5 seconds for assigned beacon
- **Range Control**: Configurable RSSI threshold for detection range
- **Reliable Detection**: Debouncing and timeout mechanisms for stable presence detection

## Usage

1. The unit will automatically connect to WiFi and the MQTT broker
2. It will scan for the configured BLE beacon (faculty's device)
3. When the beacon is detected, the faculty status is set to "Available"
4. When the beacon is not detected, the faculty status is set to "Unavailable"
5. Consultation requests from students will appear on the display

### BLE Always-Available Feature (Optional)

The faculty desk unit includes an optional "Always Available" mode that can be enabled in the config.h file:

```cpp
// Set to true to make faculty always appear as available regardless of BLE connection
#define ALWAYS_AVAILABLE true
```

When this feature is enabled:
- The faculty status is always shown as "Available" in the central system regardless of BLE detection
- The unit will still perform BLE scanning, but won't change status when beacons disconnect
- Every 5 minutes, the unit sends a "keychain_connected" message to ensure the faculty remains available
- This feature is useful for faculty members who want to be always available for consultations

By default, this feature is disabled (set to `false`), meaning the faculty status will accurately reflect the actual BLE detection status.

## Troubleshooting

If you experience issues with the faculty desk unit:

1. Check serial output at 115200 baud for error messages
2. Verify WiFi connectivity (the unit will display connection status)
3. Check MQTT broker IP address and connection status
4. Verify the MAC address of your BLE beacon is correctly configured
5. Adjust the BLE_RSSI_THRESHOLD if detection range is too small or too large
6. Refer to the TROUBLESHOOTING.md file for more detailed guidance