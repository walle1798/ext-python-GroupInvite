import asyncio
import json
import requests
import websockets
import logging
logger = logging.getLogger(__name__)

# 更换为自己的群id
wxid = '37143202205@chatroom'


async def get_uri():
    url = "http://127.0.0.1:8203/ext/www/key.ini"
    response = requests.get(url=url)
    if not response:
        logging.error("Empty response received from %s", url)
        return
    try:
        response_data = response.json()
        secret = response_data.get("key")
        _uri = "ws://127.0.0.1:8202/wx?name=www&key=" + secret
        return _uri
    except json.JSONDecodeError as e:
        logging.error("Failed to decode JSON response from %s: %s", url, e)


async def send_announcement_notify(websocket, msg):
    data = {
        "method": "sendText",
        "wxid": wxid,
        "msg": msg,
        "atid": "announcement@all",
        "pid": 0
    }
    await websocket.send(json.dumps(data))
    response = await websocket.recv()
    if response['data']['type'] == 51 and response['data']['utype'] == 3:
        logging.info(f"发送成功")


async def websocket_client():
    uri = await get_uri()
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                async for message in websocket:
                    try:
                        message = json.loads(message)
                        logging.info(f'消息:{message["data"]["msg"]}')
                        msg = message["data"]["msg"]
                        if msg and msg.startswith('发送公告'):
                            await send_announcement_notify(websocket, msg[5:])
                    except Exception as e:
                        logging.error(str(e))
                        pass
        except Exception as e:
            logging.error(e)


if __name__ == '__main__':
    asyncio.run(websocket_client())