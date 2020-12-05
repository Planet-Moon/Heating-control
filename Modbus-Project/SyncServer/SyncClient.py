from Modbus import modbus_device
import TypeConversion as TC
from time import sleep

testList = TC.number_to_wordList(1290)

ModbusServer = modbus_device("192.168.178.43", "502")
ModbusServer.newRegister("test1", address=0, length=4)
ModbusServer.newRegister("write", address=90, length=2)
ModbusServer.newRegister("all", address=0, length=125)
ModbusServer.close()
readValueOld = None
counter = [0, 0]

while True:
    if False:
        while True:
            ModbusServer.connect()
            readValue = ModbusServer.read("test1")
            writeValue = readValue
            breakpoint = 0
            for i in range(len(readValue)):
                writeValue[i] = readValue[i] + i
            ModbusServer.write_register("test1",writeValue)
            ModbusServer.close()
            pass
        pass
    elif True:
        ModbusServer.connect()
        readValue = ModbusServer.read("test1")
        if readValue != readValueOld:
            print("readValue: " + str(readValue))
        readValueOld = readValue
        ModbusServer.write_register("write",counter)
        print("write: "+str(ModbusServer.read("write")))
        print("all: "+str(ModbusServer.read("all")))
        ModbusServer.close()
    counter = [x+1 for x in counter]
    sleep(20)
pass