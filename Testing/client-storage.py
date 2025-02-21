import subprocess
import sqlite3
import uuid
import json
import os

def create_bitlocker_partition(disk_number, size_gb):
    """
    Creates a new primary partition on the given disk and enables BitLocker encryption.
    This function writes a temporary DiskPart script, runs it, then calls manage-bde.
    """
    # Calculate size in MB (DiskPart expects size in MB)
    size_mb = size_gb * 1024
    diskpart_script = f"""
select disk {disk_number}
create partition primary size={size_mb}
assign letter=E
    """
    # Write script to temporary file
    script_file = "diskpart_script.txt"
    with open(script_file, "w") as f:
        f.write(diskpart_script)
    try:
        subprocess.run(["diskpart", "/s", script_file], check=True)
        print("Partition created and assigned letter E:")
    except subprocess.CalledProcessError as e:
        print("Error during disk partitioning:", e)
    finally:
        os.remove(script_file)
    
    # Enable BitLocker encryption on the new partition (E:)
    # In practice, secure the password and consider TPM integration.
    password = "YourStrongPassword123!"  # Replace with secure retrieval in production
    partition_letter = "E:"
    try:
        subprocess.run(["manage-bde", "-on", partition_letter, "-password", password], check=True)
        print("BitLocker encryption initiated on partition", partition_letter)
    except subprocess.CalledProcessError as e:
        print("Error enabling BitLocker:", e)

def initialize_database(db_path):
    """Initializes a SQLite database for storing company data."""
    conn = sqlite3.connect(db_path)
    return conn

def create_company_table(conn, company_name):
    """
    Creates a table for a given company.
    The table includes a primary key UUID, IP, DNS, and an extra_data field (stored as JSON).
    """
    table_name = f"company_{company_name.replace(' ', '_').lower()}"
    cursor = conn.cursor()
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
      id TEXT PRIMARY KEY,
      ip TEXT,
      dns TEXT,
      extra_data TEXT
    );
    """
    cursor.execute(create_table_sql)
    conn.commit()
    print(f"Table '{table_name}' created for {company_name}.")
    return table_name

def insert_company_record(conn, table_name, ip, dns, extra_data=None):
    """Inserts a sample record into the specified company table."""
    cursor = conn.cursor()
    record_id = str(uuid.uuid4())
    extra_data_json = json.dumps(extra_data) if extra_data else "{}"
    insert_sql = f"INSERT INTO {table_name} (id, ip, dns, extra_data) VALUES (?, ?, ?, ?);"
    cursor.execute(insert_sql, (record_id, ip, dns, extra_data_json))
    conn.commit()
    print(f"Inserted record with id {record_id} into table '{table_name}'.")
    return record_id

def export_table_to_json(conn, table_name, json_file):
    """Exports all records from a table to a JSON file."""
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name};")
    rows = cursor.fetchall()
    col_names = [description[0] for description in cursor.description]
    data = [dict(zip(col_names, row)) for row in rows]
    with open(json_file, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Exported data from '{table_name}' to {json_file}.")

def dynamic_table_creation(conn, schema_json):
    """
    Dynamically creates a table based on a JSON schema.
    Expected schema_json format:
      {
         "table_name": "additional_data",
         "columns": {
            "record_id": "TEXT PRIMARY KEY",
            "description": "TEXT",
            "value": "TEXT"
         }
      }
    """
    table_name = schema_json["table_name"]
    columns = schema_json["columns"]
    column_defs = ", ".join([f"{col} {dtype}" for col, dtype in columns.items()])
    cursor = conn.cursor()
    create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({column_defs});"
    cursor.execute(create_sql)
    conn.commit()
    print(f"Dynamically created table '{table_name}'.")

def main():
    # Step 1: Create BitLocker encrypted partition (requires admin rights on Windows)
    try:
        create_bitlocker_partition(disk_number=1, size_gb=10)
    except Exception as e:
        print("Partition/encryption step failed:", e)
    
    # Step 2: Initialize local database for company data
    db_path = "companies.db"
    conn = initialize_database(db_path)
    
    # Step 3: Create tables for each company and insert a sample record
    companies = ["CompanyA", "CompanyB"]
    for company in companies:
        table = create_company_table(conn, company)
        # Insert a record with sample IP and DNS values
        insert_company_record(conn, table, ip="192.168.1.100", dns=f"{company.lower()}.example.com",
                                extra_data={"note": "Initial record"})
        # Export the table data to a company-specific JSON file
        export_table_to_json(conn, table, f"{company.lower()}_data.json")
    
    # Step 4: Dynamically create an additional table as specified by the server
    dynamic_schema = {
        "table_name": "additional_data",
        "columns": {
            "record_id": "TEXT PRIMARY KEY",
            "description": "TEXT",
            "value": "TEXT"
        }
    }
    dynamic_table_creation(conn, dynamic_schema)
    
    conn.close()

if __name__ == "__main__":
    main()
