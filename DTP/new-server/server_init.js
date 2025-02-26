//Reusable Server (Singleton Pattern) Object 
// Joseph Somogie 2025


import { TCPServer } from "./server";

let serverInstance = null;

export const Init_DTP_Server = () => {
  if (!serverInstance) {
    serverInstance = new TCPServer(5001, "0.0.0.0");
    serverInstance.start();
  }
  return serverInstance;
};