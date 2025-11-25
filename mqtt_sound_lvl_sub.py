import time
import paho.mqtt.client as paho
import json
import os
import sqlite3

broker = "192.168.10.10"
port = 1883
user = "esp8266"
password = "esp"

db_location = 'data.db'
db_table_name = 'sound_log'

phone_nr = '+37067093991'
mac_table = "/home/justi/sound_lvl_app/macs_to_id.txt"

Connected = False   # <-- FIXED


# ----------------------- DATABASE ------------------------

def write_sound_log(room_nr, sound_level):
    conn = sqlite3.connect(db_location)
    c = conn.cursor()

    c.execute(f"""
        CREATE TABLE IF NOT EXISTS {db_table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INT,
            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sound_level FLOAT NOT NULL
        );
    """)

    c.execute(f"""
        INSERT INTO {db_table_name} (room_id, sound_level)
        VALUES (?, ?)
    """, (room_nr, sound_level))

    conn.commit()
    conn.close()


# ----------------------- DEVICE REGISTRATION ------------------------

def register_device(message):
    payload = message.payload.decode("utf-8")
    python_obj = json.loads(payload)
    mac_msg = python_obj['device_id']

    if not os.path.exists(mac_table):
        open(mac_table, "w").close()

    last_id = 0
    registered = False

    # read the file
    with open(mac_table, "r") as f:
        for line in f:
            mac, room = line.strip().split("=")
            last_id = max(last_id, int(room))
            if mac == mac_msg:
                registered = True

    # write a new one if not registered
    if not registered:
        new_id = last_id + 1
        with open(mac_table, "a") as f:
            f.write(f"{mac_msg}={new_id}\n")
        print(f"Registered new device {mac_msg} as room {new_id}")
    else:
        print(f"Device {mac_msg} already registered")


# ----------------------- SOUND LEVEL HANDLER ------------------------

def handle_sound_level_info(message, topic):
    mac_msg = topic.split("/")[-1]

    id_msg = -1

    # read room number
    with open(mac_table, "r") as f:
        for line in f:
            mac, room = line.strip().split("=")
            if mac == mac_msg:
                id_msg = int(room)

    if id_msg < 0:
        print("Unknown device:", mac_msg)
        return

    payload = message.payload.decode("utf-8")
    print(f"Room {id_msg}: {payload}")

    with open("/home/justi/sound_lvl_app/logs", "a") as f:
        f.write(f"Room {id_msg}: {payload}\n")

    python_obj = json.loads(payload)
    db_lvl = python_obj['sound_10b']

    # write to DB
    write_sound_log(id_msg, db_lvl)

    # trigger SMS alert
    if db_lvl >= 450:
        os.system(
            f'/home/justi/sound_lvl_app/send_message.py '
            f'--phone-nr {phone_nr} --room-nr {id_msg}'
        )


# ----------------------- MQTT CALLBACKS ------------------------

def on_message(client, userdata, message):
    topic = message.topic
    if '/esp8266/register/' in topic:
        register_device(message)
    elif '/building/soundlevel/' in topic:
        handle_sound_level_info(message, topic)


def on_connect(client, userdata, flags, rc, properties=None):
    global Connected
    if rc == 0:
        print("Connected to broker")
        Connected = True
    else:
        print("Connection failed")


# ----------------------- MAIN ------------------------

client = paho.Client(client_id="client-001")
client.username_pw_set(user, password=password)

client.on_message = on_message
client.on_connect = on_connect

print("Connecting to broker", broker)
client.connect(broker, port)
client.loop_start()

while not Connected:
    time.sleep(0.1)

# subscribe to correct topics
client.subscribe("/esp8266/register/#")
client.subscribe("/building/soundlevel/#")

while True:
    time.sleep(1)
