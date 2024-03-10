import socket
import ssl
from pymongo import MongoClient
from Crypto.Cipher import AES
from datetime import datetime
import base64
import subprocess
import sys
import os
import subprocess
import platform

# Define paths and names of the scripts and status file
status_file_path = 'script_status.txt'
firewall_script_windows = 'OpenFirewallPort.ps1'
firewall_script_linux = 'openFirewallPort.sh'
git_install_script_windows = 'InstallGit.ps1'
git_install_script_linux = 'installGit.sh'  # Assuming you have a Linux version for Git installation

# Function to check if a script has been run before
def script_has_been_run(script_name):
    if os.path.exists(status_file_path):
        with open(status_file_path, 'r') as f:
            if script_name in f.read():
                return True
    return False

# Function to mark a script as run
def mark_script_as_run(script_name):
    with open(status_file_path, 'a') as f:
        f.write(f"{script_name}\n")

# Function to run a script
def run_script(script_path):
    try:
        if platform.system().lower() == "windows":
            subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path], check=True)
        else:
            subprocess.run([script_path], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to execute {script_path}: {e}")
        return False

#code startup check. 
# MongoDB setup for both server and client
MONGO_HOST = 'localhost'
MONGO_PORT = 27017
SERVER_DB_NAME = 'secure_app'
CLIENT_DB_NAME = 'client_secure_app'

client = MongoClient(MONGO_HOST, MONGO_PORT)
server_db = client[SERVER_DB_NAME]
client_db = client[CLIENT_DB_NAME]
whitelisted_ips_collection = server_db['whitelisted_ips']
communication_log_collection = client_db['communication_log']

# Whitelisted IPs and their associated AES keys
WHITELISTED_IPS_KEYS = {
    '127.0.0.1': 'ThisIsASecretKey123456789012345',  # Example key
}

# Function to check and update whitelisted IPs in the database
def verify_ip_and_update_db(ip_address):
    if ip_address not in WHITELISTED_IPS_KEYS:
        print(f"IP {ip_address} is not whitelisted.")
        return False
    if whitelisted_ips_collection.count_documents({"ip": ip_address}) == 0:
        whitelisted_ips_collection.insert_one({"ip": ip_address, "instances": 1})
    else:
        whitelisted_ips_collection.update_one({"ip": ip_address}, {"$inc": {"instances": 1}})
    return True

# AES Encryption Function
def encrypt_message(key, message):
    cipher = AES.new(key.encode('utf-8'), AES.MODE_EAX)
    nonce = cipher.nonce
    ciphertext, tag = cipher.encrypt_and_digest(message.encode('utf-8'))
    return base64.b64encode(nonce + tag + ciphertext).decode('utf-8')

# Function to log communication attempts in MongoDB
def log_communication(ip, status):
    communication_log_collection.insert_one({"server_ip": ip, "status": status, "attempt_time": datetime.now()})

# Client-side functionality
def connect_to_secure_server(host, port, server_cert):
    if host not in WHITELISTED_IPS_KEYS:
        print("Server IP is not whitelisted.")
        return
    aes_key = WHITELISTED_IPS_KEYS[host]
    encrypted_message = encrypt_message(aes_key, "Hello, secure server with AES encryption!")

    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=server_cert)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_REQUIRED

    with socket.create_connection((host, port)) as sock:
        with context.wrap_socket(sock, server_hostname=host) as secure_sock:
            try:
                secure_sock.sendall(encrypted_message.encode('utf-8'))
                response = secure_sock.recv(1024)
                print(f"Server response: {response.decode()}")
                log_communication(host, "Success")
            except Exception as e:
                print(f"Failed to communicate with the server: {e}")
                log_communication(host, "Failed")

# Remove conflict with other file.
def start_secure_server(host, port, certificate, key):
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile=certificate, keyfile=key)

    bindsocket = socket.socket()
    bindsocket.bind((host, port))
    bindsocket.listen(5)
    print(f"Secure server listening on {host}:{port}")

    while True:
        newsocket, fromaddr = bindsocket.accept()
        if not verify_ip_and_update_db(fromaddr[0]):
            newsocket.close()
            continue
        conn = context.wrap_socket(newsocket, server_side=True)
        try:
            # Placeholder for handle_client_connection function
            # Implement your communication logic here
            pass
        except Exception as e:
            print(e)
        finally:
            conn.shutdown(socket.SHUT_RDWR)
            conn.close()
def main():
    os_system = platform.system().lower()
    firewall_script = firewall_script_windows if os_system == "windows" else firewall_script_linux
    git_install_script = git_install_script_windows if os_system == "windows" else git_install_script_linux

    # Check and run firewall configuration script
    if not script_has_been_run(firewall_script):
        print(f"Running {firewall_script}...")
        if run_script(firewall_script):
            mark_script_as_run(firewall_script)
    
    # Check and run Git installation script
    if not script_has_been_run(git_install_script):
        print(f"Running {git_install_script}...")
        if run_script(git_install_script):
            mark_script_as_run(git_install_script)

if __name__ == "__main__":
    main()
