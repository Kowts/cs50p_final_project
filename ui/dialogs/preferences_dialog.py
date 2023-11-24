from PyQt6.QtWidgets import QDialog, QLabel, QComboBox, QVBoxLayout, QPushButton, QCheckBox, QColorDialog, QHBoxLayout, QLineEdit, QDialogButtonBox
from PyQt6.QtGui import QColor
from models.task_manager import TaskManager
from services.preferences import PreferencesManager
from helpers.utils import get_env_variable, send_windows_notification

THEME = get_env_variable('THEME').split(',')
FONT_SIZE = get_env_variable('FONT_SIZE').split(',')

class PreferencesDialog(QDialog):
    """
    A dialog window for managing user preferences.

    Args:
        task_manager (TaskManager): The task manager object.
        preferences_manager (PreferencesManager): The preferences manager object.
        parent (QWidget): The parent widget.

    Attributes:
        task_manager (TaskManager): The task manager object.
        preferences_manager (PreferencesManager): The preferences manager object.
        theme_selector (QComboBox): The combo box for selecting the theme.
        notification_checkbox (QCheckBox): The checkbox for enabling notifications.
        font_size_selector (QComboBox): The combo box for selecting the font size.
        always_on_top_checkbox (QCheckBox): The checkbox for enabling "Always on Top".
    """

    def __init__(self, task_manager: TaskManager, preferences_manager: PreferencesManager, parent=None):
        super().__init__(parent)

        self.task_manager = task_manager
        self.preferences_manager = preferences_manager

        self.setWindowTitle("Preferences")
        self.setup_ui()

    def setup_ui(self):
        """
        Sets up the user interface for the application settings.
        """
        layout = QVBoxLayout(self)

        # setting: Theme Selector
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(THEME)
        layout.addWidget(QLabel("Select Theme:"))
        layout.addWidget(self.theme_selector)

        # setting: A checkbox for enabling notifications
        self.notification_checkbox = QCheckBox("Enable Notifications", self)
        layout.addWidget(self.notification_checkbox)

        # Create a checkbox for the "Always on Top" setting
        self.always_on_top_checkbox = QCheckBox("Always on Top", self)
        layout.addWidget(self.always_on_top_checkbox)

        # Create a checkbox for the "Email Notification" setting
        self.email_notification_checkbox = QCheckBox("Email Notification", self)
        layout.addWidget(self.email_notification_checkbox)

        # setting: Font Size
        self.font_size_selector = QComboBox()
        self.font_size_selector.addItems(FONT_SIZE)
        layout.addWidget(QLabel("Font Size:"))
        layout.addWidget(self.font_size_selector)

        # Create a menu action for toggling the high contrast theme
        self.highContrastCheckbox = QCheckBox("High Contrast Theme")
        layout.addWidget(self.highContrastCheckbox)

        # Add label for Calendar Color
        layout.addWidget(QLabel("Calendar Color:"))

        # Create horizontal layout for the calendar color input group
        calendar_color_layout = QHBoxLayout()
        self.calendar_color_input = QLineEdit()
        self.calendar_color_input.setReadOnly(True)
        calendar_color_layout.addWidget(self.calendar_color_input)
        # Button for picking the calendar color
        self.calendar_color_button = QPushButton("Pick Color")
        self.calendar_color_button.clicked.connect(self.pick_calendar_color)
        calendar_color_layout.addWidget(self.calendar_color_button)
        # Add the horizontal layout to the main vertical layout
        layout.addLayout(calendar_color_layout)

        # OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Close)
        button_box.accepted.connect(self.save_preferences)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Load current preferences
        self.load_preferences()

    def pick_calendar_color(self):
        """
        Opens a color dialog to allow the user to pick a color.
        Sets the background color of the input field to the chosen color.
        Optionally, displays the color's hexadecimal value in the input field.
        """
        color = QColorDialog.getColor()
        if color.isValid():
            # Set the background color of the input field to the chosen color
            color_hex = color.name()
            self.calendar_color_input.setStyleSheet(f"background-color: {color_hex.upper()};")
            # Optionally, display the color's hexadecimal value in the input field
            self.calendar_color_input.setText(color_hex.upper())

    def save_preferences(self):
        # Save the current preferences to the database
        theme = self.theme_selector.currentText()
        enable_notifications = self.notification_checkbox.isChecked()
        font_size = self.font_size_selector.currentText()
        always_on_top = self.always_on_top_checkbox.isChecked()
        email_notification = self.email_notification_checkbox.isChecked()
        calendar_color = self.calendar_color_input.text()
        high_contrast = self.highContrastCheckbox.isChecked()

        # Save preferences
        self.task_manager.save_preferences({
            'theme': theme,
            'high_contrast': str(high_contrast),
            'enable_notifications': str(enable_notifications),
            'font_size': font_size,
            'always_on_top': str(always_on_top),
            'email_notification': str(email_notification),
            'calendar_color': calendar_color.upper()
        })

        # Apply preferences immediately
        self.preferences_manager.apply_theme(theme, font_size)
        self.preferences_manager.apply_notification_setting(enable_notifications)
        self.preferences_manager.apply_font_size(font_size)
        self.preferences_manager.apply_always_on_top(always_on_top)
        self.preferences_manager.apply_email_notification(email_notification)

        # Send notification about successful save
        send_windows_notification("Preferences Updated", "Your preferences have been successfully updated.", self.task_manager)

        # Optional: Close the preferences dialog after saving
        self.accept()

    def load_preferences(self):
        """
        Load the current preferences and update the UI.

        This method retrieves the preferences from the task manager and updates the UI elements accordingly.
        It converts preference strings to boolean values, sets the selected options in combo boxes,
        and updates the background color and text of input fields based on saved preferences.
        """

        # Load current preferences and update the UI
        preferences = self.task_manager.get_preferences()

        # Convert the preference string to a boolean
        enable_notifications = preferences.get('enable_notifications', 'False')  # Default to 'False' if not found
        enable_notifications_bool = enable_notifications.lower() == 'true'  # Convert to boolean
        self.notification_checkbox.setChecked(enable_notifications_bool)

        # Convert the high_contrast string to a boolean
        high_contrast = preferences.get('high_contrast', 'False')
        high_contrast_bool = high_contrast.lower() == 'true'  # Convert to boolean
        self.highContrastCheckbox.setChecked(high_contrast_bool)

        # Get the saved font size (default to '12' if not set)
        font_size = preferences.get('font_size', '12')  # Default to '12'
        self.font_size_selector.setCurrentText(font_size)

        # Get the saved theme (default to "Light" if not set)
        saved_theme = preferences.get('theme', 'Light')

        # Find the index of the saved theme in the combo box and set it
        index = self.theme_selector.findText(saved_theme)
        if index >= 0:
            self.theme_selector.setCurrentIndex(index)

        # Convert the preference string to a boolean
        # Default to 'False' if not found
        always_on_top = preferences.get('always_on_top', 'False')
        always_on_top_bool = always_on_top.lower() == 'true'  # Convert to boolean
        self.always_on_top_checkbox.setChecked(always_on_top_bool)

        email_notification = preferences.get('email_notification', 'False')
        email_notification_bool = email_notification.lower() == 'true'  # Convert to boolean
        self.email_notification_checkbox.setChecked(email_notification_bool)

        # Get the saved calendar color (default to a neutral color if not set)
        saved_calendar_color = preferences.get('calendar_color', '')  # Default to white
        if QColor(saved_calendar_color).isValid():
            # Set the background color of the input field to the saved color
            self.calendar_color_input.setStyleSheet(f"background-color: {saved_calendar_color};")
            # Display the color's hexadecimal value in the input field
            self.calendar_color_input.setText(saved_calendar_color.upper())
