import { createServer } from "net";
import { v4 as uuidv4 } from "uuid";

class TCPServer {
  constructor(dbAdapter, port = 5001, host = "0.0.0.0") {
    this.port = port;
    this.host = host;
    this.dbAdapter = dbAdapter;
    this.server = createServer(this.handleConnection.bind(this));
    this.handlers = {};
    this.uuid = uuidv4();
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

  async requestStore(socket, args) {
    const { client_uuid, client_ip, client_port, server_uuid, server_ip } = args;
  
    const message = {
      type: "STORE_REQUEST",
      meta: { timestamp: new Date().toISOString() },
      payload: {
        client_uuid,
        client_ip,
        client_port,
        server_uuid,
        server_ip
      }
    };
  
    socket.write(JSON.stringify(message) + '\n'); // delimiter for TCP stream
  }

  async storeData(socket, args, data) {
    const { client_uuid, client_ip, client_port, server_uuid, server_ip } = args;
    const { key, value } = data;
  
    const message = {
      type: "STORE_DATA",
      meta: { timestamp: new Date().toISOString() },
      payload: {
        client_uuid,
        client_ip,
        client_port,
        server_uuid,
        server_ip,
        data: { key, value }
      }
    };
  
    socket.write(JSON.stringify(message) + '\n');
  
    // Listen for response from THIS socket
    const handleResponse = (chunk) => {
      try {
        const responses = chunk.toString().trim().split('\n');
        responses.forEach(async (res) => {
          const parsed = JSON.parse(res);
          if (parsed.type === "STORE_APPROVED" && parsed.payload && parsed.payload.key === key) {
            console.log(`Client approved STORE for key: ${key}`);
  
            // Insert key into whitelisted_clients DB
            await this.dbAdapter.insertWhitelistedKey(client_uuid, key);
  
            // Optional: remove listener after successful response
            socket.off('data', handleResponse);
          }
        });
      } catch (err) {
        console.error("Error parsing client response:", err);
      }
    };
  
    socket.on('data', handleResponse);
  }
  
  

  start() {
    this.server.listen(this.port, this.host, () => {
      console.log(`TCP Server running at ${this.host}:${this.port}`);
    });
  }
}

export default TCPServer;
