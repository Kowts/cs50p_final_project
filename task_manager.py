import os
import csv
import sqlite3, utils
from PyQt6.QtCore import QDateTime
from dotenv import load_dotenv
import datetime
import logging
from enum import Enum

# Initialize logging configuration at application startup
utils.setup_logging()

# Constants for database file and default values, loaded from environment variables
DATABASE_FILE = utils.get_env_variable('DATABASE_FILE')
DEFAULT_PRIORITIES = utils.get_env_variable('DEFAULT_PRIORITIES').split(',')
DEFAULT_CATEGORIES = utils.get_env_variable('DEFAULT_CATEGORIES').split(',')

class DefaultStatus(Enum):
    """Enum for default status values."""
    ACTIVE = 1
    INACTIVE = 0
class TaskManager:

    """
    Manages tasks, user authentication, and database interactions.
    """

    def __init__(self, db_file=DATABASE_FILE):
        """
        Initializes the TaskManager with a database file and sets up the database.
        Validates required environment variables.
        """
        self.db_file = db_file
        self.setup_database()
        self.validate_environment_variables()

    def get_db_connection(self):
        """
        Establishes and returns a database connection.

        Returns:
            A connection object to the SQLite database.
        """
        try:
            conn = sqlite3.connect(self.db_file)
            return conn
        except sqlite3.Error as e:
            # You may want to handle this error differently depending on your application's needs
            logging.error(f"Database connection error: {e}")
            raise

    def validate_environment_variables(self):
        """
        Validates required environment variables and raises ValueError if any are missing or invalid.
        """
        # List of required environment variables
        required_vars = ['DATABASE_FILE', 'MAX_CONNECTION', 'DEFAULT_USER', 'DEFAULT_PASSWORD']
        missing_vars = [var for var in required_vars if not utils.get_env_variable(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        if not os.path.exists(self.db_file):
            raise ValueError(f"The specified database file {self.db_file} does not exist.")

        max_connection = utils.get_env_variable('MAX_CONNECTION')
        if max_connection and not max_connection.isdigit():
            raise ValueError("MAX_CONNECTION must be a numeric value.")

        if max_connection and not 1 <= int(max_connection) <= 100:
            raise ValueError("MAX_CONNECTION must be between 1 and 100.")

        admin_email = utils.get_env_variable('ADMIN_EMAIL')
        if admin_email and not utils.is_valid_email(admin_email):
            raise ValueError("Invalid email format for ADMIN_EMAIL.")

    def setup_database(self):
        """
        Sets up the database by creating necessary tables.
        """
        try:
            # Establish database connection and create tables
            with self.get_db_connection() as conn:
                self.create_tasks_table(conn)
                self.create_priorities_table(conn)
                self.create_categories_table(conn)
                self.create_users_table(conn)
                self.create_preferences_table(conn)
                self.create_user_activity_table(conn)
        except sqlite3.DatabaseError as e:
            logging.error(f"Database error: {e}")
        except Exception as e:
            logging.error(f"An error occurred: {e}")


    def create_tasks_table(self, conn):
        """Creates the tasks table in the database."""
        # SQL command for creating the tasks table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                due_date TEXT,
                priority TEXT,
                category TEXT,
                created_at TEXT,
                status INTEGER
            )
        ''')

    def create_priorities_table(self, conn):
        """
        Creates the priorities table and populates default values.
        """
        conn.execute('''
            CREATE TABLE IF NOT EXISTS priorities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status INTEGER DEFAULT 1
            )
        ''')
        self.insert_default_priorities(conn)

    def create_categories_table(self, conn):
        """
        Creates the categories table and populates default values.
        """
        conn.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status INTEGER DEFAULT 1
            )
        ''')
        self.insert_default_categories(conn)

    def create_users_table(self, conn):
        """
        Creates the users table in the database.
        """
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status INTEGER DEFAULT 1
            )
        ''')

    def create_preferences_table(self, conn):
        """
        Creates the preferences table in the database.
        """
        conn.execute('''
            CREATE TABLE IF NOT EXISTS preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE,
                value TEXT,
                created_at TEXT,
                status INTEGER DEFAULT 1
            )
        ''')

    def create_user_activity_table(self, conn):
        """Creates the tasks table in the database."""
        # SQL command for creating the tasks table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                type TEXT NOT NULL,  -- 'Login' or 'Logout'
                created_at TEXT NOT NULL,
                status TEXT  -- 'Success', 'Failure', or NULL for logout
            )
        ''')

    def insert_default_priorities(self, conn):
        """
        Inserts default priorities if they don't exist.
        """
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM priorities')
        count = cursor.fetchone()[0]

        if count == 0:
            current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
            for priority in DEFAULT_PRIORITIES:
                cursor.execute("INSERT INTO priorities (name, created_at) VALUES (?, ?)", (priority, current_time))

    def insert_default_categories(self, conn):
        """
        Inserts default categories if they don't exist.
        """
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM categories')
        count = cursor.fetchone()[0]

        if count == 0:
            current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
            for category in DEFAULT_CATEGORIES:
                cursor.execute("INSERT INTO categories (name, created_at) VALUES (?, ?)", (category, current_time))

    def load_priorities(self):
        """
        Loads priorities from the database.

        Returns:
            A list of priorities if successful, an empty list otherwise.
        """
        try:
            # [Database query logic]
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT name FROM priorities')
                priorities = [row[0] for row in cursor.fetchall()]
                return priorities
        except sqlite3.DatabaseError as e:
            # Handle specific database-related errors
            logging.error(f"Database error: {e}")
            # Consider logging this error and returning an appropriate response
            return []
        except Exception as e:
            # Handle other, more general exceptions
            logging.error(f"An error occurred: {e}")
            # Again, consider logging and how you want to handle this in the UI
            return []

    def load_categories(self):
        """
        Retrieves a list of category names from the database.

        Returns:
            A list of category names if the query is successful, an empty list otherwise.
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT name FROM categories')
                categories = [row[0] for row in cursor.fetchall()]
                return categories
        except sqlite3.DatabaseError as e:
            # Logs database-related errors and provides feedback for debugging
            logging.error(f"Database error: {e}")
            return []  # Returns an empty list to indicate failure in category retrieval
        except Exception as e:
            # Captures and logs unexpected errors
            logging.error(f"An error occurred: {e}")
            return []  # Returns an empty list as a fallback

    def priority_exists(self, priority_name):
        """
        Checks if a priority already exists in the database.

        Args:
            priority_name (str): The name of the priority to check.

        Returns:
            bool: True if priority exists, False otherwise.
        """
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM priorities WHERE name = ?", (priority_name,))
            return cursor.fetchone() is not None

    def add_priority(self, priority_name):
        """
        Adds a new priority to the priorities table.

        Args:
            priority_name (str): The name of the new priority to add.
        """
        # Avoid adding a priority if it already exists
        if self.priority_exists(priority_name):
            return f"Priority '{priority_name}' already exists."

        try:
            with self.get_db_connection() as conn:
                current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
                cursor = conn.cursor()
                cursor.execute("INSERT INTO priorities (name, created_at, status) VALUES (?, ?, ?)", (priority_name, current_time, 1))
                conn.commit()  # Make sure to commit the changes
            return f"Priority '{priority_name}' added successfully."
        except sqlite3.Error as e:
            return f"Failed to add priority: {e}"

    def category_exists(self, category_name):
        """
        Checks if a category already exists in the database.

        Args:
            category_name (str): The name of the category to check.

        Returns:
            bool: True if the category exists, False otherwise.
        """
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM categories WHERE name = ?", (category_name,))
            return cursor.fetchone() is not None

    def add_category(self, category_name):
        """
        Adds a new category to the categories table.

        Args:
            category_name (str): The name of the new category to add.
        """
        # Avoid adding a category if it already exists
        if self.category_exists(category_name):
            return f"Category '{category_name}' already exists."

        try:
            with self.get_db_connection() as conn:
                current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
                cursor = conn.cursor()
                cursor.execute("INSERT INTO categories (name, created_at, status) VALUES (?, ?, ?)", (category_name, current_time, 1))
                conn.commit()  # Make sure to commit the changes
            return f"Category '{category_name}' added successfully."
        except sqlite3.Error as e:
            return f"Failed to add category: {e}"

    def get_existing_users(self):
        """
        Retrieves a list of existing usernames from the database.

        Returns:
            A list of usernames if the query is successful, an empty list otherwise.
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT username FROM users')
                users = [row[0] for row in cursor.fetchall()]
                return users
        except sqlite3.DatabaseError as e:
            # Handles database-specific errors with logging for troubleshooting
            logging.error(f"Database error: {e}")
            return []  # Returns an empty list to indicate an issue in retrieving users
        except Exception as e:
            # Deals with general exceptions, ensuring the application remains stable
            logging.error(f"An error occurred: {e}")
            return []  # Provides an empty list as a default response

    def create_user(self, username, password):
        """
        Creates a new user in the database.

        Args:
            username: The username of the new user.
            password: The password of the new user.

        Returns:
            None if successful, an error message otherwise.
        """
        if not utils.is_valid_username(username) or not utils.is_valid_password(password):
            raise ValueError("Invalid username or password")

        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                hashed_password, salt = utils.hash_password(password)
                created_at = utils.format_datetime(QDateTime.currentDateTime())
                user_status = DefaultStatus.ACTIVE.value
                cursor.execute("INSERT INTO users (username, password, salt, created_at, status) VALUES (?, ?, ?, ?, ?)", (username, hashed_password, salt, created_at, user_status))
            return None
        except sqlite3.Error as e:
            return str(e)

    def verify_user(self, username, password):
        """
        Verifies a user's credentials.

        Args:
            username: The username of the user.
            password: The password of the user.

        Returns:
            True if credentials are valid, False otherwise.
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT password, salt FROM users WHERE username = ?", (username,))
                stored_data = cursor.fetchone()

                if stored_data:
                    stored_hashed_password, salt = stored_data
                    hashed_password, _ = utils.hash_password(password, salt)

                    if stored_hashed_password == hashed_password:
                        return True
                return False

        except sqlite3.Error:
            return False

    def log_user_activity(self, username, event_type, status=None):
        """
        Logs user activity (login/logout) to the database.

        Args:
            username: The username of the user.
            event_type: Type of the event ('Login' or 'Logout').
            status: The result of the login attempt ('Success' or 'Failure'), or None for logout.

        Returns:
            None if successful, an error message otherwise.
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                created_at = utils.format_datetime(QDateTime.currentDateTime())
                cursor.execute("INSERT INTO user_activity (username, type, created_at, status) VALUES (?, ?, ?, ?)", (username, event_type, created_at, status))
                return None
        except sqlite3.Error as e:
            return str(e)

    def add_task(self, task_name, due_date, priority, category):
        """
        Adds a new task to the database.

        Args:
            task_name: The name of the task.
            due_date: The due date of the task.
            priority: The priority of the task.
            category: The category of the task.

        Returns:
            None and the task ID if successful, an error message and None otherwise.
        """
        if not utils.is_valid_task_name(task_name):
            raise ValueError("Invalid task name.")

        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                created_at = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
                cursor.execute(
                    "INSERT INTO tasks (name, due_date, priority, category, created_at, status) VALUES (?, ?, ?, ?, ?, ?)",
                    (task_name, due_date, priority, category, created_at, DefaultStatus.ACTIVE.value)
                )
                task_id = cursor.lastrowid
            return None, task_id
        except sqlite3.Error as e:
            return str(e), None

    def update_task(self, task_id, name, due_date, priority, category):
        """
        Updates an existing task in the database.

        Args:
            task_id: The unique identifier of the task.
            name: The updated name of the task.
            due_date: The updated due date of the task.
            priority: The updated priority of the task.
            category: The updated category of the task.

        Returns:
            None if successful, an error message otherwise.
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE tasks SET name = ?, due_date = ?, priority = ?, category = ? WHERE id = ?", (name, due_date, priority, category, task_id))
        except sqlite3.Error as e:
            logging.error(f"Database error while updating task: {e}")
            return "Failed to update task."
        return None  # Indicates successful update

    def get_task_details(self, task_id):
        """
        Retrieves details of a specific task.

        Args:
            task_id: The unique identifier of the task.

        Returns:
            A tuple containing task details if successful, None otherwise.
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, due_date, priority, category FROM tasks WHERE id = ?", (task_id,))
                return cursor.fetchone()  # Returns a single task's details
        except sqlite3.Error as e:
            logging.error(f"Database error while retrieving task details: {e}")
            return None

    def list_tasks(self, status=None):
        """
        Lists tasks based on their status.

        Args:
            status: The status of the tasks to list. If None, lists active tasks.

        Returns:
            A list of tasks matching the given status, empty list in case of an error.
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                query = 'SELECT id, name, due_date, priority, category FROM tasks WHERE status = ?'
                cursor.execute(query, (status or DefaultStatus.ACTIVE.value,))
                return cursor.fetchall()  # Returns a list of tasks
        except sqlite3.DatabaseError as e:
            logging.error(f"Database error: {e}")
            return []
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return []

    def remove_tasks(self, task_ids):
        """
        Sets a task's status to inactive, effectively removing it from active listings.

        Args:
            task_id: The unique identifier of the task to be removed.

        Returns:
            None if successful, an error message otherwise.
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                # Create a query string with the correct number of placeholders
                placeholders = ', '.join(['?'] * len(task_ids))
                query = f"UPDATE tasks SET status = {DefaultStatus.INACTIVE.value} WHERE id IN ({placeholders})"
                cursor.execute(query, task_ids)
                conn.commit()
            return "Tasks successfully set as inactive."
        except sqlite3.Error as e:
            return str(e)

    def get_last_inserted_task_id(self):
        """
        Retrieves the ID of the last inserted task in the database.

        Returns:
            The ID of the last inserted task if successful, None otherwise.
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT last_insert_rowid()")
                task_id = cursor.fetchone()[0]
            return task_id
        except sqlite3.Error:
            return None  # Return None if there's an error during the operation

    def get_due_tasks(self):
        """
        Retrieves tasks that are due on the current day and have a specific status.

        Returns:
            A list of task names due today and with the specified status,
            an empty list in case of an error.
        """
        today = datetime.date.today().strftime("%Y-%m-%d")
        status = DefaultStatus.ACTIVE.value
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                query = "SELECT name FROM tasks WHERE due_date = ? AND status = ?"
                cursor.execute(query, (today, status))
                tasks = [row[0] for row in cursor.fetchall()]
                logging.info(f"Tasks due today: {tasks}")
                return tasks
        except sqlite3.DatabaseError as e:
            logging.error(f"Database error: {e}")
            return []
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return []

    def export_tasks(self, file_path):
        """
        Exports active tasks to a CSV file.

        Args:
            file_path: The file path where the tasks should be exported.

        Returns:
            A success message if the export is successful, an error message otherwise.
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM tasks WHERE status = ?', (DefaultStatus.ACTIVE.value,))
                tasks = cursor.fetchall()

            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['ID', 'Name', 'Due Date', 'Priority', 'Category', 'Created At', 'Status'])
                for task in tasks:
                    writer.writerow(task)

            return "Tasks exported successfully."
        except Exception as e:
            return f"Error exporting tasks: {e}"  # Return error message in case of failure

    def import_tasks(self, file_name):
        """
        Imports tasks from a CSV file into the database.

        Args:
            file_name: The path to the CSV file containing tasks.

        Returns:
            A success message if the import is successful, an error message otherwise.
        """
        try:
            with open(file_name, mode='r') as file:
                reader = csv.reader(file)
                next(reader, None)  # Skip the header row
                with self.get_db_connection() as conn:
                    cursor = conn.cursor()
                    for row in reader:
                        # Ensure each row has the required number of elements
                        if len(row) >= 5:
                            task_name, due_date, priority, category = row[1:5]

                            # Validate the task name
                            if not utils.is_valid_task_name(task_name):
                                raise ValueError(f"Invalid task name: {task_name}")

                            # Prepare other task details and insert into the database
                            created_at = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
                            cursor.execute(
                                "INSERT INTO tasks (name, due_date, priority, category, created_at, status) VALUES (?, ?, ?, ?, ?, ?)",
                                (task_name, due_date, priority, category,
                                created_at, DefaultStatus.ACTIVE.value)
                            )
                        else:
                            print(f"Skipping incomplete row: {row}")
            return "Import successful"
        except Exception as e:
            # Error handling with detailed message
            return f"Import failed: {str(e)}"


    def get_preferences(self):
        """
        Retrieves user preferences from the database.

        Returns:
            A dictionary of preferences if successful, an empty dictionary otherwise.
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT key, value FROM preferences")
                # Create a dictionary from the fetched preferences
                return {key: value for key, value in cursor.fetchall()}
        except sqlite3.Error as e:
            return {}  # Returns an empty dictionary in case of an error

    def save_preferences(self, preferences):
        """
        Save preferences to the database.
        :param preferences: A dictionary of preferences to be saved.
        :return: None if successful, error message if an error occurs.
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
                for key, value in preferences.items():
                    cursor.execute("REPLACE INTO preferences (key, value, created_at) VALUES (?, ?, ?)", (key, value, current_time))
        except sqlite3.Error as e:
            logging.error(f"Error saving preferences: {e}")
            return f"Failed to save preferences: {e}"
        return None  # Success
