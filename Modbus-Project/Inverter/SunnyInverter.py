from datetime import datetime
from Modbus import modbus_device
import TypeConversion as TC

def current_time():
    return datetime.now()

class sma_SolarInverter:
    #@classmethod
    def __init__(self, ipAddress):
        self.serialnumber = 0
        self.susyID = 0
        self.UnitID = 1
        self.Model = 0
        self.timeZone = 0
        self.error = 0
        self._change_IP(ipAddress)

        try:
            self.get_data("all")
        except Exception as e:
            print(str(current_time())+": Error - Initialisation of "+self.ipAddress+" failed!, "+str(e))

        self.read_all()
        pass

    #@classmethod
    def _connect_IP(self):
        self.modbus = modbus_device(self.ipAddress)
        self._Init_Modbus_Registers()

    #@classmethod
    def _change_IP(self, ipAddress):
        self.ipAddress = ipAddress
        self._connect_IP()

    #@classmethod
    def _Init_Modbus_Registers(self):

        self.modbus.newRegister("UnitID", address=42109, length=4)
        UnitID_response = self.modbus.read("UnitID")
        self.physicalSerialNumber = TC.list_to_number([UnitID_response[0], UnitID_response[1]], signed=False)
        self.physicalSusyID = UnitID_response[2]
        self.modbus.UnitID = UnitID_response[3]
        self.UnitID = UnitID_response[3]

        self.modbus.newRegister("SUSyIDModule", address=30003, length=2, signed=False)
        self.SUSyIDModule = self.get_data("SUSyIDModule")
        
        self.modbus.newRegister("serialnumber", address=30057, length=2, signed=False)
        self.serialnumber = self.get_data("serialnumber")

        self.modbus.newRegister("NameplateSerialnumber", address=30057, length=2, signed=False)
        self.NameplateSerialnumber = self.get_data("NameplateSerialnumber")

        self.modbus.newRegister("Model", address=30053, length=2, signed=False)
        self.Model = self.get_data("Model")

        self.modbus.newRegister("FirmwareVersion", address=40063, length=2, signed=False)
        self.FirmwareVersion = self.get_data("FirmwareVersion")

        self.modbus.newRegister("timeZone", address=40003, length=2)

        self.modbus.newRegister("operationHealth", address=30201, length=2)

        self.modbus.newRegister("power", address=30775, length=2, signed=True, type_="float", unit=" W")

        self.modbus.newRegister("dcwatt", address=30773, length=2, signed=True, type_="float", unit=" W")

        self.modbus.newRegister("todayEnergy", address=30535, length=2, type_="float", unit=" Wh")
        
        self.modbus.newRegister("LeistungEinspeisung", address=30867, length=2, signed=True, type_="float", unit=" W")

        self.modbus.newRegister("LeistungBezug", address=30865, length=2, signed=True, type_="float", unit=" W")

        self.modbus.newRegister("GesamtErtrag", address=30513, length=4, signed=False, type_="float", unit=" Wh")

        self.modbus.newRegister("ZählerstandBezugszähler", address=30581, length=2, signed=False, type_="float", unit=" Wh")

        self.modbus.newRegister("ZählerstandEinspeisezähler", address=30583, length=2, signed=False, type_="float", unit=" Wh")

        self.modbus.newRegister("SpeedwireEnable", address=40157, length=2, signed=False, type_="int", unit="")

        # self.modbus.read_all()
        pass
    
    #@classmethod
    def get_data(self, dataName):
        if dataName == "all":
            return self.modbus.read_all()
        else:
            return self.modbus.read_value(dataName)

    #@classmethod
    def get_deltaPower(self):
        value = self.modbus.read_value("LeistungEinspeisung") - self.modbus.read_value("LeistungBezug")
        string = "Delta: {}{}".format(value, self.modbus.register["LeistungEinspeisung"].unit)
        return string

    #@classmethod
    def read_all(self):
        data = self.modbus.read_all()
        interString = []
        for i in data:
            interString.append("{}: {}{}".format(*i)) 
        string = "\n".join(interString)
        return string

    @property
    def operationHealth(self):
        return self.get_data("operationHealth")
    
    @property
    def power(self):
        return self.get_data("power")

    @property
    def watt(self):
        return self.get_data("watt")
    
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
        super(sma_BatteryInverter, self).__init__(ipAddress)
        self._Init_Battery_Modbus_Registers()
        pass

    #@classmethod
    def _Init_Battery_Modbus_Registers(self):
        self.modbus.newRegister("Batteriestrom", address=30843, length=2, signed=True, type_="float", unit=" A")
        self.modbus.newRegister("AktuellerBatterieladezustand", address=30845, length=2, signed=False, type_="float", unit=" %")
        self.modbus.newRegister("AktuelleBatteriekapazitaet", address=30847, length=2, signed=False, type_="float", unit=" %")
        self.modbus.newRegister("Batterietemperatur", address=30849, length=2, signed=True, factor=0.1, type_="float", unit=" °C")
        self.modbus.newRegister("Batteriespannung", address=30851, length=2, signed=False, factor=0.01, type_="float", unit=" V")
        self.modbus.newRegister("MomentaneBatterieladung", address=31393, length=2, signed=False, type_="float", unit=" W")
        self.modbus.newRegister("MomentaneBatterieentladung", address=31395, length=2, signed=False, type_="float", unit=" W")
        self.modbus.newRegister("Batterieladung", address=31397, length=4, signed=False, type_="float", unit=" Wh")
        self.modbus.newRegister("Batterieentladung", address=31401, length=4, signed=False, type_="float", unit=" Wh")
        self.modbus.newRegister("UntereEntladegrenzeBeiEigenverbrauch", address=40073, length=2, signed=False, type_="int", unit="")
        self.modbus.newRegister("BatterieStatus", address=34659, length=2, signed=False, type_="int", unit="")
        self.modbus.newRegister("BatterieZustand", address=31391, length=2, signed=False, type_="int", unit="")
        self.modbus.newRegister("BatterieBetriebsstatus", address=30955, length=2, signed=False, type_="int", unit="")
        self.modbus.newRegister("BatterieNutzungsBereichStatus", address=31057, length=2, signed=False, type_="int", unit="")
        self.modbus.newRegister("UntereGrenzeTiefenendladungVorAbschaltung", address=40719, length=2, signed=False, type_="int", unit="")
        self.modbus.newRegister("MinimaleBreiteTiefenEntladeschutz", address=40721, length=2, signed=False, type_="int", unit="")
        pass

    #@classmethod
    def reboot(self):
        self.modbus.newRegister("reboot", address=40077, length=2, signed=False, type_="int", unit="")
        self.modbus.write_register("reboot", 1146)
        self.modbus.removeRegister("reboot")

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