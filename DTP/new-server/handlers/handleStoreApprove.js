async function handleStoreApprove(server, socket, args, dbAdapter) {
  try {

    const json = JSON.parse(args.join(" "));
    const { client_uuid, client_ip } = json.payload;
    

    if (!client_uuid) {
      throw new Error("Missing client_uuid in payload.");
    }

    // Check if already whitelisted
    const existing = await dbAdapter.verifyClient(client_uuid);

    if (existing) {
      console.log(`Client ${client_uuid} already whitelisted.`);
      try {
        // Step 1: Fetch existing IP array
        const { data, error: fetchError } = await dbAdapter.supabase
          .from("Whitelisted_Clients")
          .select("user_ip")
          .eq("user_key", client_uuid)
          .single();

        if (fetchError) throw fetchError;

        const currentIps = data.user_ip || [];

        // Step 2: Check if IP is already in array
        if (!currentIps.includes(client_ip)) {
          const updatedIps = [...currentIps, client_ip];

          // Step 3: Update IP array
          const { error: updateError } = await dbAdapter.supabase
            .from("Whitelisted_Clients")
            .update({ user_ip: updatedIps })
            .eq("user_key", client_uuid);

          if (updateError) throw updateError;

          console.log(`Added IP ${client_ip} to client ${client_uuid}`);
        } else {
          console.log(
            `IP ${client_ip} already exists for client ${client_uuid}`
          );
        }
      } catch (err) {
        console.error("Error updating client IP array:", err);
      }
    } else {
      await dbAdapter.insertWhitelistedKey(client_uuid, [client_ip]);
      console.log(`Whitelisted client: ${client_uuid}`);
    }

    // Map the client UUID to their socket
    server.clients.set(client_uuid, socket);
    server.socketMap.set(socket, client_uuid);
    console.log(`Client ${client_uuid} added to active clients.`);
    server.emit("client-approved", socket, client_uuid, client_ip);

    const response = {
      type: "SUCCESS_RESPONSE",
      meta: { timestamp: new Date().toISOString() },
      payload: {
        client_uuid,
        message: `Store approved for client ${client_uuid}`,
      },
    };

    socket.write(JSON.stringify(response) + "\n");
  } catch (err) {
    console.error("STORE_APPROVE error:", err);
    socket.write(
      JSON.stringify({
        type: "FAIL_RESPONSE",
        meta: { timestamp: new Date().toISOString() },
        payload: { error: err.message },
      }) + "\n"
    );
  }
}

export default handleStoreApprove;
