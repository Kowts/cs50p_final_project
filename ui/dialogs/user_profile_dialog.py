from PyQt6.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QDialog,
    QDialogButtonBox
)
from PyQt6.QtGui import QIcon
from models.task_manager import TaskManager
from services.preferences import PreferencesManager
from helpers.utils import send_windows_notification

class UserProfileDialog(QDialog):
    def __init__(self, task_manager: TaskManager, user_id):
        super().__init__()
        self.task_manager = task_manager
        self.user_id = user_id
        self.preferences_manager = PreferencesManager(self, self.task_manager, user_id)  # Initialize PreferencesManager

        # application icon and title
        self.setWindowIcon(QIcon('resources/favicon.ico'))
        self.setWindowTitle("Edit Profile")
        self.setGeometry(300, 300, 300, 200)

        self.init_ui()
        self.load_user_data()

        self.preferences_manager.load_and_apply_preferences()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Name label and input
        name_label = QLabel("Name")
        layout.addWidget(name_label)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Name")
        layout.addWidget(self.name_input)

        # Username label and input
        username_label = QLabel("Username")
        layout.addWidget(username_label)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(self.username_input)

        # Email label and input
        email_label = QLabel("Email")
        layout.addWidget(email_label)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        layout.addWidget(self.email_input)
        layout.addStretch()

        # Add OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.save_profile)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def load_user_data(self):
        # Load user data from the database and populate the fields
        user_data = self.task_manager.get_user_data(self.user_id)
        if user_data:
            self.name_input.setText(user_data['name'])
            self.username_input.setText(user_data['username'])
            self.email_input.setText(user_data['email'])

    def save_profile(self):

        # Save the updated profile data to the database
        updated_name = self.name_input.text()
        updated_username = self.username_input.text()
        updated_email = self.email_input.text()

        if not updated_username or not updated_email or not updated_name:
            QMessageBox.warning(self, "Invalid Data", "Please fill all fields.")
            return

        success = self.task_manager.update_user_profile(self.user_id, updated_name, updated_username, updated_email)
        if success:
            send_windows_notification("Success", "Profile updated successfully.", self.task_manager, self.user_id)
            self.accept()
        else:
            send_windows_notification("Error", "Failed to update profile.", self.task_manager, self.user_id)
