import os
import sys
import utils
import logging
from dotenv import load_dotenv
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
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QComboBox,
    QCalendarWidget,
    QDialog,
    QDialogButtonBox,
    QSizePolicy
)
from task_manager import TaskManager

logging.basicConfig(level=logging.INFO, filename='app.log', format='%(asctime)s - %(levelname)s - %(message)s')

# load environment variables from .env file
load_dotenv()

# Constants
DEFAULT_USER = utils.get_env_variable('DEFAULT_USER')
DEFAULT_PASSWORD = utils.get_env_variable('DEFAULT_PASSWORD')

# Initialize the task ID to row mapping dictionary
task_row_to_id = {}

class LoginDialog(QDialog):
    def __init__(self, task_manager):
        super().__init__()

        self.task_manager = task_manager

        self.setWindowTitle("Login")
        self.username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.try_login)

        layout = QVBoxLayout()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        self.setLayout(layout)

    def try_login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        # Check the credentials using the verify_user method
        if self.task_manager.verify_user(username, password):
            self.accept()  # Close the dialog and return QDialog.Accepted
        else:
            # Display an error message or handle failed login
            utils.show_error("Login Failed", "Invalid username or password.")

class MainWindow(QMainWindow):
    def __init__(self, task_manager):
        super().__init__()

        self.setWindowTitle("To-Do List Manager")
        self.setGeometry(100, 100, 800, 600)
        self.resize(800, 600)

        # Create a central widget and set it as the main window's central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Store the task_manager instance
        self.task_manager = task_manager

        # Create an instance of LoginDialog and pass the main window reference
        self.login_dialog = LoginDialog(task_manager)
        self.login_dialog.main_window = self  # Set the main window reference

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

        # Create the Priority Label
        priority_label = QLabel("Priority:")
        priority_combobox = QComboBox()
        priorities = self.task_manager.load_priorities() # Load priorities from the TaskManager
        priority_combobox.addItems(priorities)
        layout.addWidget(priority_label)
        layout.addWidget(priority_combobox)

        # Create the Category Label
        category_label = QLabel("Category:")
        category_combobox = QComboBox()
        categories = self.task_manager.load_categories() # Load categories from the TaskManager
        category_combobox.addItems(categories)
        layout.addWidget(category_label)
        layout.addWidget(category_combobox)

        # Create buttons
        add_button = QPushButton("Add Task")
        remove_button = QPushButton("Remove Selected Task(s)")

        # Create a table widget to display tasks
        task_table_widget = QTableWidget()
        task_table_widget.setShowGrid(True)  # Set to True to show grid lines
        task_table_widget.setColumnCount(4)  # Number of columns
        task_table_widget.setHorizontalHeaderLabels(["Task Name", "Due Date", "Priority", "Category"])  # Set column headers

        # Make the table widget expand horizontally and vertically with the window
        task_table_widget.horizontalHeader().setStretchLastSection(True)
        task_table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        task_table_widget.verticalHeader().setVisible(False)  # Hide vertical header

        # Set the size policy to make the table widget expand horizontally and vertically
        task_table_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        # Function to apply the table style
        def apply_table_style():
            # Set border style for header and rows
            header_style = "QHeaderView::section { border-top: 1px solid grey; border-bottom: 1px solid grey; padding-left: 5px; }"
            row_style = "QTableWidget::item { border-bottom: 1px solid grey; }"
            task_table_widget.horizontalHeader().setStyleSheet(header_style)
            task_table_widget.setStyleSheet(row_style)
            task_table_widget.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)

        # Function to update the task list
        def update_task_list():
            tasks = self.task_manager.list_tasks()

            # Sort tasks by due date in ascending order (earliest due date first)
            tasks.sort(key=lambda task: task[1])

            # Reverse the order to get highest due date first
            tasks.reverse()

            task_table_widget.setRowCount(len(tasks))

            # Clear the existing task_row_to_id dictionary
            task_row_to_id.clear()

            for row, task in enumerate(tasks):
                name_item = QTableWidgetItem(task[1])
                due_date_item = QTableWidgetItem(task[2])
                priority_item = QTableWidgetItem(task[3])
                category_item = QTableWidgetItem(task[4])

                # Set text alignment to left
                name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                due_date_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                priority_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                category_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

                # Set item flags to make cells read-only
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                due_date_item.setFlags(due_date_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                priority_item.setFlags(priority_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                category_item.setFlags(category_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                task_table_widget.setItem(row, 0, name_item)
                task_table_widget.setItem(row, 1, due_date_item)
                task_table_widget.setItem(row, 2, priority_item)
                task_table_widget.setItem(row, 3, category_item)

                # Populate the task ID to row mapping
                task_row_to_id[row] = task[0]  # Map row index to task ID

            task_table_widget.resizeColumnsToContents()
            apply_table_style()  # Apply the table style after updating

            # Set the size policy again to make sure it's effective
            task_table_widget.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )

        # Function to clear input fields
        def clear_entries():
            task_name_input.clear()
            due_date_input.clear()
            priority_combobox.setCurrentIndex(0)
            category_combobox.setCurrentIndex(0)

        # Function to add a new task
        def add_task():
            task_name = task_name_input.text().strip()

            if not task_name:
                utils.show_error("Task Name Required", "Please enter a task name.")
                return

            due_date = due_date_input.text().strip()
            priority = priority_combobox.currentText()
            category = category_combobox.currentText()

            task = (
                task_name,  # 0
                due_date,   # 1
                priority,   # 2
                category    # 3
            )

            error_message, task_id = self.task_manager.add_task(*task)

            if error_message:
                utils.show_error("Task Addition Error", error_message)
            else:
                # Retrieve the last inserted task ID
                if task_id is not None:
                    # Add the task to the table and map it to the task ID
                    row_position = task_table_widget.rowCount()
                    task_table_widget.insertRow(row_position)
                    task_table_widget.setItem(row_position, 0, QTableWidgetItem(task_name))
                    task_table_widget.setItem(row_position, 1, QTableWidgetItem(due_date))
                    task_table_widget.setItem(row_position, 2, QTableWidgetItem(priority))
                    task_table_widget.setItem(row_position, 3, QTableWidgetItem(category))

                    # Update the task ID to row mapping
                    task_row_to_id[task_id] = row_position

                    update_task_list()  # Update the table and sort by due date
                    clear_entries()
                    utils.show_message("Task Added", f"Task added successfully! ID: {task_id}")
                else:
                    utils.show_error("Task ID Error", "Failed to retrieve the task ID.")

        # Function to delete a task by ID
        def delete_task_by_id(task_id):
            if task_id in task_row_to_id:
                row = task_row_to_id[task_id]
                task_table_widget.removeRow(row)
                del task_row_to_id[task_id]

            update_task_list()  # Update the table and sort by due date

        # Function to remove selected task(s)
        def remove_selected_task():
            selected_items = task_table_widget.selectedItems()

            if not selected_items:
                utils.show_error("No Task Selected", "Please select a task to remove.")
                return

            selected_task_ids = []

            for selected_item in selected_items:
                selected_row = selected_item.row()
                selected_task_id = task_row_to_id.get(selected_row)

                if selected_task_id is not None:
                    selected_task_ids.append(selected_task_id)

            for selected_task_id in selected_task_ids:
                error_message = self.task_manager.remove_task(selected_task_id)

                if error_message:
                    utils.show_error("Task Removal Error", error_message)

            # Delete the selected rows from the table
            selected_rows = {item.row() for item in selected_items}
            for selected_row in sorted(selected_rows, reverse=True):
                task_table_widget.removeRow(selected_row)

            update_task_list()
            clear_entries()

        # Connect button click events to functions
        add_button.clicked.connect(add_task)
        remove_button.clicked.connect(remove_selected_task)

        # Create a horizontal layout for buttons
        button_layout = QHBoxLayout()
        button_layout.addWidget(add_button)
        button_layout.addWidget(remove_button)

        # Add widgets to the main layout
        layout.addLayout(button_layout)

        # Create a menu bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File") # Create a "File" menu

        # Add a "Logout" action to the "File" menu
        logout_action = file_menu.addAction("Logout")
        logout_action.triggered.connect(self.logout)

        # Create a widget to hold the table widget and add it to the main layout
        table_widget_container = QWidget()
        table_widget_container.setLayout(QVBoxLayout())
        table_widget_container.layout().addWidget(task_table_widget)
        layout.addWidget(table_widget_container)

        # Set the menu bar for the main window
        self.setMenuBar(menu_bar)

        # Apply the table style initially
        apply_table_style()

        # Load tasks from the database and populate the table widget
        update_task_list()

        # Set the layout for the central widget
        central_widget.setLayout(layout)

    def logout(self):
        # Close the session
        self.close()
        self.login_dialog.show()

def main():
    app = QApplication(sys.argv)

    try:

        # Create an instance of TaskManager
        task_manager = TaskManager()

        # Check if there are existing users
        existing_users = task_manager.get_existing_users()

        if not existing_users:
            # If there are no users, create a default user with a timestamp
            error_message = task_manager.create_user(DEFAULT_USER, DEFAULT_PASSWORD)
            if error_message:
                utils.show_error("User Creation Error", error_message)
            else:
                print(f"Default user '{DEFAULT_USER}' created with password '{DEFAULT_PASSWORD}'")
        else:
            print("Users already exist in the database.")

        login_dialog = LoginDialog(task_manager)  # Create the login dialog instance first

        if login_dialog.exec() == QDialog.DialogCode.Accepted:
            # Show the main window only if login is successful
            main_window = MainWindow(task_manager)  # Create the main window instance
            main_window.show()
            sys.exit(app.exec())
        else:
            # Handle login failure (e.g., display an error message)
            print("Login failed.")

    except ValueError as e:
        print(f"Environment variable validation error: {e}")
        # Handle the error appropriately (e.g., log it, inform the user, exit the application)

if __name__ == "__main__":
    main()
