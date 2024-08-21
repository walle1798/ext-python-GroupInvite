import json
from utils.MyApiClient import Requests

class API:
    def __init__(self):
        self.websocket = None
        self.wxid = None
        self.url = "http://127.0.0.1:8203/api?json&key=0B5A4D58834EDB5383FC9F1FF8684660E16A1FA0"



    async def post(self, data):
        opt = {
            'method': 'post',
            'name': data.get('method'),
            'kwargs': {
                "url":  self.url,
                "timeout": 5,
                "json": data
            }
        }
        status, resp = await Requests(opt)
        return status, resp
    async def Get_Qrcode(self, wxid):
        data = {
            "method": "getqrcode",
            "wxid": wxid,
            "pid": 0
        }
        status, resp = await self.post(data)
        return status, resp

    async def Get_User(self):
        data = {
            "method": "getUser",
            "pid": 0
        }
        status, resp = await self.post(data)
        return status, resp

    async def Get_GroupUser(self, Group):
        data = {
                "method": "getGroupUser",
                "wxid": Group,
                "pid": 0
            }
        status, resp = await self.post(data)
        return status, resp


    async def add_wx_user(self, encryptusername, ticket, scene):
        data = {
            "method": "agreeUser",
            "encryptusername": encryptusername,
            "ticket": ticket,
            "scene": scene
        }
        status, resp = await self.post(data)
        return status, resp

    async def send_GroupInvite(self, to_wxid, Group):
        data = {
            "method": "sendGroupInvite",
            "wxid": Group,
            "msg": to_wxid,
            "pid": 0
        }

        status, resp = await self.post(data)
        return status, resp

    async def Get_Collection(self, to_wxid, transferid):
        data = {
            "method": "agreeCash",
            "wxid": to_wxid,
            "transferid": transferid,
            "pid": 0
        }
        status, resp = await self.post(data)
        return status, resp
    # async def Get_GroupUser(self, Group):
    #     data = {
    #             "method": "getGroupUser",
    #             "wxid": f'{Group}',
    #             "pid": 0
    #         }
    #     await self.websocket.send(json.dumps(data))
    #     response = await self.websocket.recv()
    #     response = json.loads(response)
    #     print(response)

    async def send_text(self, to_wxid, message):
        data = {
            "method": "sendText",
            "wxid": to_wxid,
            "msg": message,
            "atid": "",
            "pid": 0
        }
        status, resp = await self.post(data)
        return status, resp
    async def at_text(self, to_wxid, username, message, at_id):
        data = {"method": "sendText",
                "wxid": to_wxid,
                "msg": f"@{username}\n{message}",
                "atid": at_id,
                "pid": 0}
        status, resp = await self.post(data)
        return status, resp

    async def send_image(self, to_wxid, path):
        data = {"method": "sendImage",
                "wxid": to_wxid,
                "img": path,
                "imgType": "file",
                "pid": 0}
        status, resp = await self.post(data)
        return status, resp

    async def update_user(self, wxid):
        # 获取指定用户的最新数据
        data = {"method": "netUpdateUser",
                "wxid": wxid,
                "pid": 0}

        # await self.websocket.send(json.dumps(data))
        # response = await self.websocket.recv()
        # response = json.loads(response)
        # return response.get("data")[0]
        status, resp = await self.post(data)
        return resp.get("data")[0]

    async def set_remark(self, to_wxid, message):
        data = {
            "method": "setRemark",
            "wxid": to_wxid,
            "msg": message,
            "pid": 0
        }
        status, resp = await self.post(data)
        return status, resp

    async def get_info(self):
        data = {"method": "getInfo",
                "pid": 0}
        # await self.websocket.send(json.dumps(data))
        # response = await self.websocket.recv()
        # response = json.loads(response)
        # self.wxid = response.get("myid")
        # return True

        status, resp = await self.post(data)
        self.wxid = resp.get("myid")
        return True

    async def get_msg(self):
        data = {"method": "msg",
                "pid": 0}
        status, resp = await self.post(data)
        return resp

    async def Del_RomMember(self, group, wxid):
        data = {
            "method": "delRoomMember",
            "wxid": group,
            "msg": wxid,
            "pid": 0
        }
        status, resp = await self.post(data)
        return status, resp
