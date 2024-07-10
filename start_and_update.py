import requests
import hashlib
import socket
import serial
import time
from pyboard import Pyboard, PyboardError
import pyboard
import subprocess

def is_connected(hostname="www.google.com"):
    """ Check if there is an internet connection. """
    try:
        host = socket.gethostbyname(hostname)
        s = socket.create_connection((host, 80), 2)
        s.close()
        return True
    except:
        pass
    return False

def get_file_sha(url):
    """ Get the SHA-1 hash of the file at the given URL. """
    response = requests.get(url)
    return hashlib.sha1(response.content).hexdigest() if response.status_code == 200 else None

def download_file(url, filename):
    """ Download the file from the given URL to the specified filename. """
    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, 'wb') as file:
            file.write(response.content)
        print(f"Updated {filename}")
        return True
    else:
        print(f"Failed to download {filename}")
        return False

def load_file_to_pico(filename, port=None):
    """ Upload the file to the Pico using pyboard.py. """
    try:
        board = Pyboard(port)  # Assuming /dev/ttyACM0 is the Pico port
        board.enter_raw_repl()
        with open(filename, 'rb') as file:
            script = file.read()
        board.exec(script)
        board.exit_raw_repl()
        board.close()
        print(f'Successfully uploaded {filename} to the Pico')
    except PyboardError as e:
        print(f'Failed to upload {filename} to the Pico: {e}')
        return False
    return True

def update_file(file_url, local_path, serial_port=None):
    """ Update the local file and load to Pico if needed. """
    try:
        with open(local_path, 'rb') as file:
            local_file_sha = hashlib.sha1(file.read()).hexdigest()
    except FileNotFoundError:
        local_file_sha = None

    github_file_sha = get_file_sha(file_url)

    if github_file_sha != local_file_sha:
        if download_file(file_url, local_path):
            if serial_port:
                load_file_to_pico(local_path, serial_port)
    else:
        print(f"No update needed for {local_path}")

def run_script_as_main(script_path):
    """ Execute the given script as a separate process. """
    try:
        subprocess.run(["python3", script_path], check=True)
        print(f"Successfully ran {script_path}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to run {script_path}: {e}")

def main():
    if not is_connected():
        print("No internet connection. Skipping updates.")
    else:
        gui_url = "https://raw.githubusercontent.com/Josebiochoric/Biochoric_defibrillator/main/GUI.py"
        defib_url = "https://raw.githubusercontent.com/Josebiochoric/Biochoric_defibrillator/main/defibrillator.py"

        # Paths to the local copies of the files
        #gui_path = "/home/biochoric/GUI.py"
        #defib_path = "/home/biochoric/main.py"

        gui_path = "GUI.py"
        defib_path = "defibrillator.py"

        # Update GUI.py
        update_file(gui_url, gui_path)

        # Update defibrillator.py and load to Pico
        update_file(defib_url, defib_path, serial_port='COM9')

    # Always load defibrillator.py to Pico
    print("Restarting backend...")
    load_file_to_pico( "defibrillator.py",'COM9')

    # Run GUI.py as a separate process
    run_script_as_main("GUI.py")

if __name__ == "__main__":
    main()
