
import Init_DTP_Server from '../server_init.js';

const server = Init_DTP_Server();

console.log('big steppers...')

const add_client = async (user_ip) => {
    try {
      const result = await server.dbAdapter.addClient(user_ip);
      console.log("Client added:", result);
    } catch (error) {
      console.error("Error adding client:", error);
    }
  };
  
  // Example usage of add_client function   
  add_client("192.168.1.10");