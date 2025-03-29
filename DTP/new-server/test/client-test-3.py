import datetime
import json
import socket
import sqlite3
import time


class DTPClient:
    def __init__(self, database_path):
        self.database = Database(database_path)  # Initialize the database object
        self.database.connect()  # Connect to the database
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # fix
    def handle_connection(self, conn, addr):
        """Listen for messages and process them."""
        try:
            buffer = ""
            while True:
                data = conn.recv(1024).decode("utf-8")
                if not data:
                    print(f"Disconnected from {addr}")
                    break
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        self.process_message(line, conn, addr)
        except Exception as e:
            print(f" Error in connection: {e}")
        finally:
            conn.close()

    # fix
    def connect_to_server(self, server_host, server_port):
        """Keep trying to connect and handle messages."""
        while True:
            try:
                print(f"🌐 Attempting to connect to {server_host}:{server_port}...")
                self.socket.connect((server_host, server_port))
                print(f" Connected to server at {server_host}:{server_port}")
                self.handle_connection(self.socket, (server_host, server_port))
            except Exception as e:
                print(f"Connection error: {e}. Retrying in 5 seconds...")
                time.sleep(5)
            finally:
                self.socket.close()
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Process Server Requests

    def process_message(self, msg, conn, addr):
        try:
            message = json.loads(msg)
            msg_type = message.get("type")
            payload = message.get("payload", {})

            if msg_type == "STORE_REQUEST":
                self.database.insert_log(f"{type} from {server_ip}:{server_port}")
                server_uuid = payload.get("server_uuid")
                server_ip = payload.get("server_ip")
                server_port = payload.get("server_port")
                self.process_store_request(server_uuid, server_ip, server_port, conn)

            elif msg_type == "WRITE_VALUE":
                self.database.insert_log(f"{type} from {server_ip}:{server_port}")
                server_uuid = payload.get("server_uuid")
                server_ip = payload.get("server_ip")
                server_port = payload.get("server_port")
                key = payload.get("data", {}).get("key")
                value = payload.get("data", {}).get("value")
                self.process_write_value(
                    server_uuid, server_ip, server_port, key, value, conn
                )

            elif msg_type == "REQUEST_VALUE":
                self.database.insert_log(f"{type} from {server_ip}:{server_port}")
                server_uuid = payload.get("server_uuid")
                server_ip = payload.get("server_ip")
                server_port = payload.get("server_port")
                key = payload.get("data", {}).get("key")

                self.process_request_value(
                    server_uuid, server_ip, server_port, key, conn
                )

            elif msg_type == "SUCCESS_RESPONSE":
                server_uuid = payload.get("server_uuid")
                server_ip = payload.get("server_ip")
                server_port = payload.get("server_port")
                type = payload.get("type")
                self.database.insert_log(f"{type} from {server_ip}:{server_port}")

            elif msg_type == "FAIL_RESPONSE":
                server_uuid = payload.get("server_uuid")
                server_ip = payload.get("server_ip")
                server_port = payload.get("server_port")
                type = payload.get("type")
                self.database.insert_log(f"{type} from {server_ip}:{server_port}")

        except Exception as e:
            print(f"Error processing message: {e}")

    def process_store_request(self, server_uuid, server_ip, server_port, conn):
        try:
            # Add server to whitelist
            self.database.add_whitelisted_server(server_uuid, server_ip)
            client_uuid = self.database.get_client_uuid()
            response = {
                "type": "STORE_APPROVE",
                "meta": {"timestamp": datetime.utcnow().isoformat()},
                "payload": {
                    "client_uuid": client_uuid,  # If you meant client uuid, replace accordingly
                    "message": "Store approved",
                },
            }

            # Send JSON response
            conn.sendall((json.dumps(response) + "\n").encode("utf-8"))
            print(f"STORE_APPROVE sent to {server_ip}:{server_port}")

        except Exception as e:
            print(f"Error processing STORE_REQUEST: {e}")

    def process_write_value(
        self, server_uuid, server_ip, server_port, key, value, conn
    ):
        try:
            self.database.store_data(server_uuid, key, value)
            response = {
                "type": "SUCCESS_RESPONSE",
                "meta": {"timestamp": datetime.utcnow().isoformat()},
                "payload": {"message": "Data stored successfully"},
            }
            conn.sendall((json.dumps(response) + "\n").encode("utf-8"))
            print(f"SUCCESS_RESPONSE sent to {server_ip}:{server_port}")

        except Exception as e:
            print(f" Error processing WRITE_VALUE: {e}")

    def process_request_value(self, server_uuid, server_ip, server_port, key, conn):
        try:
            value = self.database.get_data(server_uuid, key)
            response = {
                "type": "VALUE_RESPONSE",
                "meta": {"timestamp": datetime.utcnow().isoformat()},
                "payload": {"data_value": value},
            }
            conn.sendall((json.dumps(response) + "\n").encode("utf-8"))
            print(f"VALUE_RESPONSE sent to {server_ip}:{server_port}")

        except Exception as e:
            print(f" Error processing REQUEST_VALUE: {e}")


