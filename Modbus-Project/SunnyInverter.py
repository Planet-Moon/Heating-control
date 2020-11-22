from datetime import datetime
from Modbus import modbus_device
import TypeConversion as TC

def current_time():
    return datetime.now()

class sma_Inverter:
    def __init__(self, ipAddress):
        self.serialnumber = 0
        self.susyID = 0
        self.UnitID = 1
        self.Model = 0
        self.operationHealth = 0
        self.totalPower = 0 # W
        self.todayEnergy = 0 # Wh
        self.timeZone = 0
        self.error = 0
        test = TC.list_to_number([-1],signed=True)
        test = TC.list_to_number([32767],signed=True)
        test = TC.list_to_number([-32768],signed=True)

        self._change_IP(ipAddress)

        try:
            self.get_data("all")
        except Exception as e:
            print(str(current_time())+": Error - Initialisation of "+self.ipAddress+" failed!, "+str(e))
        pass

    def _connect_IP(self):
        self.modbus = modbus_device(self.ipAddress)
        
        self._Init_Modbus_Registers()

    def _Init_Modbus_Registers(self):        

        self.modbus.newRegister("UnitID", address=42109, length=4)
        UnitID_response = self.modbus.read("UnitID")
        self.modbus.physicalSerialNumber = TC.list_to_number([UnitID_response[0], UnitID_response[1]], signed=False)
        self.modbus.physicalSusyID = UnitID_response[2]
        self.modbus.UnitID = UnitID_response[3]

        self.modbus.newRegister("SUSyIDModule", address=30003, length=2, signed=False)
        self.modbus.SUSyIDModule = self.modbus.read_value("SUSyIDModule")
        
        self.modbus.newRegister("serialnumber", address=30057, length=2, signed=False)
        self.modbus.serialnumber = self.modbus.read_value("serialnumber")

        self.modbus.newRegister("NameplateSerialnumber", address=30057, length=2, signed=False)
        self.modbus.NameplateSerialnumber = self.modbus.read_value("NameplateSerialnumber")

        self.modbus.newRegister("Model", address=30053, length=2, signed=False)
        self.modbus.Model = self.modbus.read_value("Model")

        self.modbus.newRegister("FirmwareVersion", address=40063, length=2, signed=False)
        self.modbus.FirmwareVersion = self.modbus.read_value("FirmwareVersion")

        self.modbus.newRegister("operationHealth", address=30201, length=2)
        self.modbus.newRegister("totalPower", address=30775, length=2, unit=" W")
        self.modbus.newRegister("todayEnergy", address=30535, length=2, unit=" Wh")
        self.modbus.newRegister("timeZone", address=40003, length=2)
        self.modbus.newRegister("LeistungEinspeisung", address=30867, length=2, signed=True, unit=" W")
        self.LeistungEinspeisung = self.modbus.read_value("LeistungEinspeisung")
        self.modbus.newRegister("LeistungBezug", address=30865, length=2, signed=True, unit=" W")
        self.LeistungBezug = self.modbus.read_value("LeistungBezug")
        self.modbus.read_all()
        pass
    
    def _change_IP(self, ipAddress):
        self.ipAddress = ipAddress
        self._connect_IP()

    def get_data(self,dataName):
        if dataName == "all":
            return self.modbus.read_all()
        else:
            return [[dataName, self.modbus.read_value(dataName)]]