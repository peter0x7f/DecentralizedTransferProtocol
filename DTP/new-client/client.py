from database import Database
import socket
import threading
import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "data", "dtp_client.sqlite"
)


class DTPClient:
    def __init__(self, port=5001, host="localhost"):
        self.host = host
        self.port = port
        self.db = Database(DB_PATH)

    def start(self):
        self.db.init_db()
        thread = threading.Thread(target=self.listen)
        thread.start()

    def listen(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen()
            print(f"Listening on {self.host}:{self.port}")

            while True:
                conn, addr = s.accept()
                thread = threading.Thread(
                    target=self.handle_connection, args=(conn, addr)
                )
                thread.start()

    def handle_connection(self, conn, addr):
        try:
            buffer = ""
            while True:
                data = conn.recv(1024).decode("utf-8")
                if not data:
                    break
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.process_message(line, conn, addr)
        except Exception as e:
            print(f"Connection error: {e}")
        finally:
            conn.close()

    def process_message(self, msg, conn, addr):
        try:
            message = json.loads(msg)
            msg_type = message.get("type")
            payload = message.get("payload", {})

            server_uuid = payload.get("server_uuid")

            if msg_type == "STORE_REQUEST":
                if self.db.is_whitelisted(server_uuid):
                    self.send_response(
                        conn,
                        "SUCCESS_RESPONSE",
                        {"approval": True, "message": "Already whitelisted."},
                    )
                else:
                    # Auto approve for now (or prompt user)
                    self.db.add_whitelisted_server(server_uuid, addr[0])
                    self.send_response(
                        conn,
                        "STORE_APPROVE",
                        {"approval": True, "server_uuid": server_uuid},
                    )

            elif msg_type == "WRITE_VALUE" and self.db.is_whitelisted(server_uuid):
                key, value = payload.get("data", {}).get("key"), payload.get(
                    "data", {}
                ).get("value")
                self.db.store_data(server_uuid, key, value)
                self.send_response(
                    conn, "SUCCESS_RESPONSE", {"message": f"Data stored for key {key}"}
                )

            elif msg_type == "REQUEST_VALUE" and self.db.is_whitelisted(server_uuid):
                key = payload.get("data_key")
                value = self.db.get_data(server_uuid, key)
                if value:
                    self.send_response(
                        conn, "VALUE_RESPONSE", {"key": key, "value": value}
                    )
                else:
                    self.send_response(
                        conn,
                        "FAIL_RESPONSE",
                        {"message": f"No value found for key {key}"},
                    )

            else:
                self.send_response(
                    conn,
                    "FAIL_RESPONSE",
                    {"message": "Unauthorized or invalid request."},
                )

        except Exception as e:
            print(f"Failed to process message: {e}")

    def send_response(self, conn, msg_type, payload):
        response = {
            "type": msg_type,
            "meta": {"timestamp": datetime.utcnow().isoformat()},
            "payload": payload,
        }
        conn.sendall((json.dumps(response) + "\n").encode("utf-8"))


class Database:
    def __init__(self, path):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def init_db(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS WhitelistedServers (
                                server_uuid TEXT PRIMARY KEY,
                                server_ip TEXT,
                                approved_on TEXT
                              )"""
        )
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS StoredData (
                                server_uuid TEXT,
                                key TEXT,
                                value TEXT,
                                timestamp TEXT,
                                PRIMARY KEY (server_uuid, key)
                              )"""
        )
        self.conn.commit()

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
        print(f"✅ Whitelisted server: {server_uuid}")

    def store_data(self, server_uuid, key, value):
        self.cursor.execute(
            "REPLACE INTO StoredData (server_uuid, key, value, timestamp) VALUES (?, ?, ?, ?)",
            (server_uuid, key, value, datetime.utcnow().isoformat()),
        )
        self.conn.commit()
        print(f"🔑 Stored data for server {server_uuid}: {key} = {value}")

    def get_data(self, server_uuid, key):
        self.cursor.execute(
            "SELECT value FROM StoredData WHERE server_uuid = ? AND key = ?",
            (server_uuid, key),
        )
        row = self.cursor.fetchone()
        return row[0] if row else None


if __name__ == "__main__":
    client = DTPClient(port=5001)
    client.start()
