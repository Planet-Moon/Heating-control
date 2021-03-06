from Modbus import modbus_device
import TypeConversion as TC
from time import sleep
import argparse
import json
import os
from datetime import datetime, timedelta, time
import telepot
from telepot.loop import MessageLoop
import telepot.api
import urllib3
from re import findall as RegexFindAll
import codecs
from SMA_SunnyBoy import SMA_SunnyBoy
from SMA_StorageBoy import SMA_StorageBoy
import sys

# Define globals
telegramClients = None
bot_token = None
modbusDict = None
smaDict = None
dataFileName = None
args = None
logFileName = None
bot = None
HeizstabData = None

def readConfig(configFilePath):
    global bot_token, modbusDict, smaDict, dataFileName, args, logFileName, HeizstabData
    data = None
    try:
        with open(configFilePath, "r", encoding='utf-8') as outfile:
            data = json.load(outfile)
    except Exception as e:
        print("Error reading from file: " + str(e))
        sys.exit(-1)
    if data:
        if not args.noBot:
            try:
                bot_token = data.get("TelegramBot").get("token")
            except:
                bot_token = None
                args.noBot = True

        modbusDict = {}
        modbusData = data.get("Modbus")
        for i in modbusData:
            temp_modbus = modbusData.get(i)
            modbusDict[i] = modbus_device(ipAddress=temp_modbus.get("ip"), port=temp_modbus.get("port"))
            modbusRegisters = temp_modbus.get("registers")
            for j in modbusRegisters:
                modbusDict.get(i).newRegister(j.get("name"),
                    int(j.get("address")),
                    int(j.get("length")),
                    factor=float(j.get("factor")),
                    type_=j.get("type"),
                    unit=j.get("unit"),
                    signed=bool(j.get("signed")))
                print(modbusDict[i].read_string(j.get("name")))
                pass

        smaDict = {}
        smaDict["Solar"] = {}
        smaDict["Batterie"] = {}
        smaData = data.get("SMA_Inverter").get("Solar")
        counter = 0
        for i in smaData:
            smaDict["Solar"][i.get("name")] = SMA_SunnyBoy(str(i.get("ip")))
            print(str(smaDict["Solar"][i.get("name")])+", ip: "+smaDict["Solar"][i.get("name")].ipAddress)
            counter += 1

        smaData = data.get("SMA_Inverter").get("Batterie")
        for i in smaData:
            smaDict["Batterie"][i.get("name")] = SMA_StorageBoy(str(i.get("ip")))
            print(str(smaDict["Batterie"][i.get("name")])+", ip: "+smaDict["Batterie"][i.get("name")].ipAddress)
            pass

        HeizstabData = data.get("Heizstab")
        modbusDict.get("Heizung").write_register("Heizstab_SollTemp", int(HeizstabData.get("Solltemp")))

        dataFilePath = data.get("dataFile").get("path")
        dataFileName = data.get("dataFile").get("name")
        dataFileName = str(dataFilePath+"/"+dataFileName)

        logFilePath = data.get("logFile").get("path")
        logFileName = data.get("logFile").get("name")
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

    def newClient(self, id:str, timeAdded:int, firstName="", lastName="", groupName=""):
        if not self.clientExists(id):
            self.clients[id] = self.telegramChatIDClass(timeAdded, firstName, lastName, groupName)

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
                try:
                    self.newClient(id=i, firstName=j["firstName"], lastName=j["lastName"], timeAdded=j["timeAdded"])
                except:
                    self.newClient(id=i, groupName=j["groupName"], timeAdded=j["timeAdded"])
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
        def __init__(self, timeAdded:int, firstName="", lastName="", groupName=""):
            if firstName:
                self.firstName = firstName
                self.lastName = lastName
            elif groupName:
                self.groupName = groupName
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

        def _isSmaller(self, value1, value2):
            return value1 < value2

        def _isEqual(self, value1, value2):
            return value1 == value2

        def getSensorValue(self, attrib):
            retVal = None
            while not retVal:
                retVal = modbusDict.get("Heizung").register[attrib.modbusRegisterName].value
                sleep(10)
            return modbusDict.get("Heizung").register[attrib.modbusRegisterName].value

        class showerClass:
            def __init__(self, notifyTemperature=50, nextNotifyTime=str(datetime.now()), notifyInterval=str(timedelta(hours=4, seconds=0)), ignoreNight=False, notify=True):
                self.notifyTemperature = notifyTemperature
                self.nextNotifyTime = nextNotifyTime
                self.notifyInterval = notifyInterval
                self.ignoreNight = ignoreNight
                self.notify = notify
                self.notifyAllowed = True
                self.notifyMessage = "Safe to shower!\n"
                self.modbusRegisterName = "SpeicherOben"

