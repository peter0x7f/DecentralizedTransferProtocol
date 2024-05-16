import socket
import ssl
from pymongo import MongoClient

# MongoDB setup
client = MongoClient('localhost', 27017)
db = client['secure_app']
whitelisted_ips_collection = db['whitelisted_ips']

# Define your whitelisted IPs
WHITELISTED_IPS = ['127.0.0.1', 'Another Whitelisted IP']

def verify_ip_and_update_db(ip_address):
    if ip_address not in WHITELISTED_IPS:
        print(f"IP {ip_address} is not whitelisted.")
        return False
    # Check if IP exists in the database, if not, create an instance
    if whitelisted_ips_collection.count_documents({"ip": ip_address}) == 0:
        whitelisted_ips_collection.insert_one({"ip": ip_address, "instances": 1})
    else:
        whitelisted_ips_collection.update_one({"ip": ip_address}, {"$inc": {"instances": 1}})
    return True

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
            handle_client_connection(conn)  # You need to define this function
        except Exception as e:
            print(e)
        finally:
            conn.shutdown(socket.SHUT_RDWR)
            conn.close()

# Example usage
# start_secure_server('localhost', 5000, 'server.crt', 'server.key')
