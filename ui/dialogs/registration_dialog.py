from PyQt6.QtWidgets import QDialog, QLabel, QLineEdit, QHBoxLayout, QVBoxLayout, QPushButton, QMessageBox
from models.task_manager import TaskManager

class RegistrationDialog(QDialog):
    """
    A dialog window for user registration.

    Args:
        task_manager (TaskManager): An instance of the task manager.

    Attributes:
        task_manager (TaskManager): An instance of the task manager.
        username_input (QLineEdit): The input field for the username.
        password_input (QLineEdit): The input field for the password.
        password_repeat_input (QLineEdit): The input field for repeating the password.
        register_button (QPushButton): The button for registering the user.

    Methods:
        __init__(self, task_manager): Initializes the RegistrationDialog.
        register(self): Validates the inputs and creates a new user.
    """

    def __init__(self, task_manager: TaskManager):
        super().__init__()

        self.task_manager = task_manager

        self.setWindowTitle("Create Account")
        self.setGeometry(600, 300, 400, 200)

        layout = QVBoxLayout()

        # Username label and input
        username_label = QLabel("Username")
        layout.addWidget(username_label)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setMinimumHeight(32)
        layout.addWidget(self.username_input)

        # Add vertical spacing and Adjust the number to increase or decrease the space
        layout.addSpacing(12)

        # Password label
        password_label = QLabel("Password/Repeat")
        layout.addWidget(password_label)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setMinimumHeight(32)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        # Repeat password field
        self.password_repeat_input = QLineEdit()
        self.password_repeat_input.setPlaceholderText("Repeat Password")
        self.password_repeat_input.setMinimumHeight(32)
        self.password_repeat_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_repeat_input)

        # Create a horizontal layout for the button to center it
        button_layout = QHBoxLayout()
        button_layout.addStretch()  # Spacer that will push the button towards the center

        # Login button
        self.register_button = QPushButton("Register")
        self.register_button.setFixedWidth(100)
        self.register_button.clicked.connect(self.register)
        button_layout.addWidget(self.register_button)
        button_layout.addStretch()  # Add the horizontal layout to the main vertical layout
        self.register_button.setStyleSheet("background-color: #e1e1e1; padding: 5px;")
        layout.addLayout(button_layout)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.register_button)
        button_layout.addStretch()

        self.setLayout(layout)

    def register(self):
        """
        Validates the inputs and creates a new user.

        If any of the input fields are empty or the passwords do not match,
        a warning message is displayed. Otherwise, the user creation logic
        is implemented in the task_manager. If an error occurs during user
        creation, an error message is displayed. Otherwise, a success message
        is displayed and the dialog is accepted.
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

        # Assuming task_manager has a method to create user
        # Implement the user creation logic in task_manager
        error_message = self.task_manager.create_user(username, password)
        if error_message:
            QMessageBox.critical(self, "Error", error_message)
        else:
            QMessageBox.information(
                self, "Success", "Account created successfully.")
            self.accept()
