import socket
from Crypto.Cipher import AES

# Assuming this function receives the client's key and iv securely
def handle_client_connection(client_socket):
    # For illustration, not secure!
    client_key, client_iv = client_socket.recv(1024).split(b',')  # Insecure!
    cipher = AES.new(client_key, AES.MODE_CBC, client_iv)
