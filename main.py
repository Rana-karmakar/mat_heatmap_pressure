import asyncio
import json
import argparse
from bleak import BleakClient
import warnings
import re
import numpy as np
import matplotlib.pyplot as plt
import datetime

warnings.filterwarnings("ignore")

ROWS = 60
COLS = 22

async def connect_to_device(device_address):
    try:
        client = BleakClient(device_address)
        await client.connect()
        print(f"Connected: {client.address}")
        return client
    except Exception as e:
        print(f"Failed to connect to {device_address}. Error: {e}")
        return None

async def discover_services(client):
    try:
        await client.is_connected()
        services = client.services
        print(f"Services discovered for {client.address}")
        for service in services:
            print(f"Service: {service.uuid}")
    except Exception as e:
        print(f"Failed to discover services. Error: {e}")

async def send_and_receive_data_with_notifications(client, json_data):
    service_uuid = "0000180f-0000-1000-8000-00805f9b34fb"
    write_char_uuid = "0000abf1-0000-1000-8000-00805f9b34fb"
    read_char_uuid = "0000abf2-0000-1000-8000-00805f9b34fb"

    try:
        await client.start_notify(read_char_uuid, notification_handler)
        json_dumb = json.dumps(json_data).encode("utf-8")
        await client.write_gatt_char(write_char_uuid, json_dumb)
        
        await asyncio.sleep(2)  # Time ################################
        await client.stop_notify(read_char_uuid)

    except Exception as e:
        print(f"Error: {e}")

def extract_integers(input_string):
    return [int(match) for match in re.findall(r'\d+', input_string)]

def notification_handler(sender: int, data: bytearray):
    global accumulated_data
    data = data.decode('utf-8')

    if 'accumulated_data' not in globals():
        accumulated_data = []

    accumulated_data.extend(extract_integers(data))

    while len(accumulated_data) >= ROWS * COLS:
        chunk = accumulated_data[:ROWS * COLS]
        
        if 'first_iteration' not in globals():
            # print(chunk)
            count_greater_than_135 = sum(x > 135 for x in chunk)
            count_greater_than_80 = sum(x > 80 for x in chunk)
            top_10_highest = sorted(chunk, reverse=True)[:10]
            data_matrix = np.array(chunk).reshape(ROWS, COLS)
            plt.imshow(data_matrix)
            plt.title(f"Top 10: {top_10_highest}")
            plt.xlabel(f'Count > 135: {count_greater_than_135}')
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            # filename = f"heatmap_{timestamp}"
            plt.savefig(f"heatmap_{timestamp}.png")
            print("\nHeatmap generated and saved.")
            globals()['first_iteration'] = True

        accumulated_data = accumulated_data[ROWS * COLS:]

async def main():
    parser = argparse.ArgumentParser(description="Connect to a BLE device and receive notifications.")
    parser.add_argument("device_address", type=str, help="Bluetooth device address")
    args = parser.parse_args()

    try:
        client = await connect_to_device(args.device_address)

        if client:
            print("Device is connected.")
            await discover_services(client)
            json_data = {"mode": "Mat_Data", "status": True}
            await send_and_receive_data_with_notifications(client, json_data)

    except ValueError as ve:
        print(f"Invalid input: {ve}")

if __name__ == "__main__":
    asyncio.run(main())
