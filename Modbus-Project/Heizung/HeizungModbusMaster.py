from Modbus import modbus_device
import TypeConversion as TC
from time import sleep
import configparser
import argparse
import json
from os import path, chdir
from datetime import datetime, timedelta, time
import telepot
from telepot.loop import MessageLoop
import telepot.api
import urllib3
from re import findall as RegexFindAll

def readConfig(configFilePath):
    global bot_token, modbusServerIP, modbusServerPort, modbusServerRegister, dataFileName, args
    config = configparser.RawConfigParser(inline_comment_prefixes="#")
    readConfig = config.read(configFilePath)

    if not args.noBot:
        bot_token = config.get("telegrambot","token")

    modbusServerIP = config.get("modbusServer","ip")
    try:
        modbusServerPort = config.get("modbusServer","port")
    except:
        pass
    modbusServerRegisters = config.get("modbusServer","registers")
    modbusServerRegisters = modbusServerRegisters.split("\n")
    del modbusServerRegisters[0]
    modbusServerRegister = []
    for i in modbusServerRegisters:
        temp = i.split(", ")
        modbusServerRegister.append({"name": temp[0], "address": int(temp[1]), "length": int(temp[2]), "factor": float(temp[3]), "unit": temp[4]})

    dataFileName = config.get("dataFile","name")
    pass

def telegramBotInit():
    global bot

    telepot.api._pools = {
        'default': urllib3.PoolManager(num_pools=3, maxsize=10, retries=3, timeout=30),
    }
    telepot.api._onetime_pool_spec = (urllib3.PoolManager, dict(num_pools=1, maxsize=1, retries=3, timeout=30))

    bot = telepot.Bot(bot_token)
    botInfo = bot.getMe()
    MessageLoop(bot,telegramBotHandle).run_as_thread()
    print("Bot is listening ...")

class telegramClientsClass:
    def __init__(self, fileName="data.json"):
        self.clients = {}
        self.fileName = fileName
        self.readFromFile()
        pass

    def newClient(self, id, name, timeAdded):
        if not self.clientExists(id):
            self.clients[id] = self.telegramChatIDClass(name, timeAdded)

    def clientExists(self, id):
        if id in self.clients:
            return True
        else:
            return False

    def readFromFile(self):
        data = None
        try:
            with open(self.fileName, "r") as outfile:
                data = json.load(outfile)
        except Exception as e:
            print("Error reading from file" + str(e))
        if data:
            for i in data["clients"]:
                j = data["clients"][i]
                self.newClient(id=i, name=j["name"], timeAdded=j["timeAdded"])
                self.clients[i].shower["temperature"] = j["shower"]["temperature"]
                self.clients[i].shower["lastNotified"] = j["shower"]["lastNotified"]

    def saveToFile(self):
        try:
            with open(self.fileName, "w") as outfile:
                json.dump(self, outfile, default=lambda o: o.__dict__, sort_keys=True, indent=4)
            pass
        except Exception as e:
            print("Error writing to file" + str(e))

    class telegramChatIDClass:
        def __init__(self, name, timeAdded):
            self.name = name
            self.timeAdded = timeAdded
            self.nightModeStart = str(time(hour=23))
            self.nightModeEnd = str(time(hour=6))
            self.shower = {"temperature": 50, "lastNotified": str(datetime.now()), "notifyInterval": str(timedelta(hours=4, seconds=0)), "ignoreNight": False}

def clientsHandle(msg):
    telegramClients.newClient(id=str(msg['chat']['id']), name=msg['chat']['first_name']+" "+msg['chat']['last_name'],timeAdded=msg["date"])
    pass

def parseTelegramCommand(messageText):
    messageTextList = messageText.split(" ")
    commandDict = {}
    current_command = ""
    for i in messageTextList:
        command_temp = RegexFindAll("^\/\S+", i)
        if command_temp:
            current_command = command_temp[0]
            commandDict[current_command] = {}
        else:
            argument_temp = i.split("=")
            if len(argument_temp) == 2:
                commandDict[current_command][argument_temp[0]] = argument_temp[1]
            elif len(argument_temp) == 1:
                commandDict[current_command] = argument_temp[0]
            pass
    return commandDict

