import datetime
import logging
import utils

# Initialize logging at the start of the application for consistent and centralized logging.
utils.setup_logging()

class NotificationManager:
    """Manages notifications, ensuring they are sent based on predefined frequencies."""

    def __init__(self):
        # Store the last time a notification was sent as {notification_id: datetime}
        self.sent_notifications = {}

    def should_send_notification(self, notification_id, frequency="daily"):
        """Determines if a notification should be sent based on its frequency.

        Args:
            notification_id (str): Unique identifier for the notification.
            frequency (str): Frequency of the notification (e.g., 'daily', 'hourly').

        Returns:
            bool: True if the notification should be sent, False otherwise.
        """
        current_time = datetime.datetime.now()
        last_sent_time = self.sent_notifications.get(notification_id)

        # Evaluate based on the frequency if the notification should be sent
        if last_sent_time:
            if frequency == "daily":
                # Check if the notification was already sent today
                return last_sent_time.date() != current_time.date()
            elif frequency == "hourly":
                # Check if an hour has passed since the last notification
                return (current_time - last_sent_time).total_seconds() >= 3600
            # Similar checks for other frequencies...
            elif frequency == "weekly":
                # Check if the notification was sent in the current calendar week
                return current_time.isocalendar()[1] != last_sent_time.isocalendar()[1]
            # ... more frequency checks ...
            elif frequency == "immediate":
                # Send immediately regardless of the last sent time
                return True
        return True

    def send_notification(self, notification_id, title, message, task_manager, frequency="daily", timeout=10, app_name='YourApp'):
        """Sends a notification based on user preferences and frequency.

        Args:
            notification_id (str): Unique identifier for the notification.
            title (str): Title of the notification.
            message (str): Notification message content.
            task_manager (TaskManager): Task manager instance for additional operations.
            frequency (str): Frequency of the notification.
            timeout (int): Timeout for the notification.
            app_name (str): Name of the application sending the notification.

        Returns:
            bool: True if the notification was successfully sent, False otherwise.
        """
        if not title or not message:
            # Ensure that both title and message are provided
            logging.error("Notification title and message cannot be empty.")
            return False

        try:
            # Retrieve user preferences to check if notifications are enabled
            preferences = task_manager.get_preferences()
            enable_notifications = preferences.get(
                'enable_notifications', 'True') == 'True'

            if enable_notifications and self.should_send_notification(notification_id, frequency):
                # Send the notification if enabled and frequency conditions are met
                success = utils.send_windows_notification(
                    title, message, task_manager, timeout, app_name)
                if success:
                    # Update the last sent time on successful notification
                    self.sent_notifications[notification_id] = datetime.datetime.now(
                    )
                    logging.info(f"Notification sent: {title}")
                else:
                    logging.warning(f"Failed to send notification: {title}")
                return success
            else:
                # Log if notifications are disabled or already sent as per frequency
                logging.info(
                    f"Notification not sent: User has disabled notifications or already sent according to frequency '{frequency}'")
                return False
        except Exception as e:
            # Log any exceptions encountered during notification sending
            logging.error(f"Error in sending notification: {e}")
            return False
