import Init_DTP_Server from "./server_init.js";

const server =  Init_DTP_Server();

server.on("client-approved", (socket, client_uuid, client_ip) => {
    console.log("Client approved:", client_uuid, client_ip);
    const data_key = "testKey";
    const data_value = "testValue";


   /* server.WriteValue(socket, {
        client_uuid: client_uuid,
        client_ip: client_ip,
        client_port: socket.remotePort,
        server_uuid: server.uuid,
        server_ip: server.host,
        data_key: data_key,
        data_value: data_value,
    }, server.dbAdapter);*/

    server.RequestValue(socket, {
        client_uuid: client_uuid,
        client_ip: client_ip,
        client_port: socket.remotePort,
        server_uuid: server.uuid,
        server_ip: server.host,
        data_key: data_key,
     
    }, server.dbAdapter);



});

