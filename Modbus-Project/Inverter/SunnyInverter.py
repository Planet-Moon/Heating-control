from datetime import datetime
from Modbus import modbus_device
import TypeConversion as TC

def current_time():
    return datetime.now()

class sma_SolarInverter:
    @classmethod
    def __init__(cls, ipAddress):
        cls.serialnumber = 0
        cls.susyID = 0
        cls.UnitID = 1
        cls.Model = 0
        cls.timeZone = 0
        cls.error = 0
        cls._change_IP(ipAddress)

        try:
            cls.get_data("all")
        except Exception as e:
            print(str(current_time())+": Error - Initialisation of "+cls.ipAddress+" failed!, "+str(e))

        cls.read_all()
        pass

    @classmethod
    def _connect_IP(cls):
        cls.modbus = modbus_device(cls.ipAddress)
        cls._Init_Modbus_Registers()

    @classmethod
    def _change_IP(cls, ipAddress):
        cls.ipAddress = ipAddress
        cls._connect_IP()

    @classmethod
    def _Init_Modbus_Registers(cls):

        cls.modbus.newRegister("UnitID", address=42109, length=4)
        UnitID_response = cls.modbus.read("UnitID")
        cls.physicalSerialNumber = TC.list_to_number([UnitID_response[0], UnitID_response[1]], signed=False)
        cls.physicalSusyID = UnitID_response[2]
        cls.modbus.UnitID = UnitID_response[3]
        cls.UnitID = UnitID_response[3]

        cls.modbus.newRegister("SUSyIDModule", address=30003, length=2, signed=False)
        cls.SUSyIDModule = cls.get_data("SUSyIDModule")
        
        cls.modbus.newRegister("serialnumber", address=30057, length=2, signed=False)
        cls.serialnumber = cls.get_data("serialnumber")

        cls.modbus.newRegister("NameplateSerialnumber", address=30057, length=2, signed=False)
        cls.NameplateSerialnumber = cls.get_data("NameplateSerialnumber")

        cls.modbus.newRegister("Model", address=30053, length=2, signed=False)
        cls.Model = cls.get_data("Model")

        cls.modbus.newRegister("FirmwareVersion", address=40063, length=2, signed=False)
        cls.FirmwareVersion = cls.get_data("FirmwareVersion")

        cls.modbus.newRegister("timeZone", address=40003, length=2)

        cls.modbus.newRegister("operationHealth", address=30201, length=2)

        cls.modbus.newRegister("totalPower", address=30775, length=2, signed=True, type_="float", unit=" W")

        cls.modbus.newRegister("todayEnergy", address=30535, length=2, type_="float", unit=" Wh")
        
        cls.modbus.newRegister("LeistungEinspeisung", address=30867, length=2, signed=True, type_="float", unit=" W")

        cls.modbus.newRegister("LeistungBezug", address=30865, length=2, signed=True, type_="float", unit=" W")

        cls.modbus.newRegister("GesamtErtrag", address=30513, length=4, signed=False, type_="float", unit=" Wh")

        cls.modbus.newRegister("ZählerstandBezugszähler", address=30581, length=2, signed=False, type_="float", unit=" Wh")

        cls.modbus.newRegister("ZählerstandEinspeisezähler", address=30583, length=2, signed=False, type_="float", unit=" Wh")

        # cls.modbus.read_all()
        pass
    
    @classmethod
    def get_data(cls, dataName):
        if dataName == "all":
            return cls.modbus.read_all()
        else:
            return cls.modbus.read_value(dataName)

    @classmethod
    def get_deltaPower(cls):
        value = cls.modbus.read_value("LeistungEinspeisung") - cls.modbus.read_value("LeistungBezug")
        string = "Delta: {}{}".format(value, cls.modbus.register["LeistungEinspeisung"].unit)
        return string

    @classmethod
    def read_all(cls):
        data = cls.modbus.read_all()
        interString = []
        for i in data:
            interString.append("{}: {}{}".format(*i)) 
        string = "\n".join(interString)
        return string

    @property
    def operationHealth(self):
        return self.get_data("operationHealth")
    
    @property
    def totalPower(self):
        return self.get_data("totalPower")
    
    @property
    def todayEnergy(self):
        return self.get_data("todayEnergy")

    @property
    def LeistungEinspeisung(self):
        return self.get_data("LeistungEinspeisung")

    @property
    def LeistungBezug(self):
        return self.get_data("LeistungBezug")

    @property
    def GesamtErtrag(self):
        return self.get_data("GesamtErtrag")

    @property
    def ZaehlerstandBezugszaehler(self):
        return self.get_data("ZählerstandBezugszähler")

    @property
    def ZaehlerstandEinspeiseZaehler(self):
        return self.get_data("ZählerstandEinspeisezähler")

class sma_BatteryInverter(sma_SolarInverter):
    def __init__(self, ipAddress):
        sma_SolarInverter.__init__(ipAddress)
        self._Init_Battery_Modbus_Registers()
        pass

    @classmethod
    def _Init_Battery_Modbus_Registers(cls):
        cls.modbus.newRegister("Batteriestrom", address=30843, length=2, signed=True, type_="float", unit=" A")
        cls.modbus.newRegister("AktuellerBatterieladezustand", address=30845, length=2, signed=False, type_="float", unit=" %")
        cls.modbus.newRegister("AktuelleBatteriekapazitaet", address=30847, length=2, signed=False, type_="float", unit=" %")
        cls.modbus.newRegister("Batterietemperatur", address=30849, length=2, signed=True, type_="float", unit=" °C")
        cls.modbus.newRegister("Batteriespannung", address=30851, length=2, signed=False, type_="float", unit=" V")
        cls.modbus.newRegister("MomentaneBatterieladung", address=31393, length=2, signed=False, type_="float", unit=" W")
        cls.modbus.newRegister("MomentaneBatterieentladung", address=31395, length=2, signed=False, type_="float", unit=" W")
        cls.modbus.newRegister("Batterieladung", address=31397, length=4, signed=False, type_="float", unit=" Wh")
        cls.modbus.newRegister("Batterieentladung", address=31401, length=4, signed=False, type_="float", unit=" Wh")
        pass

    @property
    def Batteriestrom(self):
        return self.get_data("Batteriestrom")

    @property
    def AktuellerBatterieladezustand(self):
        return self.get_data("AktuellerBatterieladezustand")

    @property
    def AktuelleBatteriekapazitaet(self):
        return self.get_data("AktuelleBatteriekapazitaet")

    @property
    def Batterietemperatur(self):
        return self.get_data("Batterietemperatur")

    @property
    def Batteriespannung(self):
        return self.get_data("Batteriespannung")

    @property
    def MomentaneBatterieladung(self):
        return self.get_data("MomentaneBatterieladung")

    @property
    def MomentaneBatterieentladung(self):
        return self.get_data("MomentaneBatterieentladung")

    @property
    def Batterieladung(self):
        return self.get_data("Batterieladung")

    @property
    def Batterieentladung(self):
        return self.get_data("Batterieentladung")