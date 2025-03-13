import Init_DTP_Server from "../server_init.js";

const add_client = async (user_ip) => {
  try {
    const server = Init_DTP_Server();
    const result = await server.dbAdapter.addClient(user_ip);
    console.log("Client added:", result);
    return result; 
  } catch (error) {
    console.error("Error adding client:", error);
  }
};

export default add_client;
