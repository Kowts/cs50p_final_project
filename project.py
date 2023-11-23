import sys
import logging
from PyQt6.QtWidgets import QApplication, QMessageBox, QDialog
from models.task_manager import TaskManager
from ui.main_window import MainWindow
from ui.dialogs.login_dialog import LoginDialog
from services.preferences import PreferencesManager
from helpers.utils import setup_logging, get_env_variable, show_dialog

# Setup logging early for consistent application-wide debugging and tracking
setup_logging()

# Constants for default user credentials, loaded from environment variables
DEFAULT_USER = get_env_variable('DEFAULT_USER')
DEFAULT_PASSWORD = get_env_variable('DEFAULT_PASSWORD')


def main():
    """
    The main function of the program.
    This function initializes the application, task manager, and other necessary components.
    It checks for existing users and creates a default user if necessary.
    It displays the login dialog and handles the login process.
    If the login is successful, it fetches tasks for the logged-in user and starts the main window.
    """
    try:
        app = QApplication(sys.argv)  # Initialize the QApplication object
        task_manager = TaskManager()  # Create an instance of TaskManager

        # Check for existing users in the system; create a default user if none found
        existing_users = task_manager.get_existing_users()
        if not existing_users:
            # Create a default user if no users are found in the system
            error_message = create_user(DEFAULT_USER, DEFAULT_PASSWORD)
            if error_message:
                # Display an error dialog if user creation fails
                show_dialog("User Creation Error", error_message, icon=QMessageBox.Icon.Critical)
            else:
                logging.info(f"Default user '{DEFAULT_USER}' created with password '{DEFAULT_PASSWORD}'")

        # Initialize main window, login dialog, and preferences manager
        main_window = MainWindow(task_manager, None)
        login_dialog = LoginDialog(task_manager, main_window)
        main_window.login_dialog = login_dialog
        preferences_manager = PreferencesManager(main_window, task_manager)
        login_dialog.preferences_manager = preferences_manager

        # Show the login dialog and proceed if login is successful
        if login_dialog.exec() == QDialog.DialogCode.Accepted:
            user_id = login_dialog.get_user_id()
            valid_login, fetched_user_id = login_user(DEFAULT_USER, DEFAULT_PASSWORD)
            if valid_login and fetched_user_id == user_id:
                # Fetch the tasks for the logged-in user and initialize the main window with these tasks
                tasks = fetch_tasks(user_id)
                # Start the main window with fetched tasks (this step may vary based on your implementation)
                main_window = MainWindow(task_manager, login_dialog, user_id, tasks)
                main_window.start_task_tracker()  # Start the task tracker in the main window
                main_window.show()  # Show the main window
                sys.exit(app.exec())  # Start the application's event loop
            else:
                logging.error("Login failed.")

    except ValueError as e:
        # Log and handle environment variable validation errors
        logging.error(f"Environment variable validation error: {e}")


def create_user(username, password):
    """
    Creates a new user in the system with the given username and password.

    Args:
        username (str): The username for the new user.
        password (str): The password for the new user.

    Returns:
        str: An error message if the user creation fails, otherwise None.
    """
    try:
        task_manager = TaskManager()
        return task_manager.create_user(username, password)
    except Exception as e:
        logging.error(f"Error creating user: {e}")
        return str(e)


def login_user(username, password):
    """
    Authenticates a user based on username and password.

    Args:
        username (str): The username of the user.
        password (str): The password of the user.

    Returns:
        tuple: A tuple containing a boolean indicating success or failure,
               and the user ID if successful, None otherwise.
    """
    try:
        task_manager = TaskManager()
        return task_manager.verify_user(username, password)
    except Exception as e:
        logging.error(f"Error in user login: {e}")
        return False, None


def fetch_tasks(user_id):
    """
    Fetches tasks for a given user.

    Args:
        user_id (int): The ID of the user whose tasks are to be fetched.

    Returns:
        list: A list of tasks for the given user. Returns an empty list if
              there's an error or if the user has no tasks.
    """
    try:
        task_manager = TaskManager()
        return task_manager.list_tasks(user_id)
    except Exception as e:
        logging.error(f"Error fetching tasks for user {user_id}: {e}")
        return []

if __name__ == "__main__":
    main()  # Execute the main function