class Database:
    CLIENT_UUID = "client_uuid"
    CLIENT_IP = "client_ip"
    CLIENT_PORT = "client_port"

    PATH = "database.db"

    def __init__(self, path):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.init_client_info(self.CLIENT_UUID, self.CLIENT_IP, self.CLIENT_PORT)

    def create_tables(self):
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS WhitelistedServers ("
             "    server_uuid TEXT PRIMARY KEY,
            "    server_ip TEXT,
             "    approved_on TEXT
             "  )"""
        )
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS Data (""
            "    server_uuid TEXT,
            "    key TEXT,
            "    value TEXT,
            "    timestamp TEXT,
            "    PRIMARY KEY (server_uuid, key)
            "  )"""
        )

        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS clientInfo ("""
            "    client_uuid TEXT PRIMARY KEY,"
            "    client_ip TEXT,"
            "    client_port TEXT"
            "  )"
        )

        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS Logs ("""
            "    timestamp TEXT,"
            "    message TEXT"
            "  )"
        )
        self.conn.commit()

    def insert_log(self, message):
        self.cursor.execute(
            "INSERT INTO Logs (timestamp, message) VALUES (?, ?)",
            (datetime.utcnow().isoformat(), message),
        )
        self.conn.commit()

    def init_client_info(self, client_uuid, client_ip, client_port):
        self.cursor.execute(
            "INSERT OR IGNORE INTO clientInfo (client_uuid, client_ip, client_port) VALUES (?, ?, ?)",
            (client_uuid, client_ip, client_port),
        )
        self.conn.commit()

    def get_client_uuid(self):
        self.cursor.execute("SELECT client_uuid FROM clientInfo")
        row = self.cursor.fetchone()
        return row[0] if row else None

    def is_whitelisted(self, server_uuid):
        self.cursor.execute(
            "SELECT 1 FROM WhitelistedServers WHERE server_uuid = ?", (server_uuid,)
        )
        return self.cursor.fetchone() is not None

    def add_whitelisted_server(self, server_uuid, server_ip):
        self.cursor.execute(
            "INSERT OR IGNORE INTO WhitelistedServers (server_uuid, server_ip, approved_on) VALUES (?, ?, ?)",
            (server_uuid, server_ip, datetime.utcnow().isoformat()),
        )
        self.conn.commit()

    def store_data(self, server_uuid, key, value):
        self.cursor.execute(
            "INSERT OR REPLACE INTO Data (server_uuid, key, value, timestamp) VALUES (?, ?, ?, ?)",
            (server_uuid, key, value, datetime.utcnow().isoformat()),
        )
        self.conn.commit()
        print(f"🔑 Stored data for server {server_uuid}: {key} = {value}")

    def get_data(self, server_uuid, key):
        self.cursor.execute(
            "SELECT value FROM Data WHERE server_uuid = ? AND key = ?",
            (server_uuid, key),
        )
        row = self.cursor.fetchone()
        return row[0] if row else None

    def delete_whitelisted_server(self, server_uuid):
        self.cursor.execute(
            "DELETE FROM WhitelistedServers WHERE server_uuid = ?", (server_uuid,)
        )
        self.conn.commit()

    def delete_data(self, server_uuid, key):
        self.cursor.execute(
            "DELETE FROM Data WHERE server_uuid = ? AND key = ?", (server_uuid, key)
        )
        self.conn.commit()
