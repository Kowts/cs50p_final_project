from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
from qt_material import apply_stylesheet

DEFAULT_STYLESHEET = ""  # or define your default styles here

class PreferencesManager(QObject):
    """Manages user preferences for the application's UI and functionalities."""

    # Define a signal for theme change
    theme_changed = pyqtSignal()
    calendar_color_changed = pyqtSignal(str)

    def __init__(self, main_window, task_manager):
        """Initializes the PreferencesManager with the main application window and task manager.

        Args:
            main_window (QMainWindow): The main window of the application.
            task_manager (TaskManager): A manager to handle tasks and preferences.
        """
        super().__init__()  # Initialize the parent QObject class

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
        extra = {
            'font_size': font_size_px,
        }

        if theme_name == 'Dark':
            # Apply a dark theme with blue accents
            apply_stylesheet(app, theme='dark_blue.xml', extra=extra)
        elif theme_name == 'Light':
            # Apply a light theme with blue accents and inverted secondary colors
            apply_stylesheet(app, theme='light_blue.xml', extra=extra, invert_secondary=True)
        elif theme_name == 'Default':
            # Reset to the application's default theme
            app.setStyleSheet(DEFAULT_STYLESHEET)
        else:
            # Handle other themes or reset to default if an unknown theme is passed
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

    def load_and_apply_preferences(self):
        """
        Loads user preferences from the task manager and applies them.
        """
        # Retrieve preferences from the task manager
        preferences = self.task_manager.get_preferences()

        font_size = preferences.get('font_size', '10')

        # Apply each preference
        self.apply_theme(preferences.get('theme', ''), font_size)
        self.apply_font_size(font_size)
        self.apply_notification_setting(preferences.get('enable_notifications', True))
        self.apply_always_on_top(preferences.get('always_on_top', False))
