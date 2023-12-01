import os
import re
import csv
import sqlite3
from PyQt6.QtCore import QDateTime
import datetime
import logging
from helpers.utils import setup_logging, get_env_variable, is_valid_email, is_valid_username, is_valid_password, is_valid_task_name, hash_password, format_datetime
from helpers.constants import DATABASE_FILE, DEFAULT_PRIORITIES, DEFAULT_CATEGORIES, STATUS_ACTIVE, STATUS_INACTIVE, STATUS_COMPLETED

# Initialize logging configuration at application startup
setup_logging()

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
            # Handles database-specific errors with logging for troubleshooting
            logging.error(f"Database connection error: {e}")
            raise

    def validate_environment_variables(self):
        """
        Validates required environment variables and raises ValueError if any are missing or invalid.
        """
        # List of required environment variables
        required_vars = ['DATABASE_FILE', 'MAX_CONNECTION', 'DEFAULT_USER', 'DEFAULT_PASSWORD']
        missing_vars = [var for var in required_vars if not get_env_variable(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        if not os.path.exists(self.db_file):
            raise ValueError(f"The specified database file {self.db_file} does not exist.")

        max_connection = get_env_variable('MAX_CONNECTION')
        if max_connection and not max_connection.isdigit():
            raise ValueError("MAX_CONNECTION must be a numeric value.")

        if max_connection and not 1 <= int(max_connection) <= 100:
            raise ValueError("MAX_CONNECTION must be between 1 and 100.")

        admin_email = get_env_variable('ADMIN_EMAIL')
        if admin_email and not is_valid_email(admin_email):
            raise ValueError("Invalid email format for ADMIN_EMAIL.")

    def setup_database(self):
        """
        Sets up the database by creating necessary tables.
        """
        try:
            # Establish database connection and create tables
            with self.get_db_connection() as conn:
                self.create_users_table(conn)
                self.create_tasks_table(conn)
                self.create_priorities_table(conn)
                self.create_categories_table(conn)
                self.create_preferences_table(conn)
                self.create_user_activity_table(conn)
        except sqlite3.DatabaseError as e:
            logging.error(f"Database error: {e}")
        except Exception as e:
            logging.error(f"An error occurred: {e}")

    def custom_query(self, query, parameters, use_regex=False):
        try:
            with self.get_db_connection() as conn:
                if use_regex:
                    def regexp(expr, item):
                        reg = re.compile(expr)
                        return reg.search(item) is not None
                    conn.create_function("REGEXP", 2, regexp)
                cursor = conn.cursor()
                cursor.execute(query, parameters)
                return cursor.fetchall()
        except sqlite3.DatabaseError as e:
            # Handle the error
            return []

    def create_users_table(self, conn):
        """
        Creates the users table in the database.
        """
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                username TEXT NOT NULL,
                email TEXT,
                password TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status INTEGER DEFAULT 1
            )
        ''')

    def create_tasks_table(self, conn):
        """Creates the tasks table in the database with a foreign key reference to the users table."""
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                due_date TEXT,
                priority TEXT,
                category TEXT,
                created_at TEXT,
                status INTEGER,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')

    def create_priorities_table(self, conn):
        """
        Creates the priorities table and populates default values.
        """
        conn.execute('''
            CREATE TABLE IF NOT EXISTS priorities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                color TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status INTEGER DEFAULT 1,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        # self.insert_default_priorities(conn)

    def create_categories_table(self, conn):
        """
        Creates the categories table and populates default values.
        """
        conn.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status INTEGER DEFAULT 1,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        # self.insert_default_categories(conn)

    def create_preferences_table(self, conn):
        """
        Creates the preferences table in the database.
        """
        conn.execute('''
            CREATE TABLE IF NOT EXISTS preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                key TEXT UNIQUE,
                value TEXT,
                created_at TEXT,
                status INTEGER DEFAULT 1,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')

    def create_user_activity_table(self, conn):
        """Creates the tasks table in the database."""
        # SQL command for creating the tasks table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT NOT NULL,  -- 'Login' or 'Logout'
                created_at TEXT NOT NULL,
                status TEXT,  -- 'Success', 'Failure', or NULL for logout
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')

    def load_priorities(self, user_id):
        """
        Loads priorities from the database for a specific user.

        Args:
            user_id (int): The ID of the user.

        Returns:
            A list of priorities if successful, an empty list otherwise.
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT name FROM priorities WHERE user_id = ?', (user_id,))
                priorities = [row[0] for row in cursor.fetchall()]
                return priorities + DEFAULT_PRIORITIES
        except sqlite3.DatabaseError as e:
            logging.error(f"Database error: {e}")
            return []
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return []

    def load_categories(self, user_id):
        """
        Retrieves a list of category names from the database for a specific user.

        Args:
            user_id (int): The ID of the user.

        Returns:
            A list of category names if the query is successful, an empty list otherwise.
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT name FROM categories WHERE user_id = ?', (user_id,))
                categories = [row[0] for row in cursor.fetchall()]
                return categories + DEFAULT_CATEGORIES
        except sqlite3.DatabaseError as e:
            logging.error(f"Database error: {e}")
            return []
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return []

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

    def add_priority(self, priority_name, color, user_id):
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
                cursor.execute("INSERT INTO priorities (user_id, name, color, created_at, status) VALUES (?, ?, ?, ?, ?)", (user_id, priority_name, color, current_time, STATUS_ACTIVE))
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

    def add_category(self, category_name, user_id):
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
                cursor.execute("INSERT INTO categories (user_id, name, created_at, status) VALUES (?, ?, ?, ?)", (user_id, category_name, current_time, STATUS_ACTIVE))
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

    def get_user_data(self, user_id):
        """
        Fetches user data from the database based on the user ID.

        Args:
            user_id (int): The ID of the user.

        Returns:
            dict: A dictionary containing user data (username, email, etc.) or None if not found.
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()

                # Assuming the users table has columns like 'id', 'username', 'email', etc.
                query = "SELECT name, username, email, password, salt FROM users WHERE id = ?"
                cursor.execute(query, (user_id,))

                user_data = cursor.fetchone()
                if user_data:
                    return {
                        "name": user_data[0],
                        "username": user_data[1],
                        "email": user_data[2],
                        "password": user_data[3],
                        "salt": user_data[4]
                    }
                else:
                    return None

        except Exception as e:
            logging.error(f"An error occurred while fetching user data: {e}")
            return None

    def create_user(self, username, password):
        """
        Creates a new user in the database.

        Args:
            username: The username of the new user.
            password: The password of the new user.

        Returns:
            None if successful, an error message otherwise.
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                hashed_password, salt = hash_password(password)
                created_at = format_datetime(QDateTime.currentDateTime())
                cursor.execute("INSERT INTO users (username, password, salt, created_at, status) VALUES (?, ?, ?, ?, ?)", (username, hashed_password, salt, created_at, STATUS_ACTIVE))
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
            A tuple containing a boolean and the user ID if credentials are valid,
            (False, None) otherwise.
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, password, salt FROM users WHERE username = ?", (username,))
                stored_data = cursor.fetchone()

                if stored_data:
                    user_id, stored_hashed_password, salt = stored_data
                    hashed_password, _ = hash_password(password, salt)

                    if stored_hashed_password == hashed_password:
                        return True, user_id
                return False, None

        except sqlite3.Error:
            return False, None  # Return False if there's an error during the operation

    def username_exists(self, username):
        """Checks if a username already exists in the database."""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
                return cursor.fetchone() is not None
        except sqlite3.Error as e:
            logging.error(f"Database error in username_exists: {e}")
            return False  # In case of an error, safely return False

    def update_user_profile(self, user_id, name, username, email):
        """
        Updates the user's profile information in the database.

        Args:
            user_id (int): The ID of the user whose profile is being updated.
            name (str): The name of the user.
            username (str): The username of the user.
            email (str): The new email address of the user.

        Returns:
            str: A success message or an error message.
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                # Prepare the update query. You might have more fields to update.
                query = "UPDATE users SET name = ?, username = ?, email = ? WHERE id = ?"
                # Execute the query with new email and user_id
                cursor.execute(query, (name, username, email, user_id))
                # Commit the changes
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"An error occurred while updating user profile: {e}")
            return False

    def update_user_password(self, user_id, new_password):
        """
        Updates the password for a specific user.

        Args:
            user_id (int): The ID of the user whose password is to be updated.
            new_password (str): The new password for the user.

        Returns:
            bool: True if the update is successful, False otherwise.
        """
        try:
            # Hash the new password
            hashed_password, salt = hash_password(new_password)

            # Update the user's password in the database
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET password = ?, salt = ? WHERE id = ?", (hashed_password, salt, user_id))
                conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error updating user password: {e}")
            return False

    def log_user_activity(self, user_id, event_type, status=None):
        """
        Logs user activity (login/logout) to the database.

        Args:
            user_id: The ID of the user.
            event_type: Type of the event ('Login' or 'Logout').
            status: The result of the login attempt ('Success' or 'Failure'), or None for logout.

        Returns:
            None if successful, an error message otherwise.
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                created_at = format_datetime(QDateTime.currentDateTime())
                cursor.execute("INSERT INTO user_activity (user_id, type, created_at, status) VALUES (?, ?, ?, ?)", (user_id, event_type, created_at, status))
                return None
        except sqlite3.Error as e:
            return str(e)

    def add_task(self, user_id, task_name, due_date, priority, category):
        """
        Adds a new task to the database.

        Args:
            user_id: The id of the user.
            task_name: The name of the task.
            due_date: The due date of the task.
            priority: The priority of the task.
            category: The category of the task.

        Returns:
            None and the task ID if successful, an error message and None otherwise.
        """
        if not is_valid_task_name(task_name):
            raise ValueError("Invalid task name.")

        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                created_at = format_datetime(QDateTime.currentDateTime())
                cursor.execute(
                    "INSERT INTO tasks (user_id, name, due_date, priority, category, created_at, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (user_id, task_name, due_date, priority,category, created_at, STATUS_ACTIVE)
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

    def list_tasks(self, user_id, status=None):
        """
        Lists tasks along with priority color based on their status and user ID.

        Args:
            user_id: The ID of the user.
            status: The status of the tasks to list. If None, lists both active and completed tasks.

        Returns:
            A list of tasks with priority color matching the given status, empty list in case of an error.
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()

                # If status is None, fetch tasks with status 1 (active) and 2 (completed)
                if status is None:
                    status_tuple = (STATUS_ACTIVE, STATUS_COMPLETED)
                    query = '''
                    SELECT t.id, t.name, t.due_date, t.priority, t.category, t.status, p.color
                    FROM tasks t
                    LEFT JOIN priorities p ON t.priority = p.name AND t.user_id = p.user_id
                    WHERE t.user_id = ? AND t.status IN (?, ?)
                    '''
                    cursor.execute(query, (user_id, *status_tuple))
                else:
                    query = '''
                    SELECT t.id, t.name, t.due_date, t.priority, t.category, t.status, p.color
                    FROM tasks t
                    LEFT JOIN priorities p ON t.priority = p.name AND t.user_id = p.user_id
                    WHERE t.user_id = ? AND t.status = ?
                    '''
                    cursor.execute(query, (user_id, status))

                return cursor.fetchall()  # Returns a list of tasks with priority color
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
                query = f"UPDATE tasks SET status = {STATUS_INACTIVE} WHERE id IN ({placeholders})"
                cursor.execute(query, task_ids)
                conn.commit()
            return "Tasks successfully set as inactive."
        except sqlite3.Error as e:
            return str(e)

    def search_tasks(self, user_id, text, match_case=False, whole_word=False, use_regex=False):
        """
        Search tasks based on the provided criteria.

        Args:
            user_id (int): The user ID for whom to search the tasks.
            text (str): The text to search for.
            match_case (bool): Whether the search should be case-sensitive.
            whole_word (bool): Whether to match whole words only.
            use_regex (bool): Whether to treat 'text' as a regular expression.

        Returns:
            list: A list of tasks matching the search criteria.
        """
        with self.get_db_connection() as conn:
            # Define a REGEXP function for regex searches
            if use_regex:
                def regexp(expr, item):
                    reg = re.compile(
                        expr, re.IGNORECASE if not match_case else 0)
                    return reg.search(item) is not None
                conn.create_function("REGEXP", 2, regexp)
                query = '''
                    SELECT t.id, t.name, t.due_date, t.priority, t.category, t.status, p.color
                    FROM tasks t
                    LEFT JOIN priorities p ON t.priority = p.name AND t.user_id = p.user_id
                    WHERE t.user_id = ? AND t.name REGEXP ? AND t.status IN (1, 2)
                '''
                parameters = [user_id, text]
            else:
                like_clause = f"%{text}%"
                case_clause = "COLLATE RTRIM" if match_case else ""
                whole_word_clause = f"(t.name LIKE ? OR t.name LIKE ? OR t.name LIKE ? OR t.name = ?)" if whole_word else "t.name LIKE ?"
                query = f'''
                    SELECT t.id, t.name, t.due_date, t.priority, t.category, t.status, p.color
                    FROM tasks t
                    LEFT JOIN priorities p ON t.priority = p.name AND t.user_id = p.user_id
                    WHERE t.user_id = ? AND {whole_word_clause} AND t.status IN (1, 2)
                    {case_clause}
                '''
                parameters = [user_id, like_clause, f"{text} %", f"% {text}", f"% {text} %", text] if whole_word else [
                    user_id, like_clause]

            try:
                cursor = conn.cursor()
                cursor.execute(query, parameters)
                return cursor.fetchall()
            except Exception as e:
                logging.error(f"Database search error: {e}")
                return []

    def get_last_inserted_task_id(self):
        """
        Retrieves the ID of the last inserted task in the database.

        Returns:
            The ID of the last inserted task if successful, None otherwise.
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT last_insert_rowid()") # SQLite specific query
                task_id = cursor.fetchone()[0] # Fetch the first column of the first row
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
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                query = "SELECT name FROM tasks WHERE due_date = ? AND status = ?"
                cursor.execute(query, (today, STATUS_ACTIVE)) # '1' is the value indicating an active task
                tasks = [row[0] for row in cursor.fetchall()] # Fetch all rows and extract the task names
                logging.info(f"Tasks due today: {tasks}")
                return tasks
        except sqlite3.DatabaseError as e:
            logging.error(f"Database error: {e}")
            return []
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return []

    def export_tasks(self, file_path, user_id):
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
                cursor.execute(
                    'SELECT name, due_date, priority, category, created_at FROM tasks WHERE user_id = ? AND status IN (1, 2)', (user_id,))
                tasks = cursor.fetchall()

            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['Name', 'Due Date', 'Priority', 'Category', 'Created At'])
                for task in tasks:
                    writer.writerow(task)

            return "Tasks exported successfully."
        except Exception as e:
            return f"Error exporting tasks: {e}"  # Return error message in case of failure

    def import_tasks(self, file_name, user_id):
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
                            task_name, due_date, priority, category = row[0:4]

                            # Validate the task name
                            if not is_valid_task_name(task_name):
                                raise ValueError(f"Invalid task name: {task_name}")

                            # Prepare other task details and insert into the database
                            created_at = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
                            cursor.execute(
                                "INSERT INTO tasks (user_id, name, due_date, priority, category, created_at, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (user_id, task_name, due_date, priority,category, created_at, STATUS_ACTIVE)
                            )
                        else:
                            logging.error(f"Skipping incomplete row: {row}")
            return "Import successful"
        except Exception as e:
            # Error handling with detailed message
            return f"Import failed: {str(e)}"

    def set_task_complete(self, task_id):
        """
        Sets the status of the task with the given ID to complete.

        Parameters:
            task_id (int): The ID of the task to be marked as complete.
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                # '2' is the value indicating a task is complete
                cursor.execute("UPDATE tasks SET status = 2 WHERE id = ?", (task_id,))
                conn.commit()
        except Exception as e:
            logging.error(f"Error setting task as complete: {e}")
            raise

    def get_preferences(self, user_id):
        """
        Retrieves user preferences from the database.

        Returns:
            A dictionary of preferences if successful, an empty dictionary otherwise.
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT key, value FROM preferences WHERE user_id = ?', (user_id,))
                # Create a dictionary from the fetched preferences
                return {key: value for key, value in cursor.fetchall()}
        except sqlite3.Error as e:
            return {}  # Returns an empty dictionary in case of an error

    def save_preferences(self, user_id, preferences):
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
                    cursor.execute("REPLACE INTO preferences (user_id, key, value, created_at) VALUES (?,?, ?, ?)", (user_id, key, value, current_time))
        except sqlite3.Error as e:
            logging.error(f"Error saving preferences: {e}")
            return f"Failed to save preferences: {e}"
        return None  # Success

    def get_task_analytics(self, user_id):
        """
        Gathers analytical data about tasks for a specific user.

        Args:
            user_id (int): The user ID for whom to gather analytics.

        Returns:
            dict: A dictionary containing task analytics such as task count by status, category, etc.
        """
        with self.get_db_connection() as conn:
            cursor = conn.cursor()

            # Get counts for incomplete (1) and complete (2) tasks
            cursor.execute('''
                SELECT status, COUNT(*)
                FROM tasks
                WHERE user_id = ?
                GROUP BY status
                HAVING status IN (1, 2)
            ''', (user_id,))
            status_data = cursor.fetchall()


            # Get counts for each category
            cursor.execute('''
                SELECT category, COUNT(*)
                FROM tasks
                WHERE user_id = ? AND status IN (1, 2)
                GROUP BY category
            ''', (user_id,))
            category_data = cursor.fetchall()


            # Get tasks count by due date
            cursor.execute('''
                SELECT due_date, COUNT(*) as count
                FROM tasks
                WHERE user_id = ? AND status IN (1, 2)
                GROUP BY due_date
                ORDER BY due_date
            ''', (user_id,))
            due_date_data = cursor.fetchall()

        # Convert the database results into a more convenient structure if necessary
        status_data = [{'status': row[0], 'count': row[1]} for row in status_data]
        category_data = [{'category': row[0], 'count': row[1]} for row in category_data]
        due_date = [{'due_date': row[0], 'count': row[1]} for row in due_date_data]

        # Compile the analytics into a single dictionary
        analytics = {
            'status': status_data,
            'category': category_data,
            'due_date': due_date
        }

        return analytics
