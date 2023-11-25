import re
import logging
import markdown
from PyQt6.QtCore import Qt, pyqtSignal, QMarginsF
from PyQt6.QtPrintSupport import QPrintPreviewDialog, QPrinter, QPrintDialog
from PyQt6.QtGui import QAction, QTextDocument, QPageSize, QPageLayout, QColor, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QColorDialog,
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
from models.task_tracker import TaskTracker
from ui.dialogs.login_dialog import LoginDialog
from ui.dialogs.preferences_dialog import PreferencesDialog
from ui.dialogs.edit_task_dialog import EditTaskDialog
from ui.dialogs.calendar_dialog import CalendarDialog
from ui.dialogs.user_profile_dialog import UserProfileDialog
from ui.dialogs.find_dialog import FindDialog
from services.notification import NotificationManager
from services.preferences import PreferencesManager
from helpers.utils import show_dialog, send_windows_notification

# Initialize the task ID to row mapping dictionary
task_row_to_id = {}

class MainWindow(QMainWindow):
    """
    The main window of the To-Do List Manager application.

    Args:
        task_manager (TaskManager): An instance of the TaskManager class.
        login_dialog (LoginDialog): An instance of the LoginDialog class.
        user_id (int, optional): The ID of the user. Defaults to None.
    """

    def __init__(self, task_manager: TaskManager, login_dialog: LoginDialog, user_id=None, tasks=None):
        super().__init__()

        self.user_id = user_id  # Initialize user_id

        self.app = QApplication.instance()  # Reference to the QApplication instance
        self.task_manager = task_manager
        self.notification_manager = NotificationManager(self.task_manager, user_id)
        self.task_tracker = TaskTracker(task_manager)
        self.preferences_manager = PreferencesManager(self, self.task_manager, user_id)  # Initialize PreferencesManager

        # Store the login dialog as an attribute
        self.login_dialog = login_dialog

        # Load the icon
        self.setWindowIcon(QIcon('resources/favicon.ico'))

        # Set the window title and size
        self.setWindowTitle("ProTaskVista")
        self.setGeometry(100, 100, 800, 600)
        self.resize(800, 600)

        # Create and set the central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Setup UI components and load and apply preferences
        self.setup_ui()
        self.hide()  # Hide the main window initially
        self.preferences_manager.load_and_apply_preferences()

        # Initialize the task tracker thread
        self.task_tracker.notify_due_tasks.connect(self.notify_due_tasks)

    def setup_ui(self):
        """
        Set up the user interface for the application.
        """
        # Create a layout for the central widget
        layout = QVBoxLayout()
        self.centralWidget().setLayout(layout)

        # Create a QTextEdit for displaying tasks
        self.task_text_edit = QTextEdit()

        # Create task input fields and labels
        task_name_label = QLabel("Task Name:")
        self.task_name_input = QLineEdit()
        due_date_label = QLabel("Due Date:")
        self.due_date_input = QLineEdit()

        # Add widgets to layout
        layout.addWidget(task_name_label)
        layout.addWidget(self.task_name_input)
        layout.addWidget(due_date_label)
        layout.addWidget(self.due_date_input)

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

        # Create vertical layouts for Priority and Category
        priority_layout = QVBoxLayout()
        category_layout = QVBoxLayout()

        # Create the Priority Label
        priority_label = QLabel("Priority:")
        self.priority_combobox = QComboBox()
        # Load priorities from the TaskManager
        priorities = self.task_manager.load_priorities(self.user_id)
        self.priority_combobox.addItems(priorities)
        priority_layout.addWidget(priority_label)
        priority_layout.addWidget(self.priority_combobox)

        # Create the Category Label
        category_label = QLabel("Category:")
        self.category_combobox = QComboBox()
        # Load categories from the TaskManager
        categories = self.task_manager.load_categories(self.user_id)
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
        refresh_button = QPushButton("Refresh Task(s)")
        refresh_button.clicked.connect(self.refresh_task)

        # Horizontal layout for buttons
        button_layout = QHBoxLayout()
        button_layout.addWidget(add_button)
        button_layout.addWidget(remove_button)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(refresh_button)
        layout.addLayout(button_layout)

        # Create and set up the task table
        self.task_table_widget = QTableWidget()
        self.setup_table_widget()
        layout.addWidget(self.task_table_widget)

        # Update the task list to populate the table and menu
        self.update_task_list()
        self.setup_menu_widget()

    def start_task_tracker(self):
        """Starts the task tracker to check for due tasks."""
        self.task_tracker.start()

    def set_attribute(self, attribute_name, value):
        # Dynamically sets a user attribute.
        setattr(self, attribute_name, value)

    def show_calendar_dialog(self):
        # Opens a calendar dialog for the user to interact with.
        self.calendar_dialog = CalendarDialog(self.task_manager, self.user_id)
        self.calendar_dialog.exec()

    def show_date_picker(self):
        # Display a date picker dialog and set the selected date as the text of the due date input field.
        if self.date_picker_dialog.exec() == QDialog.DialogCode.Accepted:
            selected_date = self.calendar_widget.selectedDate()
            self.due_date_input.setText(
                selected_date.toString(Qt.DateFormat.ISODate))

    def apply_table_style(self):
        # Apply custom table styles to the task_table_widget.
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
        data_menu = menu_bar.addMenu("&Data")  # Create the Data menu
        settings_menu = menu_bar.addMenu(
            "&Settings")  # Create the Settings menu
        help_menu = menu_bar.addMenu("&Help")  # Create the Help menu

        # Create Export action
        export_action = QAction("&Export", self)
        export_action.setShortcut("Ctrl+Shift+E")
        export_action.triggered.connect(self.export_tasks)
        file_menu.addAction(export_action)

        # Create Import action
        import_action = QAction("&Import", self)
        import_action.setShortcut("Ctrl+Shift+I")
        import_action.triggered.connect(self.import_tasks)
        file_menu.addAction(import_action)

        # Add a separator line
        file_menu.addSeparator()

        # Create and add the Preview action
        preview_action = QAction("Pre&view", self)
        preview_action.triggered.connect(self.preview_data)
        file_menu.addAction(preview_action)

        # Add the Print action
        print_action = QAction("&Print", self)
        print_action.triggered.connect(self.print_data)
        file_menu.addAction(print_action)

        # Add a separator line
        file_menu.addSeparator()

        # Add a "Logout" action
        logout_action = file_menu.addAction("Logout")
        logout_action.setShortcut("F12")
        logout_action.triggered.connect(self.logout)

        # Add a Find action
        find_action = QAction("&Find", self)
        find_action.setShortcut("Ctrl+F")
        find_action.triggered.connect(self.show_find_dialog)
        data_menu.addAction(find_action)

        # Create Preferences action
        calendar_action = QAction("&Calendar", self)
        calendar_action.triggered.connect(self.show_calendar_dialog)
        data_menu.addAction(calendar_action)

        # Add a separator line
        data_menu.addSeparator()

        # Add "Add Priority" action
        add_priority_action = QAction("Add &Priority", self)
        add_priority_action.triggered.connect(self.show_add_priority_dialog)
        data_menu.addAction(add_priority_action)

        # Add "Add Category" action
        add_category_action = QAction("Add &Category", self)
        add_category_action.triggered.connect(self.show_add_category_dialog)
        data_menu.addAction(add_category_action)

        # Create User Guide action
        user_guide_action = QAction("&User Guide", self)
        user_guide_action.setShortcut("F1")
        user_guide_action.triggered.connect(self.show_user_guide)
        help_menu.addAction(user_guide_action)

        # Create About action
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

        # Create Preferences action
        preferences_action = QAction("&Preferences", self)
        preferences_action.triggered.connect(self.show_preferences_dialog)
        settings_menu.addAction(preferences_action)

        # Create Profile action
        profile_action = QAction("&Profile", self)
        profile_action.triggered.connect(self.show_user_profile_dialog)
        settings_menu.addAction(profile_action)

        # Create a widget to hold the table widget and add it to the main layout
        table_widget_container = QWidget()
        table_widget_container.setLayout(QVBoxLayout())
        table_widget_container.layout().addWidget(self.task_table_widget)  # Changed here
        self.centralWidget().layout().addWidget(table_widget_container)  # Changed here

    def show_user_guide(self):
        """
        Display the user guide dialog with the content of the README.md file.
        """
        # Create the dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("User Guide")
        dialog.resize(650, 450)  # Set the dialog size

        # Create a layout
        layout = QVBoxLayout()

        # Create a QTextBrowser widget to display HTML
        text_browser = QTextBrowser(dialog)

        # Read the README.md file content
        with open('README.md', 'r', encoding='utf-8') as file:
            readme_content = file.read()
            # Convert Markdown content to HTML
            html_content = markdown.markdown(readme_content)
            # Set the HTML content to the text browser
            text_browser.setHtml(html_content)

        # Add the text browser to the layout
        layout.addWidget(text_browser)

        # Add a button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        # Close the dialog when OK is clicked
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)

        # Set the layout on the dialog
        dialog.setLayout(layout)

        # Execute the dialog
        dialog.exec()

    def show_user_profile_dialog(self):
        """
        Opens a user profile dialog for the current user.
        """
        profile_dialog = UserProfileDialog(self.task_manager, self.user_id)
        profile_dialog.exec()

    def show_about_dialog(self):
        """
        Display an about dialog with information about the application.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("About Application")

        layout = QVBoxLayout()

        # Application title
        title = QLabel("Task Manager")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Version and other details
        version = QLabel("Version 1.0.0")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

        # Description
        copyright = QLabel("Copyright © 2023")
        copyright.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(copyright)

        # Developer
        developer = QLabel("Joselito Coutinho")
        developer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(developer)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)

        dialog.setLayout(layout)
        dialog.exec()

    def show_preferences_dialog(self):
        # Opens the Preferences Dialog where users can change application settings.
        dialog = PreferencesDialog(self.task_manager, self.preferences_manager, self)
        dialog.exec()

    def show_add_priority_dialog(self):
        # Opens a dialog to add a new priority.
        dialog = AddDataDialog(self.task_manager, 'priority', self.user_id)
        dialog.data_added.connect(self.update_dropdowns)
        dialog.exec()

    def show_add_category_dialog(self):
        # Opens a dialog to add a new category.
        dialog = AddDataDialog(self.task_manager, 'category', self.user_id)
        dialog.data_added.connect(self.update_dropdowns)
        dialog.exec()

    def show_find_dialog(self):
        # Displays the Find Dialog, allowing users to search for tasks.
        self.find_dialog = FindDialog(self.task_text_edit, self.task_manager, self.user_id)
        self.find_dialog.search_initiated.connect(self.search_database)
        self.find_dialog.show()

    def update_dropdowns(self):
        # Refresh priority dropdown
        self.priority_combobox.clear()
        priorities = self.task_manager.load_priorities(self.user_id)
        self.priority_combobox.addItems(priorities)

        # Refresh category dropdown
        self.category_combobox.clear()
        categories = self.task_manager.load_categories(self.user_id)
        self.category_combobox.addItems(categories)

    def search_database(self, text, match_case, whole_word, use_regex):

        # Perform the database search and update the table
        # This method will need to construct a SQL query based on the search parameters
        if not text:
            # Optionally, alert the user that the search text is empty
            return

        # Establish a database connection
        with self.task_manager.get_db_connection() as conn:

            # If regex search is enabled, define a REGEXP function
            if use_regex:
                def regexp(expr, item):
                    reg = re.compile(
                        expr, re.IGNORECASE if not match_case else 0)
                    return reg.search(item) is not None

                conn.create_function("REGEXP", 2, regexp)
                search_query = "SELECT name, due_date, priority, category FROM tasks WHERE user_id = ? AND name REGEXP ? AND status = 1"
                parameters = [self.user_id, text]
            else:
                like_clause = f"%{text}%"
                search_query = "SELECT name, due_date, priority, category FROM tasks WHERE user_id = ? AND name LIKE ? AND status = 1"
                parameters = [self.user_id, like_clause]

                if match_case:
                    # Add COLLATE RTRIM to enforce case-sensitive search in SQLite
                    search_query = "SELECT name, due_date, priority, category FROM tasks WHERE user_id = ? AND name COLLATE RTRIM LIKE ? AND status = 1"

                if whole_word:
                    # SQLite does not natively support whole-word search, so will use spaces
                    # to attempt to match whole words (this is a simple workaround and may not be perfect)
                    search_query = "SELECT name, due_date, priority, category FROM tasks WHERE " \
                        "user_id = ? AND (name LIKE ? OR name LIKE ? OR name LIKE ? OR name = ?) AND status = 1"
                    parameters = (
                        self.user_id, f"{text} %", f"% {text}", f"% {text} %", text)

            # Execute the query
            try:
                tasks = self.task_manager.custom_query(search_query, parameters, use_regex=use_regex)
                self.update_table(tasks)
            except Exception as e:
                # Handle any exceptions that occur during the query
                logging.error(f"An error occurred: {e}")

    def update_table(self, tasks):
        # Update the table with the results
        self.task_table_widget.setRowCount(0)  # Clear the table first
        for task in tasks:
            # Assuming a task is a tuple like (id, name, due_date, priority, category)
            row_position = self.task_table_widget.rowCount()
            self.task_table_widget.insertRow(row_position)

            # Add items to the table
            for column, task_data in enumerate(task):
                item = QTableWidgetItem(str(task_data))
                self.task_table_widget.setItem(row_position, column, item)

        # Resize columns to fit content and update the style
        self.task_table_widget.resizeColumnsToContents()
        self.apply_table_style()

    def clear_entries(self):
        """
        Clears the input fields and resets the comboboxes to their default values.
        """
        self.task_name_input.clear()
        self.due_date_input.clear()
        self.priority_combobox.setCurrentIndex(0)
        self.category_combobox.setCurrentIndex(0)

    # Function to add a new task
    def add_task(self):
        """
        Adds a task to the task manager.

        Retrieves the task name, due date, priority, and category from the input fields.
        Validates the task name and displays an error message if it is empty.
        Adds the task to the database using the task manager's add_task method.
        If successful, adds the task to the table and maps it to the task ID.
        Updates the task list, clears the input fields, and sends a Windows notification.
        """
        task_name = self.task_name_input.text().strip()

        if not task_name:
            show_dialog("Task Name Required", "Please enter a task name.", icon=QMessageBox.Icon.Critical)
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
        error_message, task_id = self.task_manager.add_task(self.user_id, *task)

        if error_message:
            show_dialog("Task Addition Error", error_message, icon=QMessageBox.Icon.Critical)
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
                send_windows_notification("Task Added", f"Task added successfully! ID: {task_id}", self.task_manager, self.user_id)
            else:
                show_dialog("Task ID Error", "Failed to retrieve the task ID.", icon=QMessageBox.Icon.Critical)

    def remove_selected_task(self):
        """
        Removes the selected tasks from the task table.
        """
        selected_items = self.task_table_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection",
                                "Please select a task to remove.")
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
            send_windows_notification("Success", "Tasks successfully removed.", self.task_manager, self.user_id)
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return

        # Efficiently update the table
        self.update_task_list()
        self.apply_table_style()
        self.clear_entries()

        logging.info(f"Removed tasks: {selected_task_ids}")

    def edit_selected_task(self):
        """
        Edit the selected task.
        """
        selected_items = self.task_table_widget.selectedItems()
        if not selected_items:
            show_dialog("No Task Selected", "Please select a task to edit.", icon=QMessageBox.Icon.Critical)
            return

        row = selected_items[0].row()
        task_id = task_row_to_id.get(row)
        task_details = self.task_manager.get_task_details(task_id)

        if task_details:
            self.populate_edit_dialog(task_details)

    def populate_edit_dialog(self, task_details):
        # Open a dialog to edit task details
        edit_dialog = EditTaskDialog(task_details, self.task_manager, self.user_id)
        if edit_dialog.exec() == QDialog.DialogCode.Accepted:
            # Update task details in the database
            updated_details = edit_dialog.get_updated_details()
            self.task_manager.update_task(task_details[0], *updated_details)
            self.update_task_list()

    # Function to update the task list
    def update_task_list(self):
        if self.user_id is None:
            logging.error(
                "User ID is None. Cannot update task list without a valid user ID.")
            return
        # Retrieve the list of tasks using the task manager
        try:
            tasks = self.task_manager.list_tasks(self.user_id)
            if not tasks:
                logging.error("No tasks found for user_id: %s", self.user_id)
                return

            # Sort tasks by due date in ascending order (earliest due date first)
            # Assuming task[2] is the due date
            tasks.sort(key=lambda task: task[2])

            # Reverse the order to get highest due date first
            tasks.reverse()

            # Clear the existing task_row_to_id dictionary and the table
            task_row_to_id.clear()
            self.task_table_widget.setRowCount(len(tasks))

            for row, task in enumerate(tasks):
                # Unpack the task tuple
                task_id, name, due_date, priority, category, color = task

                # Create QTableWidgetItem for each column
                name_item = QTableWidgetItem(name)
                due_date_item = QTableWidgetItem(due_date)
                priority_item = QTableWidgetItem(priority)
                category_item = QTableWidgetItem(category)

                # Set text alignment to left
                name_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                due_date_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                priority_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                category_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

                # Set item flags to make cells read-only
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                due_date_item.setFlags(due_date_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                priority_item.setFlags(priority_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                category_item.setFlags(category_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                # Apply color to the priority cell
                if color and QColor(color).isValid():
                    priority_item.setBackground(QColor(color))

                # Set items in the table
                self.task_table_widget.setItem(row, 0, name_item)
                self.task_table_widget.setItem(row, 1, due_date_item)
                self.task_table_widget.setItem(row, 2, priority_item)
                self.task_table_widget.setItem(row, 3, category_item)

                # Populate the task ID to row mapping
                task_row_to_id[row] = task_id

            # Apply the table style after updating
            self.task_table_widget.resizeColumnsToContents()
            self.apply_table_style()

            # Set the size policy again to make sure it's effective
            self.task_table_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        except Exception as e:
            logging.error("An error occurred while updating task list: %s", e)

    # Function to refreh the task list
    def refresh_task(self):
        self.update_task_list()
        self.clear_entries()

    def logout(self):
        """
        Logs out the user, closes the session, hides the main window, and shows the login dialog.
        """
        # Assuming self.username stores the username of the logged-in user
        if hasattr(self, 'username'):
            # Log the logout event
            logout_status = self.task_manager.log_user_activity(self.username, "Logout")

            if logout_status is not None:
                # Handle any errors in logging the logout event, if necessary
                logging.error(f"Error logging logout: {logout_status}")

        # Close the session and Hide the main window
        self.close()
        self.hide()

        # Reset the login dialog for the next login
        self.login_dialog.reset_login_dialog()

        # Show the login dialog
        self.login_dialog.show()

    def notify_due_tasks(self, tasks):
        # Notify the user about due tasks
        # This could be updating a status bar, displaying a message box, etc.
        for task in tasks:
            notification_id = f"task_due_{task}"  # Unique ID for each task
            if self.notification_manager.send_notification(notification_id, "Task Due", f"Task '{task}' is due today.", self.task_manager, frequency="hourly"):
                logging.info(f"Notification sent for task: {task}")
            else:
                logging.info(f"Notification already sent for task: {task}")

    def export_tasks(self):
        """
        Export tasks to a CSV file.
        """
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Export Tasks", "", "CSV Files (*.csv)")
        if file_name:
            try:
                message = self.task_manager.export_tasks(file_name, self.user_id)
                send_windows_notification("Export Successful", message, self.task_manager, self.user_id)

            except Exception as e:
                logging.error("An error occurred while exporting tasks: {e}")

    def import_tasks(self):
        """
        Opens a file dialog to select a CSV file and imports tasks from the selected file.
        Refreshes the task list in the UI and displays a success message if the import is successful.
        Displays an error message if an exception occurs during the import process.
        """
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Import Tasks", "", "CSV Files (*.csv)")
        if file_name:
            try:
                message = self.task_manager.import_tasks(
                    file_name, self.user_id)
                # Refresh the task list in the UI
                self.update_task_list()
                QMessageBox.information(self, "Import Successful", message)
            except Exception as e:
                QMessageBox.critical(
                    self, "Import Failed", f"An error occurred while importing tasks: {e}")

    def preview_data(self):

        # Create a QPrinter object
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setPageOrientation(QPageLayout.Orientation.Landscape)

        # Set the page margins
        margins = QMarginsF(12, 12, 12, 12)  # Set the margins to 12mm
        pageLayout = QPageLayout(
            QPageSize(QPageSize.PageSizeId.A4), QPageLayout.Orientation.Landscape, margins)
        printer.setPageLayout(pageLayout)

        # Create the preview dialog
        preview_dialog = QPrintPreviewDialog(printer, self)
        preview_dialog.setWindowTitle("Preview")

        # Connect the paint request to a method that will draw the content
        preview_dialog.paintRequested.connect(self.print_preview)

        # Show the dialog
        preview_dialog.exec()

    def print_preview(self, printer):
        # This method should render the table data
        # Prepare the document content
        content = self.format_table_data_for_printing()

        # Create a text document and set its content
        document = QTextDocument()
        document.setHtml(content)

        # Print the document to the printer (which is connected to the preview dialog)
        document.print(printer)

    def format_table_data_for_printing(self):
        # Retrieve the list of tasks using the task manager
        tasks = self.task_manager.list_tasks(self.user_id)

        # Initialize an HTML string to hold the formatted data
        formatted_data = "<html><head><style>"
        formatted_data += "body {margin: 0; padding: 0;}"
        formatted_data += "table {width: 100%; table-layout: fixed; border-collapse: collapse;}"
        formatted_data += "th, td {border: 1px solid black; padding: 5px; text-align: left;}"
        formatted_data += "@page{size: A4 landscape;margin: 12mm 12mm 12mm 12mm;}"
        formatted_data += "</style></head><body>"
        formatted_data += "<table>"  # Start the table

        # Add table header (adjust the headers as per your task attributes)
        formatted_data += "<tr><th>Name</th><th>Due Date</th><th>Priority</th><th>Category</th></tr>"

        # Loop through the tasks and create HTML table rows
        for task in tasks:
            if task:  # Assuming the first element indicates an 'Active' status
                formatted_data += "<tr>"
                formatted_data += f"<td>{task[1]}</td>"  # Task Name
                formatted_data += f"<td>{task[2]}</td>"  # Due Date
                formatted_data += f"<td>{task[3]}</td>"  # Priority
                formatted_data += f"<td>{task[4]}</td>"  # Category
                formatted_data += "</tr>"

        # Close the table and HTML tags
        formatted_data += "</table></body></html>"

        # Return the HTML formatted data for all active tasks
        return formatted_data

    def print_data(self):
        # This slot is called when the Print action is triggered
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        print_dialog = QPrintDialog(printer, self)

        # If the user accepts the print dialog, proceed to print
        if print_dialog.exec() == QPrintDialog.DialogCode.Accepted:
            self.print_preview(printer)


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

    def __init__(self, task_manager, data_type, user_id, parent=None):
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
        self.setWindowTitle(f"Add {self.data_type.capitalize()}")
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
                send_windows_notification("Success", f"{self.data_type.capitalize()} '{data}' added.", self.task_manager, self.user_id)
                self.data_added.emit()  # Emit the signal when data is added
                self.accept()
            elif self.data_type == 'category' and not self.task_manager.category_exists(data):
                self.task_manager.add_category(data, self.user_id)
                send_windows_notification("Success", f"{self.data_type.capitalize()} '{data}' added.", self.task_manager, self.user_id)
                self.data_added.emit()  # Emit the signal when data is added
                self.accept()
            else:
                QMessageBox.warning(
                    self, "Exists", f"{self.data_type.capitalize()} '{data}' already exists.")
