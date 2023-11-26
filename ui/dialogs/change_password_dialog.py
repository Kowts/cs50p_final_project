from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)
from models.task_manager import TaskManager
from services.preferences import PreferencesManager
from helpers.utils import hash_password

class ChangePasswordDialog(QDialog):
    def __init__(self, task_manager: TaskManager, user_id):
        super().__init__()

        self.task_manager = task_manager
        self.preferences_manager = PreferencesManager(self, self.task_manager, user_id)  # Initialize PreferencesManager
        self.user_id = user_id

        self.setWindowTitle("Change Password")
        self.setGeometry(600, 300, 400, 200)

        self.init_ui()

        self.preferences_manager.load_and_apply_preferences()

    def init_ui(self):

        layout = QVBoxLayout(self)

        # Current Password
        current_password_label = QLabel("Current Password")
        layout.addWidget(current_password_label)
        self.current_password_input = QLineEdit()
        self.current_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.current_password_input)

        # New Password
        new_password_label = QLabel("New Password")
        layout.addWidget(new_password_label)
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.new_password_input)

        # Repeat New Password
        repeat_password_label = QLabel("Repeat New Password")
        layout.addWidget(repeat_password_label)
        self.repeat_password_input = QLineEdit()
        self.repeat_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.repeat_password_input)

        # Change Button
        button_layout = QHBoxLayout()
        change_button = QPushButton("Change Password")
        change_button.clicked.connect(self.change_password)
        button_layout.addWidget(change_button)
        layout.addLayout(button_layout)

    def change_password(self):
        current_password = self.current_password_input.text()
        new_password = self.new_password_input.text()
        repeat_password = self.repeat_password_input.text()

        if not current_password or not new_password or not repeat_password:
            QMessageBox.warning(self, "Incomplete", "All fields are required.")
            return

        if new_password != repeat_password:
            QMessageBox.warning(self, "Mismatch", "New passwords do not match.")
            return

        # Verify current password
        if not self.verify_current_password(current_password):
            QMessageBox.warning(self, "Incorrect", "Current password is incorrect.")
            return

        # Update the password in the database
        success = self.task_manager.update_user_password(
            self.user_id, new_password)
        if success:
            QMessageBox.information(self, "Success", "Password changed successfully.")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Failed to change password.")

    def verify_current_password(self, password):
        user_data = self.task_manager.get_user_data(self.user_id)
        if not user_data:
            return False

        stored_hashed_password, salt = user_data.get('password'), user_data.get('salt')
        if not stored_hashed_password or not salt:
            return False

        hashed_password, _ = hash_password(password, salt)
        return hashed_password == stored_hashed_password
