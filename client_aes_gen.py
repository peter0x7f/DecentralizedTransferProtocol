def connect_to_server(host, port, data):
    key, iv = generate_key_iv()
    cipher = AES.new(key, AES.MODE_CBC, iv)
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        
        # Insecure example of sending key and IV
        s.sendall(key + b',' + iv)  # Do NOT use in production without secure channel
        
        # Encrypt and send data
        bson_data = serialize_data(data)
        padded_data = bson_data + b"\0" * (16 - len(bson_data) % 16)  # Padding
        encrypted_data = cipher.encrypt(padded_data)
        s.sendall(encrypted_data)

        # Handle server response...
