import Init_DTP_Server from "../server_init.js";
import add_client from "../methods/add_client.mjs";
import update_client from "../methods/update_client.mjs";

const server = Init_DTP_Server();

console.log("big steppers...");

// Example usage of add_client function
const main = async () => {
  try {
    const client = await add_client("192.168.1.10");

    if (!client ) {
      console.error("Failed to retrieve client UUID");
      return;
    }

   
    await update_client(client, "38.0.101.76");

    
  } catch (error) {
    console.error("Error in client update flow:", error);
  }
};

main();


 
 