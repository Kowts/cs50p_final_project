import pytest
from unittest.mock import MagicMock
from project import create_user, login_user, fetch_tasks
from models.task_manager import TaskManager

# Fixture for setting up a mock TaskManager
# Create a mock object for TaskManager.
# This avoids any real database interactions during testing.
@pytest.fixture
def mock_task_manager(monkeypatch):
    # Create a mock TaskManager instance
    mock_manager = MagicMock(spec=TaskManager)
    # Use the monkeypatch fixture to replace TaskManager with the mock
    monkeypatch.setattr("project.TaskManager", lambda: mock_manager)
    return mock_manager

def test_create_user(mock_task_manager):
    # Mock the create_user method to return None (indicating success)
    mock_task_manager.create_user.return_value = None
    assert create_user("newuser", "password") is None
    mock_task_manager.create_user.assert_called_once_with("newuser", "password")

def test_create_user_failure(mock_task_manager):
    # Mock the create_user method to return an error message
    mock_task_manager.create_user.return_value = "Error creating user"
    assert create_user("existinguser", "password") == "Error creating user"
    mock_task_manager.create_user.assert_called_once_with("existinguser", "password")

def test_login_user(mock_task_manager):
    # Mock a successful login scenario
    mock_task_manager.verify_user.return_value = (True, 1)
    assert login_user("validuser", "validpassword") == (True, 1)
    mock_task_manager.verify_user.assert_called_once_with("validuser", "validpassword")

def test_login_user_invalid(mock_task_manager):
    # Mock an unsuccessful login scenario
    mock_task_manager.verify_user.return_value = (False, None)
    assert login_user("invaliduser", "invalidpassword") == (False, None)
    mock_task_manager.verify_user.assert_called_once_with("invaliduser", "invalidpassword")

def test_fetch_tasks(mock_task_manager):
    # Mock fetching tasks for a user with existing tasks
    mock_task_manager.list_tasks.return_value = ["Task 1", "Task 2"]
    assert fetch_tasks(1) == ["Task 1", "Task 2"]
    mock_task_manager.list_tasks.assert_called_once_with(1)

def test_fetch_tasks_no_data(mock_task_manager):
    # Mock fetching tasks for a user with no tasks
    mock_task_manager.list_tasks.return_value = []
    assert fetch_tasks(2) == []
    mock_task_manager.list_tasks.assert_called_once_with(2)

def test_fetch_tasks_error(mock_task_manager):
    # Mock an error scenario while fetching tasks
    mock_task_manager.list_tasks.side_effect = Exception("Database error")
    assert fetch_tasks(3) == []
    mock_task_manager.list_tasks.assert_called_once_with(3)
