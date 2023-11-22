import re
import sqlite3
import os
import hashlib
from PyQt6.QtCore import QDateTime
from PyQt6.QtWidgets import QMessageBox
from dotenv import load_dotenv
from plyer import notification
import logging

# Load environment variables from a .env file for configuration management.
load_dotenv()

# Centralized configuration for regular expressions
REGEX_PATTERNS = {
    'password': r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()]).{8,}$',
    'email': r"[^@]+@[^@]+\.[^@]+"
}

def setup_logging(level=logging.DEBUG, filename='app.log', handler=logging.FileHandler):
    """
    Set up the logging configuration for the application.

    Args:
        level: The logging level (e.g., DEBUG, INFO).
        filename: The name of the file where logs will be stored.
    """
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    log_handler = handler(filename)
    log_handler.setLevel(level)
    log_handler.setFormatter(formatter)

    logging.basicConfig(level=level, handlers=[log_handler])

def get_db_connection(db_file):
    """
    Establish a database connection.

    Args:
        db_file: The file path of the database.

    Returns:
        A connection object to the SQLite database.

    Raises:
        sqlite3.Error: If a connection error occurs.
    """
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.OperationalError as e:
        logging.error(f"Operational error in database connection: {e}")
        raise
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        raise


def hash_password(password, salt=None):
    """
    Hash a password using SHA-256.

    Args:
        password: The password to hash.
        salt: An optional salt for hashing. If not provided, a new salt is generated.

    Returns:
        A tuple of the hashed password and the used salt.
    """
    if salt is None:
        salt = hashlib.sha256(os.urandom(32)).hexdigest()
    password_bytes = password.encode('utf-8')
    salt_bytes = salt.encode('utf-8')
    password_salt = password_bytes + salt_bytes
    hashed_password = hashlib.sha256(password_salt).hexdigest()
    return hashed_password, salt


def is_valid_username(username):
    """
    Validate a username.

    Args:
        username: The username to validate.

    Returns:
        True if the username is at least 4 characters long, False otherwise.
    """
    return len(username) >= 4


def is_valid_task_name(task_name):
    """
    Validate a task name.

    Args:
        task_name: The task name to validate.

    Returns:
        True if the task name is not empty, False otherwise.
    """
    return len(task_name.strip()) > 0


def is_valid_password(password):
    """
    Validate a password against a set of criteria.

    Args:
        password: The password to validate.

    Returns:
        True if the password meets the criteria, False otherwise.
    """
    pattern = re.compile(REGEX_PATTERNS['password'])
    valid = bool(pattern.match(password))
    if not valid:
        return False, "Password must contain at least one uppercase, one lowercase, one number, one special character, and be at least 8 characters long."
    return True, ""


def is_valid_email(email):
    """
    Validate an email address format.

    Args:
        email: The email address to validate.

    Returns:
        True if the email is in a proper format, False otherwise.
    """
    pattern = re.compile(REGEX_PATTERNS['email'])
    return bool(pattern.match(email)), "Invalid email format."


def get_env_variable(var_name, default=None):
    """
    Retrieve an environment variable.

    Args:
        var_name: The name of the environment variable.
        default: An optional default value if the variable is not found.

    Returns:
        The value of the environment variable or the default value.
    """
    return os.getenv(var_name, default)


def format_datetime(date_time, format="yyyy-MM-dd HH:mm:ss"):
    """
    Format a QDateTime object into a string.

    Args:
        date_time: The QDateTime object to format.
        format: The format string.

    Returns:
        A formatted string representation of the date and time.
    """
    return date_time.toString(format)


def parse_datetime(date_time_str, format="%Y-%m-%d %H:%M:%S"):
    """
    Parse a string into a QDateTime object.

    Args:
        date_time_str: The date-time string to parse.
        format: The format of the date-time string.

    Returns:
        A QDateTime object.
    """
    return QDateTime.fromString(date_time_str, format)

def show_dialog(title, message, icon=QMessageBox.Icon.Information):
    """
    Display a general message box.

    Args:
        title: The title of the message box.
        message: The message to display.
        icon: QMessageBox.Icon.Critical or QMessageBox.Icon.Information
    """
    msg = QMessageBox()
    msg.setIcon(icon)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec()

def send_windows_notification(title: str, message: str, task_manager, timeout: int = 10, app_name: str = 'YourApp') -> bool:
    """
    Send a Windows notification if the user has enabled notifications.

    Args:
        title: The title of the notification.
        message: The message content of the notification.
        task_manager: Instance of TaskManager to retrieve user preferences.
        timeout: The time in seconds for the notification to disappear.
        app_name: The name of your application.

    Returns:
        True if the notification was sent successfully, False otherwise.
    """
    try:
        preferences = task_manager.get_preferences()
        enable_notifications = preferences.get('enable_notifications', 'True') == 'True'

        if enable_notifications:
            notification.notify(title=title,message=message,app_name=app_name,timeout=timeout)
            logging.info(f"Sent Windows notification: Title='{title}', Message='{message}', Timeout={timeout}, App Name='{app_name}'")
            return True
        else:
            logging.info("Notification not sent: User has disabled notifications")
            return False
    except Exception as e:
        logging.error(f"Error sending Windows notification: {str(e)}")
        return False
