const { Pool } = require("pg");
require("dotenv").config();

class PostgreSQLAdapter {
  constructor() {
    this.pool = new Pool({
      user: process.env.DB_USER,
      host: process.env.DB_HOST,
      database: process.env.DB_DATABASE,
      password: process.env.DB_PASSWORD,
      port: parseInt(process.env.DB_PORT, 10),
      ssl: process.env.DB_SSL === "true" ? { rejectUnauthorized: false } : false, // Required for Supabase
    });

    this.pool.on("error", (err) => {
      console.error("Unexpected PostgreSQL client error:", err);
      process.exit(-1);
    });

    this.initTable(); 
  }

  async initTable() {
    const createTableQuery = `
      CREATE TABLE IF NOT EXISTS logs (
        id SERIAL PRIMARY KEY,
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    `;

    try {
      await this.pool.query(createTableQuery);
      console.log(" 'logs' table verified/created in PostgreSQL (Supabase).");
    } catch (err) {
      console.error(" Error creating 'logs' table:", err);
    }
  }

  async insert(data) {
    try {
      await this.pool.query("INSERT INTO logs (message) VALUES ($1)", [data]);
      console.log(" Data inserted into PostgreSQL (Supabase):", data);
    } catch (err) {
      console.error(" PostgreSQL insert error (Supabase):", err);
    }
  }

  async close() {
    await this.pool.end();
    console.log(" PostgreSQL connection closed");
  }
}

module.exports = PostgreSQLAdapter;


