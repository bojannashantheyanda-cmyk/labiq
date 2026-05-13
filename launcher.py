import uvicorn
import webbrowser
import threading
import time
import os
import sys
import json
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

# Set base path for finding app files
if getattr(sys, 'frozen', False):
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

# Set working directory so uvicorn can find main.py
os.chdir(BASE_PATH)

# Load .env if it exists (for local dev)
env_path = os.path.join(BASE_PATH, '.env')
if os.path.exists(env_path):
    from dotenv import load_dotenv
    load_dotenv(env_path)

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".labiq_config.json")

def get_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def get_db_path():
    return get_config().get("db_path", None)

def get_api_key():
    return get_config().get("anthropic_api_key", None)

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
        return os.path.join(folder, "labiq.db")
    return os.path.join(BASE_PATH, "labiq.db")

def ask_api_key():
    root = tk.Tk()
    root.withdraw()
    key = simpledialog.askstring(
        "LabIQ — API Key Required",
        "Enter your Anthropic API Key to enable the AI Assistant:\n(starts with sk-ant-api03-...)\n\nThis is saved locally and never shared.",
        show='*'
    )
    root.destroy()
    return key

def open_browser():
    time.sleep(3)
    webbrowser.open("http://127.0.0.1:8000/login")

if __name__ == "__main__":
    config = get_config()

    # Get or ask for DB path
    db_path = config.get("db_path")
    if not db_path:
        db_path = choose_folder()
        config["db_path"] = db_path
        save_config(config)

    # Get or ask for API key
    api_key = config.get("anthropic_api_key") or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        api_key = ask_api_key()
        if api_key:
            config["anthropic_api_key"] = api_key
            save_config(config)

    os.environ["LABIQ_DB_PATH"] = db_path
    if api_key:
        os.environ["ANTHROPIC_API_KEY"] = api_key

    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("main:app", host="127.0.0.1", port=8000, log_config=None)
