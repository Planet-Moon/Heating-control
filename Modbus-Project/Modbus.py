from pymodbus.client.sync import ModbusTcpClient as ModbusClient
import TypeConversion as TC

class modbus_device(object):
    def __init__(self, ipAddress: str, port="", unitID=1):
        self.ipAddress = ipAddress
        self.port = port
        if self.port:
            self.client = ModbusClient(self.ipAddress, port=self.port)
        else:
            self.client = ModbusClient(self.ipAddress)
        self.UnitID = unitID
        self.connect()
        self.register = {}
        pass

    def connect(self):
        try:
            self.client.connect()
            self.connected = True
        except:
            print("Connection to {}:{} failed!".format(self.ipAddress, self.port))
            exit()

    def close(self):
        try:
            self.client.close()
            self.connected = False
        except:
            print("Connection could not be closed!")

    def newRegister(self, name: str, address: int, length: int, signed=False, factor=1, type_="int", unit=""):
        self.register[name] = self.modbus_register(address, length, signed, factor, type_, unit)
        test = self.read(name) # Init values
        if test:
            return True
        else:
            del self.register[name]

    def read(self, name: str):
        try:
            return self.register[name].get_data(self.client, self.UnitID)
        except:
            print("Error reading register "+name)

    def read_value(self, name: str):
        try:
            value = round(float(TC.list_to_number(self.read(name), signed=self.register[name].signed) * self.register[name].factor), 2)
            value_type = self.register[name].type
            if value_type == "float":
                self.register[name].value = float(value)
            elif value_type == "int":
                self.register[name].value = int(value)
            elif value_type == "bool":
                if value == 0.0:
                    self.register[name].value = False
                else:
                    self.register[name].value = True
            return self.register[name].value
        except Exception as e:
            print("Error reading value from register "+name) 
            print("Exeption: "+str(e))

    def write_register(self, name: str, value: int):
        try:
            self.register[name].write(self.client, value, self.UnitID)
        except:
            print("Error writing register "+name+" with value "+str(value)) 

    def read_string(self, name: str):
        value = self.read_value(name)
        unit = self.register[name].unit
        if not unit:
            unit = ""
        string = name+": "+str(value)+unit
        self.register[name].string = string
        return string

    def read_all(self):
        ret_val = []
        for i in self.register:
            if self.register[i].unit :
                ret_val.append([i, round(self.read_value(i),2), self.register[i].unit])
            else:
                ret_val.append([i, round(self.read_value(i),2), ""])
            pass
        pass
        return ret_val

    class modbus_register:
        def __init__(self, address: int, length: int, signed: bool, factor: float, type_: str, unit: str):
            self.address = address
            self.length = length
            self.response = []
            self.data = []
            self.error = 0
            self.signed = signed
            self.factor = factor
            self.type = type_
            self.unit = unit
            self.value = None

        def read(self, client, unitID: int):
            self.error = 0
            try:
                self.response = client.read_holding_registers(self.address,count=self.length, unit=unitID)
            except Exception as e:
                self.error = 1
                print("Error reading "+str(client)+", "+str(e))
            assert(not self.response.isError())
            return self.response

        def get_data(self, client, unitID: int):
            self.read(client, unitID)
            try: 
                self.data = self.response.registers
                return self.data
            except:
                print("Error reading "+str(client.host)+", register "+str(self.address))
            pass

        def write(self, client, value: int, unitID: int):
            if isinstance(value, list):
                if not len(value) > self.length:
                    rq = client.write_registers(self.address, value, unit=unitID)
                else:
                    raise Exception("Value too long for register. length = "+str(self.length)) 
            else:
                rq = client.write_registers(self.address, value, unit=unitID)
