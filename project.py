import sys

import logging
from PyQt6.QtWidgets import (
    QApplication,
    QMessageBox,
    QDialog
)
from models.task_manager import TaskManager
from ui.main_window import MainWindow
from ui.dialogs.login_dialog import LoginDialog
from services.preferences import PreferencesManager
from helpers.utils import setup_logging, get_env_variable, show_dialog

# Setup logging as soon as possible, ideally at the start of the application
setup_logging()

# Constants
DEFAULT_USER = get_env_variable('DEFAULT_USER')
DEFAULT_PASSWORD = get_env_variable('DEFAULT_PASSWORD')

def main():
    """
    Main entry point of the application.
    Initializes the QApplication, TaskManager, MainWindow, LoginDialog, and PreferencesManager.
    Checks for existing users and creates a default user if none exist.
    Displays the login dialog and shows the main window if login is successful.
    Handles any value errors that occur during execution.
    """
    app = QApplication(sys.argv)

    try:
        # Create an instance of TaskManager
        task_manager = TaskManager()

        # Initialize MainWindow with task_manager
        main_window = MainWindow(task_manager, login_dialog=None)

        # Create the login dialog instance with main_window
        login_dialog = LoginDialog(task_manager, main_window)

        # Set the login_dialog attribute in main_window
        main_window.login_dialog = login_dialog

        # Initialize PreferencesManager with main_window and task_manager
        preferences_manager = PreferencesManager(main_window, task_manager)

        # Set preferences_manager in login_dialog
        login_dialog.preferences_manager = preferences_manager

        # Check if there are existing users
        existing_users = task_manager.get_existing_users()
        if not existing_users:
            # Create a default user if no users exist
            error_message = task_manager.create_user(
                DEFAULT_USER, DEFAULT_PASSWORD)
            if error_message:
                show_dialog("User Creation Error", error_message, icon=QMessageBox.Icon.Critical)
            else:
                logging.info(f"Default user '{DEFAULT_USER}' created with password '{DEFAULT_PASSWORD}'")
        else:
            logging.warning("Users already exist in the database.")

        if login_dialog.exec() == QDialog.DialogCode.Accepted:
            # Show the main window only if login is successful
            user_id = login_dialog.get_user_id()  # Retrieve the user_id
            main_window = MainWindow(task_manager, login_dialog, user_id)
            main_window.start_task_tracker()  # Start the task tracker here
            main_window.show()
            sys.exit(app.exec())
        else:
            logging.error("Login failed.")

    except ValueError as e:
        logging.error(f"Environment variable validation error: {e}")
        # Handle the error (e.g., log, inform the user, exit the application)

if __name__ == "__main__":
    main()
