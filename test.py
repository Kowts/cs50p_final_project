import sys
import json
import os
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QMessageBox,
    QComboBox,
    QCalendarWidget,
    QDialog,
    QDialogButtonBox,
)

# Constants
TASKS_FILE = 'tasks.json'

# Initialize the tasks list from a file or create an empty list
if not os.path.exists(TASKS_FILE):
    with open(TASKS_FILE, 'w') as file:
        json.dump([], file)

with open(TASKS_FILE, 'r') as file:
    tasks = json.load(file)

# Function to save tasks to the tasks file
def save_tasks():
    with open(TASKS_FILE, 'w') as file:
        json.dump(tasks, file)

# Function to add a new task
def add_task():
    task_name = task_name_input.text().strip()

    if not task_name:
        show_error("Task Name Required", "Please enter a task name.")
        return

    due_date = due_date_input.text().strip()
    priority = priority_combobox.currentText()
    category = category_combobox.currentText()

    task = {
        'name': task_name,
        'due_date': due_date,
        'priority': priority,
        'category': category,
    }

    tasks.append(task)
    save_tasks()
    update_task_list()
    clear_entries()
    show_message("Task Added", "Task added successfully!")

# Function to remove selected task(s)
def remove_selected_task():
    selected_items = task_list_widget.selectedItems()

    if not selected_items:
        show_error("No Task Selected", "Please select a task to remove.")
        return

    for selected_item in selected_items:
        selected_task_name = selected_item.text().split(' - ')[0]
        tasks[:] = [task for task in tasks if task['name'] != selected_task_name]

    save_tasks()
    update_task_list()
    clear_entries()
    show_message("Task Removed", "Selected task(s) removed successfully!")

# Function to update the task list widget
def update_task_list():
    task_list_widget.clear()
    for task in tasks:
        task_info = f"{task['name']} - {task['due_date']} - {task['priority']} - {task['category']}"
        task_list_widget.addItem(task_info)

# Function to clear input fields
def clear_entries():
    task_name_input.clear()
    due_date_input.clear()
    priority_combobox.setCurrentIndex(0)
    category_combobox.setCurrentIndex(0)

# Function to show an error message
def show_error(title, message):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec()

# Function to show an information message
def show_message(title, message):
    msg = QMessageBox()
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec()

# Create the application and main window
app = QApplication(sys.argv)
main_window = QMainWindow()
main_window.setWindowTitle("To-Do List Manager")

# Create a central widget and set it as the main window's central widget
central_widget = QWidget()
main_window.setCentralWidget(central_widget)

# Create a vertical layout for the central widget
layout = QVBoxLayout()

# Create labels and entry fields
task_name_label = QLabel("Task Name:")
task_name_input = QLineEdit()
layout.addWidget(task_name_label)
layout.addWidget(task_name_input)

due_date_label = QLabel("Due Date:")
due_date_input = QLineEdit()
layout.addWidget(due_date_label)
layout.addWidget(due_date_input)

# Create a QDialog for the date picker
date_picker_dialog = QDialog()
date_picker_dialog.setWindowTitle("Due Date Picker")
date_picker_layout = QVBoxLayout()

# Add a label for the date picker
date_picker_label = QLabel("Due Date Picker")
date_picker_layout.addWidget(date_picker_label)

calendar_widget = QCalendarWidget()
date_picker_layout.addWidget(calendar_widget)

date_picker_button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
date_picker_button_box.accepted.connect(date_picker_dialog.accept)
date_picker_button_box.rejected.connect(date_picker_dialog.reject)

date_picker_layout.addWidget(date_picker_button_box)
date_picker_dialog.setLayout(date_picker_layout)

# Function to show the date picker dialog
def show_date_picker():
    if date_picker_dialog.exec() == QDialog.DialogCode.Accepted:
        selected_date = calendar_widget.selectedDate()
        due_date_input.setText(selected_date.toString(Qt.DateFormat.ISODate))

# Connect the date picker function to the input field's click event
due_date_input.mousePressEvent = lambda event: show_date_picker()

# Create labels and input fields for priority and category
priority_label = QLabel("Priority:")
priority_combobox = QComboBox()
priority_combobox.addItems(["Low", "Medium", "High"])
layout.addWidget(priority_label)
layout.addWidget(priority_combobox)

category_label = QLabel("Category:")
category_combobox = QComboBox()
category_combobox.addItems(["Other", "Work", "Personal", "Shopping"])
layout.addWidget(category_label)
layout.addWidget(category_combobox)

# Create buttons
add_button = QPushButton("Add Task")
add_button.clicked.connect(add_task)
remove_button = QPushButton("Remove Selected Task(s)")
remove_button.clicked.connect(remove_selected_task)

button_layout = QHBoxLayout()
button_layout.addWidget(add_button)
button_layout.addWidget(remove_button)

layout.addLayout(button_layout)

# Create a list widget to display tasks
task_list_widget = QListWidget()
layout.addWidget(task_list_widget)

# Initialize the task list
update_task_list()

# Set the layout for the central widget
central_widget.setLayout(layout)

# Show the main window
main_window.show()

# Run the application
sys.exit(app.exec())
