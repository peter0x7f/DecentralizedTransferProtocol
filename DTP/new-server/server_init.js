// Reusable Server (Singleton Pattern) Object
// Joseph Somogie 2025
import dotenv from "dotenv";

dotenv.config({ path: "/.env" });

import TCPServer from "./server.js";
import SupabaseAdapter from "./Adapters/SupabaseAdapter.mjs";


import updateClientHandler from "./handlers/updateClientHandler.js";
import handleStoreApprove from "./handlers/handleStoreApprove.js";
import handleValueResponse from "./handlers/handleValueResponse.js";

let serverInstance = null;

const Init_DTP_Server = () => {
  if (!serverInstance) {
    const dbAdapter = new SupabaseAdapter();
    serverInstance = new TCPServer(dbAdapter, 5001, "0.0.0.0");

    // Register command handlers
    serverInstance.registerHandler("UPDATE_CLIENT", updateClientHandler);
    serverInstance.registerHandler("STORE_APPROVE", handleStoreApprove);
    serverInstance.registerHandler("VALUE_RESPONSE", handleValueResponse);

    //add more handlers for other server handlers (server functions for specific command types)

    serverInstance.start();
  }
  return serverInstance;
};

export default Init_DTP_Server;
