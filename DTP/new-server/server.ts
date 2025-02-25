import net from "net";

export class TCPServer {
  private server: net.Server;
  private port: number;
  private host: string;

  constructor(port: number = 8080, host: string = "0.0.0.0") {
    this.port = port;
    this.host = host;
    this.server = net.createServer(this.handleConnection);
  }

  private handleConnection(socket: net.Socket): void {
    console.log(`Client connected: ${socket.remoteAddress}:${socket.remotePort}`);

    socket.on("data", (data) => {
      console.log(`Received: ${data.toString().trim()}`);
      socket.write(`Echo: ${data}`);
    });

    socket.on("close", () => console.log("Client disconnected"));
    socket.on("error", (err) => console.error("Socket error:", err.message));
  }

  public start(): void {
    this.server.listen(this.port, this.host, () => {
      console.log(`TCP Server running at ${this.host}:${this.port}`);
    });
  }

  public stop(): void {
    this.server.close(() => console.log("Server stopped"));
  }
}
