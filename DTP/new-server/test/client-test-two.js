import net from "net";
import { v4 as uuidv4 } from "uuid";

const client_uuid = uuidv4();
const client_ip = "127.0.0.1";
const client_port = 6000;
const server_ip = "127.0.0.1"; // Adjust if needed
const server_port = 5001;

const socket = new net.Socket();

socket.connect(server_port, server_ip, () => {
  console.log(`Connected to TCP server at ${server_ip}:${server_port}`);
});

socket.setEncoding("utf8");

socket.on("data", (chunk) => {
  const messages = chunk.toString().split("\n").filter(Boolean);

  messages.forEach((msg) => {
    try {
      const parsed = JSON.parse(msg);
      const { type, meta, payload } = parsed;

      console.log(`📩 Received: ${type}`);
      console.log("Payload:", payload);

      switch (type) {
        case "STORE_REQUEST":
          return handleStoreRequest(payload);
        case "WRITE_VALUE":
          return handleWriteValue(payload);
        case "REQUEST_VALUE":
          return handleRequestValue(payload);
          case "SUCCESS_RESPONSE":
            console.log('✅ Received: SUCCESS_RESPONSE' + "\n" + payload.message);
            break;
          case "FAIL_RESPONSE":
            console.log('❌ Received: FAIL_RESPONSE' + "\n" + payload.message);
            break;
        default:
          console.log("Unknown command type.");
      }
    } catch (err) {
      console.error("Invalid JSON:", err.message);
    }
  });
});

socket.on("close", () => {
  console.log("Connection closed.");
});

socket.on("error", (err) => {
  console.error("Client socket error:", err.message);
});

// === Handlers ===

function handleStoreRequest(payload) {
  const client_uuid = uuidv4();
  const response = {
    type: "STORE_APPROVE",
    meta: { timestamp: new Date().toISOString() },
    payload: {
      ...payload,
      client_uuid,
      message: "Store approved",
    },
  };

  socket.write(JSON.stringify(response) + "\n");
  console.log("✅ Sent: STORE_APPROVE");
}

function handleWriteValue(payload) {
  const {  key,  value } = payload.data;

  if (!key || !value) {
    console.error("Invalid WRITE_VALUE payload:", payload);
    return;
  }

  console.log(`📝 Write request for key: ${key} with value: ${value}`);

  const response = {
    type: "SUCCESS_RESPONSE",
    meta: { timestamp: new Date().toISOString() },
    payload: {
      client_uuid,
      message: `Stored key "${key}" successfully`,
    },
  };

  socket.write(JSON.stringify(response) + "\n");
  console.log("✅ Sent: SUCCESS_RESPONSE (WRITE_VALUE)");
}


function handleRequestValue(payload) {
  const data_value = "mocked_value_from_client"; // Just for test logging

  const response = {
    type: "VALUE_RESPONSE",
    meta: { timestamp: new Date().toISOString() },
    payload: {
      client_uuid,
      client_ip,
      client_port,
      server_uuid: payload.server_uuid,
      server_ip: payload.server_ip,
      data_value,
    },
  };

  socket.write(JSON.stringify(response) + "\n");
  console.log(`📤 Sent: VALUE_RESPONSE with mocked value`);
}
