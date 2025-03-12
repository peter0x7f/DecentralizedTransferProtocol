// Reusable Server (Singleton Pattern) Object
// Joseph Somogie 2025

import TCPServer from './server.js';
import SupabaseAdapter from './Adapters/SupabaseAdapter.mjs';

let serverInstance = null;

const Init_DTP_Server = () => {
  if (!serverInstance) {
    const dbAdapter = new SupabaseAdapter(); 
    serverInstance = new TCPServer(dbAdapter, 5001, "0.0.0.0");
    serverInstance.start();
  }
  return serverInstance;
};

export default Init_DTP_Server;

