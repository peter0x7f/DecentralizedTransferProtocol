import { createServer } from "net";


class TCPServer {
  constructor(dbAdapter, port = 5001, host = "0.0.0.0") {
    this.port = port;
    this.host = host;
    this.dbAdapter = dbAdapter;
    this.server = createServer(this.handleConnection.bind(this));
  }

  async handleConnection(socket) {
    console.log(`Client connected: ${socket.remoteAddress}:${socket.remotePort}`);

    socket.on("data", async (data) => {
      const message = data.toString().trim();
      console.log(`Received: ${message}`);

      try {
        await this.dbAdapter.insert(message);
        socket.write(`Saved to database: ${message}`);
      } catch (err) {
        socket.write("Database error");
        console.error("Database insert error:", err);
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
