import os
import sqlite3
import hashlib
from PyQt6.QtCore import QDateTime
from PyQt6.QtWidgets import QMessageBox

class TaskManager:
    def __init__(self, db_file='database.db'):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        self.create_table()

    def hash_password(self, password, salt=None):
        if salt is None:
            # Generate a random salt
            salt = hashlib.sha256(os.urandom(32)).hexdigest()

        # Encode the password to bytes
        password_bytes = password.encode('utf-8')

        # Encode the salt to bytes
        salt_bytes = salt.encode('utf-8')
        print(f"salt: {salt}")
        print(f"salt_bytes: {salt_bytes}")

        # Combine the password and salt
        password_salt = password_bytes + salt_bytes

        # Create a SHA-256 hash of the password + salt
        hashed_password = hashlib.sha256(password_salt).hexdigest()

        return hashed_password

    def create_table(self):
        self.cursor.execute('''
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
        self.conn.commit()

        # Create priorities and categories tables if they don't exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS priorities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        ''')
        self.conn.commit()

        # Create a table for user credentials
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status INTEGER
            )
        ''')
        self.conn.commit()

        # Insert default priorities and categories if they don't exist
        self.insert_default_priorities()
        self.insert_default_categories()

    def insert_default_priorities(self):
        # Check if there are any priorities in the table
        self.cursor.execute('SELECT COUNT(*) FROM priorities')
        count = self.cursor.fetchone()[0]

        if count == 0:
            # Insert default priorities
            default_priorities = ["Low", "Medium", "High"]
            for priority in default_priorities:
                self.cursor.execute("INSERT INTO priorities (name) VALUES (?)", (priority,))
            self.conn.commit()

    def insert_default_categories(self):
        # Check if there are any categories in the table
        self.cursor.execute('SELECT COUNT(*) FROM categories')
        count = self.cursor.fetchone()[0]

        if count == 0:
            # Insert default categories
            default_categories = ["Work", "Personal", "Shopping", "Other"]
            for category in default_categories:
                self.cursor.execute("INSERT INTO categories (name) VALUES (?)", (category,))
            self.conn.commit()

    def load_priorities(self):
        try:
            self.cursor.execute('SELECT name FROM priorities')
            priorities = [row[0] for row in self.cursor.fetchall()]
            return priorities
        except sqlite3.Error as e:
            return []

    def load_categories(self):
        try:
            self.cursor.execute('SELECT name FROM categories')
            categories = [row[0] for row in self.cursor.fetchall()]
            return categories
        except sqlite3.Error as e:
            return []

    def get_existing_users(self):
        try:
            self.cursor.execute('SELECT username FROM users')
            users = [row[0] for row in self.cursor.fetchall()]
            return users
        except sqlite3.Error as e:
            return []

    def create_user(self, username, password):
        try:
            # Generate a unique salt for the user
            salt = hashlib.sha256(os.urandom(32)).hexdigest()

            # Hash the password with the salt
            hashed_password = self.hash_password(password, salt)

            # Get the current timestamp
            created_at = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")

            # Set the default user status to 1 (active)
            user_status = 1

            # Store the username, hashed password, salt, created_at timestamp, and status in the database
            self.cursor.execute("INSERT INTO users (username, password, salt, created_at, status) VALUES (?, ?, ?, ?, ?)",
                                (username, hashed_password, salt, created_at, user_status))
            self.conn.commit()

            return None  # No error message
        except sqlite3.Error as e:
            return str(e)  # Return the error message

    def verify_user(self, username, password):
        try:
            self.cursor.execute("SELECT password, salt FROM users WHERE username = ?", (username,))
            stored_data = self.cursor.fetchone()

            if stored_data:
                stored_hashed_password, salt = stored_data
                hashed_password = self.hash_password(password, salt)

                if stored_hashed_password == hashed_password:
                    return True  # Password is correct
            return False  # Password is incorrect or user not found

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False  # Error or user not found


    def add_task(self, task_name, due_date, priority, category):
        try:
            # Use the current timestamp for the "created_at" field
            created_at = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")

            # Add the task to the database
            self.cursor.execute(
                "INSERT INTO tasks (name, due_date, priority, category, created_at, status) VALUES (?, ?, ?, ?, ?, ?)",
                (task_name, due_date, priority, category, created_at, 1)  # Set status to 1 for active
            )
            self.conn.commit()

            # Retrieve the ID of the last inserted task
            task_id = self.cursor.lastrowid

            return None, task_id  # No error message, return the task ID

        except Exception as e:
            return str(e), None  # Return the error message and None for task ID if an exception occurs

    def list_tasks(self, status=None):
        if status is None:
            self.cursor.execute('SELECT id, name, due_date, priority, category FROM tasks WHERE status = 1')
        else:
            self.cursor.execute('SELECT id, name, due_date, priority, category FROM tasks WHERE status = ?', (status,))
        return self.cursor.fetchall()

    def remove_task(self, task_id):
        try:
            self.cursor.execute('UPDATE tasks SET status = 0 WHERE id = ?', (task_id,))
            self.conn.commit()
            return None  # No error message
        except sqlite3.Error as e:
            return str(e)

    def close_database(self):
        self.conn.close()

    def get_last_inserted_task_id(self):
        try:
            self.cursor.execute("SELECT last_insert_rowid()")
            task_id = self.cursor.fetchone()[0]
            return task_id
        except sqlite3.Error as e:
            return None

def show_error(title, message):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec()

def show_message(title, message):
    msg = QMessageBox()
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec()
