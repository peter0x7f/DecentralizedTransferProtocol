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

def get_or_create_secret(file_path, length):
    """Get the secret from file or create it if it does not exist."""
    try:
        # Check if the file already exists
        if os.path.exists(file_path):
            # Read the secret from file
            with open(file_path, 'rb') as file:
                secret = file.read()
            if len(secret) == length:
                return secret
            else:
                print("Secret in file does not match the expected length.")
        # If file does not exist or secret is incorrect, generate a new one
        secret = secrets.token_bytes(length)
        with open(file_path, 'wb') as file:
            file.write(secret)
        return secret
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# File paths for the key and IV
key_path = 'encryption_key.bin'
iv_path = 'encryption_iv.bin'

# Generate or retrieve the key and IV
KEY = get_or_create_secret(key_path, 16)  # AES key should be 16 bytes (128-bit), 24 bytes (192-bit), or 32 bytes (256-bit)
IV = get_or_create_secret(iv_path, 16)    # IV should typically be 16 bytes for AES

def encrypt_addr(data):
    """Encrypt data using AES (CBC mode) with PKCS7 padding."""
    if isinstance(data, str):
        data = data.encode()  # Converts string to bytes if necessary

    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    padded_data = pad(data, AES.block_size, style='pkcs7')
    encrypted_data = cipher.encrypt(padded_data)
    return encrypted_data

def encrypt_data(data):
    # Dummy encryption for demonstration
    return data  # Replace with actual encryption in production

def save_to_whitelist(addr_key):
    addr_key_str = str(f"{addr_key[0]}")
    print(f"Saving to whitelist: {addr_key_str}")  # Debug print
    with open('data/whitelisted_ips.txt', 'a') as f:
        f.write(addr_key_str + '\n')

def is_whitelisted(addr_key):
    """Check if the given address key is in the whitelist by reading a text file."""
    addr_key_str = str(f"{addr_key[0]}") # Convert addr_key to string if it's not already
    print(f"Checking if whitelisted: {addr_key_str}")  # Debug print as string
    try:
        with open('data/whitelisted_ips.txt', 'r') as f:  # Open file in read mode, text mode
            for line in f:
                print(line.strip())
                if addr_key_str == line.strip():  # Compare against stripped line
                    print("Found whitelisted IP")
                    return True
        print("IP not found in whitelist")
        return False
    except FileNotFoundError:
        print("Whitelist file not found.")
        return False

    

def handle_connections(port):
    """Handles incoming connections and processes data."""
    user_approved = {}  # Dictionary to keep track of user approvals

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('localhost', port))
        s.listen()
        print(f"Listening on localhost:{port}")

        while True:
            conn, addr = s.accept()
            # Convert addr tuple to a string that represents the client address
            addr_key = encrypt_data(addr)  # Now passing a string
            print(f"Connected by {addr}, Processed address key: {addr_key}")

            try:
                data = conn.recv(1024).decode()
                print(f"Data received: {data}")

                if 'store_data_request' in data:
                    if is_whitelisted(addr_key):
                        conn.sendall(b'1')
                        user_approved[addr_key] = True
                        print("Address is already whitelisted. Auto-approved.")
                    else:
                        print("Received store data request.")
                        open_new_terminal()
                        if check_user_confirmation():
                            conn.sendall(b'1') #send ricardian contract
                            user_approved[addr_key] = True
                            save_to_whitelist(addr_key)
                            print(encrypt_addr(addr[0]).decode('utf-8', "replace"))
                            save_to_whitelist(encrypt_addr(addr[0]).decode('utf-8', 'replace'))#would save to bin file without decode
                            print("User confirmed, sent '1' to the server and whitelisted.")
                        else:
                            conn.sendall(b'0')
                            user_approved[addr_key] = False
                            print("User did not confirm.")
                elif 'sensitive_information:' in data and user_approved.get(addr_key, True):
                    field_name, sensitive_data = data.split(':', 1)
                    print(f"Received {field_name}: {sensitive_data}")
                    save_to_file(field_name, sensitive_data)
                #make field for images which encodes ricardian contract in image as well as in tos, so companies can search images on the web which contain metadata to see if anyone has broken said ricardian contract, make unique signature for each user.
                elif data == 'retrieve_sensitive_data' and user_approved.get(addr_key, True):
                    print("Received request to retrieve sensitive data.") 
                    # Check if user approved
                    open_new_terminal()
                    if check_user_confirmation():
                        send_sensitive_data(conn)
                    else:
                        conn.sendall(b'User denied access.')
                else:
                    print("Failed to parse data correctly.")

            except Exception as e:
                print(f"Error during connection handling: {e}")
                conn.close()


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
