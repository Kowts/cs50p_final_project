import os
import sqlite3, utils
from PyQt6.QtCore import QDateTime
from dotenv import load_dotenv
import datetime
import logging
from enum import Enum

# Setup logging as soon as possible, ideally at the start of the application
utils.setup_logging()

# Constants
DATABASE_FILE = utils.get_env_variable('DATABASE_FILE')
DEFAULT_PRIORITIES = utils.get_env_variable('DEFAULT_PRIORITIES').split(',')
DEFAULT_CATEGORIES = utils.get_env_variable('DEFAULT_CATEGORIES').split(',')

class UserStatus(Enum):
    ACTIVE = 1
    INACTIVE = 0
class TaskManager:

    """
    A class to manage tasks and user authentication.
    """

    def __init__(self, db_file=DATABASE_FILE):
        self.db_file = db_file
        self.validate_environment_variables()
        self.setup_database()

    def validate_environment_variables(self):
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
        Sets up the database and creates necessary tables.
        """
        try:
            with utils.get_db_connection(self.db_file) as conn:
                self.create_tasks_table(conn)
                self.create_priorities_table(conn)
                self.create_categories_table(conn)
                self.create_users_table(conn)
        except sqlite3.DatabaseError as e:
            logging.error(f"Database error: {e}")
        except Exception as e:
            logging.error(f"An error occurred: {e}")


    def create_tasks_table(self, conn):
        """
        Creates the tasks table in the database.
        """
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
                name TEXT NOT NULL
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
                name TEXT NOT NULL
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
                status INTEGER
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
            for priority in DEFAULT_PRIORITIES:
                cursor.execute("INSERT INTO priorities (name) VALUES (?)", (priority,))

    def insert_default_categories(self, conn):
        """
        Inserts default categories if they don't exist.
        """
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM categories')
        count = cursor.fetchone()[0]

        if count == 0:
            for category in DEFAULT_CATEGORIES:
                cursor.execute("INSERT INTO categories (name) VALUES (?)", (category,))

    def load_priorities(self):
        try:
            with sqlite3.connect(self.db_file) as conn:
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
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT name FROM categories')
                categories = [row[0] for row in cursor.fetchall()]
                return categories
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

    def get_existing_users(self):
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT username FROM users')
                users = [row[0] for row in cursor.fetchall()]
                return users
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

    def create_user(self, username, password):
        if not utils.is_valid_username(username) or not utils.is_valid_password(password):
            raise ValueError("Invalid username or password")

        try:
            with utils.get_db_connection(self.db_file) as conn:
                cursor = conn.cursor()
                hashed_password, salt = utils.hash_password(password)
                created_at = utils.format_datetime(QDateTime.currentDateTime())
                user_status = UserStatus.ACTIVE.value

                cursor.execute("INSERT INTO users (username, password, salt, created_at, status) VALUES (?, ?, ?, ?, ?)",
                            (username, hashed_password, salt, created_at, user_status))
            return None
        except sqlite3.Error as e:
            return str(e)

    def verify_user(self, username, password):
        try:
            with sqlite3.connect(self.db_file) as conn:
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

    def add_task(self, task_name, due_date, priority, category):
        if not utils.is_valid_task_name(task_name):
            raise ValueError("Invalid task name.")

        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                created_at = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
                cursor.execute(
                    "INSERT INTO tasks (name, due_date, priority, category, created_at, status) VALUES (?, ?, ?, ?, ?, ?)",
                    (task_name, due_date, priority, category, created_at, UserStatus.ACTIVE.value)
                )
                task_id = cursor.lastrowid
            return None, task_id
        except sqlite3.Error as e:
            return str(e), None

    def list_tasks(self, status=None):
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                if status is None:
                    cursor.execute('SELECT id, name, due_date, priority, category FROM tasks WHERE status = ?', (UserStatus.ACTIVE.value,))
                else:
                    cursor.execute('SELECT id, name, due_date, priority, category FROM tasks WHERE status = ?', (status,))
                return cursor.fetchall()
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

    def remove_task(self, task_id):
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE tasks SET status = ? WHERE id = ?', (UserStatus.INACTIVE.value, task_id,))
            return None
        except sqlite3.Error as e:
            return str(e)

    def get_last_inserted_task_id(self):
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT last_insert_rowid()")
                task_id = cursor.fetchone()[0]
            return task_id
        except sqlite3.Error:
            return None

    def get_due_tasks(self):
        today = datetime.date.today().strftime("%Y-%m-%d")
        try:
            with utils.get_db_connection(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM tasks WHERE due_date = ?", (today,))
                tasks = [row[0] for row in cursor.fetchall()]
                logging.info(f"Tasks due today: {tasks}")
                return tasks
        except sqlite3.DatabaseError as e:
            logging.error(f"Database error: {e}")
            return []
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return []
