import asyncio
import websockets
import time
import json
from dataclasses import dataclass
from datetime import datetime

import db

@dataclass
class SeismicData:
    mag: float
    reg: str
    lat: float
    lon: float
    dep: float
    time: str 
    updated: str
    src_id: int

# GLOBALS
web_socket_url = 'wss://www.seismicportal.eu/standing_order/websocket'
queue = asyncio.Queue()
last_message = None

def save_data(info):
    parsed_data = SeismicData(
                    mag=info['mag'],
                    reg=info['flynn_region'],
                    lat=info['lat'],
                    lon=info['lon'],
                    dep=info['depth'],
                    time=info['time'],
                    updated=info['lastupdate'],
                    src_id=info['source_id'])

    db.add_data(parsed_data)
    return parsed_data

def process_json(data):
    try:
        json_data = json.loads(data) 

        info = json_data['data']['properties']
        #info['time'] = datetime.fromisoformat(info['time'][:-1]).strftime("%Y-%m-%d %H:%M:%S")
        #info['lastupdate'] = datetime.fromisoformat(info['lastupdate'][:-1]).strftime("%Y-%m-%d %H:%M:%S")
        info['time'] = datetime.strptime(info['time'][:-1], '%Y-%m-%dT%H:%S.%f')
        info['lastupdate'] = datetime.strptime(info['lastupdate'][:-1], '%Y-%m-%dT%H:%S.%f')
        result = save_data(info)
    except Exception as e:
        print("Unable to process with error:", e)

async def receive():
    async with websockets.connect(web_socket_url) as ws:
        print("Connected to websockets server...")
        while True:
            res = await ws.recv()
            if res is None:
                print("Error receiving message")
                break
            await queue.put(res)

async def process_recv():
    global last_message
    message_count = 0
    while True:
        msg = await queue.get()
        message_count += 1
        if msg == last_message:
            queue.task_done()
            continue
        last_message = msg 
        process_json(msg)
        queue.task_done()

async def run():
    recv_task = asyncio.create_task(receive())
    process_task = asyncio.create_task(process_recv())
    await asyncio.gather(recv_task, process_task)

