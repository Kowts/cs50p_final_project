
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QIcon, QShortcut, QKeySequence
from PyQt6.QtWidgets import (
    QCheckBox,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QDialog
)

from models.task_manager import TaskManager

class FindDialog(QDialog):
    """
    Dialog for searching tasks with various filter options.

    Attributes:
        text_widget (QLineEdit): The input widget for search text.
        task_manager (TaskManager): The task manager to handle search operations.
        search_initiated (pyqtSignal): Signal to emit search parameters.
    """
    # Signal with the search parameters
    search_initiated = pyqtSignal(str, bool, bool, bool)

    def __init__(self, text_widget, task_manager: TaskManager):
        """
        Initializes the FindDialog with a text widget and a task manager.

        Args:
            text_widget (QLineEdit): The input widget for search text.
            task_manager (TaskManager): The task manager for handling search operations.
        """
        super().__init__()
        self.text_widget = text_widget
        self.task_manager = task_manager
        self.setWindowTitle("Find")
        self.init_ui()

        # Shortcut for 'Find next' (e.g., Enter key)
        self.find_next_shortcut = QShortcut(QKeySequence("Return"), self)
        self.find_next_shortcut.activated.connect(self.find_next)

    def init_ui(self):
        """
        Initializes the user interface components of the dialog.
        """
        layout = QVBoxLayout()

        # Search text input
        self.find_what_label = QLabel("What:")
        self.find_what_input = QLineEdit()
        layout.addWidget(self.find_what_label)
        layout.addWidget(self.find_what_input)

        # Match case checkbox
        self.match_case_checkbox = QCheckBox("Match case")
        layout.addWidget(self.match_case_checkbox)

        # Whole word checkbox
        self.whole_word_checkbox = QCheckBox("Whole word")
        layout.addWidget(self.whole_word_checkbox)

        # Regular expressions checkbox
        self.regular_expression_checkbox = QCheckBox("Regular expressions")
        layout.addWidget(self.regular_expression_checkbox)

        # Find and Cancel buttons
        self.find_button = QPushButton("Find next")
        self.find_button.clicked.connect(self.find_next)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        # Layout for buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.find_button)
        buttons_layout.addWidget(self.cancel_button)
        layout.addLayout(buttons_layout)

        # Styling buttons for a better visual appeal
        self.find_button.setStyleSheet("background-color: lightblue; padding: 5px;")
        self.cancel_button.setStyleSheet("background-color: lightcoral; padding: 5px;")

        self.setLayout(layout)

    def find_next(self):
        """
        Handles the 'Find next' button click event with validation.
        """
        text = self.find_what_input.text().strip()
        if not text:
            QMessageBox.warning(self, "Empty Search",
                                "Please enter a search term.")
            return

        # Retrieve search parameters
        match_case = self.match_case_checkbox.isChecked()
        whole_word = self.whole_word_checkbox.isChecked()
        use_regex = self.regular_expression_checkbox.isChecked()

        # Emit the search_initiated signal with the retrieved parameters
        self.search_initiated.emit(text, match_case, whole_word, use_regex)
