import Init_DTP_Server from "../server_init.js";

const update_client = async (client_uuid, new_user_ip) => {
  try {
    const server = Init_DTP_Server();
    const updatedClient = await server.dbAdapter.updateClient(
      client_uuid,
      new_user_ip
    );
    
    return updatedClient;
  } catch (error) {
    console.error("Error in client update flow:", error);
  }
};

export default update_client;