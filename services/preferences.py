"""
preferences.py: Handles user preferences settings, such as theme, notifications, and other customizable options.
It provides functionalities to save, load, and apply user preferences.
"""
from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
from qt_material import apply_stylesheet
import logging
from helpers.utils import setup_logging
from helpers.constants import THEME_MAP, DEFAULT_STYLESHEET

# Setup logging as soon as possible, ideally at the start of the application
setup_logging()

class PreferencesManager(QObject):
    """Manages user preferences for the application's UI and functionalities."""

    # Define a signal for theme change
    theme_changed = pyqtSignal()
    calendar_color_changed = pyqtSignal(str)

    def __init__(self, main_window, task_manager, user_id=None):
        """Initializes the PreferencesManager with the main application window and task manager.

        Args:
            main_window (QMainWindow): The main window of the application.
            task_manager (TaskManager): A manager to handle tasks and preferences.
        """
        super().__init__()  # Initialize the parent QObject class

        self.user_id = user_id  # Initialize user_id

        self.main_window = main_window
        self.task_manager = task_manager

    def apply_theme(self, theme_name, font_size):
        """Applies a theme to the application based on the user's preference.

        Args:
            theme_name (str): Name of the theme to apply (e.g., 'Dark', 'Light').
        """
        app = QApplication.instance()

        # Convert the font size to a string with 'px' suffix
        font_size_px = f'{font_size}px'
        extra = {'font_size': font_size_px}

        # Get the theme file or default to empty string
        theme_file = THEME_MAP.get(theme_name, '')

        if theme_file.endswith('.xml'):
            apply_stylesheet(app, theme=theme_file, extra=extra)
        elif theme_name == 'Default':
            app.setStyleSheet(DEFAULT_STYLESHEET)
        else:
            app.setStyleSheet("")  # Fallback to PyQt's built-in styles

        # Apply the font size at the end
        self.apply_font_size(font_size)

        # Emit the theme_changed signal
        self.theme_changed.emit()

    def apply_notification_setting(self, enable_notifications):
        """Enables or disables notifications based on user preference.

        Args:
            enable_notifications (bool): Flag indicating whether notifications should be enabled.
        """
        # Implement the logic for enabling or disabling notifications
        # This could involve interacting with the notification system in your application
        pass

    def apply_email_notification(self, email_notification):
        """
        Apply the specified email notification preference.

        Args:
            email_notification (bool): The email notification preference to apply.
        """
        pass

    def apply_high_contrast_theme(self, high_contrast):
        """
        Apply or remove a high contrast theme to the application.

        Args:
            high_contrast (bool): True to apply the high contrast theme, False to remove it.
        """
        app = QApplication.instance()

        # Convert high_contrast to boolean if it's a string
        high_contrast_bool = high_contrast.lower() == 'true' if isinstance(high_contrast, str) else high_contrast

        if high_contrast_bool:
            app = QApplication.instance()
            with open("resources/stylesheet.qss", "r") as file:
                app.setStyleSheet(file.read())
        else:
            app.setStyleSheet("")  # or apply the default theme

    def apply_font_size(self, font_size):
        """Adjusts the application's font size based on user preference.

        Args:
            font_size (str): Desired font size (e.g., '12pt').
        """
        font = QApplication.instance().font()
        # Set the point size of the font, removing 'pt' from the font_size string
        font.setPointSize(int(font_size.replace('pt', '')))
        QApplication.instance().setFont(font)

    def apply_always_on_top(self, always_on_top):
        # Convert always_on_top to boolean if it's a string
        always_on_top_bool = always_on_top.lower() == 'true' if isinstance(always_on_top, str) else always_on_top

        # Check if the main window is currently visible
        is_visible = self.main_window.isVisible()

        # Apply the 'Always on Top' setting
        try:
            self.main_window.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, always_on_top_bool)

            if is_visible:
                # Hide and show the window only if it was already visible
                self.main_window.hide()  # Necessary to reapply the window flags
                self.main_window.show()  # Re-show the window to apply the change
        except Exception as e:
            print("An error occurred while setting Always on Top:", e)

    def apply_calendar_color(self, color):
        """
        Apply the calendar color preference.
        """
        self.calendar_color_changed.emit(color)

    def validate_font_size(self, font_size):
        """
        Validates the font size preference.

        Args:
            font_size (str): The font size to validate, typically provided as a string like '12pt'.

        Returns:
            str: A validated font size, with a fallback to a default value if the input is invalid.
        """

        # Define minimum and maximum allowable font sizes
        min_font_size = 8
        max_font_size = 24

        # Default font size to use if validation fails
        default_font_size = '10pt'

        try:
            # Extract the numeric part of the font size (e.g., '12' from '12pt')
            size = int(font_size.replace('pt', ''))

            # Check if the font size is within the acceptable range
            if min_font_size <= size <= max_font_size:
                return font_size
            else:
                # If the size is outside the range, log a warning and return the default size
                logging.warning(f"Font size {font_size} is out of range. Using default size {default_font_size}.")
                return default_font_size
        except ValueError:
            # If the font size string cannot be converted to an integer, log an error and return the default size
            logging.error(f"Invalid font size format: {font_size}. Using default size {default_font_size}.")
            return default_font_size

    def load_and_apply_preferences(self):
        """
        Loads and applies user preferences.

        Retrieves preferences from the task manager and applies them to the application.
        This method validates the font size preference, applies the theme, font size,
        high contrast theme, notification settings, email notification, and always on top
        preference based on the retrieved preferences.

        Raises:
            Exception: If there is an error loading and applying preferences.
        """
        try:
            # Retrieve preferences from the task manager
            preferences = self.task_manager.get_preferences(self.user_id)

            # Validate the font size preference
            font_size = self.validate_font_size(preferences.get('font_size', '10'))

            # Apply theme first
            self.apply_theme(preferences.get('theme', ''), font_size)
            self.apply_font_size(font_size)

            # Check for high contrast preference and apply if enabled
            high_contrast = preferences.get('high_contrast', False)
            high_contrast_bool = high_contrast.lower() == 'true' if isinstance(high_contrast, str) else high_contrast
            if high_contrast_bool:
                self.apply_high_contrast_theme(True)

            # Apply other preferences
            self.apply_notification_setting(preferences.get('enable_notifications', True))
            self.apply_email_notification(preferences.get('email_notification', True))
            self.apply_always_on_top(preferences.get('always_on_top', False))

        except Exception as e:
            print("Error loading and applying preferences:", e)
