
import asyncio
import time
import websockets
import json
import requests
from utils.logger import setup_logger

logging = setup_logger(__name__)

type_dict = {
    3: '图片',
    47: '表情',
    49: '卡片',
    10002: '撤回',
}

Group = '98652916482@chatroom'

async def get_uri():
    url = "http://127.0.0.1:8203/ext/www/key.ini"
    try:
        response = requests.get(url=url, timeout=10)
        response.raise_for_status()
        response_data = response.json()
        secret = response_data.get("key")
        if not secret:
            logging.error("Secret key not found in response from %s", url)
            return None
        _uri = "ws://127.0.0.1:8202/wx?name=www&key=" + secret
        return _uri
    except requests.exceptions.RequestException as e:
        logging.error("Request to %s failed: %s", url, e)
    except json.JSONDecodeError as e:
        logging.error("Failed to decode JSON response from %s: %s", url, e)
    return None

async def send_GroupInvite(websocket, Group, wxid):
    data = {
        "method": "sendGroupInvite",
        "wxid": Group,
        "msg": wxid,
        "pid": 0
    }
    try:
        await websocket.send(json.dumps(data))
        response = await websocket.recv()
        logging.info("Received response for GroupInvite: %s", response)
    except websockets.exceptions.ConnectionClosedError as e:
        logging.error("Connection closed while sending GroupInvite: %s", e)
    except asyncio.TimeoutError as e:
        logging.error("Timeout occurred while sending GroupInvite: %s", e)
    except Exception as e:
        logging.error("Unexpected error occurred while sending GroupInvite: %s", e)

async def main():
    uri = await get_uri()
    if not uri:
        logging.error("Failed to get WebSocket URI, exiting...")
        return

    async with websockets.connect(uri) as websocket:
        wxid = 'my_vx_id' 
        await send_GroupInvite(websocket, Group, wxid)

if __name__ == "__main__":
    asyncio.run(main())
