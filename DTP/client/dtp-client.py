import socket
import threading
import subprocess
import platform
import os
import time
import sys
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import secrets

def generate_random_string(length):
    """Generates a cryptographically strong random string of the specified length."""
    # Each byte has 2 hex digits, so we need length * 2 hex digits
    return secrets.token_hex(length)

def get_random_string_key():
    """Returns a random string of length 16, 24, or 32 bytes."""
    length = secrets.choice([16, 24, 32])  # Randomly choose between 16, 24, or 32 bytes
    return generate_random_string(length)

def get_random_string_IV():
    """Returns a random string of length 16, 24, or 32 bytes."""
    length = secrets.choice([16])  # Randomly choose between 16, 24, or 32 bytes
    return generate_random_string(length)

random_string = get_random_string_key()
random_string_IV = get_random_string_IV()
KEY = f"{random_string}" # Ensure this is 16, 24, or 32 bytes long
IV = f'{random_string_IV}'  # IV must be 16 bytes long

def encrypt_data(data):
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    encrypted_data = cipher.encrypt(pad(data.encode(), AES.block_size))
    return encrypted_data

def decrypt_data(encrypted_data):
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)
    return decrypted_data.decode()
def handle_connections(port):
    """Handles incoming connections and processes data."""
    user_approved = {}  # Dictionary to keep track of user approvals

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', port))
        s.listen()
        print(f"Listening on localhost:{port}")

        while True:
            conn, addr = s.accept()
            addr_key = encrypt_data(f"{addr[0]}:{addr[1]}")  # Create a aes enc key based on client address

            with conn:
                print(f"Connected by {addr}")
                data = conn.recv(1024).decode()
                print(f"Data received: {data}")

                if data == 'store_data_request':
                    print("Received data store request.")
                    open_new_terminal()
                    if check_user_confirmation():
                        conn.sendall(b'1')
                        user_approved[addr_key] = True  # Set approval for this user
                        print("User confirmed, sent '1' to the server.")
                    else:
                        conn.sendall(b'0')
                        print("User did not confirm.")
                        user_approved[addr_key] = False  # Set disapproval for this user

                elif 'sensitive_information:' in data and user_approved.get(addr_key, True):
                    field_name, sensitive_data = data.split(':', 1)
                    print(f"Received {field_name}: {sensitive_data}")
                    save_to_file(field_name, sensitive_data)

                elif data == 'retrieve_sensitive_data' and user_approved.get(addr_key, True):
                    print("Received request to retrieve sensitive data.")
                    if user_approved.get(addr_key, False):  # Check if user approved
                        open_new_terminal()
                        if check_user_confirmation():
                            send_sensitive_data(conn)
                        else:
                            conn.sendall(b'User denied access.')
                    else:
                        print("Access denied: User has not confirmed data storage.")
                        conn.sendall(b'Access denied: User has not confirmed data storage.')

def save_to_file(field_name, data):
    """Saves the received data and field name to a text file in the specified directory."""
    # Get the directory of the currently executing script
    base_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
    # Correctly form the path to the data directory relative to the base_dir
    target_dir = os.path.join(base_dir, 'data')  # Ensuring 'data' directory is within the script's directory
    os.makedirs(target_dir, exist_ok=True)  # Ensure the directory exists

    # Form the full path to the file within the target directory
    file_path = os.path.join(target_dir, "received_data.txt")

    # Debugging output to check the path
    print(f"Attempting to save to: {file_path}")

    try:
        # Write data to the file
        with open(file_path, "a") as file:
            file.write(f"{field_name}: {data}\n")
        print(f"Data successfully saved to file: {file_path}")
    except Exception as e:
        print("Failed to write to file due to error")

def open_new_terminal():
    base_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
    script_path = os.path.join(base_dir, 'user_input_handler.py')
    print(f"Script path resolved to: {script_path}")  # Debug to confirm path
    current_os = platform.system()

    try:
        if current_os == 'Windows':
            escaped_script_path = script_path.replace('\\', '\\\\')
            command = f'start cmd /k python "{escaped_script_path}"'
            subprocess.run(command, shell=True)
        elif current_os == 'Linux':
            subprocess.run(['gnome-terminal', '--', 'python3', script_path], check=True)
        elif current_os == 'Darwin':
            subprocess.run(['osascript', '-e', f'tell app "Terminal" to do script "python3 \'{script_path}\'"'])
    except Exception as e:
        print(f"Error opening terminal: {e}")

def check_user_confirmation():
    confirmation_file = "user_confirmation.txt"
    wait_time = 0.5
    timeout = 30

    for _ in range(int(timeout / wait_time)):
        if os.path.exists(confirmation_file):
            with open(confirmation_file, 'r') as file:
                response = file.read().strip().lower()
            os.remove(confirmation_file)
            return response == 'yes'
        time.sleep(wait_time)

    print("Timeout waiting for user confirmation.")
    return False

def send_sensitive_data(conn):
    """Reads sensitive data from a file and sends it to the server."""
    base_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
    data_file = os.path.join(base_dir, 'data', 'received_data.txt')
    print(data_file)
    try:
        if os.path.exists(data_file):
            with open(data_file, 'r') as file:
                data = file.read()
                if data:
                    conn.sendall(data.encode())
                    print("Sensitive data sent successfully.")
                else:
                    print("File is empty.")
                    conn.sendall(b'No data available')
        else:
            print("No data found to send.")
            conn.sendall(b'No data available')
    except Exception as e:
        print(f"Failed to read/send data: {e}")
        conn.sendall(b'Error sending data')

def start_listener(port):
    listener_thread = threading.Thread(target=handle_connections, args=(port,))
    listener_thread.start()

if __name__ == "__main__":
    start_listener(5001)
