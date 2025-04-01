from datetime import datetime, timedelta
import atexit
from client import DTPClient

if __name__ == "__main__":
    now = datetime.now()

    # Datetime from last week
    last_week = now - timedelta(days=10000)

    # ISO format
    last_week_iso = last_week.isoformat()

    client = DTPClient("database.db")
    atexit.register(client.database.close)
    client.database.print_logs(last_week_iso)
    # client.connect_to_server("localhost", 5001)
