from datetime import datetime

import json
import os
import socket
import sqlite3
import time

from clientpopup import prompt_user
from database import Database


class DTPClient:
    def __init__(self, database_path):
        self.database = Database(database_path)
        self.database.connect()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.uuid = (
            "86394b22-fd0e-4f59-9c1b-bf2e4e0b8a1d"  # env variable for client uuid
        )

    # fix
    def handle_connection(self, conn, addr):
        """Listen for messages and process them."""
        try:
            print(f"🌐 Connected to {addr}")
            buffer = ""

            while True:
                data = conn.recv(1024).decode("utf-8")
                if not data:
                    print(f"Disconnected from {addr}")
                    break

                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        print(f"[DEBUG] Empty message from {addr}, skipping...")
                        continue

                    try:
                        self.process_message(line, conn, addr)
                    except Exception as e:
                        print(f"Failed to process message from {addr}: {e}")

        except Exception as e:
            print(f"Error in connection with {addr}: {e}")
        finally:
            conn.close()
            print(f"Connection with {addr} closed.")

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

            client_uuid = self.uuid
            server_uuid = payload.get("server_uuid")
            isWhitelisted = self.database.cursor.execute(
                "SELECT * FROM WhitelistedServers WHERE server_uuid = ?",
                (server_uuid,),
            ).fetchone()
            if isWhitelisted is None:
                approved = prompt_user(
                    payload.get("server_ip"),
                    payload.get("server_port"),
                    payload.get("server_name"),
                    server_uuid,
                )
                if not approved:
                    return

            if msg_type == "STORE_REQUEST":
                server_uuid = payload.get("server_uuid")
                server_ip = payload.get("server_ip")
                type = payload.get("type")

                self.database.insert_log(f"{type} from {server_ip}")
                serverExists = self.database.cursor.execute(
                    "SELECT * FROM WhitelistedServers WHERE server_uuid = ?",
                    (server_uuid,),
                ).fetchone()

                if serverExists:
                    self.process_store_request(
                        server_uuid, server_ip, conn, client_uuid
                    )
                else:
                    approved = prompt_user(
                        server_ip, "5001", "test_server", server_uuid
                    )
                    if approved:
                        self.process_store_request(
                            server_uuid, server_ip, conn, client_uuid
                        )
                    else:
                        print(f"STORE_REQUEST rejected from {server_ip}")

            elif msg_type == "WRITE_VALUE":

                server_uuid = payload.get("server_uuid")
                server_ip = payload.get("server_ip")

                key = payload.get("data", {}).get("key")
                value = payload.get("data", {}).get("value")
                type = payload.get("type")
                print(f"WRITE_VALUE received from {server_ip}")
                print(f"Key: {key}, Value: {value}")
                self.database.insert_log(f"{type} from {server_ip}")
                self.process_write_value(
                    server_uuid, server_ip, key, value, conn, client_uuid
                )

            elif msg_type == "REQUEST_VALUE":

                server_uuid = payload.get("server_uuid")
                server_ip = payload.get("server_ip")

                key = payload.get("data_key")
                type = payload.get("type")
                self.database.insert_log(f"{type} from {server_ip}")
                self.process_request_value(
                    server_uuid, server_ip, key, conn, client_uuid
                )

            elif msg_type == "SUCCESS_RESPONSE":
                server_uuid = payload.get("server_uuid")
                server_ip = payload.get("server_ip")

                type = payload.get("type")
                self.database.insert_log(f"{type} from {server_ip}")

            elif msg_type == "FAIL_RESPONSE":
                server_uuid = payload.get("server_uuid")
                server_ip = payload.get("server_ip")

                type = payload.get("type")
                self.database.insert_log(f"{type} from {server_ip}")

        except Exception as e:
            print(f"Error processing message: {e}")

    def process_store_request(self, server_uuid, server_ip, conn, client_uuid):
        try:
            # Add server to whitelist
            self.database.add_whitelisted_server(server_uuid, server_ip)

            response = {
                "type": "STORE_APPROVE",
                "meta": {"timestamp": datetime.now().isoformat()},
                "payload": {
                    "client_uuid": client_uuid,
                    "client_ip": "client_ip",
                    "client_port": "client_port",
                    "server_uuid": server_uuid,
                    "server_ip": server_ip,
                    "message": "Store approved",
                },
            }

            # Send JSON response
            conn.sendall((json.dumps(response) + "\n").encode("utf-8"))
            print(f"STORE_APPROVE sent to {server_ip}")

        except Exception as e:
            print(f"Error processing STORE_REQUEST: {e}")

    def process_write_value(
        self, server_uuid, server_ip, key, value, conn, client_uuid
    ):
        try:
            self.database.store_data(server_uuid, key, value)
            response = {
                "type": "SUCCESS_STORE",
                "meta": {"timestamp": datetime.now().isoformat()},
                "payload": {
                    "client_uuid": client_uuid,
                    "message": "Data stored successfully",
                    "key": key,
                },
            }
            conn.sendall((json.dumps(response) + "\n").encode("utf-8"))
            print(f"SUCCESS_RESPONSE sent to {server_ip}")

        except Exception as e:
            print(f" Error processing WRITE_VALUE: {e}")

    def process_request_value(self, server_uuid, server_ip, key, conn, client_uuid):
        try:
            value = self.database.get_data(server_uuid, key)
            print(f"process request value for key: {key}")
            response = {
                "type": "VALUE_RESPONSE",
                "meta": {"timestamp": datetime.now().isoformat()},
                "payload": {
                    "client_uuid": client_uuid,
                    "client_ip": "client_ip",
                    "client_port": "client_port",
                    "server_uuid": server_uuid,
                    "server_ip": server_ip,
                    "data_value": value,
                },
            }
            conn.sendall((json.dumps(response) + "\n").encode("utf-8"))
            print(f"VALUE_RESPONSE with val {value} sent to {server_ip}")

        except Exception as e:
            print(f" Error processing REQUEST_VALUE: {e}")


if __name__ == "__main__":
    import atexit

    client = DTPClient("database.db")
    atexit.register(client.database.close)
    client.connect_to_server("localhost", 5001)
