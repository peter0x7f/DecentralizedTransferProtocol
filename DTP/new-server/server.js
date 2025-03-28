import { createServer } from "net";
import { v4 as uuidv4 } from "uuid";

class TCPServer {
  constructor(dbAdapter, port = 5001, host = "0.0.0.0") {
    this.onClientConnect = null;
    this.clients = new Map();
    this.socketMap = new Map();
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


  // === On client connection callback ===
  // This will be called whenever a new client connects
  async handleConnection(socket) {
 
    console.log(
      `Client connected: ${socket.remoteAddress}:${socket.remotePort}`
    );


    // Prepare client + server info

    const client_ip = socket.remoteAddress;
    const client_port = socket.remotePort;

    const server_uuid = this.uuid;
    const server_ip = this.host;

    // Call requestStore immediately on connect
    // if client already approved, send STORE_APPROVED
    // else prompt winform
 
    this.requestStore(socket, {
      client_ip,
      client_port,
      server_uuid,
      server_ip,
    });

    // listen for client response to requestStore 
    // if STORE_APPROVED, the message should include the clientUUID
    // if STORE_DENIED, the message should not include the clientUUID

   
    //parse client responses
    socket.on("data", async (chunk) => {
      const messages = chunk.toString().split("\n").filter(Boolean);

      for (const msg of messages) {
        try {
          const parsed = JSON.parse(msg);
          const handler = this.handlers[parsed.type];
          if (handler) {
            await handler(this, socket, [msg], this.dbAdapter); // send raw JSON string in array
          } else {
            socket.write("ERROR: Unrecognized type\n");
          }
        } catch (err) {
          console.error("Invalid JSON received:", msg);
          socket.write("ERROR: Invalid JSON\n");
        }
      }
    });
    
    // when connection closes
    socket.on("close", () => {
      const client_uuid = this.socketMap.get(socket);
      this.clients.delete(client_uuid);
      this.socketMap.delete(socket);
      console.log(`Client ${client_uuid} disconnected`);
    });
    socket.on("error", (err) => console.error("Socket error:", err.message));
  }

  async requestStore(socket, args) {
    const {  client_ip, client_port, server_uuid, server_ip } =
      args;

    const message = {
      type: "STORE_REQUEST",
      meta: { timestamp: new Date().toISOString() },
      payload: {
        client_ip,
        client_port,
        server_uuid,
        server_ip,
      },
    };

    socket.write(JSON.stringify(message) + "\n"); // delimiter for TCP stream
  }

  async storeData(socket, args, data) {
    const { client_uuid, client_ip, client_port, server_uuid, server_ip } =
      args;
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
        data: { key, value },
      },
    };

    socket.write(JSON.stringify(message) + "\n");

    // Listen for response from THIS socket
    const handleResponse = (chunk) => {
      try {
        const responses = chunk.toString().trim().split("\n");
        responses.forEach(async (res) => {
          const parsed = JSON.parse(res);
          if (
            parsed.type === "STORE_APPROVED" &&
            parsed.payload &&
            parsed.payload.key === key
          ) {
            console.log(`Client approved STORE for key: ${key}`);

            // Insert key into whitelisted_clients DB
            await this.dbAdapter.insertWhitelistedKey(client_uuid, key);

            // Optional: remove listener after successful response
            socket.off("data", handleResponse);
          }
        });
      } catch (err) {
        console.error("Error parsing client response:", err);
      }
    };

    socket.on("data", handleResponse);
  }
  async handleWriteValue(socket, args, dbAdapter) {
    try {
      const {
        client_uuid,
        client_ip,
        client_port,
        server_uuid,
        server_ip,
        data_key,
        data_value,
      } = args;

      const message = {
        type: "WRITE_VALUE",
        meta: { timestamp: new Date().toISOString() },
        payload: {
          client_uuid,
          client_ip,
          client_port,
          server_uuid,
          server_ip,
          data: [data_key, data_value],
        },
      };

      socket.write(JSON.stringify(message) + "\n");

      // Optional: log the action
      await dbAdapter.insert(
        `[${client_uuid}] WRITE_VALUE issued for key: ${data_key}`
      );
    } catch (err) {
      console.error("WRITE_VALUE error:", err);
      socket.write(
        JSON.stringify({
          type: "FAIL_RESPONSE",
          meta: { timestamp: new Date().toISOString() },
          payload: { error: err.message },
        }) + "\n"
      );
    }
  }

  async handleRequestValue(socket, args, dbAdapter) {
    try {
      const {
        client_uuid,
        client_ip,
        client_port,
        server_uuid,
        server_ip,
        data_key,
      } = args;

      const message = {
        type: "REQUEST_VALUE",
        meta: { timestamp: new Date().toISOString() },
        payload: {
          client_uuid,
          client_ip,
          client_port,
          server_uuid,
          server_ip,
          data_key,
        },
      };

      socket.write(JSON.stringify(message) + "\n");

      await dbAdapter.insert(
        `[${client_uuid}] REQUEST_VALUE issued for key: ${data_key}`
      );
    } catch (err) {
      console.error("REQUEST_VALUE error:", err);
      socket.write(
        JSON.stringify({
          type: "FAIL_RESPONSE",
          meta: { timestamp: new Date().toISOString() },
          payload: { error: err.message },
        }) + "\n"
      );
    }
  }

  start() {
    this.server.listen(this.port, this.host, () => {
      console.log(`TCP Server running at ${this.host}:${this.port}`);
    });
  }
}

export default TCPServer;
