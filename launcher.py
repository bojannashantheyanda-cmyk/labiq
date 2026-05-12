import uvicorn
import webbrowser
import threading
import time
import os
import sys
import json
import tkinter as tk
from tkinter import filedialog, messagebox

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".labiq_config.json")

def get_db_path():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            config = json.load(f)
            return config.get("db_path", "./labiq.db")
    return None

def choose_folder():
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(
        "LabIQ — First Launch",
        "Welcome to LabIQ!\n\nPlease select your Google Drive folder where LabIQ data will be stored.\n\nAll lab members should point to the same shared folder."
    )
    folder = filedialog.askdirectory(title="Select your LabIQ Google Drive folder")
    root.destroy()
    if folder:
        db_path = os.path.join(folder, "labiq.db")
        with open(CONFIG_FILE, "w") as f:
            json.dump({"db_path": db_path}, f)
        return db_path
    return "./labiq.db"

def open_browser():
    time.sleep(2)
    webbrowser.open("http://127.0.0.1:8000/login")

if __name__ == "__main__":
    db_path = get_db_path()
    if not db_path:
        db_path = choose_folder()
    os.environ["LABIQ_DB_PATH"] = db_path
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("main:app", host="127.0.0.1", port=8000, log_config=None)