import socket
import threading
import subprocess
import platform
import os
import time
import sys
import sqlite3
import uuid
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import secrets

# ---------- Encryption Utilities ----------
def get_or_create_secret(file_path, length):
    """Get the secret from file or create it if it does not exist."""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'rb') as file:
                secret = file.read()
            if len(secret) == length:
                return secret
            else:
                print("Secret in file does not match the expected length.")
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
KEY = get_or_create_secret(key_path, 16)  # 16 bytes for AES-128
IV = get_or_create_secret(iv_path, 16)    # 16 bytes IV

def encrypt_addr(data):
    """Encrypt data using AES (CBC mode) with PKCS7 padding."""
    if isinstance(data, str):
        data = data.encode()
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    padded_data = pad(data, AES.block_size, style='pkcs7')
    encrypted_data = cipher.encrypt(padded_data)
    return encrypted_data

def encrypt_data(data):
    # Dummy encryption for demonstration
    return data  # Replace with actual encryption in production

# ---------- Database & Partition Initialization ----------
def create_and_encrypt_vhd(vhd_path, drive_letter, size_gb, password):
    """
    Create a VHD, mount it, and encrypt it with BitLocker.
    This code is taken from your original client storage example.
    """
    size_mb = size_gb * 1024
    create_vhd_script = f"""
    create vdisk file="{vhd_path}" maximum={size_mb} type=expandable
    select vdisk file="{vhd_path}"
    attach vdisk
    create partition primary
    format fs=ntfs quick
    assign letter={drive_letter}
    """
    script_file = "create_vhd_script.txt"
    with open(script_file, "w") as f:
        f.write(create_vhd_script)
    try:
        subprocess.run(["diskpart", "/s", script_file], check=True)
        print(f"VHD created and mounted as drive {drive_letter}:")
    except subprocess.CalledProcessError as e:
        print("Error during VHD creation:", e)
        return
    finally:
        os.remove(script_file)

    secure_password = f'ConvertTo-SecureString "{password}" -AsPlainText -Force'
    enable_cmd = (
        f"powershell.exe -Command "
        f"$SecureString = {secure_password}; "
        f"Enable-BitLocker -MountPoint {drive_letter}: "
        f"-EncryptionMethod Aes256 "
        f"-PasswordProtector -Password $SecureString"
    )
    try:
        subprocess.run(enable_cmd, check=True, shell=True)
        print(f"BitLocker encryption initiated on drive {drive_letter}:")
    except subprocess.CalledProcessError as e:
        print(f"Error enabling BitLocker on drive {drive_letter}: {e}")