def telegramBotHandle(msg):
    global bot
    chat_id = str(msg['chat']['id'])
    messageText = msg['text']
    content_type, _, _ = telepot.glance(msg)
    clientsHandle(msg)
    commandDict = parseTelegramCommand(messageText)
    currentClient = telegramClients.clients[chat_id]
    print(str(datetime.now())+': Got message: '+str(messageText)+" from chatID "+chat_id)    
    
    try: 
        send_string = ""

        if "/all" in commandDict:
            response = HeizungModbusServer.read_all()
            interString = []
            for i in response:
                interString.append("{}: {}{}".format(*i)) 
            send_string = "\n".join(interString)
            pass

        if "/showertemp" in commandDict:
            if commandDict["/showertemp"]:
                currentClient.shower["temperature"] = round(float(commandDict["/showertemp"]),2)
                currentClient.shower["lastNotified"] = str(datetime.now())
                send_string += "Shower temperature set to "+str(currentClient.shower["temperature"])+"°C\n"
            else:
                send_string += "Current shower temperature is "+str(currentClient.shower["temperature"])+"°C\n"
            pass
        
        if not send_string:
            send_string = "not recognized command"

        telegramClients.saveToFile()
        bot.sendMessage(chat_id, send_string)
    except:
        bot.sendMessage(chat_id, "Error reading modbus")
    pass

def argsParse():
    global args
    parser = argparse.ArgumentParser(description='SMA Inverter Modbus reader.')
    parser.add_argument("--debug", help="Run with debug features", action="store_true")
    parser.add_argument("--noBot", help="Don't run telegramBot", action="store_true")
    args = parser.parse_args()

def main():
    global HeizungModbusServer, registerData, telegramClients
    readConfig("config.cfg")

    HeizungModbusServer = modbus_device(ipAddress=modbusServerIP, port=modbusServerPort)
    for i in modbusServerRegister:
        HeizungModbusServer.newRegister(name=i["name"], address=i["address"], length=i["length"], factor=i["factor"], unit=i["unit"])
        HeizungModbusServer.read_string(name=i["name"])        
    
    if not args.noBot:
        telegramClients = telegramClientsClass()
        telegramBotInit()
    pass

if __name__ == "__main__":
    argsParse()
    if args.debug:
        chdir("Modbus-Project/Heizung")
    main()
    while not args.noBot:
        waterTemperature = HeizungModbusServer.read_value("TSP.oben2")
        for i in telegramClients.clients:
            if waterTemperature > telegramClients.clients[i].shower["temperature"]:
                lastNotifiedTime = datetime.strptime(telegramClients.clients[i].shower["lastNotified"],"%Y-%m-%d %H:%M:%S.%f")
                deltaNotifiedTime = datetime.strptime(telegramClients.clients[i].shower["notifyInterval"],"%H:%M:%S")
                deltaNotifiedTime = timedelta(hours=deltaNotifiedTime.hour, minutes=deltaNotifiedTime.minute, seconds=deltaNotifiedTime.second)
                currentTime = datetime.now()
                timeNextNotify = lastNotifiedTime + deltaNotifiedTime
                nightMode = False

                if currentTime < datetime.strptime(telegramClients.clients[i].nightModeEnd,"%H:%M:%S"):
                    nightMode = True
                elif currentTime > datetime.strptime(telegramClients.clients[i].nightModeStart,"%H:%M:%S"):
                    nightMode = True

                if timeNextNotify < currentTime and not nightMode:
                    print("ShowerMessage to "+telegramClients.clients[i].name)
                    telegramClients.clients[i].shower["lastNotified"] = str(datetime.now())
                    bot.sendMessage(i, "Safe to shower!")
                    pass
        telegramClients.saveToFile()
        sleep(600)
    if args.noBot:
        print(str(HeizungModbusServer.read_all()))
        print("Done.")
