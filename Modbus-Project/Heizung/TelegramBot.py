import requests
import json
import threading
import time

class TelegramBot:
    def __init__(self, token):
        self.address = "https://api.telegram.org/bot" + token + "/"
        self.last_update = -1
        self.commands = self.getMyCommands()

    def _parse(self, message):
        return message.json()

    def _get(self, method:str):
        r = self._parse(requests.get(self.address+method))
        if r["ok"]:
            return r["result"]

    def getMe(self):
        return self._get("getMe")

    def getMyCommands(self):
        return self._get("getMyCommands")

    def _post(self, method:str, args:dict):
        r = self._parse(requests.post(self.address+method, args))
        if r["ok"]:
            return r["result"]

    def setMyCommands(self,commands):
        message_obj = {}
        message_obj["commands"] = json.dumps(commands)
        r = self._post("setMyCommands", message_obj)
        return r

    def getUpdates(self,offset:int,limit:int,timeout:int):
        message_obj = {}
        message_obj["offset"] = offset
        message_obj["limit"] = limit
        message_obj["timeout"] = timeout
        r = self._post("getUpdates", message_obj)
        return r

    def getChat(self, chat_id):
        message_obj = {}
        message_obj["chat_id"] = chat_id
        return self._post("getChat",message_obj)

    def pinChatMessage(self, chat_id, message_id:int, disable_notification=False):
        message_obj = {}
        message_obj["chat_id"] = chat_id
        message_obj["message_id"] = message_id
        message_obj["disable_notification"] = disable_notification
        r = self._post("pinChatMessage", message_obj)
        return r

    def unPinChatMessage(self, chat_id, message_id:int):
        message_obj = {}
        message_obj["chat_id"] = chat_id
        message_obj["message_id"] = message_id
        r = self._post("unpinChatMessage", message_obj)
        return r

    def unpinAllChatMessages(self,chat_id):
        message_obj = {}
        message_obj["chat_id"] = chat_id
        r = self._post("unpinAllChatMessages", message_obj)
        return r

    def sendChatAction(self, chat_id, action):
        message_obj = {}
        message_obj["chat_id"] = chat_id
        message_obj["action"] = action
        r = self._post("sendChatAction", message_obj)
        return r

    def sendMessage(self, chat_id, message, parse_mode="", disable_notification=False, reply_to_message_id=-1):
        self.sendChatAction(chat_id, "typing")
        message_obj = {}
        message_obj["chat_id"] = chat_id
        message_obj["text"] = message
        message_obj["parse_mode"] = parse_mode
        message_obj["disable_notification"] = disable_notification
        if reply_to_message_id >= 0:
            message_obj["reply_to_message_id"] = reply_to_message_id
        r = self._post("sendMessage", message_obj)
        return r

    def get_new_messages(self):
        updates = self.getUpdates(offset=self.last_update+1,limit=10,timeout=1)
        if len(updates):
            self.last_update = updates[-1]["update_id"]
            messages = []
            for i in updates:
                messages.append(i["message"])
            return messages

    def loop(self,update_period):
        while True:
            time.sleep(update_period)

    def start(self,update_period=120):
        thread = threading.Thread(target=self.loop, args=(update_period,))
        thread.start()
