import secrets
from datetime import datetime

from message import API
import time
import aioredis, asyncio, json
import aiofiles
from utils.logger import setup_logger
import urllib.parse
from utils.OpenApi import QL
from cofnig.config import config
from utils.DotDict import DotDict


class Message(API):
    def __init__(self, message, websocket, reids):

        self.log = setup_logger(__name__)
        super().__init__()
        self.websocket = websocket
        self.message = message.get("data")
        # 消息本体
        self.type = self.message.get("type")
        # 消息类型,文本1,图片3,转账49
        self.private = 1
        # 默认为私信消息
        self.Group = None
        self.Admin_Group = config['Group']['Group_list']
        self.admin = None
        self.group_id = None
        self.config = config
        self.user_id, self.username = self.get_user_info()
        self.content = self.message.get("msg")
        self.timestamp = self.message.get("time")
        self.redis_url = 'redis://127.0.0.1/1'
        self.redis = reids
        self.url = "http://127.0.0.1:8203/api?json&key=0B5A4D58834EDB5383FC9F1FF8684660E16A1FA0"
        self.q = QL(config["qinglong"]['url'], config["qinglong"]['id'], config["qinglong"]['secret'])
    def DotDict(self, dict):
        f = DotDict(dict)
        return f

    def __str__(self):
        attributes = vars(self)
        formatted_message = ''
        for key, value in attributes.items():
            if isinstance(value, (dict, list)):
                formatted_message += f'{key}: {value}\n'
            else:
                formatted_message += f'{key}: {value}\n'
        return formatted_message

    async def initialize_redis(self):
        self.redis = await aioredis.StrictRedis.from_url(self.redis_url)

    async def close_redis(self):
        if self.redis:
            await self.redis.close()

    async def get_config(self, filename):
        async with aiofiles.open(filename, 'r') as file:
            data = await file.read()
            return json.loads(data)

    async def validate_token(self, token):
        if self.redis is None:
            await self.initialize_redis()
        # 获取与令牌关联的数据
        stored_data = await self.redis.hget("token_user", token)
        if stored_data:
            # 删除令牌，确保它只能使用一次
            await self.redis.hdel("token_user", token)
            pin = json.loads(stored_data.decode())['pin']
            await self.redis.hdel("user_token", pin)
            return stored_data.decode()  # 返回解码后的数据
        return None

    async def Del_Points_Token(self, token):
        if self.redis is None:
            await self.initialize_redis()
        stored_data = await self.redis.hget("Points_Token", token)
        if stored_data:
            await self.redis.hdel("Points_Token", token)
            return stored_data.decode()  # 返回解码后的数据
        return None

    async def Add_Points_Token(self, data):
        if self.redis is None:
            await self.initialize_redis()
        prefix = "Pts_T_"
        token = prefix + secrets.token_urlsafe(16)
        data_str = json.dumps(data)
        await self.redis.hset("Points_Token", token, data_str)
        return token

    async def if_cookie(self):
        vlaue = await self.get_value('Jd_pin_Wxid', self.user_id)
        if vlaue == []:
            await self.reply('你还没登录JD呢, 先去登录JD吧')
            return False
        cklist = [ck[0] for ck in vlaue]
        resp = self.q.getEnvs()
        pt_pins = [entry['value'].split(';')[1].split('=')[1] for entry in resp if entry['status'] == 0]
        result = [ck for ck in cklist if ck in pt_pins]
        if result == []:
            await self.reply('你无有效JDCK, 请重新登录')
            return False
        return True


    async def Get_Cookie(self, msg_name='需要查询账号'):
        text = '┄┅┄┅┄┅┄┅┄┅┄┅┄'
        resp = await self.get_value('Jd_pin_Wxid', self.user_id)
        if resp == []:
            self.log.warning(f'用户:{self.username}, 你还没登录呢, 先去登录吧')
            await self.reply('你还没登录呢, 先去登录吧')
            return False
        if len(resp) == 1:
            result = self.q.getEnvs(resp[0][0])
            return result[0].get('value')
        msg = f'{text}\n{msg_name}:\n{text}'
        for i, account in enumerate(resp, 1):
            msg += f'\n[{i}]:[{account[0]}]'
        msg += f'\n{text}'
        await self.reply(msg)
        status, slep = await self.get_message()
        if not status: return False
        try:
            selected_index = int(slep) - 1
            selected_account = resp[selected_index]
        except Exception as e:
            self.log.error('输入错误退出')
            await self.reply('输入错误， 程序退出')
            return False
        result = self.q.getEnvs(selected_account[0])
        if result == []:
            await self.reply('你还没登录呢, 先去登录吧')
            self.log.warning(f'用户:{self.username}, 你还没登录呢, 先去登录吧')
            return False
        return result[0].get('value')


    async def add_users(self):
        if self.redis is None:
            await self.initialize_redis()
        """添加新用户"""
        if not await self.redis.hexists("user_password", self.user_id):
            await self.redis.hset("user_password", self.user_id, json.dumps({}))
            self.log.info(f"用户 {self.user_id} 已添加.")
        else:
            self.log.info(f"用户 {self.user_id} 已经存在.")

    import json

    async def get_user_passwds(self, user_id=None):
        all_users_data = {}
        if user_id:
            resp = await self.get_value('Jd_pin_Wxid', self.user_id)
            if resp == []:
                return {}
            for account in resp:
            # 获取特定用户的信息
                if await self.redis.hexists("user_password", account[0]):
                    user_data_json = await self.redis.hget("user_password", account[0])
                    user_data = json.loads(user_data_json)
                    all_users_data[account[0]] = user_data
                    self.log.info(f"成功获取用户 {account[0]} 的信息.")
                else:
                    self.log.error(f"用户 {account[0]} 不存在.")
        else:
            user_keys = await self.redis.hkeys("user_password")
            for uid in user_keys:
                user_data_json = await self.redis.hget("user_password", uid)
                user_data = json.loads(user_data_json)
                all_users_data[uid.decode() if isinstance(uid, bytes) else uid] = user_data

        return all_users_data

    from datetime import datetime, timedelta

    async def elm_send_ck(self, cookie, phone, end_time=None, authorize=False):
        if self.redis is None:
            await self.initialize_redis()

        # 从 Redis 中获取现有的用户数据
        existing_data = await self.redis.hget("elm_ck", self.user_id)
        if existing_data:
            # 将现有的数据解析为字典
            user_data = json.loads(existing_data)
        else:
            # 如果没有现有数据，初始化一个空字典
            user_data = {}

        if authorize:
            # 授权操作，通过 phone 直接查找并更新记录
            if phone in user_data:
                # 更新已有记录的 cookie 和 end_time
                user_data[phone]['cookie'] = cookie
                if end_time:
                    user_data[phone]['end_time'] = end_time.isoformat()
            else:
                # 如果没有找到对应的 phone 记录，提示未找到
                print(f"Phone {phone} not found for authorization.")
        else:
            if phone in user_data:
                # 如果已经存在该 phone 的记录，只更新 cookie，保持其他数据不变
                user_data[phone]['cookie'] = cookie
            else:
                # 如果不存在该 phone 的记录，创建新的记录
                new_cookie_data = {
                    "cookie": cookie,
                    "phone": phone,
                    "status": True,
                    "start_time": datetime.now().isoformat(),  # 当前时间作为字符串
                    "end_time": end_time.isoformat() if end_time else None  # 如果提供了 end_time，将其转换为字符串
                }
                user_data[phone] = new_cookie_data
        await self.redis.hset("elm_ck", self.user_id, json.dumps(user_data))

    async def get_elm_ck(self):
        if self.redis is None:
            await self.initialize_redis()
        result = await self.redis.hget("elm_ck", self.user_id)
        return result


    async def send_user_passwd(self, pin, username=None, password=None, remark=None, status=None):
        # 获取现有的用户数据，如果不存在则初始化一个新的字典
        existing_data = await self.redis.hget("user_password", pin)
        if existing_data:
            user_data = json.loads(existing_data)
        else:
            user_data = {
                "pin": pin,
                "username": "",
                "password": "",
                "remark": "",
                "wxid": self.user_id,
                "status": True
            }
        if not user_data['wxid']:
            user_data['wxid'] = self.user_id
        if status is not None:
            user_data['status'] = status
        if username is not None:
            user_data['username'] = username
        if password is not None:
            user_data['password'] = password
        if remark is not None:
            user_data['remark'] = remark
        await self.redis.hset("user_password", pin, json.dumps(user_data))
        self.log.info(f"已为用户 {self.user_id} 添加或更新 {username} 用户. 备注: {remark} ")

    async def send_message(self, message):
        if not self.redis:
            await self.initialize_redis()
        timestamp = time.time()
        await self.redis.zadd('message_queue', {json.dumps(message): timestamp})

    async def delete_value(self, table_name, key):
        if not self.redis:
            await self.initialize_redis()
        await self.redis.hdel(table_name, key)

    async def send_value(self, table_name, key, value):
        if not self.redis:
            await self.initialize_redis()
        await self.redis.hset(table_name, key, value)


    # async def get_value(self, table_name, value=None):
    #     if not self.redis:
    #         await self.initialize_redis()
    #     all_keys = await self.redis.hkeys(table_name)
    #     all_keys = [key.decode('utf-8') for key in all_keys]
    #     if value is None: return [(key, (await self.redis.hget(table_name, key)).decode('utf-8')) for key in all_keys]
    #     values = await self.redis.hmget(table_name, *all_keys)
    #     return [(key, stored_value.decode('utf-8')) for key, stored_value in zip(all_keys, values) if
    #             stored_value.decode('utf-8') == value]



    async def get_value(self, table_name, value=None):
        if not self.redis:
            await self.initialize_redis()
        all_keys = await self.redis.hkeys(table_name)
        all_keys = [key.decode('utf-8') for key in all_keys]
        all_keys.sort()  # 对键进行排序
        if value is None:
            return [(key, (await self.redis.hget(table_name, key)).decode('utf-8')) for key in all_keys]
        values = await self.redis.hmget(table_name, *all_keys)
        return [(key, stored_value.decode('utf-8')) for key, stored_value in zip(all_keys, values) if
                stored_value and stored_value.decode('utf-8') == value]

    async def get_keys(self, table_name, key=None):
        if not self.redis:
            await self.initialize_redis()
        value = await self.redis.hget(table_name, key)
        return value.decode() if value else False


    async def get_message(self, timeout=60):
        if not self.redis:
            await self.initialize_redis()
        end_time = time.time() + timeout
        while time.time() < end_time:
            current_time = time.time()
            messages = await self.redis.zrangebyscore('message_queue', '-inf', '+inf', withscores=True)
            for message, timestamp in messages:
                message_dict = json.loads(message.decode('utf-8'))
                user_id = message_dict.get("fromid")
                if not user_id:
                    user_id = self.message.get("wxid")
                    if not user_id:
                        continue
                if "@chatroom" in user_id:
                    user_id = message_dict.get("memid")
                if message_dict.get("time") - self.timestamp > 0 and self.user_id == user_id and message_dict.get("type") == 1:
                    await self.redis.zrem('message_queue', message)
                    return True, message_dict['msg']
            expired_messages = [message for message, timestamp in messages if current_time - timestamp > 60]
            if expired_messages:
                await self.redis.zrem('message_queue', *expired_messages)
            await asyncio.sleep(0.1)

        await self.reply('输入超时, 程序退出！')
        return False, '输入超时, 程序退出！'

    async def Group_Invite(self, Group, user_id=False):
        if "@chatroom" in Group:
            await self.send_GroupInvite(to_wxid=user_id if user_id else self.user_id, Group=Group)
            return True

    async def Collection(self, transferid):
        from_id = self.message.get("fromid")
        if "@chatroom" not in from_id:
            await self.Get_Collection(to_wxid=self.user_id, transferid=transferid)

    async def add_user(self, encryptusername, ticket, scene):
        await self.add_wx_user(encryptusername, ticket, scene)
        return True

    async def reply(self, message, no_at=False):
        from_id = self.message.get("fromid")
        if no_at:
            await self.send_text(to_wxid=from_id, message=message)
            return True
        if "@chatroom" in from_id:
            # 群聊信息
            await self.at_text(to_wxid=from_id, username=self.username, message=message, at_id=self.user_id)
            return True
        await self.send_text(to_wxid=from_id, message=message)
        return True

    async def callback(self, message):
        # 与回复相反,处理我主动发的消息
        to_id = self.message.get("toid")
        if "@chatroom" in to_id:
            # 群聊信息
            await self.at_text(to_wxid=to_id, username=self.username, message=message, at_id=self.user_id)
            return True
        await self.send_text(to_wxid=to_id, message=message)
        return True

    async def remark(self, message):
        to_id = self.message.get("toid")
        if "@chatroom" in to_id:
            return False
        await self.set_remark(to_wxid=to_id, message=message)
        return True

    async def file(self, path):
        from_id = self.message.get("fromid")
        await self.send_image(to_wxid=from_id, path=path)
        return True

    def get_user_info(self):
        user_id = self.message.get("fromid")
        if not user_id:
            user_id = self.message.get("wxid")
        if "@chatroom" in user_id:
            self.private = 0
            self.Group = True
            self.group_id = self.message.get("fromid")
            if not self.group_id: self.group_id= self.message.get("wxid")
            user_id = self.message.get("memid")
            user_name = self.message.get("nickName2")
            user_name = user_name if user_name else self.message.get("memname")


            # user_name = user_name if user_name else self.message.get("member")
        else:
            self.Group = False
            user_name = self.message.get("reMark")
            user_name = user_name if user_name else self.message.get("nickName")
        if user_id in config['Admin_wxid']:
            self.admin = True
        return user_id, user_name

    async def update(self):
        res = await self.update_user(self.user_id)
        user_name = res.get("reMark")
        user_name = user_name if user_name else self.message.get("nickName")
        self.username = user_name
        return

    async def wait(self, timeout=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            data = await self.get_msg()
            user_id = data.get("data").get("fromid")
            if "@chatroom" in user_id:
                user_id = self.message.get("memid")
            if user_id == self.user_id:
                return data.get("data").get("msg")

    async def GroupUser_if(self, user_id, Group):
        data = []
        for group in Group:
            status, resp = await self.Get_GroupUser(group)
            data += resp.get('data')
        return any(user['wxid'] == user_id for user in data)


    async def Qrcode(self, wxid):
        status, resp = await self.Get_Qrcode(wxid)
        return status, resp
    async def Remove_Group(self, wxid):
        status, resp = await self.Del_RomMember(self.group_id, wxid)
        return status, resp
