async function handleValueResponse(server, socket, args, dbAdapter) {
    try {
      const json = JSON.parse(args.join(" "));
      const { client_uuid, data_value } = json.payload;
  
      if (!client_uuid || !data_value) {
        throw new Error("Missing client_uuid or data_value.");
      }
  
      await dbAdapter.insert(`[${client_uuid}] Value sent: ${data_value}`);
  
      socket.write(
        JSON.stringify({
          type: "SUCCESS_RESPONSE",
          meta: { timestamp: new Date().toISOString() },
          payload: { message: "Value received and logged." },
        }) + "\n"
      );
    } catch (err) {
      console.error("VALUE_RESPONSE error:", err);
      socket.write(
        JSON.stringify({
          type: "FAIL_RESPONSE",
          meta: { timestamp: new Date().toISOString() },
          payload: { error: err.message },
        }) + "\n"
      );
    }
  }
  export default handleValueResponse;