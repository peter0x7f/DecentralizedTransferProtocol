import secrets
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

app = Flask(__name__)

# Simulate a database of tokens and whitelisted IPs
tokens_db = {}
whitelisted_ips = []

def generate_token(ip):
    """Generates a unique invitation token for a given IP address."""
    token = secrets.token_urlsafe(16)
    tokens_db[token] = {
        "ip": ip,
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(hours=1),  # 1 hour validity
    }
    return token

def validate_token(token, client_ip):
    """Validates an invitation token and whitelists the IP if valid."""
    token_data = tokens_db.get(token)
    if not token_data:
        return False, "Invalid token."
    
    if token_data["ip"] != client_ip:
        return False, "IP address mismatch."
    
    if datetime.now() > token_data["expires_at"]:
        return False, "Token expired."
    
    whitelisted_ips.append(client_ip)  # Whitelist the IP
    del tokens_db[token]  # Remove the used token
    return True, "IP whitelisted successfully."

@app.route("/request_invitation", methods=["POST"])
def request_invitation():
    # Assume the client sends their IP in the request for simplicity
    client_ip = request.json.get("ip")
    token = generate_token(client_ip)
    # Here, implement your secure method to deliver the token to the client
    return jsonify({"message": "Invitation sent.", "token": token}), 200

@app.route("/claim_invitation", methods=["POST"])
def claim_invitation():
    token = request.json.get("token")
    client_ip = request.remote_addr  # Get client IP from the request
    valid, message = validate_token(token, client_ip)
    if valid:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 400

if __name__ == "__main__":
    app.run(debug=True, port=5000)
