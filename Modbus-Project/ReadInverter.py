#!/usr/bin/env python
from SunnyInverter import sma_Inverter
import time
import configparser
import argparse
from datetime import datetime
import telepot
from telepot.loop import MessageLoop
import telepot.api
import urllib3
telepot.api._pools = {
    'default': urllib3.PoolManager(num_pools=3, maxsize=10, retries=3, timeout=30),
}
telepot.api._onetime_pool_spec = (urllib3.PoolManager, dict(num_pools=1, maxsize=1, retries=3, timeout=30))

class sma_EnergyMeter:
    def __init__(self):
        print("created sma_Energymeter"+str(self))

def current_time():
    return datetime.now()

def handle(msg):
    global bot
    chat_id = msg['chat']['id']
    command = msg['text']
    print(str(current_time())+': Got command: '+str(command))

    try:
        send_string = "not recognized command"
        if command == "/power":
            send_string = MyInverter.modbus.read_string("totalPower")

        elif command == "/energy":
            send_string =  MyInverter.modbus.read_string("todayEnergy")

        elif command == "/einspeisung":
            send_string =  MyInverter.modbus.read_string("LeistungEinspeisung")

        elif command == "/bezug":
            send_string =  MyInverter.modbus.read_string("LeistungBezug")

        elif command == "/all":
            send_string = MyInverter.modbus.read_string("totalPower")+"\n"+MyInverter.modbus.read_string("todayEnergy")
        
        elif command == "/ip":
            send_string = "IP Address: "+str(MyInverter.ipAddress)
        
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


parser = argparse.ArgumentParser(description='SMA Inverter Modbus reader.')
parser.add_argument("-ip", help="ipAddress of the Inverter")
args = parser.parse_args()

MyEnergyMeter = sma_EnergyMeter()

defaultInverterIP = "192.168.178.113" # Sunny Boy storage
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