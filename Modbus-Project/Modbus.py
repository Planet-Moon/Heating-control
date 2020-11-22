from pymodbus.client.sync import ModbusTcpClient as ModbusClient
import TypeConversion as TC

class modbus_device(object):
    def __init__(self, ipAddress):
        self.client = ModbusClient(ipAddress)
        self.UnitID = 1
        try:
            self.client.connect()
            print("Connected!")
        except:
            print("Connection failed!")
            exit()

        self.register = {}
        pass

    def newRegister(self, name, address, length, signed=False, unit=""):
        self.register[name] = self.modbus_register(address, length, signed, unit)
        self.read(name)

    def read(self, name):
        try:
            return self.register[name].get_data(self.client, self.UnitID)
        except:
            print("Error reading register "+name)

    def read_value(self, name):
        try:
            return TC.list_to_number(self.read(name), signed=self.register[name].signed)
        except:
            print("Error reading value from register "+name) 

    def read_string(self, name):
        value = self.read_value(name)
        unit = self.register[name].unit
        return name+": "+str(value)+unit

    def read_all(self):
        ret_val = []
        for i in self.register:
            ret_val.append([i, self.read_value(i)])
            pass
        pass
        return ret_val

    class modbus_register:
        def __init__(self, address, length, signed, unit):
            self.address = address
            self.length = length
            self.response = []
            self.data = []
            self.error = 0
            self.signed = signed
            self.unit = unit

        def read(self,client, unitID):
            self.error = 0
            try:
                self.response = client.read_holding_registers(self.address,count=self.length, unit=unitID)
            except Exception as e:
                self.error = 1
                print("Error reading "+str(client)+", "+str(e))
            return self.response

        def get_data(self, client, unitID):
            self.read(client, unitID)
            try: 
                self.data = self.response.registers
                return self.data
            except:
                print("Error reading "+str(client.host)+", register "+str(self.address))
            pass