import { createServer } from "net";


class TCPServer {
  constructor(dbAdapter, port = 5001, host = "0.0.0.0") {
    this.port = port;
    this.host = host;
    this.dbAdapter = dbAdapter;
    this.server = createServer(this.handleConnection.bind(this));
    this.handlers = {};
  }

  registerHandler(command, handler) {
    this.handlers[command] = handler; 
  }
  
  async handleConnection(socket) {
    console.log(`Client connected: ${socket.remoteAddress}:${socket.remotePort}`);

    socket.on("data", async (data) => {
      const message = data.toString().trim();
      console.log(`Received: ${message}`);

      const [command, ...args] = message.split(" "); // Extract command
      if (this.handlers[command]) {
        this.handlers[command](socket, args, this.dbAdapter); // Call handler function
      } else {
        socket.write("ERROR: Unrecognized command\n");
      }
    });

    socket.on("close", () => console.log("Client disconnected"));
    socket.on("error", (err) => console.error("Socket error:", err.message));
  }

  start() {
    this.server.listen(this.port, this.host, () => {
      console.log(`TCP Server running at ${this.host}:${this.port}`);
    });
  }
}

export default TCPServer;
