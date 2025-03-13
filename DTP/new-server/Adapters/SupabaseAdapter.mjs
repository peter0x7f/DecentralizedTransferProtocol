import dotenv from "dotenv";

dotenv.config({ path: "../.env" });

import { createClient } from "@supabase/supabase-js";

import { v4 as uuidv4 } from "uuid";
class SupabaseAdapter {
  constructor() {
    this.supabase = createClient(
      "https://hxsdvqydfjswvlvsmanu.supabase.co",
      process.env.SUPABASE_SERVICE_ROLE_KEY
    );
  }

  async initTable() {
    // Call the function we created in the Supabase database
    const { data, error } = await this.supabase.rpc("init_logs_table");
    if (error) {
      console.error("Error initializing logs table:", error);
    } else {
      console.log("'logs' table initialized in Supabase.");
    }
  }

  async addClient(user_ip) {
    const client_uuid = uuidv4();
    const { data, error } = await this.supabase
      .from("Whitelisted_Clients")
      .insert([{ user_key: client_uuid, user_ip }]);

    if (error) {
      console.error("Error adding client to Whitelisted_Clients:", error);
      return null;
    }

    console.log(
      "Client added: ",
      client_uuid,
      " with IP:",
      user_ip,
      " - data returned: ",
      data
    );
    return client_uuid;
  }

  async updateClient(client_uuid, new_user_ip) {
    try {
      const { data, error } = await this.supabase
        .from("Whitelisted_Clients")
        .update({ user_ip: new_user_ip })
        .eq("user_key", client_uuid)
        .select();

      if (error) throw error;

      console.log("Client updated:", data);
      return data;
    } catch (err) {
      console.error("Error updating client:", err);
    }
  }
  async verifyClient(client_uuid) {
    try {
      const { data, error } = await this.supabase
        .from("Whitelisted_Clients")
        .select()
        .eq("user_key", client_uuid);

      if (error) throw error;

      if (data.length > 0) {
        console.log("Client verified:", data);
        return data;
      } else {
        console.log("Client not found:", client_uuid);
        return null;
      }
    } catch (err) {
      console.error("Error verifying client:", err);
    }
  }

  async insert(data) {
    const { error } = await this.supabase
      .from("logs")
      .insert([{ message: data }]);
    if (error) {
      console.error("Supabase insert error:", error);
    } else {
      console.log("Data inserted into Supabase:", data);
    }
  }

  async close() {
    console.log("Supabase does not require manual connection closing.");
  }
}

export default SupabaseAdapter;
