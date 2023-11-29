from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QTextCharFormat, QIcon
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QCalendarWidget,
    QDialog
)
from models.task_manager import TaskManager
from services.preferences import PreferencesManager

class CalendarDialog(QDialog):
    """
    Calendar dialog to display tasks in a calendar view and allow users to interact with them.

    Attributes:
        task_manager (TaskManager): The task manager to handle task-related operations.
        user_id (int): The ID of the current user.
        tasks (list): A list of tasks associated with the user.
    """

    def __init__(self, task_manager: TaskManager, user_id=None):
        """
        Initializes the CalendarDialog with a task manager and a user ID.

        Args:
            task_manager (TaskManager): The task manager for task operations.
            user_id (int): The ID of the user whose tasks are to be displayed.
        """
        super().__init__()
        self.setWindowTitle("Calendar")
        self.setGeometry(200, 200, 500, 400)

        # Load the icon
        self.setWindowIcon(QIcon('resources/favicon.ico'))

        self.task_manager = task_manager
        self.user_id = user_id
        self.preferences_manager = PreferencesManager(self, self.task_manager, user_id)  # Initialize PreferencesManager

        self.init_ui()
        self.load_tasks()

        self.preferences_manager.calendar_color_changed.connect(self.update_calendar_color)
        self.preferences_manager.load_and_apply_preferences()

    def init_ui(self):
        """
        Initializes the user interface components of the dialog.
        """
        self.layout = QVBoxLayout(self)
        self.calendar = QCalendarWidget(self)
        self.calendar.clicked.connect(self.date_clicked)
        self.layout.addWidget(self.calendar)

        self.info_label = QLabel("Select a date to view tasks", self)
        self.layout.addWidget(self.info_label)

    def load_tasks(self):
        """
        Loads tasks from the task manager and displays them in the calendar.
        """
        self.calendar_color = self.task_manager.get_preferences(self.user_id).get('calendar_color', 'yellow')  # Load the calendar color preference
        self.tasks = self.task_manager.list_tasks(self.user_id)
        self.display_tasks()

    def display_tasks(self):
        """
        Updates the calendar display with task markers or indicators.
        """
        format = QTextCharFormat()
        format.setBackground(QColor(self.calendar_color)
                             )  # Use the selected color

        for task in self.tasks:
            task_date = QDate.fromString(task[2], "yyyy-MM-dd")
            self.calendar.setDateTextFormat(task_date, format)

    def update_calendar_color(self, color):
        """
        Update the calendar with the new color.

        Args:
            color (str): The new color for the calendar.
        """
        self.calendar_color = color
        self.display_tasks()  # Refresh the display to apply the new color

    def date_clicked(self, date):
        """
        Handles the event when a date is clicked on the calendar.

        Args:
            date (QDate): The date clicked by the user.
        """
        tasks_on_date = [task for task in self.tasks if task[2]
                         == date.toString("yyyy-MM-dd")]
        self.show_tasks_for_date(tasks_on_date, date)

    def show_tasks_for_date(self, tasks, date):
        """
        Displays a dialog with tasks scheduled for a specific date.

        Args:
            tasks (list): List of tasks for the selected date.
            date (QDate): The selected date.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Tasks for {date.toString()}")
        layout = QVBoxLayout(dialog)

        task_table = QTableWidget(len(tasks), 3)
        task_table.setHorizontalHeaderLabels(["Name", "Priority", "Category"])
        task_table.horizontalHeader().setStretchLastSection(True)
        task_table.verticalHeader().setVisible(False)
        task_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        for row, task in enumerate(tasks):

            name_item = QTableWidgetItem(task[1])
            priority_item = QTableWidgetItem(task[3])
            category_item = QTableWidgetItem(task[4])

            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            priority_item.setFlags(priority_item.flags()
                                   & ~Qt.ItemFlag.ItemIsEditable)
            category_item.setFlags(category_item.flags()
                                   & ~Qt.ItemFlag.ItemIsEditable)

            task_table.setItem(row, 0, name_item)
            task_table.setItem(row, 1, priority_item)
            task_table.setItem(row, 2, category_item)

        task_table.resizeColumnsToContents()
        task_table.setStyleSheet("QTableWidget { border: none; }"
                                 "QTableWidget::item { border-bottom: 1px solid #ddd; }"
                                 "QHeaderView::section { background-color: #f0f0f0; padding: 4px; }"
                                 "QTableWidget::item:selected { background-color: #e0e0e0; }")

        dialog.resize(task_table.sizeHint().width(),
                      task_table.sizeHint().height())
        layout.addWidget(task_table)
        dialog.exec()
