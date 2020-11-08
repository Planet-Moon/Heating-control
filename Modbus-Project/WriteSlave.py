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


class sma_EnergyMeter:
    def __init__(self):
        print("created sma_Energymeter"+str(self))

class sma_Inverter:
    def __init__(self):
        self.serialnumber = 0
        self.susyID = 0
        self.UnitID = 1
        self.Model = 0
        self.operationHealth = 0
        self.totalPower = 0 # W
        self.todayPower = 0 # Wh
        self.timeZone = 0

        self.UnitID_Register = modbus_register(42109,4,1)
        self.MACAddress_Register = modbus_register(40497,1,self.UnitID)
        self.Model_Register = modbus_register(30053,2,self.UnitID)
        self.get_pysical_data()

        self.operationHealth_Register = modbus_register(30201,2,self.UnitID)
        self.get_operationHealth()

        self.totalPower_Register = modbus_register(30775,2,self.UnitID)
        self.get_totalPower()

        self.todayPower_Register = modbus_register(30535,2,self.UnitID)
        self.get_todayPower()

        self.timeZone_Register = modbus_register(40003,2,self.UnitID)
        self.get_timeZone()

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

    def get_todayPower(self):
        todayPower_response = self.todayPower_Register.get_data()
        self.todayPower = todayPower_response[0] * 65536 + todayPower_response[1]
        return self.todayPower

    def get_timeZone(self):
        timeZone_response = self.timeZone_Register.get_data()
        self.timeZone = timeZone_response[0] * 65536 + timeZone_response[1]
        return self.timeZone

class modbus_register:
    def __init__(self,address,length,unitID):
        self.address = address
        self.length = length
        self.unitID = unitID
        self.response = []
        self.data = []    

    def read(self):
        global client
        self.response = client.read_holding_registers(self.address,count=self.length, unit=self.unitID)
        return self.response

    def get_data(self):
        self.read()
        try: 
            self.data = self.response.registers
            return self.data
        except:
            return

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
        
MyEnergyMeter = sma_EnergyMeter()

MyInverter = sma_Inverter()
print("MyInverter.serialnumber: "+str(MyInverter.serialnumber))
print("MyInverter.operationHealth: "+str(MyInverter.operationHealth))

while True:
    current_power = MyInverter.get_totalPower()
    print("Current Power: "+str(current_power)+" W")
    print("Current Power * 3.5: "+str(current_power * 3.5)+" W")
    print("Power today: "+str(MyInverter.get_todayPower())+" Wh")
    time.sleep(15)