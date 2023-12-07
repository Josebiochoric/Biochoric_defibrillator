import subprocess
import sys

# Specify the serial port and the file you want to execute
serial_port = "/dev/tty.usbmodem14201"  # Replace with your serial port
file_to_run = "path/to/your_script.py"  # Replace with your script's path

# Run the pyboard.py script with subprocess
subprocess.run([sys.executable, "path/to/pyboard.py", "--device", serial_port, "-f", file_to_run])