async function handleStoreApprove(socket, args, dbAdapter) {
    try {
      const json = JSON.parse(args.join(" "));
      const { client_uuid, client_ip, client_port, server_uuid, server_ip, data_key } = json.payload;
      const data = json.payload.data || {};
  
      const key = data_key;
  
      if (!client_uuid || !key) {
        throw new Error("Missing client_uuid or key in payload.");
      }
  
      await dbAdapter.insertWhitelistedKey(client_uuid, key);
  
      const response = {
        type: "SUCCESS_RESPONSE",
        meta: { timestamp: new Date().toISOString() },
        payload: {
          client_uuid,
          message: `Key ${key} approved for client ${client_uuid}`,
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
  