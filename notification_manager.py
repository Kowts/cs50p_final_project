import datetime
import logging
import utils

# Setup logging as soon as possible, ideally at the start of the application
utils.setup_logging()

class NotificationManager:
    def __init__(self):
        # Dictionary to store the last sent time of notifications
        self.sent_notifications = {}

    def should_send_notification(self, notification_id, frequency="daily"):
        current_time = datetime.datetime.now()
        last_sent_time = self.sent_notifications.get(notification_id)

        if last_sent_time:
            if frequency == "daily":
                if last_sent_time.date() == current_time.date():
                    return False
            elif frequency == "hourly":
                hour_diff = (current_time - last_sent_time).total_seconds() / 3600
                if hour_diff < 1:
                    return False
            elif frequency == "weekly":
                if current_time.isocalendar()[1] == last_sent_time.isocalendar()[1]:
                    return False
            elif frequency == "monthly":
                if last_sent_time.month == current_time.month and last_sent_time.year == current_time.year:
                    return False
            elif frequency == "biweekly":
                day_diff = (current_time - last_sent_time).days
                if day_diff < 14:
                    return False
            elif frequency.startswith("custom_"):
                hours = int(frequency.split("_")[1])
                hour_diff = (current_time - last_sent_time).total_seconds() / 3600
                if hour_diff < hours:
                    return False
            elif frequency == "yearly":
                if last_sent_time.year == current_time.year:
                    return False
            elif frequency == "immediate":
                return True
        return True

    def send_notification(self, notification_id, title, message, frequency="daily", timeout=10, app_name='YourApp'):
        if not title or not message:
            logging.error("Notification title and message cannot be empty.")
            return False

        try:
            if self.should_send_notification(notification_id, frequency):
                success = utils.send_windows_notification(title, message, timeout, app_name)
                if success:
                    self.sent_notifications[notification_id] = datetime.datetime.now()
                    logging.info(f"Notification sent: {title}")
                else:
                    logging.warning(f"Failed to send notification: {title}")
                return success
            else:
                logging.info(f"Notification not sent (already sent according to frequency '{frequency}'): {title}")
                return False
        except Exception as e:
            logging.error(f"Error in sending notification: {e}")
            return False
