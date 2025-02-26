var net = require('net');



export class TCPServer {
  

  constructor(port = 5001, host = "0.0.0.0") {
    this.port = port;
    this.host = host;
    this.server = net.createServer(this.handleConnection);
  }

 handleConnection(socket) {
    console.log(`Client connected: ${socket.remoteAddress}:${socket.remotePort}`);

    socket.on("data", (data) => {
      console.log(`Received: ${data.toString().trim()}`);
      socket.write(`Echo: ${data}`);
    });

    socket.on("close", () => console.log("Client disconnected"));
    socket.on("error", (err) => console.error("Socket error:", err.message));
  }

  start(){
    this.server.listen(this.port, this.host, () => {
      console.log(`TCP Server running at ${this.host}:${this.port}`);
    });
  }

 stop() {
    this.server.close(() => console.log("Server stopped"));
  }


  
}
