import os

APP_NAME = os.getenv('APP_NAME')

# Constants for database file and default values, loaded from environment variables
DATABASE_FILE = os.getenv('DATABASE_FILE')
DEFAULT_PRIORITIES = os.getenv('DEFAULT_PRIORITIES').split(',')
DEFAULT_CATEGORIES = os.getenv('DEFAULT_CATEGORIES').split(',')

# Constants for status
STATUS_INACTIVE = 0
STATUS_ACTIVE = 1
STATUS_COMPLETED = 2

# Constants for theme, style and font size
THEME = os.getenv('THEME').split(',')
FONT_SIZE = os.getenv('FONT_SIZE').split(',')
DEFAULT_STYLESHEET = ""
THEME_MAP = {
    'Default': DEFAULT_STYLESHEET,
    'Light': 'light_blue.xml',
    'Dark': 'dark_blue.xml'

}

# Constants for default user credentials, loaded from environment variables
DEFAULT_USER = os.getenv('DEFAULT_USER')
DEFAULT_PASSWORD = os.getenv('DEFAULT_PASSWORD')

# Constants for regular expressions
REGEX_PATTERNS = {
    'password': r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()]).{8,}$',
    'email': r"[^@]+@[^@]+\.[^@]+"
}
