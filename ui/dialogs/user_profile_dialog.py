import re
import sys
import utils
import logging
import markdown
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QMarginsF, QDate
from PyQt6.QtPrintSupport import QPrintPreviewDialog, QPrinter, QPrintDialog
from PyQt6.QtGui import QAction, QTextDocument, QPageSize, QPageLayout, QCursor, QColor, QTextCharFormat, QIcon, QShortcut, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QColorDialog,
    QCheckBox,
    QTextBrowser,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QComboBox,
    QCalendarWidget,
    QDialog,
    QDialogButtonBox,
    QSizePolicy,
    QFileDialog
)
from models.task_manager import TaskManager
from notification import NotificationManager
from preferences import PreferencesManager


class UserProfileDialog(QDialog):
    def __init__(self, task_manager: TaskManager, user_id):
        super().__init__()
        self.task_manager = task_manager
        self.user_id = user_id

        self.setWindowTitle("Edit Profile")
        self.setGeometry(300, 300, 300, 200)

        self.init_ui()
        self.load_user_data()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Username label and input
        username_label = QLabel("Username")
        layout.addWidget(username_label)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(self.username_input)

        # Password label and input
        email_label = QLabel("Password")
        layout.addWidget(email_label)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Password")
        layout.addWidget(self.email_input)
        layout.addStretch()

        # Add OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def load_user_data(self):
        # Load user data from the database and populate the fields
        user_data = self.task_manager.get_user_data(self.user_id)
        if user_data:
            self.username_input.setText(user_data['username'])
            self.email_input.setText(user_data['email'])

    def save_profile(self):
        # Save the updated profile data to the database
        updated_username = self.username_input.text()
        updated_email = self.email_input.text()

        if not updated_username or not updated_email:
            QMessageBox.warning(self, "Invalid Data",
                                "Please fill all fields.")
            return

        success = self.task_manager.update_user_profile(
            self.user_id, updated_username, updated_email)
        if success:
            QMessageBox.information(
                self, "Success", "Profile updated successfully.")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Failed to update profile.")
