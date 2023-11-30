from PyQt6.QtWidgets import QDialog, QLabel, QLineEdit, QVBoxLayout, QPushButton, QMessageBox
from PyQt6.QtGui import QIcon
from models.task_manager import TaskManager

class RegistrationDialog(QDialog):
    """
    A dialog window for user registration.

    This dialog provides a user-friendly interface for creating a new account with
    input validation and informative messages.

    Attributes:
        task_manager (TaskManager): An instance of the task manager.
        username_input (QLineEdit): Input field for the username.
        password_input (QLineEdit): Input field for the password.
        password_repeat_input (QLineEdit): Input field for confirming the password.
        register_button (QPushButton): Button to trigger the registration process.
    """

    def __init__(self, task_manager: TaskManager):
        super().__init__()

        self.task_manager = task_manager

        # application icon and title
        self.setWindowIcon(QIcon('resources/favicon.ico'))
        self.setWindowTitle("Create Account")
        self.setGeometry(600, 300, 400, 200)

        self.init_ui()

    def init_ui(self):
        """
        Initializes the user interface components of the registration dialog.

        This method sets up a clean and structured layout with labeled input fields
        and a registration button.
        """

        layout = QVBoxLayout()
        layout.setSpacing(10)  # Set spacing between elements
        layout.setContentsMargins(20, 20, 20, 20)  # Set margins for the layout

        # Stylish and clear username input section
        username_label = QLabel("Username")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setMinimumHeight(32)
        layout.addWidget(username_label)
        layout.addWidget(self.username_input)

        # Password input fields with proper spacing and clear labeling
        layout.addSpacing(12)
        password_label = QLabel("Password / Repeat Password")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(32)
        self.password_repeat_input = QLineEdit()
        self.password_repeat_input.setPlaceholderText("Repeat your password")
        self.password_repeat_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_repeat_input.setMinimumHeight(32)
        layout.addWidget(password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.password_repeat_input)

        # Register button with enhanced visual appeal
        self.register_button = QPushButton("Register")
        self.register_button.setMinimumHeight(35)  # Set minimum height
        self.register_button.clicked.connect(self.register)
        layout.addWidget(self.register_button)

        self.setLayout(layout)

    def register(self):
        """
        Handles the registration process by validating input fields and creating a new user account.

        Validates the provided username and passwords, checking for their completeness,
        correctness, and uniqueness. Displays appropriate messages for any validation failures
        or registration success.
        """

        # Validate the inputs
        username = self.username_input.text()
        password = self.password_input.text()
        password_repeat = self.password_repeat_input.text()

        # Check if any input fields are empty
        if not username or not password or not password_repeat:
            QMessageBox.warning(self, "Incomplete", "Please fill out all fields.")
            return

        # Check if the passwords match
        if password != password_repeat:
            QMessageBox.warning(self, "Mismatch", "Passwords do not match.")
            return

        # Check if the username is valid
        if not self.task_manager.is_valid_username(username):
            QMessageBox.warning(self, "Invalid Username", "Username is invalid. Please choose a different username.")
            return

        # Check if the password is valid
        if not self.task_manager.is_valid_password(password):
            QMessageBox.warning(self, "Invalid Password", "Password does not meet the required criteria.")
            return

        # Check if the username already exists
        if self.task_manager.username_exists(username):
            QMessageBox.warning(self, "Username Taken", "This username is already taken. Please choose another.")
            return

        # User creation logic with error handling
        error_message = self.task_manager.create_user(username, password)
        if error_message:
            QMessageBox.critical(self, "Registration Failed", error_message)
        else:
            QMessageBox.information(self, "Success", "Account created successfully.")
            self.accept()
