import re
import sqlite3
import os
import hashlib
from PyQt6.QtCore import QDateTime
from PyQt6.QtWidgets import QMessageBox
from dotenv import load_dotenv
import logging

# Load environment variables from a .env file.
load_dotenv()

# Function to set up the logging configuration.
# Allows specification of the log level and the filename for the log file.
def setup_logging(level=logging.INFO, filename='app.log'):
    logging.basicConfig(level=level, filename=filename, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to establish a database connection.
# Takes the database file path as an argument and returns the connection object.
def get_db_connection(db_file):
    try:
        return sqlite3.connect(db_file)
    except sqlite3.Error as e:
        # Logs any database connection errors and re-raises the exception.
        logging.error(f"Database connection error: {e}")
        raise

# Function to hash a password using SHA-256.
# Takes a password and an optional salt. If no salt is provided, it generates one.
def hash_password(password, salt=None):
    if salt is None:
        salt = hashlib.sha256(os.urandom(32)).hexdigest()
    password_bytes = password.encode('utf-8')
    salt_bytes = salt.encode('utf-8')
    password_salt = password_bytes + salt_bytes
    hashed_password = hashlib.sha256(password_salt).hexdigest()
    return hashed_password, salt

# Function to validate a username.
# Ensures that the username is at least 4 characters long.
def is_valid_username(username):
    return len(username) >= 4

def is_valid_task_name(task_name):
    # Example: Task name should not be empty
    return len(task_name.strip()) > 0

# Function to validate a password.
# Checks that the password meets certain criteria using regular expressions.
def is_valid_password(password):
    password_pattern = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()]).{8,}$')
    return bool(password_pattern.match(password))

# Function to validate an email address.
# Uses a regular expression to ensure the email is in a proper format.
def is_valid_email(email):
    pattern = re.compile(r"[^@]+@[^@]+\.[^@]+")
    return bool(pattern.match(email))

# Function to retrieve an environment variable.
# Takes the variable name and an optional default value.
def get_env_variable(var_name, default=None):
    return os.getenv(var_name, default)

# Function to format a QDateTime object into a string.
# Allows specification of the format.
def format_datetime(date_time, format="%Y-%m-%d %H:%M:%S"):
    return date_time.strftime(format)

# Function to parse a string into a QDateTime object.
# Takes a date-time string and the format it's in.
def parse_datetime(date_time_str, format="%Y-%m-%d %H:%M:%S"):
    return QDateTime.fromString(date_time_str, format)

# Function to display an error message box using PyQt6.
# Takes the title and the message as arguments.
def show_error(title, message):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec()

# Function to display a general message box using PyQt6.
# Takes the title and the message as arguments.
def show_message(title, message):
    msg = QMessageBox()
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec()
