import os
import random
import pyautogui

def random_mouse():
    for _ in range(3):
        x = random.randint(0, 800)
        y = random.randint(0, 600)
        pyautogui.moveTo(x, y, duration=0.5)

def simulate_user_action(action):
    print(f"[Simulated] Action: {action}")
    
    if action == "open_browser":
        print("[Fake] Opened browser")
    elif action == "visit_website":
        print("[Fake] Visited website")
    elif action == "download_file":
        os.makedirs("data/fake_files", exist_ok=True)
        with open("data/fake_files/downloaded.exe", "w") as f:
            f.write("Fake malware content")
    elif action in ("open_editor", "write_notes"):
        os.makedirs("honeypot/data/fake_files", exist_ok=True)
        with open("honeypot/data/fake_files/note.txt", "a") as f:
            f.write("User wrote something.\n")
    elif action == "save_file":
        print("[Fake] Saved file")
    elif action == "check_email":
        print("[Fake] Checked email")
    elif action == "open_attachment":
        print("[Fake] Opened attachment")
    elif action == "move_mouse":
        random_mouse()