from Modbus import modbus_device
import TypeConversion as TC
from time import sleep
import configparser
import argparse
import json
from os import path, chdir
from datetime import datetime
import telepot
from telepot.loop import MessageLoop
import telepot.api
import urllib3

def readConfig(configFilePath):
    global bot_token, modbusServerIP, modbusServerRegister, dataFileName, args
    config = configparser.RawConfigParser()
    readConfig = config.read(configFilePath)

    if not args.noBot:
        bot_token = config.get("telegrambot","token")

    modbusServerIP = config.get("modbusServer","ip")
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

def dataJsonInit():
    global data, dataFileName
    try:
        with open(dataFileName) as json_file:
            data = json.load(json_file)
            if not data:
                data["clients"] = []
    except:
        data = {}

def clientsHandle(msg):
    global data, dataFileName
    client_missing = True

    for i in data["clients"]:
        if i["id"] == msg['chat']['id']:
            client_missing = False
            break
        
    if client_missing:
        data["clients"].append({"id": msg['chat']['id'], "name": msg['chat']['first_name']+" "+msg['chat']['last_name'], "timeAdded": msg["date"]})
        with open(dataFileName, "w") as outfile:
            print(data)
            json.dump(data, outfile)


def telegramBotHandle(msg):
    global bot
    chat_id = msg['chat']['id']
    command = msg['text']
    print(str(datetime.now())+': Got command: '+str(command))
    clientsHandle(msg)
    try: 
        send_string = "not recognized command"
        if command == "/all":
            data = HeizungModbusServer.read_all()
            interString = []
            for i in data:
                interString.append("{}: {}{}".format(*i)) 
            send_string = "\n".join(interString)
            pass
        bot.sendMessage(chat_id, send_string)
    except:
        bot.sendMessage(chat_id, "Error reading modbus")

def main():
    global HeizungModbusServer, registerData, args
    parser = argparse.ArgumentParser(description='SMA Inverter Modbus reader.')
    parser.add_argument("--noBot", help="Don't run telegramBot", action="store_true")
    args = parser.parse_args()
    readConfig("config.cfg")

    HeizungModbusServer = modbus_device(modbusServerIP)
    for i in modbusServerRegister:
        HeizungModbusServer.newRegister(name=i["name"], address=i["address"], length=i["length"], factor=i["factor"], unit=i["unit"])
        HeizungModbusServer.read_string(name=i["name"])        
    
    dataJsonInit()
    if not args.noBot:
        telegramBotInit()
    pass

if __name__ == "__main__":
    if __debug__:
        chdir("Modbus-Project/Heizung")
    main()
    while not args.noBot:
        sleep(20)
    if args.noBot:
        print(str(HeizungModbusServer.read_all()))
        print("Done.")
