import os
import subprocess
import ctypes
import sys
import sqlite3
import uuid
import json

def is_admin():
    """Check if the script is running with administrative privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def create_and_encrypt_vhd(vhd_path, drive_letter, size_gb, password):
    """
    Create a VHD, mount it, and encrypt it with BitLocker.

    :param vhd_path: The full path where the VHD will be created.
    :param drive_letter: The drive letter to assign to the mounted VHD.
    :param size_gb: The size of the VHD in gigabytes.
    :param password: The password to use for BitLocker encryption.
    """
    size_mb = size_gb * 1024
    create_vhd_script = f"""
    create vdisk file="{vhd_path}" maximum={size_mb} type=expandable
    select vdisk file="{vhd_path}"
    attach vdisk
    create partition primary
    format fs=ntfs quick
    assign letter={drive_letter}
    """
    script_file = "create_vhd_script.txt"
    with open(script_file, "w") as f:
        f.write(create_vhd_script)
    try:
        subprocess.run(["diskpart", "/s", script_file], check=True)
        print(f"VHD created and mounted as drive {drive_letter}:")
    except subprocess.CalledProcessError as e:
        print("Error during VHD creation:", e)
        return
    finally:
        os.remove(script_file)

    # Convert the password to a secure string
    secure_password = f'ConvertTo-SecureString "{password}" -AsPlainText -Force'

    # Enable BitLocker with the password protector
    enable_cmd = (
        f"powershell.exe -Command "
        f"$SecureString = {secure_password}; "
        f"Enable-BitLocker -MountPoint {drive_letter}: "
        f"-EncryptionMethod Aes256 "
        f"-PasswordProtector -Password $SecureString"
    )

    try:
        subprocess.run(enable_cmd, check=True, shell=True)
        print(f"BitLocker encryption initiated on drive {drive_letter}:")
    except subprocess.CalledProcessError as e:
        print(f"Error enabling BitLocker on drive {drive_letter}: {e}")

def main():
    if not is_admin():
        print("This script requires administrative privileges. Restarting with elevated permissions...")
        # Restart the script with elevated permissions
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, ' '.join(sys.argv), None, 1)
        return

    vhd_path = os.path.join(os.getcwd(), "test.vhd")
    size_gb = 1  # Size of the VHD
    drive_letter = "Z"  # Drive letter to assign to the VHD
    password = "YourSecurePassword123"  # Replace with a strong password
    create_and_encrypt_vhd(vhd_path, drive_letter, size_gb, password)
    # The database file and JSON export files will be stored on this partition.
    db_path = os.path.join(f"{drive_letter}:\\", "companies.db")
    conn = initialize_database(db_path)
    
    # Create company tables and insert sample records.
    companies = ["CompanyA", "CompanyB"]
    for company in companies:
        table = create_company_table(conn, company)
        insert_company_record(conn, table, ip="192.168.1.100", dns=f"{company.lower()}.example.com",
                              extra_data={"note": "Initial record"})
        # Export each table to a JSON file stored on the same partition.
        json_file = os.path.join(f"{drive_letter}:\\", f"{company.lower()}_data.json")
        export_table_to_json(conn, table, json_file)
    
    # Dynamically create an additional table as specified by a JSON schema.
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
    print("Database operations completed successfully.")
if __name__ == "__main__":
    main()


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


if __name__ == "__main__":
    main()
