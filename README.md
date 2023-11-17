# Task Manager Pro

## Introduction

Task Manager Pro is a PyQt-based desktop application designed to streamline personal task management. With a focus on simplicity and ease of use, it provides a robust platform for users to manage their daily tasks effectively.

## Features

- **Task CRUD**: Create, read, update, and delete tasks with ease.
- **Task Prioritization**: Assign priorities to tasks and organize your day.
- **Search Functionality**: Quickly find tasks with a powerful search feature.
- **Printing Capability**: Print out task lists for offline reference.
- **User Customization**: Set preferences such as themes and notification settings.

## Project Structure

- `main.py`: The entry point of the application, initializing the main window and event loop.
- `task_manager.py`: Contains the logic for task management operations and database interactions.
- `preferences_manager.py`: Manages user preferences and applies settings such as themes and window flags.
- `login_dialog.py`: Handles user authentication and session initiation.
- `utils.py`: A collection of utility functions that aid in various operations like logging and password hashing.

## Design Decisions

### User Authentication

We implemented a login system to provide a personalized experience for each user. This decision was debated; however, the need for personalized task lists was a deciding factor.

### Task Persistence

SQLite was chosen as the database solution for its simplicity and ease of deployment. While other database systems offer more features, SQLite meets our requirements without adding complexity.

### Extensibility

We designed the system with extensibility in mind. The modular nature of the codebase allows for easy expansion, such as adding new features or integrating with external services.

## Getting Started

To get started with Task Manager Pro, clone the repository and install the required dependencies:

```bash
git clone https://github.com/yourusername/task-manager-pro.git
cd task-manager-pro
pip install -r requirements.txt
