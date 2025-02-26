// Reusable Server (Singleton Pattern) Object
// Joseph Somogie 2025

import TCPServer from "./server";
import PostgreSQLAdapter from "../DB/Adapters/PostgreSqlAdapter";


let serverInstance = null;

const Init_DTP_Server = () => {
  if (!serverInstance) {
    const dbAdapter = new PostgreSQLAdapter(); 
    serverInstance = new TCPServer(dbAdapter, 5001, "0.0.0.0");
    serverInstance.start();
  }
  return serverInstance;
};

module.exports = Init_DTP_Server;