def initialize_database(db_path):
    """
    Initialize (or open) the SQLite database and create the whitelisted_companies table.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS whitelisted_companies (
       id TEXT PRIMARY KEY,
       address_key TEXT UNIQUE,
       timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    return conn

def export_whitelist_to_json(db_conn):
    """
    Exports all records from the whitelisted_companies table to a JSON file.
    """
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM whitelisted_companies;")
    rows = cursor.fetchall()
    col_names = [description[0] for description in cursor.description]
    data = [dict(zip(col_names, row)) for row in rows]
    data_dir = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'data')
    os.makedirs(data_dir, exist_ok=True)
    json_file = os.path.join(data_dir, "whitelisted_companies.json")
    with open(json_file, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Exported whitelist data to {json_file}")

def initialize_storage():
    """
    Checks if the storage partition (and thus the database) exists.
    If not, creates the partition and then initializes the database.
    """
    drive_letter = "Z"
    db_path = os.path.join(f"{drive_letter}:\\", "companies.db")
    if not os.path.exists(db_path):
         # First initialization – create and encrypt VHD partition.
         vhd_path = os.path.join(os.getcwd(), "test.vhd")
         size_gb = 1  # VHD size
         password = "YourSecurePassword123"  # Replace with a strong password
         create_and_encrypt_vhd(vhd_path, drive_letter, size_gb, password)
    conn = initialize_database(db_path)
    return conn

# ---------- Whitelist Functions using the Database ----------
def save_to_whitelist(addr_key, db_conn):
    """
    Instead of saving to a text file, insert the whitelisted address into the database
    and export the updated table to a JSON file.
    """
    addr_key_str = str(addr_key[0])
    print(f"Saving to whitelist in DB: {addr_key_str}")
    cursor = db_conn.cursor()
    record_id = str(uuid.uuid4())
    try:
        cursor.execute(
            "INSERT INTO whitelisted_companies (id, address_key) VALUES (?, ?);",
            (record_id, addr_key_str)
        )
        db_conn.commit()
        print(f"Inserted record with id {record_id} into whitelisted_companies table.")
    except sqlite3.IntegrityError:
        print("Address already whitelisted in DB.")
    export_whitelist_to_json(db_conn)

def is_whitelisted(addr_key, db_conn):
    """
    Check if the given address key exists in the whitelisted_companies table.
    """
    addr_key_str = str(addr_key[0])
    print(f"Checking whitelist in DB for: {addr_key_str}")
    cursor = db_conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM whitelisted_companies WHERE address_key = ?;",
        (addr_key_str,)
    )
    result = cursor.fetchone()
    return result[0] > 0

# ---------- Existing Functions Remain Unchanged ----------
def save_to_file(field_name, data):
    """Saves the received data and field name to a text file in the specified directory."""
    base_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
    target_dir = os.path.join(base_dir, 'data')
    os.makedirs(target_dir, exist_ok=True)
    file_path = os.path.join(target_dir, "received_data.txt")
    print(f"Attempting to save to: {file_path}")
    try:
        with open(file_path, "a") as file:
            file.write(f"{field_name}: {data}\n")
        print(f"Data successfully saved to file: {file_path}")
    except Exception as e:
        print("Failed to write to file due to error:", e)

def open_new_terminal():
    base_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
    script_path = os.path.join(base_dir, 'user_input_handler.py')
    print(f"Script path resolved to: {script_path}")
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
    """Reads sensitive data from a file and sends it to the client."""
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

# ---------- Modified Connection Handling Using the DB ----------
def handle_connections(port, db_conn):
    """Handles incoming connections and processes data using the database for whitelist storage."""
    user_approved = {}
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('localhost', port))
        s.listen()
        print(f"Listening on localhost:{port}")
        while True:
            conn, addr = s.accept()
            addr_key = encrypt_data(addr)
            print(f"Connected by {addr}, Processed address key: {addr_key}")
            try:
                data = conn.recv(1024).decode()
                print(f"Data received: {data}")
                if 'store_data_request' in data:
                    if is_whitelisted(addr_key, db_conn):
                        conn.sendall(b'1')
                        user_approved[addr_key] = True
                        print("Address is already whitelisted. Auto-approved.")
                    else:
                        print("Received store data request.")
                        open_new_terminal()
                        if check_user_confirmation():
                            conn.sendall(b'1')  # Send Ricardian contract
                            user_approved[addr_key] = True
                            save_to_whitelist(addr_key, db_conn)
                            print("User confirmed, sent '1' to the client and whitelisted.")
                        else:
                            conn.sendall(b'0')
                            user_approved[addr_key] = False
                            print("User did not confirm.")
                elif 'sensitive_information:' in data and user_approved.get(addr_key, True):
                    field_name, sensitive_data = data.split(':', 1)
                    print(f"Received {field_name}: {sensitive_data}")
                    save_to_file(field_name, sensitive_data)
                elif data == 'retrieve_sensitive_data' and user_approved.get(addr_key, True):
                    print("Received request to retrieve sensitive data.")
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

def start_listener(port, db_conn):
    listener_thread = threading.Thread(target=handle_connections, args=(port, db_conn))
    listener_thread.start()

# ---------- Main Entry Point ----------
if __name__ == "__main__":
    # Initialize storage; if the DB (and partition) doesn’t exist, it will be created.
    db_conn = initialize_storage()
    start_listener(5001, db_conn)
