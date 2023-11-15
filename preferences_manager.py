from PyQt6.QtWidgets import QApplication
from qt_material import apply_stylesheet

class PreferencesManager:
    def __init__(self, main_window, task_manager):
        self.main_window = main_window
        self.task_manager = task_manager

    def apply_theme(self, theme_name):
        app = QApplication.instance()

        if theme_name == 'Dark':
            # Apply dark theme stylesheet
            apply_stylesheet(app, theme='dark_blue.xml')
        elif theme_name == 'Light':
            # Apply light theme stylesheet with inverted secondary color
            apply_stylesheet(app, theme='light_blue.xml', invert_secondary=True)
        else:
            # Reset to default style or handle other themes
            app.setStyleSheet("")

    def apply_notification_setting(self, enable_notifications):
        # Logic to enable or disable notifications
        # You may need to implement this based on how your notification system is set up
        return None

    def apply_font_size(self, font_size):
        font = QApplication.instance().font()
        font.setPointSize(int(font_size.replace('pt', '')))
        QApplication.instance().setFont(font)

    def load_and_apply_preferences(self):
        # Fetch preferences using TaskManager
        preferences = self.task_manager.get_preferences()

        # Apply preferences
        self.apply_theme(preferences.get('theme', 'Light'))
        self.apply_notification_setting(preferences.get('enable_notifications', True))
        self.apply_font_size(preferences.get('font_size', '10pt'))
