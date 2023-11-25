from helpers.utils import get_env_variable

# Constants for database file and default values, loaded from environment variables
DATABASE_FILE = get_env_variable('DATABASE_FILE')
DEFAULT_PRIORITIES = get_env_variable('DEFAULT_PRIORITIES').split(',')
DEFAULT_CATEGORIES = get_env_variable('DEFAULT_CATEGORIES').split(',')

# Constants for status
STATUS_ACTIVE = 1
STATUS_INACTIVE = 0
