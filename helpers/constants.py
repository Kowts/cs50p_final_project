from helpers.utils import get_env_variable

# Constants for database file and default values, loaded from environment variables
DATABASE_FILE = get_env_variable('DATABASE_FILE')
DEFAULT_PRIORITIES = get_env_variable('DEFAULT_PRIORITIES').split(',')
DEFAULT_CATEGORIES = get_env_variable('DEFAULT_CATEGORIES').split(',')

# Constants for status
STATUS_ACTIVE = 1
STATUS_INACTIVE = 0

# Constants for theme and font size
THEME = get_env_variable('THEME').split(',')
FONT_SIZE = get_env_variable('FONT_SIZE').split(',')

# Centralized configuration for regular expressions
REGEX_PATTERNS = {
    'password': r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()]).{8,}$',
    'email': r"[^@]+@[^@]+\.[^@]+"
}
