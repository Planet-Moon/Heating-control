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

        self.newRegister("UnitID", address=42109, length=4)
        UnitID_response = self.read("UnitID")
        self.physicalSerialNumber = TC.list_to_number([UnitID_response[0], UnitID_response[1]], signed=False)
        self.physicalSusyID = UnitID_response[2]
        self.UnitID = UnitID_response[3]

        self.newRegister("SUSyIDModule", address=30003, length=2, signed=False)
        self.SUSyIDModule = self.read_value("SUSyIDModule")
        
        self.newRegister("serialnumber", address=30057, length=2, signed=False)
        self.serialnumber = self.read_value("serialnumber")

        self.newRegister("NameplateSerialnumber", address=30057, length=2, signed=False)
        self.NameplateSerialnumber = self.read_value("NameplateSerialnumber")

        self.newRegister("Model", address=30053, length=2, signed=False)
        self.Model = self.read_value("Model")

        self.newRegister("FirmwareVersion", address=40063, length=2, signed=False)
        self.FirmwareVersion = self.read_value("FirmwareVersion")

        pass

    def newRegister(self, name, address, length, signed=False):
        self.register[name] = self.modbus_register(address, length, signed)
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

    def read_all(self):
        ret_val = []
        for i in self.register:
            ret_val.append([i, self.read_value(i)])
            pass
        pass
        return ret_val

    class modbus_register:
        def __init__(self, address, length, signed):
            self.address = address
            self.length = length
            self.response = []
            self.data = []
            self.error = 0
            self.signed = signed

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