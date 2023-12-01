"""
notification.py: Manages the sending of notifications within the application.
It encapsulates all the logic required to notify users about different events or task reminders.
"""
import os
import datetime
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Tuple, List
from models.task_manager import TaskManager
from helpers.utils import setup_logging, get_env_variable, send_windows_notification
from helpers.constants import APP_NAME

# Initialize logging at the start of the application for consistent and centralized logging.
setup_logging()

class NotificationManager:
    """Manages notifications, ensuring they are sent based on predefined frequencies."""

    def __init__(self, task_manager: TaskManager, user_id=None):
        # Store the last time a notification was sent as {notification_id: datetime}
        self.sent_notifications = {}
        self.task_manager = task_manager
        self.user_id = user_id

    # Helper function to update the last sent time for a notification
    def update_last_sent_time(self, notification_id):
        self.sent_notifications[notification_id] = datetime.datetime.now()

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
            elif frequency == "immediate":
                # Send immediately regardless of the last sent time
                return True
        return True

    def send_notification(self, notification_id, title, message, frequency="daily", timeout=10, app_name=APP_NAME):
        """Sends a notification based on user preferences and frequency.

        Args:
            notification_id (str): Unique identifier for the notification.
            title (str): Title of the notification.
            message (str): Notification message content.
            frequency (str): Frequency of the notification. Defaults to 'daily'.
            timeout (int): Timeout for the notification. Defaults to 10.
            app_name (str): Name of the application sending the notification. Defaults to APP_NAME.

        Returns:
            bool: True if the notification was successfully sent, False otherwise.
        """
        if not title or not message:
            # Ensure that both title and message are provided
            logging.error("Notification title and message cannot be empty.")
            return False

        try:
            # Retrieve user preferences to check if notifications are enabled
            preferences = self.task_manager.get_preferences(self.user_id)
            enable_notifications = preferences.get('enable_notifications', 'True') == 'True'

            if enable_notifications and self.should_send_notification(notification_id, frequency):

                # Retrieve user email to send an email notification
                user_info = self.task_manager.get_user_data(self.user_id)
                email = user_info['email'] if user_info else None

                # Send the notification and Send an email
                success = send_windows_notification(title, message, self.task_manager, self.user_id, timeout=timeout, app_name=app_name)
                if success:
                    # Update the last sent time on successful notification
                    self.update_last_sent_time(notification_id)
                    if email:
                        self.send_email(email, title, message)  # Send an email
                    logging.info(f"Notification sent: {title}")
                else:
                    logging.warning(f"Failed to send notification: {title}")
                return success
            else:
                # Log if notifications are disabled or already sent as per frequency
                logging.info(f"Notification not sent: User has disabled notifications or already sent according to frequency '{frequency}'")
                return False
        except Exception as e:
            # Log any exceptions encountered during notification sending
            logging.error(f"Error in sending notification: {e}")
            return False

    def connect_smtp(self) -> Tuple[smtplib.SMTP, str]:
        """
        Connects to the SMTP server using the provided credentials and returns the SMTP server object and the username.

        Returns:
            A tuple containing the SMTP server object and the username.

        Raises:
            ValueError: If there is an error fetching the SMTP credentials.
            smtplib.SMTPException: If there is an error connecting to the SMTP server.
        """
        try:
            # Get SMTP credentials
            username = get_env_variable('SMTP_USER')
            password = get_env_variable('SMTP_PASS')
            server = get_env_variable('SMTP_URL')
            port = get_env_variable('SMTP_PORT')

        except ValueError as e:
            # Log and re-raise any exceptions encountered while fetching credentials
            logging.error(f"Failed to get SMTP credentials: {e}")
            raise

        try:
            # Connect to the SMTP server
            smtp_server = smtplib.SMTP(server, port)
            # Upgrade the connection to a secure encrypted SSL/TLS connection
            smtp_server.starttls()
            # Login to the SMTP server
            smtp_server.login(username, password)
        except smtplib.SMTPException as e:
            # Log and re-raise any exceptions encountered while connecting to the SMTP server
            logging.error(f"Failed to connect to SMTP server: {e}")
            raise

        # Return the SMTP server object and the username
        return smtp_server, username

    def send_email(self, recipient_email: str, subject: str, message_body: str, attachment_paths: List[str] = []) -> None:
        """
        Sends an email with optional attachments.

        Parameters:
        - recipient_email: The email address of the recipient.
        - subject: The subject of the email.
        - message_body: The body of the email.
        - attachment_paths: A list of file paths to attach to the email.
        """

        # Check user preference for email notifications
        preferences = self.task_manager.get_preferences(self.user_id)
        email_notification_enabled = preferences.get('email_notification', 'True') == 'True'
        if not email_notification_enabled:
            # Log and return if email notifications are disabled
            logging.info("Email notification is disabled in user preferences.")
            return

        if not recipient_email or not subject or not message_body:
            # Ensure that all required parameters are provided
            logging.error("Recipient email or subject or message body cannot be empty.")
            return

        # Connect to the SMTP server
        server, username = self.connect_smtp()

        try:
            # Create a message object
            msg = MIMEMultipart()
            msg['From'] = username
            msg['To'] = recipient_email
            msg['Subject'] = subject  # No need to encode as bytes

            # Attach the HTML message to the email
            # Specify UTF-8 encoding for the message body
            msg.attach(MIMEText(message_body, 'html', 'utf-8'))

            # Attach the files if attachment_paths is not empty
            if attachment_paths:
                for attachment_path in attachment_paths:
                    if os.path.isfile(attachment_path):
                        # Use 'with' statement to ensure the file is closed properly
                        with open(attachment_path, 'rb') as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f"attachment; filename= {attachment_path}")
                        msg.attach(part)

            # Send the email
            server.sendmail(username, recipient_email, msg.as_string())
            logging.info("E-mail sent successfully!")
        except smtplib.SMTPException as e:
            # Log SMTP exceptions
            logging.error(f"Error sending email: {str(e)}")
        except Exception as e:
            # Log other exceptions
            logging.error(f"An error occurred: {str(e)}")
        finally:
            # Close the SMTP connection
            server.quit()
