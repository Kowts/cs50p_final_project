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

# Constants for theme and font size
DEFAULT_STYLESHEET = ""
THEME_MAP = {
    'Dark': 'dark_blue.xml',
    'Light': 'light_blue.xml',
    'Default': DEFAULT_STYLESHEET
}
