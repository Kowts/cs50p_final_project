from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtGui import QIcon
from models.task_manager import TaskManager
from services.preferences import PreferencesManager
from helpers.utils import hash_password


class ChangePasswordDialog(QDialog):
    """
    A dialog window that allows a user to change their password.

    Args:
        task_manager (TaskManager): An instance of TaskManager to handle database operations.
        user_id (int): The unique identifier of the user whose password will be changed.

    Attributes:
        task_manager (TaskManager): Instance to access task management functionalities.
        preferences_manager (PreferencesManager): Manages user preferences throughout the application.
        user_id (int): Stores the ID of the currently logged-in user.
        current_password_input (QLineEdit): Input field for entering the current password.
        new_password_input (QLineEdit): Input field for entering the new password.
        repeat_password_input (QLineEdit): Input field for confirming the new password.
    """

    def __init__(self, task_manager: TaskManager, user_id):
        super().__init__()

        # Assign passed task manager and user ID to class attributes.
        self.task_manager = task_manager
        self.user_id = user_id
        # PreferencesManager is initialized to handle user-specific settings.
        self.preferences_manager = PreferencesManager(
            self, self.task_manager, user_id)

        # Set window title and size for the change password dialog.
        self.setWindowTitle("Change Password")
        self.setWindowIcon(QIcon('resources/favicon.ico'))
        self.setGeometry(600, 300, 400, 200)

        # Initialize the UI components.
        self.init_ui()

        # Load and apply user preferences such as theme, font size, etc.
        self.preferences_manager.load_and_apply_preferences()

    def init_ui(self):
        """
        Set up the user interface components for the change password dialog.
        This includes labels, line edits for password fields, and the change password button.
        """
        layout = QVBoxLayout(self)

        # Setup UI elements for current password input.
        current_password_label = QLabel("Current Password")
        layout.addWidget(current_password_label)
        self.current_password_input = QLineEdit()
        self.current_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.current_password_input)

        # Setup UI elements for new password input.
        new_password_label = QLabel("New Password")
        layout.addWidget(new_password_label)
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.new_password_input)

        # Setup UI elements for repeating new password input.
        repeat_password_label = QLabel("Repeat New Password")
        layout.addWidget(repeat_password_label)
        self.repeat_password_input = QLineEdit()
        self.repeat_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.repeat_password_input)

        # Setup UI elements for the change password button.
        button_layout = QHBoxLayout()
        change_button = QPushButton("Change Password")
        change_button.clicked.connect(self.change_password)
        button_layout.addWidget(change_button)
        layout.addLayout(button_layout)

    def change_password(self):
        """
        Handles the password change process. Validates input fields, verifies the current password,
        and updates the password in the database. It also handles user notifications via message boxes.
        """
        current_password = self.current_password_input.text()
        new_password = self.new_password_input.text()
        repeat_password = self.repeat_password_input.text()

        # Ensure all fields are filled out.
        if not current_password or not new_password or not repeat_password:
            QMessageBox.warning(self, "Incomplete", "All fields are required.")
            return

        # Ensure the new passwords entered match.
        if new_password != repeat_password:
            QMessageBox.warning(self, "Mismatch", "New passwords do not match.")
            return

        # Verify the current password with the stored hash.
        if not self.verify_current_password(current_password):
            QMessageBox.warning(self, "Incorrect", "Current password is incorrect.")
            return

        # Attempt to update the password in the database and provide user feedback.
        success = self.task_manager.update_user_password(self.user_id, new_password)
        if success:
            QMessageBox.information(self, "Success", "Password changed successfully.")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Failed to change password.")

    def verify_current_password(self, password):
        """
        Verifies if the provided current password is correct by comparing it with the stored hash.

        Args:
            password (str): The current password input by the user.

        Returns:
            bool: True if the password is correct, False otherwise.
        """
        user_data = self.task_manager.get_user_data(self.user_id)
        # Validate that user data is retrieved successfully.
        if not user_data:
            return False

        # Retrieve the stored hash and salt for the password.
        stored_hashed_password, salt = user_data.get(
            'password'), user_data.get('salt')
        # Validate that the necessary data for verification is present.
        if not stored_hashed_password or not salt:
            return False

        # Hash the provided password using the retrieved salt and compare.
        hashed_password, _ = hash_password(password, salt)
        return hashed_password == stored_hashed_password
