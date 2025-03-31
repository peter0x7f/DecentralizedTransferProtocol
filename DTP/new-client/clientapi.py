from flask import Flask, request, jsonify
from client import DTPClient
import threading

app = Flask(__name__)
client = DTPClient("client_data/database.db")


@app.route("/connect", methods=["POST"])
def connect():
    data = request.get_json()
    server_ip = data.get("server_ip")
    server_port = data.get("server_port")
    server_uuid = data.get("server_uuid")

    if not server_ip or not server_port or not server_uuid:
        return jsonify({"error": "Invalid payload"}), 400

    print(f"🤝 Handshake requested for server {server_ip}:{server_port}")

    # Start connection in background thread
    threading.Thread(
        target=client.connect_to_server, args=(server_ip, server_port), daemon=True
    ).start()

    return jsonify({"status": "Connection initiated"}), 200


@app.route("/disconnect", methods=["POST"])
def disconnect():
    #  disconnect logic 
    return jsonify({"status": "Disconnected"}), 200


if __name__ == "__main__":
    app.run(port=5005)

