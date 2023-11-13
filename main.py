import sys
import utils
import logging
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction
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
    QMessageBox,
    QComboBox,
    QCalendarWidget,
    QDialog,
    QDialogButtonBox,
    QSizePolicy,
    QFileDialog
)
from task_manager import TaskManager
from notification_manager import NotificationManager

# Setup logging as soon as possible, ideally at the start of the application
utils.setup_logging()

# Constants
DEFAULT_USER = utils.get_env_variable('DEFAULT_USER')
DEFAULT_PASSWORD = utils.get_env_variable('DEFAULT_PASSWORD')

# Initialize the task ID to row mapping dictionary
task_row_to_id = {}


class TaskTracker(QThread):
    notify_due_tasks = pyqtSignal(list)

    def __init__(self, task_manager):
        super().__init__()
        self.task_manager = task_manager

    def run(self):
        while True:
            self.sleep(10)  # Check every hour
            logging.info("Checking for due tasks...")
            today_tasks = self.task_manager.get_due_tasks()
            if today_tasks:
                self.notify_due_tasks.emit(today_tasks)
                logging.info(f"Found {len(today_tasks)} due tasks.")
            else:
                logging.info("No tasks due today.")


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

        self.task_manager = task_manager
        self.notification_manager = NotificationManager()
        self.task_tracker = TaskTracker(task_manager)

        self.setWindowTitle("To-Do List Manager")
        self.setGeometry(100, 100, 800, 600)
        self.resize(800, 600)

        # Create and set the central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Setup UI components and layout
        self.setup_ui()

        # Start the task tracker thread
        self.task_tracker.notify_due_tasks.connect(self.notify_due_tasks)
        self.task_tracker.start()

    def setup_ui(self):
        # Create a layout for the central widget
        layout = QVBoxLayout()
        self.centralWidget().setLayout(layout)

        # Create task input fields and labels
        task_name_label = QLabel("Task Name:")
        self.task_name_input = QLineEdit()
        due_date_label = QLabel("Due Date:")
        self.due_date_input = QLineEdit()

        # Setup date picker dialog
        self.date_picker_dialog = QDialog()
        date_picker_layout = QVBoxLayout(self.date_picker_dialog)
        self.calendar_widget = QCalendarWidget()
        date_picker_layout.addWidget(self.calendar_widget)
        date_picker_button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        date_picker_button_box.accepted.connect(self.date_picker_dialog.accept)
        date_picker_button_box.rejected.connect(self.date_picker_dialog.reject)
        date_picker_layout.addWidget(date_picker_button_box)

        # Connect the date picker function to the input field's click event
        self.due_date_input.mousePressEvent = lambda event: self.show_date_picker()

        # Add widgets to layout
        layout.addWidget(task_name_label)
        layout.addWidget(self.task_name_input)
        layout.addWidget(due_date_label)
        layout.addWidget(self.due_date_input)

        # Create vertical layouts for Priority and Category
        priority_layout = QVBoxLayout()
        category_layout = QVBoxLayout()

        # Create the Priority Label
        priority_label = QLabel("Priority:")
        self.priority_combobox = QComboBox()
        # Load priorities from the TaskManager
        priorities = self.task_manager.load_priorities()
        self.priority_combobox.addItems(priorities)
        priority_layout.addWidget(priority_label)
        priority_layout.addWidget(self.priority_combobox)

        # Create the Category Label
        category_label = QLabel("Category:")
        self.category_combobox = QComboBox()
        # Load categories from the TaskManager
        categories = self.task_manager.load_categories()
        self.category_combobox.addItems(categories)
        category_layout.addWidget(category_label)
        category_layout.addWidget(self.category_combobox)

        # Create a horizontal layout and add the vertical layouts to it
        priority_category_layout = QHBoxLayout()
        priority_category_layout.addLayout(priority_layout)
        priority_category_layout.addLayout(category_layout)

        # Add the priority_category_layout to the main vertical layout
        layout.addLayout(priority_category_layout)

        # Create buttons and add them to layout
        add_button = QPushButton("Add Task")
        add_button.clicked.connect(self.add_task)
        remove_button = QPushButton("Remove Selected Task(s)")
        remove_button.clicked.connect(self.remove_selected_task)
        edit_button = QPushButton("Edit Selected Task")
        edit_button.clicked.connect(self.edit_selected_task)

        # Horizontal layout for buttons
        button_layout = QHBoxLayout()
        button_layout.addWidget(add_button)
        button_layout.addWidget(remove_button)
        button_layout.addWidget(edit_button)
        layout.addLayout(button_layout)

        # Create and set up the task table
        self.task_table_widget = QTableWidget()
        self.setup_table_widget()
        layout.addWidget(self.task_table_widget)

        # Update the task list to populate the table and menu
        self.update_task_list()
        self.setup_menu_widget()

    def show_date_picker(self):
        if self.date_picker_dialog.exec() == QDialog.DialogCode.Accepted:
            selected_date = self.calendar_widget.selectedDate()
            self.due_date_input.setText(
                selected_date.toString(Qt.DateFormat.ISODate))

    def apply_table_style(self):
        header_style = "QHeaderView::section { border-top: 1px solid grey; border-bottom: 1px solid grey; padding-left: 5px; }"
        row_style = "QTableWidget::item { border-bottom: 1px solid grey; }"
        self.task_table_widget.horizontalHeader().setStyleSheet(header_style)
        self.task_table_widget.setStyleSheet(row_style)
        self.task_table_widget.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)

    def setup_table_widget(self):
        # Set up the task table widget
        self.task_table_widget.setColumnCount(4)
        self.task_table_widget.setHorizontalHeaderLabels(["Task Name", "Due Date", "Priority", "Category"])
        self.task_table_widget.horizontalHeader().setStretchLastSection(True)
        self.task_table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.task_table_widget.verticalHeader().setVisible(False)
        self.task_table_widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.task_table_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Apply the table style
        self.apply_table_style()


    def setup_menu_widget(self):
        # Create a menu bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")  # Create a "File" menu

        # Add a "Logout" action to the "File" menu
        logout_action = file_menu.addAction("Logout")
        logout_action.triggered.connect(self.logout)

        # Add Export action
        export_action = QAction("&Export", self)
        export_action.triggered.connect(self.export_tasks)
        file_menu.addAction(export_action)

        # Add Import action
        import_action = QAction("&Import", self)
        import_action.triggered.connect(self.import_tasks)
        file_menu.addAction(import_action)

        # Create a widget to hold the table widget and add it to the main layout
        table_widget_container = QWidget()
        table_widget_container.setLayout(QVBoxLayout())
        table_widget_container.layout().addWidget(self.task_table_widget)  # Changed here
        self.centralWidget().layout().addWidget(table_widget_container)  # Changed here

    def clear_entries(self):
        self.task_name_input.clear()
        self.due_date_input.clear()
        self.priority_combobox.setCurrentIndex(0)
        self.category_combobox.setCurrentIndex(0)

    # Function to add a new task
    def add_task(self):
        task_name = self.task_name_input.text().strip()

        if not task_name:
            utils.show_error("Task Name Required", "Please enter a task name.")
            return

        due_date = self.due_date_input.text().strip()
        priority = self.priority_combobox.currentText()
        category = self.category_combobox.currentText()

        task = (
            task_name,  # 0
            due_date,   # 1
            priority,   # 2
            category    # 3
        )

        # Add the task to the database
        error_message, task_id = self.task_manager.add_task(*task)

        if error_message:
            utils.show_error("Task Addition Error", error_message)
        else:
            # Retrieve the last inserted task ID
            if task_id is not None:
                # Add the task to the table and map it to the task ID
                row_position = self.task_table_widget.rowCount()
                self.task_table_widget.insertRow(row_position)
                self.task_table_widget.setItem(row_position, 0, QTableWidgetItem(task_name))
                self.task_table_widget.setItem(row_position, 1, QTableWidgetItem(due_date))
                self.task_table_widget.setItem(row_position, 2, QTableWidgetItem(priority))
                self.task_table_widget.setItem(row_position, 3, QTableWidgetItem(category))

                # Update the task ID to row mapping
                task_row_to_id[task_id] = row_position

                # Refresh the task list and clear the input fields
                self.update_task_list()
                self.clear_entries()
                utils.send_windows_notification("Task Added", f"Task added successfully! ID: {task_id}")
            else:
                utils.show_error("Task ID Error", "Failed to retrieve the task ID.")

    def remove_selected_task(self):
        selected_items = self.task_table_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a task to remove.")
            return

        # Confirm before removing tasks
        reply = QMessageBox.question(self, "Confirm Removal", "Are you sure you want to remove the selected tasks?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return

        selected_task_ids = []

        for item in selected_items:
            row = item.row()
            task_id = task_row_to_id.get(row)
            if task_id is not None:
                selected_task_ids.append(task_id)

        # Bulk remove tasks from database (implement this in TaskManager)
        try:
            self.task_manager.remove_tasks(selected_task_ids)
            utils.send_windows_notification("Success", "Tasks successfully removed.")
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return

        # Efficiently update the table
        self.update_task_list()
        self.apply_table_style()
        self.clear_entries()

        logging.info(f"Removed tasks: {selected_task_ids}")

    def edit_selected_task(self):
        selected_items = self.task_table_widget.selectedItems()
        if not selected_items:
            utils.show_error("No Task Selected","Please select a task to edit.")
            return

        row = selected_items[0].row()
        task_id = task_row_to_id.get(row)
        task_details = self.task_manager.get_task_details(task_id)

        if task_details:
            self.populate_edit_dialog(task_details)

    def populate_edit_dialog(self, task_details):
        # Open a dialog to edit task details
        edit_dialog = EditTaskDialog(task_details, self.task_manager)
        if edit_dialog.exec() == QDialog.DialogCode.Accepted:
            # Update task details in the database
            updated_details = edit_dialog.get_updated_details()
            self.task_manager.update_task(task_details[0], *updated_details)
            self.update_task_list()

    # Function to update the task list
    def update_task_list(self):
        tasks = self.task_manager.list_tasks()

        # Sort tasks by due date in ascending order (earliest due date first)
        tasks.sort(key=lambda task: task[1])  # Assuming task[1] is the due date

        # Reverse the order to get highest due date first
        tasks.reverse()

        # Clear the existing task_row_to_id dictionary and the table
        task_row_to_id.clear()
        self.task_table_widget.setRowCount(len(tasks))

        for row, task in enumerate(tasks):
            # Assuming the task tuple is structured as (id, name, due_date, priority, category)
            task_id = task[0]
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

            # Set items in the table
            self.task_table_widget.setItem(row, 0, name_item)
            self.task_table_widget.setItem(row, 1, due_date_item)
            self.task_table_widget.setItem(row, 2, priority_item)
            self.task_table_widget.setItem(row, 3, category_item)

            # Populate the task ID to row mapping
            task_row_to_id[row] = task_id  # Map row index to task ID

        self.task_table_widget.resizeColumnsToContents()
        self.apply_table_style()  # Apply the table style after updating

        # Set the size policy again to make sure it's effective
        self.task_table_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def logout(self):
        # Close the session
        self.close()
        self.login_dialog.show()

    def notify_due_tasks(self, tasks):
        # Notify the user about due tasks
        # This could be updating a status bar, displaying a message box, etc.
        for task in tasks:
            notification_id = f"task_due_{task}"  # Unique ID for each task
            if self.notification_manager.send_notification(
                notification_id,
                "Task Due",
                f"Task '{task}' is due today.",
                frequency="hourly"
            ):
                logging.info(f"Notification sent for task: {task}")
            else:
                logging.info(f"Notification already sent for task: {task}")

    def export_tasks(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Export Tasks", "", "CSV Files (*.csv)")
        if file_name:
            try:
                message = self.task_manager.export_tasks(file_name)
                utils.send_windows_notification("Export Successful", message)

            except Exception as e:
                logging.error("An error occurred while exporting tasks: {e}")

    def import_tasks(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Import Tasks", "", "CSV Files (*.csv)")
        if file_name:
            try:
                message = self.task_manager.import_tasks(file_name)
                # Refresh the task list in the UI
                self.update_task_list()
                QMessageBox.information(self, "Import Successful", message)
            except Exception as e:
                QMessageBox.critical(self, "Import Failed", f"An error occurred while importing tasks: {e}")

class EditTaskDialog(QDialog):
    def __init__(self, task_details, task_manager):
        super().__init__()
        self.task_details = task_details
        self.task_manager = task_manager

        self.setWindowTitle("Edit Task")
        layout = QVBoxLayout(self)

        # Add input fields for task name, due date, priority, and category
        self.name_input = QLineEdit()
        self.due_date_input = QLineEdit()
        self.priority_combobox = QComboBox()
        self.category_combobox = QComboBox()

        # Populate the comboboxes with existing priorities and categories
        self.priority_combobox.addItems(self.task_manager.load_priorities())
        self.category_combobox.addItems(self.task_manager.load_categories())

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
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
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

def main():
    app = QApplication(sys.argv)

    try:

        # Create an instance of TaskManager
        task_manager = TaskManager()

        # Check if there are existing users
        existing_users = task_manager.get_existing_users()

        if not existing_users:
            # If there are no users, create a default user with a timestamp
            error_message = task_manager.create_user(
                DEFAULT_USER, DEFAULT_PASSWORD)
            if error_message:
                utils.show_error("User Creation Error", error_message)
            else:
                print(f"Default user '{DEFAULT_USER}' created with password '{DEFAULT_PASSWORD}'")
        else:
            print("Users already exist in the database.")

        # Create the login dialog instance first
        login_dialog = LoginDialog(task_manager)

        if login_dialog.exec() == QDialog.DialogCode.Accepted:
            # Show the main window only if login is successful
            # Create the main window instance
            main_window = MainWindow(task_manager)
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
