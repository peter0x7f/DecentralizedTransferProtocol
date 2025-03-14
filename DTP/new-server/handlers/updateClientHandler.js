

const updateClientHandler = async (socket, args, dbAdapter) => {
    if (args.length < 2) {
      socket.write("ERROR: Missing parameters (UUID & new IP)\n");
      return;
    }
  
    const [client_uuid, new_ip] = args;
    console.log(`Updating client ${client_uuid} to IP: ${new_ip}`);
  
    try {
      const result = await dbAdapter.updateClient(client_uuid, new_ip);
      socket.write(`Client updated: ${JSON.stringify(result)}\n`);
    } catch (err) {
      socket.write("ERROR: Failed to update client\n");
      console.error("Error updating client:", err);
    }
  };
  
  export default updateClientHandler;
  