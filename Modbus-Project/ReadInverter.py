#!/usr/bin/env python
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
import time
import configparser
from math import floor
import telepot
from telepot.loop import MessageLoop
import telepot.api
import urllib3
telepot.api._pools = {
    'default': urllib3.PoolManager(num_pools=3, maxsize=10, retries=3, timeout=30),
}
telepot.api._onetime_pool_spec = (urllib3.PoolManager, dict(num_pools=1, maxsize=1, retries=3, timeout=30))

def word_to_uint32(word): #little endian
    return word[0]*65536 + word[1]

def word_to_int32(word): #little endian
    word = word_to_uint32(word)
    if word & 0x80000000:
        word = -1 * (word & 0x7FFFFFFF)/2
    else: 
        word = floor((word & 0x7FFFFFFF)/2)
    return word

class sma_EnergyMeter:
    def __init__(self):
        print("created sma_Energymeter"+str(self))

class sma_Inverter:
    def __init__(self, ipAddress):
        self.ipAddress = ipAddress
        self.client = ModbusClient(self.ipAddress)
        try:
            self.client.connect()
            print("Connected!")
        except:
            print("Connection failed!")
            exit()
        self.serialnumber = 0
        self.susyID = 0
        self.UnitID = 1
        self.Model = 0
        self.operationHealth = 0
        self.totalPower = 0 # W
        self.todayEnergy = 0 # Wh
        self.timeZone = 0
        self.error = 0

        self.UnitID_Register = modbus_register(self.client,42109,4,1)
        self.MACAddress_Register = modbus_register(self.client,40497,1,self.UnitID)
        self.Model_Register = modbus_register(self.client,30053,2,self.UnitID)
        self.operationHealth_Register = modbus_register(self.client,30201,2,self.UnitID)
        self.totalPower_Register = modbus_register(self.client,30775,2,self.UnitID)
        self.todayEnergy_Register = modbus_register(self.client,30535,2,self.UnitID)
        self.timeZone_Register = modbus_register(self.client,40003,2,self.UnitID)

        try: 
            self.get_data("all")
        except Exception as e:
            print(str(current_time())+": Initialisation of "+self.ipAddress+" failed!, "+str(e))

    def get_data(self,dataName):
        if dataName == "pysicalData" or dataName == "all":
            UnitID_response = self.UnitID_Register.get_data()
            self.serialnumber = UnitID_response[0]*65536 + UnitID_response[1]
            self.susyID = UnitID_response[2]
            self.UnitID = UnitID_response[3]
            self.Model = word_to_uint32(Model_response)
            if dataName != "all":
                return UnitID_response

        elif dataName == "operationHealth" or dataName == "all":
            self.operationHealth = word_to_uint32(operationHealth_response)
            if dataName != "all":
                return self.operationHealth

        elif dataName == "totalPower" or dataName == "all":
            self.totalPower = word_to_int32(totalPower_response_byte)
            if dataName != "all":
                return self.totalPower

        elif dataName == "todayEnergy" or dataName == "all":
            self.todayEnergy = word_to_uint32(todayEnergy_response)
            if dataName != "all":
                return self.todayEnergy

        elif dataName == "timeZone" or dataName == "all":
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
            return

def current_time():
    return datetime.datetime.now()

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


MyEnergyMeter = sma_EnergyMeter()

InverterIP = "192.168.178.114"
MyInverter = sma_Inverter(InverterIP)
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
    print("uint {}".format(byte_to_uint16([32768,1])))
    time.sleep(15)