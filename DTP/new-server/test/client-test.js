import net from "net";

const SERVER_HOST = "127.0.0.1";
const SERVER_PORT = 5001; 

const addClient = (user_ip) => {
  return new Promise((resolve, reject) => {
    const client = new net.Socket();

    client.connect(SERVER_PORT, SERVER_HOST, () => {
      console.log(`Connected to TCP server at ${SERVER_HOST}:${SERVER_PORT}`);
      client.write(`ADD_CLIENT ${user_ip}`); 
    });

    client.on("data", (data) => {
      console.log("Server response:", data.toString().trim());
      resolve(data.toString().trim());
      client.destroy(); // Close connection after response
    });

    client.on("error", (err) => {
      console.error("Client error:", err.message);
      reject(err);
    });

    client.on("close", () => {
      console.log("Connection closed");
    });
  });
};

// Add a client with IP `192.168.1.50`
addClient("192.168.1.60")
  .then((response) => console.log("Client added:", response))
  .catch((err) => console.error("Error:", err));
