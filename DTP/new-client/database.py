from database import Database
import socket
import threading
import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'dtp_client.sqlite')
class Database:
    def __init__(self, path):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def init_db(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS WhitelistedServers (
                                server_uuid TEXT PRIMARY KEY,
                                server_ip TEXT,
                                approved_on TEXT
                              )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS StoredData (
                                server_uuid TEXT,
                                key TEXT,
                                value TEXT,
                                timestamp TEXT,
                                PRIMARY KEY (server_uuid, key)
                              )''')
        self.conn.commit()

    def is_whitelisted(self, server_uuid):
        self.cursor.execute("SELECT 1 FROM WhitelistedServers WHERE server_uuid = ?", (server_uuid,))
        return self.cursor.fetchone() is not None

    def add_whitelisted_server(self, server_uuid, server_ip):
        self.cursor.execute("INSERT OR IGNORE INTO WhitelistedServers (server_uuid, server_ip, approved_on) VALUES (?, ?, ?)",
                            (server_uuid, server_ip, datetime.utcnow().isoformat()))
        self.conn.commit()
        print(f"✅ Whitelisted server: {server_uuid}")

    def store_data(self, server_uuid, key, value):
        self.cursor.execute("REPLACE INTO StoredData (server_uuid, key, value, timestamp) VALUES (?, ?, ?, ?)",
                            (server_uuid, key, value, datetime.utcnow().isoformat()))
        self.conn.commit()
        print(f"🔑 Stored data for server {server_uuid}: {key} = {value}")

    def get_data(self, server_uuid, key):
        self.cursor.execute("SELECT value FROM StoredData WHERE server_uuid = ? AND key = ?", (server_uuid, key))
        row = self.cursor.fetchone()
        return row[0] if row else None


if __name__ == "__main__":
    client = DTPClient(port=5001)
    client.start()
