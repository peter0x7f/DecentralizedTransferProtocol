from flask import Flask, request, render_template_string, redirect, url_for
import socket
import requests

def get_server_public_ip():
    try:
        response = requests.get('https://api.ipify.org')
        return response.text
    except requests.exceptions.RequestException as e:
        return f"Failed to get IP: {e}"

server_public_ip = get_server_public_ip()

app = Flask(__name__)

@app.route('/')
def home():
    return '<h1>Welcome</h1><a href="/initiate">Initiate Data Store Request</a>'

@app.route('/initiate')
def initiate():
    client_ip = '127.0.0.1'  # Assume the client is running on localhost
    client_port = 5001        # The port on which the client is listening
    data_to_send = f'store_data_request, company ip:{server_public_ip}'

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((client_ip, client_port))
        sock.sendall(data_to_send.encode())
        response = sock.recv(1024).decode()

    if response == '1':
        return redirect(url_for('submit_sensitive'))
    else:
        return '<h1>Data store request denied.</h1>'

@app.route('/submit_sensitive', methods=['GET', 'POST'])
def submit_sensitive():
    company_name = "Unight"
    if request.method == 'POST':
        sensitive_info = request.form['sensitive_information']
        client_ip = '127.0.0.1'
        client_port = 5001
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(('localhost', client_port))  # Connecting to localhost for demonstration
            data_to_send = f"company_name:{company_name}, company ip:{server_public_ip}, sensitive_information:{sensitive_info}"
            sock.sendall(data_to_send.encode())
            return redirect(url_for('request_permission'))
    else:
        return '''
        <form method="post">
            Sensitive Information: <input type="text" name="sensitive_information"><br>
            <input type="submit" value="Submit">
        </form>
        '''

@app.route('/request_permission')
def request_permission():
    return '''
    <h1>Request Access to Display Sensitive Data</h1>
    <form action="/display_data" method="post">
        <input type="submit" name="action" value="retrieve_sensitive_data">
    </form>
    '''

@app.route('/display_data', methods=['POST'])
def display_data():
    if request.form['action'] == 'retrieve_sensitive_data':
        client_ip = '127.0.0.1'
        client_port = 5001

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((client_ip, client_port))
            sock.sendall(b'retrieve_sensitive_data')
            sensitive_data = sock.recv(1024).decode()

        return f'<h1>Displayed Information:</h1><p>{sensitive_data}</p>'
    else:
        return '<h1>Permission to access data denied by the user.</h1>'

if __name__ == "__main__":
    app.run(debug=True, port=5000)
