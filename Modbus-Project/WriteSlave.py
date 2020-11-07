#!/usr/bin/env python
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
import time

ModbusTargetIP = "192.168.178.114"
MAC_Address_Register = 40497

class modbus_register:
    def __init__(self,address,length):
        self.address = address
        self.length = length
        self.response = []
        self.data = []

    def read(self):
        global client
        self.response = client.read_holding_registers(self.address,count=self.length, unit=1)
        return self.response

    def get_data(self):
        self.read()
        self.data = self.response.registers
        return self.data

UnitID_Register = modbus_register(42109,4)

client = ModbusClient(ModbusTargetIP)
try:
    client.connect()
    print("Connected!")
except:
    print("Connection failed!")

def write_modbus(write_register, write_value):
    global client
    client.write_register(write_register, write_value)

def read_modbus(read_register, count):
    global client
    try:
        read_value = client.read_coils(read_register, count)
        return read_value
    except:
        print("modbus read of register "+str(read_register)+" failed!")    

def test():
    response = client.read_holding_registers(0x00,4,unit=1)
    print(response.registers)


#for i in range(0,255):
#    print("value at "+str(i)+": "+str(read_modbus(i)))

#print("value at "+str(Register_MAC_Address)+" = "+str(read_modbus(Register_MAC_Address)))
while True:
    #test = read_modbus(MAC_Address_Register, 1)
    test = client.read_holding_registers(42109,count=4, unit=1)
    try: 
        print(test.message)
    except:
        print("No return message")
    try: 
        print("1")
    except: 
        print("2")
    time.sleep(2)