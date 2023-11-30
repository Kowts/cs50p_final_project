from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QColorDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QDialog
)
from models.task_manager import TaskManager
from helpers.utils import send_windows_notification
from services.preferences import PreferencesManager

class AddDataDialog(QDialog):
    """
    A dialog window for adding data (priority or category) to the task manager.

    Attributes:
    - data_added: A signal to notify that new data was added.
    - task_manager: The task manager object.
    - data_type: The type of data to be added ('priority' or 'category').
    - user_id: The user ID.
    """
    data_added = pyqtSignal()  # Signal to notify that new data was added

    def __init__(self, task_manager: TaskManager, data_type, user_id, parent=None):
        """
        Initialize the AddDataDialog.

        Parameters:
        - task_manager: The task manager object.
        - data_type: The type of data to be added ('priority' or 'category').
        - user_id: The user ID.
        - parent: The parent widget (default is None).
        """
        super().__init__(parent)
        self.task_manager = task_manager
        self.data_type = data_type  # 'priority' or 'category'
        self.user_id = user_id  # Store the user_id
        self.preferences_manager = PreferencesManager(self, self.task_manager, user_id)  # Initialize PreferencesManager
        self.setWindowTitle(f"Add {self.data_type.capitalize()}")
        self.setWindowIcon(QIcon('resources/favicon.ico'))
        self.init_ui()

    def init_ui(self):
        """
        Initialize the user interface of the dialog.
        """
        layout = QVBoxLayout()

        self.data_input = QLineEdit()
        layout.addWidget(QLabel("Name:"))
        layout.addWidget(self.data_input)

        if self.data_type == 'priority':
            # Add label for Color
            layout.addWidget(QLabel("Color:"))
            layout.addStretch()
            # Create layout for the color input group
            color_layout = QHBoxLayout()
            self.color_input = QLineEdit()
            self.color_input.setReadOnly(True)
            color_layout.addWidget(self.color_input)
            # Button for picking the calendar color
            self.calendar_color_button = QPushButton("Pick Color")
            self.calendar_color_button.clicked.connect(self.pick_color)
            color_layout.addWidget(self.calendar_color_button)
            # Add the horizontal layout to the main vertical layout
            layout.addLayout(color_layout)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_data)
        layout.addWidget(save_button)

        # Load and apply preferences
        self.preferences_manager.load_and_apply_preferences()

        self.setLayout(layout)

    def pick_color(self):
        """
        Opens a color dialog to allow the user to pick a color.
        """
        color = QColorDialog.getColor()
        if color.isValid():
            # Set the background color of the input field to the chosen color
            color_hex = color.name()
            self.color_input.setStyleSheet(
                f"background-color: {color_hex.upper()};")
            # Optionally, display the color's hexadecimal value in the input field
            self.color_input.setText(color_hex.upper())

    def save_data(self):
        """
        Save the entered data to the task manager.
        """
        data = self.data_input.text().strip()

        if data:
            if self.data_type == 'priority' and not self.task_manager.priority_exists(data):
                color = self.color_input.text().strip()
                self.task_manager.add_priority(data, color, self.user_id)
                send_windows_notification(
                    "Success", f"{self.data_type.capitalize()} '{data}' added.", self.task_manager, self.user_id)
                self.data_added.emit()  # Emit the signal when data is added
                self.accept()
            elif self.data_type == 'category' and not self.task_manager.category_exists(data):
                self.task_manager.add_category(data, self.user_id)
                send_windows_notification(
                    "Success", f"{self.data_type.capitalize()} '{data}' added.", self.task_manager, self.user_id)
                self.data_added.emit()  # Emit the signal when data is added
                self.accept()
            else:
                QMessageBox.warning(
                    self, "Exists", f"{self.data_type.capitalize()} '{data}' already exists.")