def clientsHandle(msg):
    chat_type = msg['chat']['type']
    if chat_type == 'private':
        try:
            last_name = msg['chat']['last_name']
        except:
            last_name = ""
        telegramClients.newClient(id=str(msg['chat']['id']),
            firstName=msg['chat']['first_name'],
            lastName=last_name,
            timeAdded=msg["date"])
    if chat_type == 'group':
        telegramClients.newClient(id=str(msg['chat']['id']),
            groupName=msg['chat']['title'],
            timeAdded=msg["date"])

def parseTelegramCommand(messageText):
    messageTextList = messageText.split(" ")
    commandDict = {}
    current_command = ""
    for i in messageTextList:
        command_temp = RegexFindAll(r"^\/[a-z0-9]*(?=[\s\@])?", i)
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
    content_type, a, b = telepot.glance(msg)
    del a, b
    clientsHandle(msg)
    commandDict = parseTelegramCommand(messageText)
    currentClient = telegramClients.clients[chat_id]
    print(str(datetime.now())+': Got message: '+str(messageText)+" from chatID "+chat_id)
    writeLog(3, "Got message: \""+str(messageText)+"\" from chatID "+chat_id)

    send_string = ""

    if "/all" in commandDict:
        calculate_total_power_draw()
        try:
            response = modbusDict.get("Heizung").read_all()
            interString = []
            for i in response:
                interString.append("{}: {}{}".format(*i))
            send_string += "Heizung:\n"
            send_string += "\n".join(interString)

            send_string += "\n------------------\n"
            send_string += "Solar:\n"
            send_string += smaDict.get("Solar").get("128").read_all()

            send_string += "\n------------------\n"
            send_string += "Batterie:\n"
            send_string += smaDict.get("Batterie").get("113").read_all()
        except:
            send_string += "Error reading modbus"
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

def SolarPowerToHeater():
    totalSolarPower = 0
    solarModbus = smaDict.get("Solar")
    heizungModbus = modbusDict.get("Heizung")
    heizungModbus.write_register("Heizstab_Ein_nAus", 1)
    for i in solarModbus:
        totalSolarPower += solarModbus.get(i).LeistungEinspeisung # LeistungEinspeisung identisch bei allen Wechselrichtern, wird vom Stromzähler gelesen
        break # nur der Wert des ersten Wechselrichters wird verwendet
    PowerLevels = HeizstabData.get("Leistungsstufen")
    for i in range(len(PowerLevels)-1,-1,-1):
        if float(PowerLevels[i].get("Leistung")) <= totalSolarPower:
            if args.debug:
                print("powerlevel is "+PowerLevels[i].get("Leistung"))
            for j in range(len(HeizstabData.get("modbusRegister"))):
                heizungModbus.write_register(HeizstabData.get("modbusRegister")[j], int(PowerLevels[i].get("modbusRegister")[j]))
            break
    pass

def init():
    global telegramClients
    readConfig("config.json")

    if not args.noBot:
        telegramClients = telegramClientsClass()
        telegramBotInit()
    pass

def calculate_total_power_draw():
    for key, value in smaDict.get("Solar").items():
        current_solar_inverter = value
    leistung_einspeisung = current_solar_inverter.LeistungEinspeisung
    leistung_bezug = current_solar_inverter.LeistungBezug
    leistung_solar = 0
    for i in smaDict.get("Solar"):
        current_solar_inverter = smaDict.get("Solar")[i]
        current_power = current_solar_inverter.power
        if current_power > 0:
            leistung_solar += current_power

    leistung_batterie = 0
    for i in smaDict.get("Batterie"):
        current_battery_inverter = smaDict.get("Batterie")[i]
        current_power = current_battery_inverter.power
        if current_power > 0:
            leistung_batterie += current_power

    aktueller_verbrauch = leistung_bezug + leistung_solar + leistung_batterie - leistung_einspeisung
    modbusDict.get("Heizung").write_register("AktuellerVerbrauch", aktueller_verbrauch)

if __name__ == "__main__":
    argsParse()
    if args.debug:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
    init()
    while True:
        if not args.noBot:
            modbusDict.get("Heizung").read_value("SpeicherOben")
            for i in telegramClients.clients:
                notifyMessage = ""
                checkClient = telegramClients.clients[i]
                # notifyMessage += checkClient.notify(checkClient.shower)
                if notifyMessage:
                    bot.sendMessage(i, notifyMessage)
            telegramClients.saveToFile()
        else:
            print(str(modbusDict.get("Heizung").read_all()))

        calculate_total_power_draw()

        SolarPowerToHeater()
        sleep(180)
