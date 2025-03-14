

const addClientHandler = async (socket, args, dbAdapter) => {
  if (args.length < 1) {
    socket.write("ERROR: Missing IP address\n");
    return;
  }

  const user_ip = args[0];
  console.log(`Adding new client with IP: ${user_ip}`);

  try {
    const result = await dbAdapter.addClient(user_ip);
    socket.write(`Client added: ${JSON.stringify(result)}\n`);
  } catch (err) {
    socket.write("ERROR: Failed to add client\n");
    console.error("Error adding client:", err);
  }
};

export default addClientHandler;
