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
import json
from datetime import datetime


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
    """Save the whitelisted IP as a JSON entry."""
    # Get a string representation (if addr_key is a tuple, use its first element)
    addr_key_str = str(addr_key[0]) if isinstance(addr_key, tuple) else str(addr_key)
    print(f"Saving to whitelist: {addr_key_str}")
    
    whitelist_file = 'data/whitelisted_ips.json'
    whitelist = {"whitelisted_ips": []}
    
    # Load existing whitelist if available
    if os.path.exists(whitelist_file):
        try:
            with open(whitelist_file, 'r') as f:
                whitelist = json.load(f)
        except json.JSONDecodeError:
            print("JSON decode error, starting a new whitelist.")
    
    # Append the new whitelist entry with a timestamp
    entry = {"ip": addr_key_str, "approved_on": datetime.utcnow().isoformat()}
    whitelist["whitelisted_ips"].append(entry)
    
    # Save back to file
    with open(whitelist_file, 'w') as f:
        json.dump(whitelist, f, indent=4)
        

def is_whitelisted(addr_key):
    """Check if the given address key is whitelisted in the JSON file."""
    addr_key_str = str(addr_key[0]) if isinstance(addr_key, tuple) else str(addr_key)
    print(f"Checking if whitelisted: {addr_key_str}")
    
    whitelist_file = 'data/whitelisted_ips.json'
    try:
        with open(whitelist_file, 'r') as f:
            whitelist = json.load(f)
        for entry in whitelist.get("whitelisted_ips", []):
            print(f"Found entry: {entry['ip']}")
            if entry["ip"] == addr_key_str:
                print("Found whitelisted IP")
                return True
        print("IP not found in whitelist")
        return False
    except FileNotFoundError:
        print("Whitelist file not found.")
        return False


def handle_connections(port):
    """Handles incoming connections and processes JSON messages."""
    user_approved = {}  # Tracks user approval status by address key

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('localhost', port))
        s.listen()
        print(f"Listening on localhost:{port}")

        while True:
            conn, addr = s.accept()
            # Process addr into a key (using your encryption/dummy method)
            addr_key = encrypt_data(addr)
            print(f"Connected by {addr}, Processed address key: {addr_key}")

            try:
                data = conn.recv(4096).decode('utf-8')
                print(f"Data received: {data}")
                message = json.loads(data)
                message_type = message.get("type")
                payload = message.get("payload", {})

                if message_type == "STORE_REQUEST":
                    if is_whitelisted(addr_key):
                        response = {
                            "type": "SUCCESS_RESPONSE",
                            "meta": {"timestamp": datetime.utcnow().isoformat()},
                            "payload": {"approval": True, "message": "Already whitelisted."}
                        }
                        conn.sendall(json.dumps(response).encode('utf-8'))
                        user_approved[addr_key] = True
                        print("Address is already whitelisted. Auto-approved.")
                    else:
                        print("Received STORE_REQUEST.")
                        open_new_terminal()
                        if check_user_confirmation():
                            response = {
                                "type": "STORE_APPROVE",
                                "meta": {"timestamp": datetime.utcnow().isoformat()},
                                "payload": {"approval": True}
                            }
                            conn.sendall(json.dumps(response).encode('utf-8'))
                            user_approved[addr_key] = True
                            save_to_whitelist(addr_key)
                            print("User confirmed, sent approval and whitelisted.")
                        else:
                            response = {
                                "type": "FAIL_RESPONSE",
                                "meta": {"timestamp": datetime.utcnow().isoformat()},
                                "payload": {"approval": False, "message": "User did not confirm."}
                            }
                            conn.sendall(json.dumps(response).encode('utf-8'))
                            user_approved[addr_key] = False
                            print("User did not confirm.")
                elif message_type == "WRITE_VALUE" and user_approved.get(addr_key, False):
                    # Expecting payload with data as a two-element list: [data_key, data_value]
                    data_field = payload.get("data")
                    if data_field and isinstance(data_field, list) and len(data_field) == 2:
                        field_name, sensitive_data = data_field
                        print(f"Received WRITE_VALUE for {field_name}: {sensitive_data}")
                        save_to_file(field_name, sensitive_data)
                        response = {
                            "type": "SUCCESS_RESPONSE",
                            "meta": {"timestamp": datetime.utcnow().isoformat()},
                            "payload": {"message": "Data written successfully."}
                        }
                        conn.sendall(json.dumps(response).encode('utf-8'))
                    else:
                        response = {
                            "type": "FAIL_RESPONSE",
                            "meta": {"timestamp": datetime.utcnow().isoformat()},
                            "payload": {"message": "Invalid data format for WRITE_VALUE."}
                        }
                        conn.sendall(json.dumps(response).encode('utf-8'))
                elif message_type == "REQUEST_VALUE" and user_approved.get(addr_key, False):
                    print("Received REQUEST_VALUE.")
                    open_new_terminal()
                    if check_user_confirmation():
                        send_sensitive_data(conn)
                    else:
                        response = {
                            "type": "FAIL_RESPONSE",
                            "meta": {"timestamp": datetime.utcnow().isoformat()},
                            "payload": {"message": "User denied access."}
                        }
                        conn.sendall(json.dumps(response).encode('utf-8'))
                else:
                    print("Failed to parse message correctly or unknown message type.")
            except Exception as e:
                print(f"Error during connection handling: {e}")
                conn.close()


def save_to_file(field_name, data):
    """Save the received data in a structured JSON file."""
    base_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
    target_dir = os.path.join(base_dir, 'data')
    os.makedirs(target_dir, exist_ok=True)
    
    file_path = os.path.join(target_dir, "received_data.json")
    print(f"Attempting to save to: {file_path}")
    
    # Load existing data, if any
    stored_data = {"data": []}
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                stored_data = json.load(f)
        except json.JSONDecodeError:
            print("Error loading existing data; starting new file.")
    
    # Add new entry with a timestamp
    entry = {
        "field": field_name,
        "value": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    stored_data["data"].append(entry)
    
    with open(file_path, "w") as f:
        json.dump(stored_data, f, indent=4)
    print(f"Data successfully saved to file: {file_path}")


def send_sensitive_data(conn):
    """Reads sensitive data from a JSON file and sends it as a JSON message to the client."""
    base_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
    data_file = os.path.join(base_dir, 'data', 'received_data.json')
    print(f"Reading data from: {data_file}")
    
    if os.path.exists(data_file):
        try:
            with open(data_file, 'r') as file:
                data = json.load(file)
            response = {
                "type": "VALUE_RESPONSE",
                "meta": {"timestamp": datetime.utcnow().isoformat()},
                "payload": data  # Can include the full stored data structure
            }
            conn.sendall(json.dumps(response).encode('utf-8'))
            print("Sensitive data sent successfully.")
        except Exception as e:
            print(f"Failed to read/send data: {e}")
            response = {
                "type": "FAIL_RESPONSE",
                "meta": {"timestamp": datetime.utcnow().isoformat()},
                "payload": {"message": "Error sending data"}
            }
            conn.sendall(json.dumps(response).encode('utf-8'))
    else:
        print("No data found to send.")
        response = {
            "type": "FAIL_RESPONSE",
            "meta": {"timestamp": datetime.utcnow().isoformat()},
            "payload": {"message": "No data available"}
        }
        conn.sendall(json.dumps(response).encode('utf-8'))


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

def start_listener(port):
    listener_thread = threading.Thread(target=handle_connections, args=(port,))
    listener_thread.start()

if __name__ == "__main__":
    start_listener(5001)
