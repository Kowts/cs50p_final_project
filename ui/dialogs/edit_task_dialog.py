from PyQt6.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QDialog,
    QDialogButtonBox,
)
from models.task_manager import TaskManager


class EditTaskDialog(QDialog):
    """
    Initializes the EditTaskDialog class.

    Args:
        task_details (tuple): The details of the task to be edited.
        task_manager (TaskManager): The task manager object.
        user_id (int): The ID of the user.

    Returns:
        None
    """

    def __init__(self, task_details, task_manager: TaskManager, user_id):
        super().__init__()
        self.task_details = task_details
        self.task_manager = task_manager
        self.user_id = user_id  # Add user_id attribute

        self.setWindowTitle("Edit Task")
        layout = QVBoxLayout(self)

        # Add input fields for task name, due date, priority, and category
        self.name_input = QLineEdit()
        self.due_date_input = QLineEdit()
        self.priority_combobox = QComboBox()
        self.category_combobox = QComboBox()

        # Populate the comboboxes with existing priorities and categories for the given user
        self.priority_combobox.addItems(
            self.task_manager.load_priorities(self.user_id))
        self.category_combobox.addItems(
            self.task_manager.load_categories(self.user_id))

        # Add widgets to layout
        layout.addWidget(QLabel("Task Name:"))
        layout.addWidget(self.name_input)
        layout.addWidget(QLabel("Due Date:"))
        layout.addWidget(self.due_date_input)
        layout.addWidget(QLabel("Priority:"))
        layout.addWidget(self.priority_combobox)
        layout.addWidget(QLabel("Category:"))
        layout.addWidget(self.category_combobox)

        # Add OK and Cancel buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Set layout to dialog
        self.setLayout(layout)

        # Populate fields with current task details
        self.populate_fields()

    def populate_fields(self):
        # Populate the fields with the current task details
        task_id, name, due_date, priority, category = self.task_details
        self.name_input.setText(name)
        self.due_date_input.setText(due_date)
        self.priority_combobox.setCurrentText(priority)
        self.category_combobox.setCurrentText(category)

    def get_updated_details(self):
        """
        Retrieves the updated task details from the dialog's input fields.
        """
        name = self.name_input.text()
        due_date = self.due_date_input.text()
        priority = self.priority_combobox.currentText()
        category = self.category_combobox.currentText()
        return (name, due_date, priority, category)
