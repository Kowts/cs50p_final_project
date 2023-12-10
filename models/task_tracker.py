"""
task_tracker.py: Implements a background thread for tracking due tasks.
It periodically checks for tasks that are nearing their deadline and emits signals to notify the user.
"""
from PyQt6.QtCore import QThread, pyqtSignal
from models.task_manager import TaskManager
import logging

class TaskTracker(QThread):
    """
    A class that tracks tasks and emits a signal when due tasks are found.

    Attributes:
        notify_due_tasks (pyqtSignal): A signal that is emitted when due tasks are found.

    Methods:
        __init__(self, task_manager): Initializes the TaskTracker object.
        run(self): Runs the task tracking process.
    """

    notify_due_tasks = pyqtSignal(list)

    def __init__(self, task_manager: TaskManager):
        """
        Initializes the TaskTracker object.

        Parameters:
            task_manager (TaskManager): The task manager object.
        """
        super().__init__()
        self.task_manager = task_manager

    def run(self):
        """
        Runs the task tracking process.
        """
        while True:
            self.sleep(10) # Sleep for 10 seconds
            logging.info("Checking for due tasks...")
            if today_tasks := self.task_manager.get_due_tasks():
                self.notify_due_tasks.emit(today_tasks)
                logging.info(f"Found {len(today_tasks)} due tasks.")
            else:
                logging.info("No tasks due today.")

    def stop(self):
        self.running = False
        self.wait()
