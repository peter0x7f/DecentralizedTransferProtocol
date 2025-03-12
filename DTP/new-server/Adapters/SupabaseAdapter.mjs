import dotenv from "dotenv";
dotenv.config();


import { createClient } from "@supabase/supabase-js";

import { v4 as uuidv4 } from "uuid";
class SupabaseAdapter {
  constructor() {
    this.supabase = createClient('https://hxsdvqydfjswvlvsmanu.supabase.co', '');
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
    const { data, error } = await this.supabase
      .from("Whitelisted_Clients")
      .insert([{ user_key: uuidv4(), user_ip }]);

    if (error) {
      console.error("Error adding client to Whitelisted_Clients:", error);
      return null;
    }

    console.log("Client added:", data);
    return data;
  }
  async insert(data) {
    const { error } = await this.supabase.from("logs").insert([{ message: data }]);
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