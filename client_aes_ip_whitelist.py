import socket
import ssl
from pymongo import MongoClient
from Crypto.Cipher import AES
from datetime import datetime
import json
import base64

# MongoDB client setup
client = MongoClient('localhost', 27017)
db = client['client_secure_app']
communication_log_collection = db['communication_log']

# Whitelisted IPs and their associated AES keys (for demonstration purposes, keys are shown here, but in a real application, ensure secure key management)
WHITELISTED_IPS_KEYS = {
    '127.0.0.1': 'ThisIsASecretKey123456789012345',  # Example key, ensure 32 bytes for AES-256
}

def log_communication(ip, status):
    """Logs communication attempts to the local MongoDB database."""
    communication_log_collection.insert_one({"server_ip": ip, "status": status, "attempt_time": datetime.now()})

def encrypt_message(key, message):
    """Encrypts a message using AES."""
    cipher = AES.new(key.encode('utf-8'), AES.MODE_EAX)
    nonce = cipher.nonce
    ciphertext, tag = cipher.encrypt_and_digest(message.encode('utf-8'))
    return base64.b64encode(nonce + tag + ciphertext).decode('utf-8')

def connect_to_secure_server(host, port, server_cert):
    """Connects to a secure server with SSL and sends an encrypted message."""
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

if __name__ == "__main__":
    SERVER_HOST = '127.0.0.1'  # Example server host
    SERVER_PORT = 5000  # Example server port
    SERVER_CERT = 'path/to/the/server_cert.pem'  # Path to the server's certificate

    connect_to_secure_server(SERVER_HOST, SERVER_PORT, SERVER_CERT)
