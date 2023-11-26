import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QHBoxLayout
from PyQt6.QtGui import QShortcut, QKeySequence, QIcon
from models.task_manager import TaskManager
from ui.dialogs.registration_dialog import RegistrationDialog

class LoginDialog(QDialog):
    def __init__(self, task_manager: TaskManager, main_window, preferences_manager=None):
        """
        Initializes the Login class.

        Args:
            task_manager (TaskManager): The task manager object.
            main_window (MainWindow): The main window object.
            preferences_manager (PreferencesManager, optional): The preferences manager object. Defaults to None.
        """
        super().__init__()

        self.task_manager = task_manager
        self.main_window = main_window
        self.preferences_manager = preferences_manager

        # Counter for failed login attempts
        self.failed_attempts = 0

        # Only apply preferences if preferences_manager is provided
        if self.preferences_manager:
            self.preferences_manager.load_and_apply_preferences()

        # Set up the login dialog
        self.setWindowTitle("Login - ProTaskVista")
        self.setGeometry(600, 300, 400, 200)

        # Load the icon
        self.setWindowIcon(QIcon('resources/favicon.ico'))

        # Set up the UI components here
        self.init_ui()

    def init_ui(self):
        """
        Initializes the user interface for the login dialog.

        This method sets up a visually appealing layout with input fields, buttons, and labels.
        It also applies user preferences for 'Always on Top' if set.
        """

        # Main layout with improved spacing and alignment
        login_layout = QVBoxLayout()
        login_layout.setSpacing(10)  # Set spacing between elements
        login_layout.setContentsMargins(20, 20, 20, 20)  # Set margins for the layout

        # LOGIN header label with enhanced styling
        login_title_label = QLabel("LOGIN")
        login_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center-align the label
        login_title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #4a4a4a;")
        login_layout.addWidget(login_title_label)

        # Username input section with user-friendly placeholder
        username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")  # Placeholder text
        self.username_input.setMinimumHeight(35)  # Set minimum height for better readability
        login_layout.addWidget(username_label)
        login_layout.addWidget(self.username_input)

        # Password input section with show/hide toggle (not implemented here)
        password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")  # Placeholder text
        self.password_input.setMinimumHeight(35)  # Set minimum height
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)  # Hide password characters
        login_layout.addWidget(password_label)
        login_layout.addWidget(self.password_input)

        # Login button with improved styling and interaction
        self.login_button = QPushButton("Login")
        self.login_button.setMinimumHeight(35)  # Set minimum height
        self.login_button.clicked.connect(self.try_login)  # Connect button to login function
        login_layout.addWidget(self.login_button)

        # Link to create a new account with interactive styling
        create_account_label = QLabel("<a href='#'>Create an Account</a>")
        create_account_label.setStyleSheet("color: #007bff; text-decoration: underline;")
        create_account_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center-align the label
        create_account_label.linkActivated.connect(self.create_account)  # Connect to account creation dialog
        login_layout.addWidget(create_account_label)

        # Set the layout to the dialog and improve keyboard navigation
        self.setLayout(login_layout)
        self.username_input.setFocus()  # Focus on username input when dialog opens
        login_shortcut = QShortcut(QKeySequence("Return"), self)
        login_shortcut.activated.connect(self.try_login)  # Allow pressing Enter to login

        # Apply user preferences for 'Always on Top' if set
        if self.preferences_manager:
            self.preferences_manager.load_and_apply_preferences()

    def try_login(self):
        """
        Attempts to log in the user with the provided username and password.
        If the login is successful, the user is accepted and their user_id is stored.
        If the login fails, the number of failed attempts is incremented.
        If the number of failed attempts exceeds the maximum allowed attempts, the application is exited.
        """

        MAX_ATTEMPTS = 3  # Maximum number of allowed attempts

        username = self.username_input.text()
        password = self.password_input.text()

        # Basic validation
        if not username or not password:
            QMessageBox.warning(self, "Login Failed", "Please enter both username and password.")
            return

        valid_login, user_id = self.task_manager.verify_user(username, password)
        if valid_login:
            self.accept()  # Successful login
            self.user_id = user_id  # Store the user_id in the LoginDialog
            self.task_manager.log_user_activity(username, "Login", "Success")

            # Check if the user has seen the welcome message
            preferences = self.task_manager.get_preferences(self.user_id)
            welcome_message = preferences.get('has_seen_welcome_message') == 'True'
            if not welcome_message:
                self.show_welcome_message()
                self.task_manager.save_preferences(self.user_id, {'has_seen_welcome_message': str(True)})  # Save preferences
        else:
            self.task_manager.log_user_activity(username, "Login", "Failure")
            self.failed_attempts += 1
            if self.failed_attempts >= MAX_ATTEMPTS:
                QMessageBox.critical(self, "Login Failed", "Maximum login attempts reached. Exiting application.")
                sys.exit()  # Exit the application after too many failed attempts
            else:
                remaining_attempts = MAX_ATTEMPTS - self.failed_attempts
                QMessageBox.warning(self, "Login Failed", f"Invalid username or password. {remaining_attempts} attempts remaining.")

    def show_welcome_message(self):
        """
        Shows a welcome message to the user.

        This method creates a QMessageBox and displays a welcome message to the user.
        """
        welcome_message = QMessageBox()
        welcome_message.setWindowTitle("Welcome to ProTaskVista")
        welcome_message.setText("Welcome to your Task Manager app! Get started by adding new tasks and enjoy organizing your tasks more efficiently!")
        welcome_message.exec()

    def get_user_id(self):
        """
        Returns the user ID if it exists, otherwise returns None.
        """
        try:
            return self.user_id
        except AttributeError:
            return None

    def reset_login_dialog(self):
        """
        Resets the login dialog to its initial state.

        This method clears the username and password input fields and resets the number of failed login attempts to zero.
        """
        self.username_input.clear()
        self.password_input.clear()
        self.failed_attempts = 0

    def create_account(self):
        """
        Opens a registration dialog for creating a new account.

        This method creates an instance of the RegistrationDialog class and
        executes it, allowing the user to register and create a new account.
        """
        registration_dialog = RegistrationDialog(self.task_manager)
        registration_dialog.exec()
