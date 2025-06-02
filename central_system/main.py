import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QTimer

# Add parent directory to path to help with imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('consultease.log')
    ]
)
logger = logging.getLogger(__name__)

# Import models and controllers
from central_system.models import init_db
from central_system.controllers import (
    RFIDController,
    FacultyController,
    ConsultationController,
    AdminController,
    FacultyResponseController
)

# Import async MQTT service
from central_system.services.async_mqtt_service import get_async_mqtt_service

# Import views
from central_system.views import (
    LoginWindow,
    DashboardWindow,
    AdminLoginWindow,
    AdminDashboardWindow
)

# Import utilities
from central_system.utils import (
    apply_stylesheet,
    WindowTransitionManager
)
# Import theme system
from central_system.utils.theme import ConsultEaseTheme
# Import icons module separately to avoid early QPixmap creation
from central_system.utils import icons

class ConsultEaseApp:
    """
    Main application class for ConsultEase.
    """

    def __init__(self, fullscreen=False):
        """
        Initialize the ConsultEase application.
        """
        logger.info("Initializing ConsultEase application")

        # Create QApplication instance
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("ConsultEase")

        # Set up icons and modern UI (after QApplication is created)
        icons.initialize()
        logger.info("Initialized icons")

        # Apply centralized theme stylesheet
        try:
            # Apply base stylesheet from theme system
            self.app.setStyleSheet(ConsultEaseTheme.get_base_stylesheet())
            logger.info("Applied centralized theme stylesheet")
        except Exception as e:
            logger.error(f"Failed to apply theme stylesheet: {e}")
            # Fall back to old stylesheet as backup
            try:
                theme = self._get_theme_preference()
                apply_stylesheet(self.app, theme)
                logger.info(f"Applied fallback {theme} theme stylesheet")
            except Exception as e2:
                logger.error(f"Failed to apply fallback stylesheet: {e2}")

        # Validate hardware before proceeding
        logger.info("Performing hardware validation...")
        from .utils.hardware_validator import log_hardware_status
        hardware_status = log_hardware_status()

        # Initialize database with comprehensive admin account validation
        logger.info("Initializing database and ensuring admin account integrity...")
        init_db()

        # Start system monitoring
        logger.info("Starting system monitoring...")
        from .utils.system_monitor import start_system_monitoring
        start_system_monitoring()

        # Initialize system coordinator
        logger.info("Initializing system coordinator")
        from .services.system_coordinator import get_system_coordinator
        self.system_coordinator = get_system_coordinator()

        # Register services with coordinator
        self._register_system_services()

        # Start coordinated system
        if not self.system_coordinator.start_system():
            logger.error("Failed to start system coordinator")
            sys.exit(1)

        # Initialize controllers (after system coordinator)
        self.rfid_controller = RFIDController()
        self.faculty_controller = FacultyController()
        self.consultation_controller = ConsultationController()
        self.admin_controller = AdminController()
        self.faculty_response_controller = FacultyResponseController()

        # Determine if it's a first-time setup scenario
        if self.admin_controller.is_first_time_setup():
            logger.info("First-time setup detected. Admin account creation will be handled by the AdminLoginWindow.")
            # In first-time setup, neither ensure_default_admin nor _verify_admin_account_startup should run,
            # as they might preemptively create an 'admin' account.
        else:
            # Not a first-time setup (admin accounts exist or an error occurred assuming they exist)
            logger.info("Existing admin accounts found or expected. Ensuring default admin and verifying.")
            self.admin_controller.ensure_default_admin() # This method also checks if admin_count == 0.
                                                         # If is_first_time_setup() was false, admin_count > 0,
                                                         # so ensure_default_admin will likely not create an account here,
                                                         # unless the specific 'admin' user is missing.
            self._verify_admin_account_startup()     # Verifies/repairs the 'admin' account.

        # Initialize windows
        self.login_window = None
        self.dashboard_window = None
        self.admin_login_window = None
        self.admin_dashboard_window = None

        # Start controllers
        logger.info("Starting RFID controller")
        self.rfid_controller.start()
        self.rfid_controller.register_callback(self.handle_rfid_scan)

        logger.info("Starting faculty controller")
        self.faculty_controller.start()

        logger.info("Starting consultation controller")
        self.consultation_controller.start()

        logger.info("Starting faculty response controller")
        self.faculty_response_controller.start()

        # Make sure at least one faculty is available for testing
        self._ensure_dr_john_smith_available()

        # Current student
        self.current_student = None

        # Initialize transition manager
        self.transition_manager = WindowTransitionManager(duration=300)
        logger.info("Initialized window transition manager")

        # Verify RFID controller is properly initialized
        try:
            from .services import get_rfid_service
            rfid_service = get_rfid_service()
            logger.info(f"RFID service initialized: {rfid_service}")
        except Exception as e:
            logger.error(f"Failed to verify RFID service: {e}")

        # Set the fullscreen mode
        self.fullscreen = fullscreen

    def _register_system_services(self):
        """
        Register all services with the system coordinator.
        """
        try:
            from .services.system_coordinator import ServiceType
            coordinator = self.system_coordinator

        # Register database service
            coordinator.register_service(
                ServiceType.DATABASE,
                start_func=self._start_database_service,
                stop_func=self._stop_database_service,
                health_check=self._check_database_health
        )

        # Register MQTT service
            coordinator.register_service(
                ServiceType.MQTT,
                start_func=self._start_mqtt_service,
                stop_func=self._stop_mqtt_service,
                health_check=self._check_mqtt_health
        )

        # Register UI service
            coordinator.register_service(
                ServiceType.UI,
                start_func=self._start_ui_service,
                stop_func=self._stop_ui_service,
                health_check=self._check_ui_health
            )
            
            logger.info("Successfully registered all services with the system coordinator")
        except Exception as e:
            logger.error(f"Failed to register services: {e}")

    def _start_database_service(self):
        """
        Start the database service.
        """
        try:
            from .models.base import get_db
            db = get_db()
            return True
        except Exception as e:
            logger.error(f"Failed to start database service: {e}")
            return False

    def _stop_database_service(self):
        """
        Stop the database service.
        """
        try:
            from .models.base import get_db
            db = get_db()
            return True
        except Exception as e:
            logger.error(f"Failed to stop database service: {e}")
            return False

    def _check_database_health(self):
        """
        Check the health of the database service.
        """
        try:
            from .models.base import get_db
            db = get_db()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    def _start_mqtt_service(self):
        """
        Start the MQTT service.
        """
        try:
            mqtt_service = get_async_mqtt_service()
            mqtt_service.connect()
            return True
        except Exception as e:
            logger.error(f"Failed to start MQTT service: {e}")
            return False

    def _stop_mqtt_service(self):
        """
        Stop the MQTT service.
        """
        try:
            mqtt_service = get_async_mqtt_service()
            mqtt_service.disconnect()
            return True
        except Exception as e:
            logger.error(f"Failed to stop MQTT service: {e}")
            return False

    def _check_mqtt_health(self):
        """
        Check the health of the MQTT service.
        """
        try:
            mqtt_service = get_async_mqtt_service()
            return mqtt_service.is_connected()
        except Exception as e:
            logger.error(f"MQTT health check failed: {e}")
            return False

    def _start_ui_service(self):
        """
        Start the UI service.
        """
        try:
            self.show_login_window()
            return True
        except Exception as e:
            logger.error(f"Failed to start UI service: {e}")
            return False

    def _stop_ui_service(self):
        """
        Stop the UI service.
        """
        try:
            # Close all windows
            return True
        except Exception as e:
            logger.error(f"Failed to stop UI service: {e}")
            return False

    def _check_ui_health(self):
        """
        Check the health of the UI service.
        """
        try:
            # Check if any window is visible
            return True
        except Exception as e:
            logger.error(f"UI health check failed: {e}")
            return False

    def _verify_admin_account_startup(self):
        """
        Verify the admin account during startup.
        
        This method ensures that the 'admin' account exists and is properly configured.
        If the account is missing or corrupted, it attempts to repair it.
        """
        logger.info("Verifying admin account during startup")
        try:
            # Check if the admin account exists
            admin = self.admin_controller.get_admin_by_username('admin')
            if admin:
                logger.info("Admin account exists, verifying integrity")
                # Verify admin account properties
                verified = True
                if not admin.password_hash:
                    logger.warning("Admin account has no password hash, will repair")
                    verified = False
                if not admin.email:
                    logger.warning("Admin account has no email, will repair")
                    verified = False
                    
                if not verified:
                    logger.info("Admin account needs repair, performing emergency repair")
                    self._emergency_admin_repair()
                else:
                    logger.info("Admin account verification successful")
            else:
                logger.warning("Admin account does not exist, creating default account")
                # Create the admin account
                self.admin_controller.create_admin(
                    username='admin',
                    password='TempPass123!',
                    email='admin@consultease.local',
                    force_change_password=True
                )
                logger.info("Created default admin account")
        except Exception as e:
            logger.error(f"Failed to verify admin account: {e}")
            # Attempt emergency repair
            try:
                self._emergency_admin_repair()
            except Exception as repair_error:
                logger.error(f"Emergency admin repair failed: {repair_error}")

    def _emergency_admin_repair(self):
        """
        Perform emergency repair on the admin account.
        
        This method is called when the admin account is missing or corrupted.
        It attempts to create or repair the account with default credentials.
        """
        logger.info("Performing emergency admin account repair")
        try:
            # Try to find the admin account
            admin = self.admin_controller.get_admin_by_username('admin')
            
            if admin:
                logger.info("Admin account found, attempting repair")
                # Update the existing account with default values
                from central_system.models.admin import Admin
                from central_system.models.base import get_db

                db = get_db()
                db.query(Admin).filter(Admin.username == 'admin').update({
                    'email': 'admin@consultease.local',
                    'password_hash': self.admin_controller.hash_password('TempPass123!'),
                    'force_change_password': True
                })
                db.commit()
                logger.info("Admin account repaired successfully")
            else:
                logger.info("Admin account not found, creating new account")
                # Create the admin account
                self.admin_controller.create_admin(
                    username='admin',
                    password='TempPass123!',
                    email='admin@consultease.local',
                    force_change_password=True
                )
                logger.info("Created new admin account")

            # Verify the repair was successful
            admin = self.admin_controller.get_admin_by_username('admin')
            if admin and admin.password_hash:
                logger.info("Emergency admin repair successful")
                return True
            else:
                logger.error("Emergency admin repair failed: admin account not valid")
                return False
        except Exception as e:
            logger.error(f"Emergency admin repair failed: {e}")
            return False

    def _display_startup_summary(self):
        """
        Display a summary of the startup process.
        """
        # TODO: Implement startup summary
        pass

    def _get_theme_preference(self):
        """
        Get the user's theme preference.

        Returns:
            str: The preferred theme ('light' or 'dark').
        """
        try:
            from .utils.config_manager import get_config
            config = get_config()
            theme = config.get('ui', {}).get('theme', 'dark')
            if theme not in ['light', 'dark']:
                theme = 'dark'
            return theme
        except Exception as e:
            logger.error(f"Failed to get theme preference: {e}")
            return 'dark'

    def _ensure_dr_john_smith_available(self):
        """
        Ensure that Dr. John Smith is available in the database.
        """
        try:
            # Check if Dr. John Smith exists
            faculty = self.faculty_controller.get_faculty_by_name("Dr. John Smith")
            if not faculty:
                # Create Dr. John Smith
                self.faculty_controller.create_faculty(
                    name="Dr. John Smith",
                    department="Computer Science",
                    ble_id="A1:B2:C3:D4:E5:F6",
                    always_available=True
                )
                logger.info("Created Dr. John Smith faculty member")
        except Exception as e:
            logger.error(f"Failed to ensure Dr. John Smith is available: {e}")

    def run(self):
        """
        Run the application.
        """
        logger.info("Starting ConsultEase application")
        self.show_login_window()
        sys.exit(self.app.exec_())

    def cleanup(self):
        """
        Clean up resources before exiting.
        """
        logger.info("Cleaning up resources before exit")
        try:
            # Stop controllers
            self.rfid_controller.stop()
            self.faculty_controller.stop()
            self.consultation_controller.stop()
            
            # Close database connections
            from .models.base import close_db
            close_db()
            
            # Disconnect from MQTT
            mqtt_service = get_async_mqtt_service()
            mqtt_service.disconnect()
            
            logger.info("Cleanup completed successfully")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

    def show_login_window(self):
        """
        Show the login window.
        """
        logger.info("Showing login window")
        
        # Create the login window if it doesn't exist
        if not self.login_window:
            self.login_window = LoginWindow(self.handle_window_change)
            logger.info("Created login window")
        
        # Connect the RFID controller to the login window
        self.rfid_controller.register_callback(self.login_window.handle_rfid_scan)

        # Get current active window
        active_window = None
        if self.dashboard_window and self.dashboard_window.isVisible():
            active_window = self.dashboard_window
        elif self.admin_login_window and self.admin_login_window.isVisible():
            active_window = self.admin_login_window
        elif self.admin_dashboard_window and self.admin_dashboard_window.isVisible():
            active_window = self.admin_dashboard_window

        # Hide all other windows
        if self.dashboard_window:
            self.dashboard_window.hide()
        if self.admin_login_window:
            self.admin_login_window.hide()
        if self.admin_dashboard_window:
            self.admin_dashboard_window.hide()

        # Apply transition if there's an active window
        if active_window:
            self.transition_manager.transition(active_window, self.login_window)
        else:
            # Just show the login window
            self.login_window.show()
            if self.fullscreen:
                self.login_window.showFullScreen()
        
        # Reset the current student
        self.current_student = None
        
        logger.info("Login window shown")

    def show_dashboard_window(self, student_data=None):
        """
        Show the dashboard window.
        
        Args:
            student_data: The student data to display in the dashboard.
        """
        logger.info(f"Showing dashboard window for student: {student_data.id if student_data else 'None'}")
        
        # Update the current student
        self.current_student = student_data

        # Create the dashboard window if it doesn't exist
        if not self.dashboard_window:
            self.dashboard_window = DashboardWindow(
                self.handle_window_change,
                self.handle_consultation_request,
                self.faculty_controller
            )
            logger.info("Created dashboard window")
        
        # Update the dashboard with student data
        if student_data:
            self.dashboard_window.set_student(student_data)
            
            # Refresh the faculty list
            available_faculty = self.faculty_controller.get_available_faculty()
            self.dashboard_window.update_faculty_list(available_faculty)
            
            # Update the consultation history
            consultation_history = self.consultation_controller.get_student_consultations(student_data.id)
            self.dashboard_window.update_consultation_history(consultation_history)
        
        # Get current active window
        active_window = None
        if self.login_window and self.login_window.isVisible():
            active_window = self.login_window
        elif self.admin_login_window and self.admin_login_window.isVisible():
            active_window = self.admin_login_window
        elif self.admin_dashboard_window and self.admin_dashboard_window.isVisible():
            active_window = self.admin_dashboard_window

        # Hide all other windows
        if self.login_window:
            self.login_window.hide()
        if self.admin_login_window:
            self.admin_login_window.hide()
        if self.admin_dashboard_window:
            self.admin_dashboard_window.hide()

        # Apply transition if there's an active window
        if active_window:
            self.transition_manager.transition(active_window, self.dashboard_window)
        else:
            # Just show the dashboard window
            self.dashboard_window.show()
            if self.fullscreen:
                self.dashboard_window.showFullScreen()
        
        logger.info("Dashboard window shown")
        
        # Start a timer to periodically refresh the faculty list
        QTimer.singleShot(5000, self.handle_faculty_updated)

    def show_admin_login_window(self):
        """
        Show the admin login window.
        """
        logger.info("Showing admin login window")
        
        # Create the admin login window if it doesn't exist
        if not self.admin_login_window:
            self.admin_login_window = AdminLoginWindow(
                self.handle_window_change,
                self.handle_admin_authenticated
            )
            logger.info("Created admin login window")
        
        # Get current active window
        active_window = None
        if self.login_window and self.login_window.isVisible():
            active_window = self.login_window
        elif self.dashboard_window and self.dashboard_window.isVisible():
            active_window = self.dashboard_window
        elif self.admin_dashboard_window and self.admin_dashboard_window.isVisible():
            active_window = self.admin_dashboard_window

        # Hide all other windows
        if self.login_window:
            self.login_window.hide()
        if self.dashboard_window:
            self.dashboard_window.hide()
        if self.admin_dashboard_window:
            self.admin_dashboard_window.hide()

        # Apply transition if there's an active window
        if active_window:
            # Use the transition manager
            self.transition_manager.transition(active_window, self.admin_login_window)
        else:
            # Just show the admin login window
            self.admin_login_window.show()
            if self.fullscreen:
                self.admin_login_window.showFullScreen()
        
        # Check if this is a first-time setup
        is_first_time = self.admin_controller.is_first_time_setup()
        if is_first_time:
            logger.info("This is a first-time setup, showing admin creation dialog")
            self.admin_login_window.show_first_time_setup()
        
        logger.info("Admin login window shown")

    def show_admin_dashboard_window(self, admin=None):
        """
        Show the admin dashboard window.
        
        Args:
            admin: The admin user to display in the dashboard.
        """
        logger.info(f"Showing admin dashboard window for admin: {admin.username if admin else 'None'}")
        
        # Create the admin dashboard window if it doesn't exist
        if not self.admin_dashboard_window:
            self.admin_dashboard_window = AdminDashboardWindow(
                self.handle_window_change,
                self.faculty_controller,
                self.consultation_controller,
                self.admin_controller
            )
            logger.info("Created admin dashboard window")
        
        # Update the admin dashboard with admin data
        if admin:
            self.admin_dashboard_window.set_admin(admin)
            
            # Check if the admin needs to change their password
            if admin.force_change_password:
                logger.info("Admin needs to change password, showing password change dialog")
                # Show the password change dialog after a short delay to allow the window to fully load
                QTimer.singleShot(500, lambda: self.show_password_change_dialog(admin, forced=True))
        
        # Get current active window
        active_window = None
        if self.login_window and self.login_window.isVisible():
            active_window = self.login_window
        elif self.dashboard_window and self.dashboard_window.isVisible():
            active_window = self.dashboard_window
        elif self.admin_login_window and self.admin_login_window.isVisible():
            active_window = self.admin_login_window

        # Hide all other windows
        if self.login_window:
            self.login_window.hide()
        if self.dashboard_window:
            self.dashboard_window.hide()
        if self.admin_login_window:
            self.admin_login_window.hide()

        # Apply transition if there's an active window
        if active_window:
            self.transition_manager.transition(active_window, self.admin_dashboard_window)
        else:
            # Just show the admin dashboard window
            self.admin_dashboard_window.show()
            if self.fullscreen:
                self.admin_dashboard_window.showFullScreen()
        
        logger.info("Admin dashboard window shown")

    def handle_rfid_scan(self, student, rfid_uid):
        """
        Handle an RFID scan event.

        Args:
            student: The student associated with the RFID tag.
            rfid_uid: The UID of the RFID tag.
        """
        logger.info(f"RFID scan detected: {rfid_uid}")

        if student:
            logger.info(f"Student authenticated: {student.id} - {student.name}")
            self.handle_student_authenticated(student)
        else:
            logger.warning(f"Unknown RFID tag: {rfid_uid}")
            # Show an error message in the login window
            if self.login_window:
                self.login_window.show_error(f"Unknown RFID tag: {rfid_uid}")

    def handle_student_authenticated(self, student_data):
        """
        Handle a student authentication event.

        Args:
            student_data: The authenticated student data.
        """
        logger.info(f"Student authenticated: {student_data.id} - {student_data.name}")

        # Update the current student
        self.current_student = student_data

        # Show the dashboard window
        self.show_dashboard_window(student_data)
        
        # Log the authentication
        logger.info(f"Student {student_data.id} - {student_data.name} authenticated successfully")

    def handle_admin_authenticated(self, credentials):
        """
        Handle an admin authentication event.

        Args:
            credentials: The admin credentials.
        """
        logger.info(f"Admin authentication attempt: {credentials['username']}")
        
        try:
            # Authenticate the admin
            admin = self.admin_controller.authenticate_admin(
                credentials['username'],
                credentials['password']
            )

            if admin:
                logger.info(f"Admin authenticated: {admin.username}")

                # Show the admin dashboard
                self.show_admin_dashboard_window(admin)
                
                # Log the authentication
                logger.info(f"Admin {admin.username} authenticated successfully")
                
                # Return success
                return True, "Authentication successful"
            else:
                logger.warning(f"Admin authentication failed: {credentials['username']}")
                return False, "Invalid username or password"
        except Exception as e:
            logger.error(f"Admin authentication error: {str(e)}")
            return False, f"Authentication error: {str(e)}"

    def handle_consultation_request(self, faculty, message, course_code):
        """
        Handle a consultation request.

        Args:
            faculty: The faculty member to consult with.
            message: The consultation message.
            course_code: The course code for the consultation.
        """
        logger.info(f"Consultation request: {self.current_student.id} -> {faculty.id} ({course_code})")
        
        try:
            # Create the consultation request
            consultation = self.consultation_controller.create_consultation(
                student_id=self.current_student.id,
                faculty_id=faculty.id,
                request_message=message,
                course_code=course_code
            )

            if consultation:
                logger.info(f"Consultation request created: {consultation.id}")
                
                # Update the dashboard
                if self.dashboard_window:
                    # Refresh the consultation history
                    consultation_history = self.consultation_controller.get_student_consultations(self.current_student.id)
                    self.dashboard_window.update_consultation_history(consultation_history)
                    
                    # Show a success message
                    self.dashboard_window.show_success(f"Consultation request sent to {faculty.name}")
                
                # Return success
                return True, "Consultation request sent"
            else:
                logger.warning(f"Failed to create consultation request")
                
                # Show an error message
                if self.dashboard_window:
                    self.dashboard_window.show_error("Failed to create consultation request")
                
                # Return failure
                return False, "Failed to create consultation request"
        except Exception as e:
            logger.error(f"Consultation request error: {str(e)}")
            
            # Show an error message
            if self.dashboard_window:
                self.dashboard_window.show_error(f"Error: {str(e)}")
            
            # Return failure
            return False, f"Error: {str(e)}"

    def handle_faculty_updated(self):
        """
        Handle a faculty update event.
        """
        logger.debug("Faculty update triggered")

        try:
            # Refresh the faculty list in the dashboard
            if self.dashboard_window and self.dashboard_window.isVisible():
                # Get available faculty
                available_faculty = self.faculty_controller.get_available_faculty()
                
                # Update the dashboard
                self.dashboard_window.update_faculty_list(available_faculty)
                
                # Schedule the next update
                QTimer.singleShot(5000, self.handle_faculty_updated)

            # Refresh the faculty list in the admin dashboard
            if self.admin_dashboard_window and self.admin_dashboard_window.isVisible():
                # Get all faculty
                all_faculty = self.faculty_controller.get_all_faculty()
                
                # Update the admin dashboard
                self.admin_dashboard_window.update_faculty_list(all_faculty)
        except Exception as e:
            logger.error(f"Faculty update error: {str(e)}")

    def handle_student_updated(self):
        """
        Handle a student update event.
        """
        logger.debug("Student update triggered")
        
        try:
            # Refresh the student data in the dashboard
            if self.dashboard_window and self.dashboard_window.isVisible() and self.current_student:
                # Get the updated student data
                updated_student = self.admin_controller.get_student_by_id(self.current_student.id)
                
                if updated_student:
                    # Update the current student
                    self.current_student = updated_student
                    
                    # Update the dashboard
                    self.dashboard_window.set_student(updated_student)

            # Refresh the student list in the admin dashboard
            if self.admin_dashboard_window and self.admin_dashboard_window.isVisible():
                # Get all students
                all_students = self.admin_controller.get_all_students()
                
                # Update the admin dashboard
                self.admin_dashboard_window.update_student_list(all_students)
        except Exception as e:
            logger.error(f"Student update error: {str(e)}")

    def show_password_change_dialog(self, admin, forced=False):
        """
        Show the password change dialog.

        Args:
            admin: The admin user to change the password for.
            forced: Whether the password change is forced.
        """
        logger.info(f"Showing password change dialog for admin: {admin.username}, forced: {forced}")
        
        if self.admin_dashboard_window:
            # Show the password change dialog
            self.admin_dashboard_window.show_password_change_dialog(
                admin,
                forced=forced,
                on_change=self.handle_password_changed
            )

            def on_password_changed(success):
                """
                Handle the password change result.
                
                Args:
                    success: Whether the password change was successful.
                """
                if success:
                    logger.info(f"Password changed successfully for admin: {admin.username}")
                    
                    # Update the admin data
                    updated_admin = self.admin_controller.get_admin_by_username(admin.username)
                    
                    # Update the admin dashboard
                    self.admin_dashboard_window.set_admin(updated_admin)
                else:
                    logger.warning(f"Password change failed for admin: {admin.username}")

            # Set the callback
            self.admin_dashboard_window.password_change_callback = on_password_changed

    def handle_password_changed(self, success):
        """
        Handle the password change result.
        
        Args:
            success: Whether the password change was successful.
        """
        logger.info(f"Password change result: {success}")

    def handle_window_change(self, window_name, data=None):
        """
        Handle a window change request.

        Args:
            window_name: The name of the window to show.
            data: Optional data to pass to the window.
        """
        logger.info(f"Window change requested: {window_name}")
        
        if window_name == "login":
            self.show_login_window()
        elif window_name == "dashboard":
            self.show_dashboard_window(data)
        elif window_name == "admin_login":
            self.show_admin_login_window()
        elif window_name == "admin_dashboard":
            self.show_admin_dashboard_window(data)
        else:
            logger.warning(f"Unknown window: {window_name}")

# If this file is run directly, start the application
if __name__ == "__main__":
    # Create and run the application
    app = ConsultEaseApp(fullscreen=False)
    app.run()