from flask import Flask, request, render_template_string, redirect, url_for
import socket

app = Flask(__name__)

@app.route('/')
def home():
    return '<h1>Welcome</h1><a href="/initiate">Initiate Data Store Request</a>'

@app.route('/initiate')
def initiate():
    client_ip = '127.0.0.1'  # Assume the client is running on localhost
    client_port = 5001        # The port on which the client is listening
    data_to_send = 'store_data_request'

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
    if request.method == 'POST':
        sensitive_info = request.form['sensitive_information']
        client_ip = '127.0.0.1'
        client_port = 5001
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((client_ip, client_port))
            sock.sendall(f"sensitive_information:{sensitive_info}".encode())
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