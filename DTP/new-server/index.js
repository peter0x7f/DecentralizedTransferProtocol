import Init_DTP_Server from "./server_init.js";

const server =  Init_DTP_Server(); // Returns your TCPServer instance

// Give the server a moment to accept clients
setTimeout(() => {
  // Mock client info for testing
  const clientInfo = {
    client_uuid: "test-client-uuid",
    client_ip: "127.0.0.1",
    client_port: 6000,
    server_uuid: server.uuid,
    server_ip: server.host,
  };

  // Grab the first connected socket
  const [socket] = server.server.connections || Array.from(server.server._connections || []);
  
  if (!socket) {
    console.error("No client connected yet.");
    return;
  }

  // === Trigger each test one-by-one ===

  // 1. Test STORE_REQUEST
  server.requestStore(socket, clientInfo);

  // 2. Test WRITE_VALUE
  server.handleWriteValue(socket, {
    ...clientInfo,
    data_key: "username",
    data_value: "thesandwich"
  }, server.dbAdapter);

  // 3. Test REQUEST_VALUE
  server.handleRequestValue(socket, {
    ...clientInfo,
    data_key: "username"
  }, server.dbAdapter);

}, 1000); // Wait a second to ensure the client connects
