from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QGridLayout, QLineEdit, QFrame, 
                              QMessageBox, QDialog, QDesktopWidget, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QFont

import logging
import time
from .base_window import BaseWindow
from ..themes import ConsultEaseTheme

# Set up logging
logger = logging.getLogger(__name__)

class LoginWindow(BaseWindow):
    """
    Login window for student RFID authentication.
    """
    # Signal to notify when a student is authenticated
    student_authenticated = pyqtSignal(object)

    def __init__(self, parent=None):
        """
        Initialize the login window.
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing LoginWindow")
        
        # Initialize scanning animation state
        self.scanning_animation_frame = 0
        self.rfid_reading = False
        
        super().__init__(parent)
        
        # Set up scanning animation timer
        self.scanning_timer = QTimer(self)
        self.scanning_timer.timeout.connect(self.update_scanning_animation)
        
        # Initialize manual RFID entry
        self.rfid_input = QLineEdit(self)
        self.rfid_input.setVisible(False)  # Hidden by default
        self.rfid_input.returnPressed.connect(self.handle_manual_rfid_entry)
        
        self.logger.info("LoginWindow initialized")

    def init_ui(self):
        """
        Initialize the user interface.
        """
        super().init_ui()
        
        self.logger.info("Setting up LoginWindow UI")
        
        # Set window title and size
        self.setWindowTitle("ConsultEase - Student Login")
        
        # Create the main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setSpacing(20)
        
        # Header with logo
        header_layout = QHBoxLayout()
        
        # Logo
        logo_label = QLabel()
        logo_label.setFixedSize(120, 120)
        
        # Load logo image
        try:
            from ..utils.icons import IconProvider, Icons
            logo = IconProvider.get_icon(Icons.LOGO, QPixmap, large=True)
            if logo and not logo.isNull():
                logo_label.setPixmap(logo.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                logo_label.setText("LOGO")
                logo_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc; font-size: 14pt; font-weight: bold;")
        except Exception as e:
            self.logger.error(f"Error loading logo: {e}")
            logo_label.setText("LOGO")
            logo_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc; font-size: 14pt; font-weight: bold;")
        
        logo_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(logo_label)
        
        # Title
        title_label = QLabel("ConsultEase")
        title_label.setStyleSheet(f"font-size: {ConsultEaseTheme.FONT_SIZE_XXLARGE}pt; font-weight: bold; color: {ConsultEaseTheme.PRIMARY_COLOR};")
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label, 1)
        
        main_layout.addLayout(header_layout)
        
        # Welcome message
        welcome_label = QLabel("Welcome to the Consultation Management System")
        welcome_label.setStyleSheet(f"font-size: {ConsultEaseTheme.FONT_SIZE_LARGE}pt; color: {ConsultEaseTheme.TEXT_COLOR};")
        welcome_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(welcome_label)
        
        # Subtitle
        subtitle_label = QLabel("Please scan your student ID to continue")
        subtitle_label.setStyleSheet(f"font-size: {ConsultEaseTheme.FONT_SIZE_MEDIUM}pt; color: {ConsultEaseTheme.TEXT_COLOR_SECONDARY};")
        subtitle_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(subtitle_label)
        
        # Spacer
        main_layout.addSpacing(20)
        
        # RFID scanning frame
        self.scanning_frame = QFrame()
        self.scanning_frame.setFixedSize(300, 200)
        self.scanning_frame.setStyleSheet(f'''
            QFrame {{
                background-color: {ConsultEaseTheme.BG_SECONDARY};
                border-radius: {ConsultEaseTheme.BORDER_RADIUS_LARGE}px;
                border: 2px solid #ccc;
            }}
        ''')
        
        scanning_layout = QVBoxLayout(self.scanning_frame)
        scanning_layout.setContentsMargins(20, 20, 20, 20)
        scanning_layout.setSpacing(10)
        
        # RFID icon
        self.rfid_icon_label = QLabel("🔄")
        self.rfid_icon_label.setStyleSheet(f"font-size: 48pt; color: {ConsultEaseTheme.SECONDARY_COLOR};")
        self.rfid_icon_label.setAlignment(Qt.AlignCenter)
        scanning_layout.addWidget(self.rfid_icon_label)
        
        # Scanning status
        self.scanning_status_label = QLabel("Ready to Scan")
        self.scanning_status_label.setStyleSheet(f"font-size: {ConsultEaseTheme.FONT_SIZE_LARGE}pt; color: {ConsultEaseTheme.SECONDARY_COLOR};")
        self.scanning_status_label.setAlignment(Qt.AlignCenter)
        scanning_layout.addWidget(self.scanning_status_label)
        
        # Center the scanning frame
        scanning_container = QHBoxLayout()
        scanning_container.addStretch()
        scanning_container.addWidget(self.scanning_frame)
        scanning_container.addStretch()
        
        main_layout.addLayout(scanning_container)
        
        # Manual entry option
        manual_entry_layout = QHBoxLayout()
        
        manual_entry_label = QLabel("Manual Entry:")
        manual_entry_label.setStyleSheet(f"font-size: {ConsultEaseTheme.FONT_SIZE_SMALL}pt; color: {ConsultEaseTheme.TEXT_COLOR_SECONDARY};")
        manual_entry_layout.addWidget(manual_entry_label)
        
        self.rfid_input.setPlaceholderText("Enter RFID manually")
        self.rfid_input.setFixedWidth(200)
        self.rfid_input.setStyleSheet(f'''
            QLineEdit {{
                padding: 8px;
                border-radius: {ConsultEaseTheme.BORDER_RADIUS_SMALL}px;
                border: 1px solid #ccc;
                font-size: {ConsultEaseTheme.FONT_SIZE_SMALL}pt;
            }}
        ''')
        self.rfid_input.setVisible(True)  # Make visible by default for testing
        manual_entry_layout.addWidget(self.rfid_input)
        
        manual_entry_layout.addStretch()
        
        main_layout.addLayout(manual_entry_layout)
        
        # Add spacer
        main_layout.addStretch()
        
        # Admin login button
        admin_login_button = QPushButton("Admin Login")
        admin_login_button.setStyleSheet(f'''
            QPushButton {{
                background-color: {ConsultEaseTheme.ACCENT_COLOR};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: {ConsultEaseTheme.BORDER_RADIUS_MEDIUM}px;
                font-size: {ConsultEaseTheme.FONT_SIZE_SMALL}pt;
            }}
            QPushButton:hover {{
                background-color: {ConsultEaseTheme.ACCENT_COLOR_HOVER};
            }}
        ''')
        admin_login_button.clicked.connect(self.admin_login)
        
        admin_button_layout = QHBoxLayout()
        admin_button_layout.addStretch()
        admin_button_layout.addWidget(admin_login_button)
        
        main_layout.addLayout(admin_button_layout)
        
        # Set the main layout
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        self.logger.info("LoginWindow UI setup complete")

    def showEvent(self, event):
        """
        Handle show event.
        """
        super().showEvent(event)
        
        # Refresh RFID service to ensure it has the latest student data
        try:
            from ..services import get_rfid_service
            rfid_service = get_rfid_service()
            rfid_service.refresh_student_data()
            self.logger.info("Refreshed RFID service student data when login window shown")
        except Exception as e:
            self.logger.error(f"Error refreshing RFID service: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")

        # Start RFID scanning when the window is shown
        self.logger.info("LoginWindow shown, starting RFID scanning")
        self.start_rfid_scanning()

        # Focus the RFID input field
        self.rfid_input.setFocus()

    def resizeEvent(self, event):
        """Handle window resize"""
        super().resizeEvent(event)

    def start_rfid_scanning(self):
        """
        Start the RFID scanning animation and process.
        """
        # Refresh RFID service to ensure it has the latest student data
        try:
            from ..services import get_rfid_service
            rfid_service = get_rfid_service()
            rfid_service.refresh_student_data()
            self.logger.info("Refreshed RFID service student data when starting RFID scanning")
        except Exception as e:
            self.logger.error(f"Error refreshing RFID service: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")

        self.rfid_reading = True
        self.scanning_status_label.setText("Scanning...")
        self.scanning_status_label.setStyleSheet(f"font-size: {ConsultEaseTheme.FONT_SIZE_XLARGE}pt; color: {ConsultEaseTheme.SECONDARY_COLOR};")
        self.scanning_frame.setStyleSheet(f'''
            QFrame {{
                background-color: {ConsultEaseTheme.BG_SECONDARY};
                border-radius: {ConsultEaseTheme.BORDER_RADIUS_LARGE}px;
                border: 2px solid {ConsultEaseTheme.SECONDARY_COLOR};
            }}
        ''')
        self.scanning_timer.start(500)  # Update animation every 500ms 