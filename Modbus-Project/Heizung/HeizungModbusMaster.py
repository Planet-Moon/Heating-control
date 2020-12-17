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
import codecs

def readConfig(configFilePath):
    global bot_token, modbusServerIP, modbusServerPort, modbusServerRegister, dataFileName, args, logFileName
    config = configparser.RawConfigParser(inline_comment_prefixes="#")
    readConfig = config.read_file(codecs.open(configFilePath, "r", "utf8"))

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
    dataFilePath = config.get("dataFile","path")
    dataFileName = str(dataFilePath+"/"+dataFileName)
    
    logFilePath = config.get("logFile","path")
    logFileName = config.get("logFile","name")
    logFileName = str(logFilePath+"/"+logFileName)
    pass

def writeLog(severity, message):
    message = message.replace("\n", "\\n")
    with open(logFileName, "a") as outfile:
        outfile.write("{{\"time\":{}, \"severity\":{}, \"message\":{}}}\n".format(datetime.now(), severity, message))
    outfile.close()

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
    writeLog(1, "Bot is listening")

class telegramClientsClass:
    def __init__(self, fileName="data.json"):
        self.clients = {}
        self.fileName = fileName
        self.readFromFile()
        pass

    def newClient(self, id, firstName, lastName, timeAdded):
        if not self.clientExists(id):
            self.clients[id] = self.telegramChatIDClass(firstName, lastName, timeAdded)

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
            writeLog(2, "Error reading from file "+str(e))
        if data:
            for i in data["clients"]:
                j = data["clients"][i]
                self.newClient(id=i, firstName=j["firstName"], lastName=j["lastName"], timeAdded=j["timeAdded"])
                if "shower" in j:
                    k = j["shower"]
                    self.clients[i].shower = self.clients[i].createShowerClass()
                    m = self.clients[i].shower
                    m.notifyTemperature=k["notifyTemperature"]
                    m.nextNotifyTime=k["nextNotifyTime"]
                    m.notifyInterval=k["notifyInterval"]
                    m.ignoreNight=k["ignoreNight"]
                    m.notify=k["notify"]
                    m.notifyAllowed=k["notifyAllowed"]
                    m.notifyMessage=k["notifyMessage"]
                else:
                    self.clients[i].shower = self.clients[i].createShowerClass()

    def saveToFile(self):
        try:
            with open(self.fileName, "w") as outfile:
                json.dump(self, outfile, default=self.parseObjJson, sort_keys=True, indent=4, check_circular=True)
                pass
        except Exception as e:
            print("Error writing to file: " + str(e))

    def parseObjJson(self, Obj):
        try:
            retVal = Obj.__dict__
        except Exception as e:
            print("Error parsing Object: "+str(e))
        return retVal

    class telegramChatIDClass:
        def __init__(self, firstName, lastName, timeAdded):
            self.firstName = firstName
            self.lastName = lastName
            self.timeAdded = timeAdded
            self.nightModeStart = str(time(hour=23))
            self.nightModeEnd = str(time(hour=6))
            self.nightTime = self.checkNightTime()
            pass

        def strToDateTimeObj(self, dateTimeString, simple=False):
            if not simple:
                return datetime.strptime(dateTimeString,"%Y-%m-%d %H:%M:%S.%f")
            else:
                return datetime.strptime(dateTimeString,"%H:%M:%S")

        def strToDeltaTimeObj(self, deltaTimeSring):
            _datetime = datetime.strptime(deltaTimeSring,"%H:%M:%S")
            return timedelta(hours=_datetime.hour, minutes=_datetime.minute, seconds=_datetime.second)

        def checkNightTime(self):
            currentTime = datetime.now()
            currentTime = (1900, 1, 1, currentTime.hour, currentTime.minute, currentTime.second)
            currentTime = datetime(*currentTime)
            _nightModeStart = self.strToDateTimeObj(self.nightModeStart, True)
            _nightModeEnd = self.strToDateTimeObj(self.nightModeEnd, True)
            if currentTime > _nightModeStart or currentTime < _nightModeEnd:
                self.nightTime = True
                return True
            else:
                self.nightTime = False
                return False

        def calcNextNotify(self, attrib):
                deltaNotifiedTime = self.strToDeltaTimeObj(attrib.notifyInterval)
                currentTime = datetime.now()
                attrib.nextNotifyTime = str(currentTime + deltaNotifiedTime)

        def checkNotifyAllowed(self, attrib):
            _nextNotifyTime = self.strToDateTimeObj(attrib.nextNotifyTime)
            if datetime.now() > _nextNotifyTime:
                attrib.notifyAllowed = True
                return True
            else:
                attrib.notifyAllowed = False
                return False

        def notify(self, attrib, force=False):
            retrunString = ""
            if (not self.checkNightTime() and self.checkNotifyAllowed(attrib)) or force:
                if self._isLarger(self.getSensorValue(attrib), float(attrib.notifyTemperature)):
                    print("ShowerMessage to "+self.firstName+" "+self.lastName)
                    writeLog(3, "ShowerMessage to "+self.firstName+" "+self.lastName)
                    self.calcNextNotify(attrib)
                    retrunString += attrib.notifyMessage
            return retrunString

        def createShowerClass(self):
            self.shower = self.showerClass()
            self.shower.notifyAllowed = self.checkNotifyAllowed(self.shower)
            return self.shower

        def _isLarger(self, value1, value2):
            return value1 > value2

        def getSensorValue(self, attrib):
            retVal = None
            while not retVal:
                retVal = HeizungModbusServer.register[attrib.modbusRegisterName].value
                sleep(10)
            return HeizungModbusServer.register[attrib.modbusRegisterName].value

        class showerClass:
            def __init__(self, notifyTemperature=50, nextNotifyTime=str(datetime.now()), notifyInterval=str(timedelta(hours=4, seconds=0)), ignoreNight=False, notify=True):
                self.notifyTemperature = notifyTemperature
                self.nextNotifyTime = nextNotifyTime
                self.notifyInterval = notifyInterval
                self.ignoreNight = ignoreNight
                self.notify = notify
                self.notifyAllowed = True
                self.notifyMessage = "Safe to shower!\n"
                self.modbusRegisterName = "TSP.oben2"

