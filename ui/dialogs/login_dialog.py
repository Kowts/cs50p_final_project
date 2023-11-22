import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QHBoxLayout
from PyQt6.QtGui import QCursor, QShortcut, QKeySequence
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

        self.setWindowTitle("Login")
        self.setGeometry(600, 300, 400, 200)

        # Set up the UI components here
        self.init_ui()

    def init_ui(self):
        """
        Initializes the user interface for the login dialog.

        This method sets up the layout and widgets for the login dialog, including the login header label,
        username and password input fields, login button, and create account label. It also applies user
        preferences for 'Always on Top' if set.

        Parameters:
        - self: The instance of the class.

        Returns:
        - None
        """

        # Main layout for the login dialog
        login_layout = QVBoxLayout()

        # Create the LOGIN header label
        login_title_label = QLabel("LOGIN")
        login_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        login_title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1d1f21;")
        login_layout.addWidget(login_title_label)

        # Username input section
        username_label = QLabel("Username")
        login_layout.addWidget(username_label)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setMinimumHeight(32)
        login_layout.addWidget(self.username_input)

        # Password input section
        # Spacing between username and password inputs
        login_layout.addSpacing(12)
        password_label = QLabel("Password")
        login_layout.addWidget(password_label)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setMinimumHeight(32)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        login_layout.addWidget(self.password_input)

        # Login button section
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.login_button = QPushButton("Login")
        self.login_button.setFixedWidth(100)
        self.login_button.setStyleSheet(
            "background-color: #e1e1e1; padding: 5px;")
        self.login_button.clicked.connect(self.try_login)
        button_layout.addWidget(self.login_button)
        button_layout.addStretch()
        login_layout.addLayout(button_layout)

        # Create account label
        account_layout = QHBoxLayout()
        account_layout.addStretch()
        create_account_label = QLabel("<a href='#'>Create an Account</a>")
        create_account_label.setStyleSheet("color: blue; text-decoration: underline;")
        create_account_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        create_account_label.setOpenExternalLinks(False)
        create_account_label.linkActivated.connect(self.create_account)
        account_layout.addWidget(create_account_label)
        account_layout.addStretch()
        login_layout.addLayout(account_layout)

        # Set the layout to the dialog
        self.setLayout(login_layout)

        # Shortcut for login
        login_shortcut = QShortcut(QKeySequence("Return"), self)
        login_shortcut.activated.connect(self.try_login)

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
            QMessageBox.warning(self, "Login Failed",
                                "Please enter both username and password.")
            return

        valid_login, user_id = self.task_manager.verify_user(
            username, password)
        if valid_login:
            self.accept()  # Successful login
            self.user_id = user_id  # Store the user_id in the LoginDialog
            self.task_manager.log_user_activity(username, "Login", "Success")
        else:
            self.task_manager.log_user_activity(username, "Login", "Failure")
            self.failed_attempts += 1
            if self.failed_attempts >= MAX_ATTEMPTS:
                QMessageBox.critical(self, "Login Failed", "Maximum login attempts reached. Exiting application.")
                sys.exit()  # Exit the application after too many failed attempts
            else:
                remaining_attempts = MAX_ATTEMPTS - self.failed_attempts
                QMessageBox.warning(
                    self, "Login Failed", f"Invalid username or password. {remaining_attempts} attempts remaining.")

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
