import readline from "readline";
import Init_DTP_Server from "./server_init.js";

const server = Init_DTP_Server();

server.on("client-approved", (socket, client_uuid, client_ip) => {
  console.log(`✅ Client approved: ${client_uuid} (${client_ip})`);

  // Store the socket for interaction
  server.clients.set(client_uuid, socket);

  // Start CLI loop after approval
  startCLI(socket, client_uuid, client_ip);
});

function startCLI(socket, client_uuid, client_ip) {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  console.log("\n🔐 Connected. Available Commands:\n");
  console.log(`  write → Store a value`);
  console.log(`  read → Retrieve a value`);
  console.log(`  exit → Exit CLI\n`);

  rl.on("line", async (input) => {
    const cmd = input.trim().toLowerCase();

    if (cmd === "write") {
      rl.question("Enter key: ", (key) => {
        rl.question("Enter value: ", (value) => {
          server.WriteValue(socket, {
            client_uuid,
            client_ip,
            client_port: socket.remotePort,
            server_uuid: server.uuid,
            server_ip: server.host,
            data_key: key,
            data_value: value,
          }, server.dbAdapter);
        });
      });
    } else if (cmd === "read") {
      rl.question("Enter key to retrieve: ", (key) => {
        server.RequestValue(socket, {
          client_uuid,
          client_ip,
          client_port: socket.remotePort,
          server_uuid: server.uuid,
          server_ip: server.host,
          data_key: key,
        }, server.dbAdapter);
      });
    } else if (cmd === "exit") {
      console.log("👋 Exiting CLI...");
      rl.close();
      process.exit(0);
    } else {
      console.log("❓ Unknown command. Type 'write', 'read', or 'exit'.");
    }
  });
}
