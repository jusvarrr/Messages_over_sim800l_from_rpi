import sqlite3
import json
import time
import requests
import os

# Local DB & config
db_location = '/home/justi/sound_lvl_app/data.db'
db_table_name = 'sound_log'
postcode_file = '/home/justi/sound_lvl_app/postcode.txt'
server_ip = '192.168.137.1'  # your PC's IP on the Ethernet network
server_port = 3000
server_url = f'http://{server_ip}:{server_port}/api/sensor/bulk'

def get_postal_code():
    if not os.path.exists(postcode_file):
        raise FileNotFoundError("Postal code file missing")
    with open(postcode_file, 'r') as f:
        code = f.read().strip()
        if not code.isdigit():
            raise ValueError("Postal code must be numeric")
        return int(code)

def get_logs_from_db():
    conn = sqlite3.connect(db_location)
    c = conn.cursor()
    c.execute(f"""
        CREATE TABLE IF NOT EXISTS {db_table_name} (
            room_id INT,
            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sound_level FLOAT NOT NULL
        )
    """)
    # fetch all logs
    c.execute(f"SELECT room_id, sound_level, time FROM {db_table_name}")
    rows = c.fetchall()
    conn.close()
    logs = []
    for row in rows:
        logs.append({
            'apt': row[0],
            'adc': row[1],
            'time': row[2]
        })
    return logs

def send_bulk_logs():
    postal_code = get_postal_code()
    logs = get_logs_from_db()
    if not logs:
        print("No logs to send")
        return

    payload = {
        'postal_code': postal_code,
        'logs': logs
    }

    try:
        response = requests.post(server_url, json=payload, timeout=10)
        if response.ok:
            print(f"Sent {len(logs)} logs to server")
            # Optionally, clear DB after sending
            clear_db_logs()
        else:
            print("Failed to send logs:", response.text)
    except Exception as e:
        print("Error sending logs:", e)

def clear_db_logs():
    conn = sqlite3.connect(db_location)
    c = conn.cursor()
    c.execute(f"DELETE FROM {db_table_name}")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    while True:
        send_bulk_logs()
        time.sleep(60)  # repeat every minute
