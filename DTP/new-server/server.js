import { createServer } from "net";
import { EventEmitter } from "events";
import { v4 as uuidv4 } from "uuid";

class TCPServer extends EventEmitter {
  constructor(dbAdapter, port = 5001, host = "0.0.0.0") {
    super();
    this.clients = new Map();
    this.socketMap = new Map();
    this.port = port;
    this.host = host;
    this.dbAdapter = dbAdapter;
    this.server = createServer(this.handleConnection.bind(this));
    this.handlers = {};
    this.uuid = 'b63aef45-2e2e-4f8f-94c2-58c17162e80f'; // uuidv4(); || process.env.SERVER_UUID
  }

  // === Register handler ===
  // Allows dynamic registration of handlers for specific command types
  registerHandler(command, handler) {
    this.handlers[command] = handler;
  }

  // === On client connection callback ===
  // This will be called whenever a new client connects
  async handleConnection(socket) {
    console.log(
      `Client connected: ${socket.remoteAddress}:${socket.remotePort}`
    );
    //emit client connect event
    this.emit("client-connected", socket);

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

  // === Server Side Data Store Request / Verification ===
  //SYN from server, sent on client connection.
  //Client responds with STORE_APPROVED or STORE_DENIED
  // if STORE_APPROVED, the message should include the clientUUID
  // if STORE_DENIED, the message should not include the clientUUID
  async requestStore(socket, args) {
    const { client_ip, client_port, server_uuid, server_ip } = args;

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

  // === Server side write value to client partition ===
  // should only be called after requestStore is approved.
  // NOTE: approved clients will be in 'clients' map && 'socketMap' map

  // TODO: add handler for success_write ? or add logic to function based on response from client.
  // (SUCCESS_RESPONSE -> add key to db : FAIL_RESPONSE -> don't add key to db)
  // if key exists in db , update else create
  async WriteValue(socket, args, dbAdapter) {
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
          data: {
            key: data_key,
            value: data_value,
          },
        },
      };

      socket.write(JSON.stringify(message) + "\n");

     
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
  // === Server side request value from client partition ===
  //
  async RequestValue(socket, args, dbAdapter) {
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

      //get response ? and process it.
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
