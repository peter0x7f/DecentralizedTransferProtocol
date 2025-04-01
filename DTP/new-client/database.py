from datetime import datetime
import os
import sqlite3


class Database:
    """Replace with ENV vars for production"""

    CLIENT_UUID = "86394b22-fd0e-4f59-9c1b-bf2e4e0b8a1d"
    CLIENT_IP = "client_ip"
    CLIENT_PORT = "client_port"

    DEFAULT_PATH = "database.db"

    def __init__(self, path=DEFAULT_PATH):
        self.path = path
        self.conn = None
        self.cursor = None

    def connect(self):
        (
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            if os.path.dirname(self.path)
            else None
        )
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.init_client_info(self.CLIENT_UUID, self.CLIENT_IP, self.CLIENT_PORT)

    def close(self):
        if self.conn:
            self.conn.close()

    def create_tables(self):
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS WhitelistedServers (
                 server_uuid TEXT PRIMARY KEY,
                 server_ip TEXT,
                 approved_on TEXT
              )"""
        )
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS Data (
                 server_uuid TEXT,
                 key TEXT,
                 value TEXT,
                 timestamp TEXT,
                 PRIMARY KEY (server_uuid, key)
              )"""
        )
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS clientInfo (
                 client_uuid TEXT PRIMARY KEY,
                 client_ip TEXT,
                 client_port TEXT
              )"""
        )
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS Logs (
                 timestamp TEXT,
                 message TEXT
              )"""
        )
        self.conn.commit()

    def insert_log(self, message):
        self.cursor.execute(
            "INSERT INTO Logs (timestamp, message) VALUES (?, ?)",
            (datetime.now().isoformat(), message),
        )
        self.conn.commit()

    def print_logs(self, time):
        self.cursor.execute("SELECT * FROM Logs WHERE timestamp > ?", (time,))
        logs = self.cursor.fetchall()
        for log in logs:
            print(f"{log[0]}: {log[1]}")

    def init_client_info(self, client_uuid, client_ip, client_port):
        self.cursor.execute("SELECT client_uuid FROM clientInfo")
        row = self.cursor.fetchone()
        if not row:
            self.cursor.execute(
                "INSERT INTO clientInfo (client_uuid, client_ip, client_port) VALUES (?, ?, ?)",
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
            (server_uuid, server_ip, datetime.now().isoformat()),
        )
        self.conn.commit()

    def store_data(self, server_uuid, key, value):
        self.cursor.execute(
            "INSERT OR REPLACE INTO Data (server_uuid, key, value, timestamp) VALUES (?, ?, ?, ?)",
            (server_uuid, key, value, datetime.now().isoformat()),
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
