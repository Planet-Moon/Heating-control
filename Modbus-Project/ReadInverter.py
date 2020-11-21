#!/usr/bin/env python
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
import time
import configparser
import argparse
from math import floor
from datetime import datetime
import telepot
from telepot.loop import MessageLoop
import telepot.api
import urllib3
telepot.api._pools = {
    'default': urllib3.PoolManager(num_pools=3, maxsize=10, retries=3, timeout=30),
}
telepot.api._onetime_pool_spec = (urllib3.PoolManager, dict(num_pools=1, maxsize=1, retries=3, timeout=30))

def word_to_uint32(word): #big endian
    return word[0]*65536 + word[1]

def word_to_int32(word): #little endian
    word1 = word_to_uint32(word)
    if word1 & 0x80000000:
        positive = False
        word2 = -1*0x80000000 + (word1 & 0x7FFFFFFF)
    else:
        positive = True
        word2 = word1 & 0x7FFFFFFF
    return floor(word2)

class sma_EnergyMeter:
    def __init__(self):
        print("created sma_Energymeter"+str(self))

class sma_Inverter:
    def __init__(self, ipAddress):
        self.serialnumber = 0
        self.susyID = 0
        self.UnitID = 1
        self.Model = 0
        self.operationHealth = 0
        self.totalPower = 0 # W
        self.todayEnergy = 0 # Wh
        self.timeZone = 0
        self.error = 0

        self._change_IP(ipAddress)

        try: 
            self.get_data("all")
        except Exception as e:
            print(str(current_time())+": Error - Initialisation of "+self.ipAddress+" failed!, "+str(e))

    def _connect_IP(self):
        self.client = ModbusClient(self.ipAddress)
        try:
            self.client.connect()
            print("Connected!")
        except:
            print("Connection failed!")
            exit()
        self._Init_Modbus_Registers()

    def _Init_Modbus_Registers(self):
        self.modbus = {}
        self.modbus["UnitID"] = modbus_register(self.client,42109,4,1)
        self.modbus["MACAddress"] = modbus_register(self.client,40497,1,self.UnitID)
        self.modbus["Model"] = modbus_register(self.client,30053,2,self.UnitID)
        self.modbus["operationHealth"] = modbus_register(self.client,30201,2,self.UnitID)
        self.modbus["totalPower"] = modbus_register(self.client,30775,2,self.UnitID)
        self.modbus["todayEnergy"] = modbus_register(self.client,30535,2,self.UnitID)
        self.modbus["timeZone"] = modbus_register(self.client,40003,2,self.UnitID)
        pass
    
    def _change_IP(self, ipAddress):
        self.ipAddress = ipAddress
        self._connect_IP()

    def get_data(self,dataName):
        if dataName == "pysicalData" or dataName == "all":
            UnitID_response = self.modbus["UnitID"].get_data()
            self.serialnumber = UnitID_response[0]*65536 + UnitID_response[1]
            self.susyID = UnitID_response[2]
            self.UnitID = UnitID_response[3]
            Model_response = self.modbus["Model"].get_data()
            self.Model = word_to_uint32(Model_response)
            if dataName != "all":
                return UnitID_response

        elif dataName == "operationHealth" or dataName == "all":
            operationHealth_response = self.modbus["operationHealth"].get_data()
            self.operationHealth = word_to_uint32(operationHealth_response)
            if dataName != "all":
                return self.operationHealth

        elif dataName == "totalPower" or dataName == "all":
            totalPower_response_byte = self.modbus["totalPower"].get_data()
            self.totalPower = word_to_int32(totalPower_response_byte)
            if dataName != "all":
                return self.totalPower

        elif dataName == "todayEnergy" or dataName == "all":
            todayEnergy_response = self.modbus["todayEnergy"].get_data()
            self.todayEnergy = word_to_uint32(todayEnergy_response)
            if dataName != "all":
                return self.todayEnergy

        elif dataName == "timeZone" or dataName == "all":
            timeZone_response = self.modbus["timeZone"].get_data()
            self.timeZone = word_to_uint32(timeZone_response)
            if dataName != "all":
                return self.timeZone

        return 0

class modbus_register:
    def __init__(self,client,address,length,unitID):
        self.client = client
        self.address = address
        self.length = length
        self.unitID = unitID
        self.response = []
        self.data = []
        self.error = 0

    def read(self):
        self.error = 0
        try:
            self.response = self.client.read_holding_registers(self.address,count=self.length, unit=self.unitID)
        except Exception as e:
            self.error = 1
            print(str(current_time())+": Error reading "+str(self.client)+", "+str(e))
        return self.response

    def get_data(self):
        self.read()
        try: 
            self.data = self.response.registers
            return self.data
        except:
            print("Error reading "+str(self.client.host)+", register "+str(self.address))
        pass

def current_time():
    return datetime.now()

def handle(msg):
    global bot
    chat_id = msg['chat']['id']
    command = msg['text']
    print(str(current_time())+': Got command: '+str(command))

    try:
        if command == "/power":
            bot.sendMessage(chat_id, str(MyInverter.get_data("totalPower"))+" W")

        elif command == "/energy":
            bot.sendMessage(chat_id, str(MyInverter.get_data("todayEnergy"))+" Wh")

        elif command == "/all":
            send_string = "Power: "+str(MyInverter.get_data("totalPower"))+" W\nEnergy: "+ str(MyInverter.get_data("todayEnergy"))+" Wh"
            bot.sendMessage(chat_id, send_string)

        elif command == "/ip ":
            ip = msg["text"][2:]
            pass

    except:
        bot.sendMessage(chat_id, "Error reading modbus")

def TelegramBot(modbusClient):
    global bot
    config = configparser.RawConfigParser()
    configFilePath = "telegrambot.cfg"
    readConfig = config.read(configFilePath)
    bot_token = config.get("telegrambot","token")
    bot = telepot.Bot(bot_token)
    botInfo = bot.getMe()
    MessageLoop(bot,handle).run_as_thread()
    print("Bot is listening ...")


parser = argparse.ArgumentParser(description='SMA Inverter Modbus reader.')
parser.add_argument("-ip", help="ipAddress of the Inverter")
args = parser.parse_args()

MyEnergyMeter = sma_EnergyMeter()

defaultInverterIP = "192.168.178.114"
if not args.ip:
    InverterIp = defaultInverterIP
else: 
    InverterIp = args.ip
MyInverter = sma_Inverter(InverterIp)
print("MyInverter.serialnumber: "+str(MyInverter.serialnumber))
print("MyInverter.operationHealth: "+str(MyInverter.operationHealth))

bot = ""
TelegramBot(MyInverter)

while True:
    # current_power = MyInverter.get_totalPower()
    # print("Current Power: "+str(current_power)+" W")
    # print("Current Power * 3.5: "+str(current_power * 3.5)+" W")
    # print("Energy today: "+str(MyInverter.get_todayEnergy())+" Wh")
    # print("System Energy today: "+str(MyInverter.get_todayEnergy() * 3.5)+" Wh")
    time.sleep(15)