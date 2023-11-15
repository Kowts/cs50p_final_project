from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
from qt_material import apply_stylesheet

DEFAULT_STYLESHEET = ""  # or define your default styles here

class PreferencesManager(QObject):
    """Manages user preferences for the application's UI and functionalities."""

    # Define a signal for theme change
    theme_changed = pyqtSignal()

    def __init__(self, main_window, task_manager):
        """Initializes the PreferencesManager with the main application window and task manager.

        Args:
            main_window (QMainWindow): The main window of the application.
            task_manager (TaskManager): A manager to handle tasks and preferences.
        """
        super().__init__()  # Initialize the parent QObject class

        self.main_window = main_window
        self.task_manager = task_manager

    def apply_theme(self, theme_name):
        """Applies a theme to the application based on the user's preference.

        Args:
            theme_name (str): Name of the theme to apply (e.g., 'Dark', 'Light').
        """
        app = QApplication.instance()

        if theme_name == 'Dark':
            # Apply a dark theme with blue accents
            apply_stylesheet(app, theme='dark_blue.xml')
        elif theme_name == 'Light':
            # Apply a light theme with blue accents and inverted secondary colors
            apply_stylesheet(app, theme='light_blue.xml', invert_secondary=True)
        elif theme_name == 'Default':
            # Reset to the application's default theme
            app.setStyleSheet(DEFAULT_STYLESHEET)
        else:
            # Handle other themes or reset to default if an unknown theme is passed
            app.setStyleSheet("")  # Fallback to PyQt's built-in styles

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

    def apply_font_size(self, font_size):
        """Adjusts the application's font size based on user preference.

        Args:
            font_size (str): Desired font size (e.g., '12pt').
        """
        font = QApplication.instance().font()
        # Set the point size of the font, removing 'pt' from the font_size string
        font.setPointSize(int(font_size.replace('pt', '')))
        QApplication.instance().setFont(font)

    def load_and_apply_preferences(self):
        """Loads user preferences from the task manager and applies them."""
        # Retrieve preferences from the task manager
        preferences = self.task_manager.get_preferences()

        # Apply each preference
        self.apply_theme(preferences.get('theme', 'Light'))
        self.apply_notification_setting(preferences.get('enable_notifications', True))
        self.apply_font_size(preferences.get('font_size', '10'))
