async function handleSuccessStore(server, socket, args, dbAdapter) {
  try {
    const json = JSON.parse(args.join(" "));
    const { client_uuid, key, message } = json.payload;
    console.log("handleSuccessStore: ", json.payload);
    await server.dbAdapter.insertDataKey(client_uuid, key);
    socket.write(
      JSON.stringify({
        type: "SUCCESS_RESPONSE",
        meta: { timestamp: new Date().toISOString() },
        payload: { client_uuid: client_uuid },
      }) + "\n"
    );
  } catch (err) {
    console.error("STORE_APPROVED error:", err);
    socket.write(
      JSON.stringify({
        type: "FAIL_RESPONSE",
        meta: { timestamp: new Date().toISOString() },
        payload: { error: err.message },
      }) + "\n"
    );
  }
}

export default handleSuccessStore;
