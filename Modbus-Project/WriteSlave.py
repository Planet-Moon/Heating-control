#!/usr/bin/env python
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
import time

ModbusTargetIP = "192.168.178.114"
client = ModbusClient(ModbusTargetIP)
try:
    client.connect()
    print("Connected!")
except:
    print("Connection failed!")
    exit()
MAC_Address_Register = 40497

class sma_inverter:
    def __init__(self):
        self.serialnumber = 0
        self.susyID = 0
        self.UnitID = 1
        self.Model = 0
        self.operationHealth = 0
        self.totalPower = 0

        self.UnitID_Register = modbus_register(42109,4,1)
        self.MACAddress_Register = modbus_register(40497,1,self.UnitID)
        self.Model_Register = modbus_register(30053,2,self.UnitID)
        self.get_pysical_data()

        self.operationHealth_Register = modbus_register(30201,2,self.UnitID)
        self.get_operationHealth()

        self.totalPower_Register = modbus_register(30775,2,self.UnitID)
        self.get_totalPower()

    def get_pysical_data(self):
        UnitID_response = self.UnitID_Register.get_data()
        self.serialnumber = UnitID_response[0]*65536 + UnitID_response[1]
        self.susyID = UnitID_response[2]
        self.UnitID = UnitID_response[3]
        Model_response = self.Model_Register.get_data()
        self.Model = Model_response[0]*65536 + Model_response[1]
        return UnitID_response

    def get_operationHealth(self):
        operationHealth_response = self.operationHealth_Register.get_data()
        self.operationHealth = operationHealth_response[0]*65536 + operationHealth_response[1]
        return self.operationHealth

    def get_totalPower(self):
        totalPower_response = self.totalPower_Register.get_data()
        self.totalPower = totalPower_response[0] * 65536 + totalPower_response[1]
        return self.totalPower   

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

MySMAInverter = sma_inverter()

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