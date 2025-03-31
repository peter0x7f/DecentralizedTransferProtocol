import dotenv from "dotenv";

dotenv.config({ path: "../.env" });

import { createClient } from "@supabase/supabase-js";

import { v4 as uuidv4 } from "uuid";
class SupabaseAdapter {
  constructor() {
    this.supabase = createClient(
      "https://hxsdvqydfjswvlvsmanu.supabase.co",
      process.env.SUPABASE_ROLE_SERVICE_KEY
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

  //add client is now handled from handleStoreApprove

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

  async insertWhitelistedKey(client_uuid, key) {
    const { error } = await this.supabase
      .from("Whitelisted_Clients")
      .insert([{ user_key: client_uuid, user_ip: key }]);

      
    if (error) {
      console.error("Supabase insert error:", error);
    } else {
      console.log("Whitelisted key inserted into Supabase:", key);
    }
  }
  async insertDataKey(client_uuid, key) {
    // First, get current keys
    const { data } = await this.supabase
      .from("Whitelisted_Clients")
      .select("data_keys")
      .eq("user_key", client_uuid)
      .single();


    const existingKeys = data.data_keys || [];
    const updatedKeys = [...new Set([...existingKeys, key])]; // avoid duplicates

    // Then update the array
    const { error: updateError } = await this.supabase
      .from("Whitelisted_Clients")
      .update({ data_keys: updatedKeys })
      .eq("user_key", client_uuid);

    if (updateError) {
      console.error("Supabase update error:", updateError);
    } else {
      console.log(`🔑 Added key "${key}" to user ${client_uuid}`);
    }
  }

  async close() {
    console.log("Supabase does not require manual connection closing.");
  }
}

export default SupabaseAdapter;