def clientsHandle(msg):
    try:
        last_name = msg['chat']['last_name']
    except: 
        last_name = ""
    telegramClients.newClient(id=str(msg['chat']['id']),
        firstName=msg['chat']['first_name'],
        lastName=last_name,
        timeAdded=msg["date"])
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
    writeLog(3, "Got message: \""+str(messageText)+"\" from chatID "+chat_id) 

    send_string = ""

    if "/all" in commandDict:
        try: 
            response = HeizungModbusServer.read_all()
        except:
            send_string += "Error reading modbus"
        interString = []
        for i in response:
            interString.append("{}: {}{}".format(*i)) 
        send_string = "\n".join(interString)
        pass

    if "/showertemp" in commandDict:
        if not hasattr(currentClient, "shower"):
            currentClient.createShowerClass()
        if commandDict["/showertemp"]:
            currentClient.shower.notifyTemperature = round(float(commandDict["/showertemp"]),2)
            currentClient.shower.nextNotifyTime = str(datetime.now())
            send_string += "Shower temperature set to "+str(currentClient.shower.notifyTemperature)+"°C\n"
            notifyString = currentClient.notify(currentClient.shower, force=False)
            if notifyString:
                send_string += notifyString
        else:
            send_string += "Current shower temperature is "+str(currentClient.shower.notifyTemperature)+"°C\n"
        pass
    
    if not send_string:
        send_string = "not recognized command"

    telegramClients.saveToFile()
    bot.sendMessage(chat_id, send_string)
    writeLog(3, "Sent message: \"{}\" to ChatID {}".format(send_string, chat_id))
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
        HeizungModbusServer.read_value("TSP.oben2")
        for i in telegramClients.clients:
            notifyMessage = ""
            checkClient = telegramClients.clients[i]
            notifyMessage += checkClient.notify(checkClient.shower)
            if notifyMessage:
                bot.sendMessage(i, notifyMessage)
        telegramClients.saveToFile()
        sleep(600)
    if args.noBot:
        print(str(HeizungModbusServer.read_all()))
        print("Done.")
