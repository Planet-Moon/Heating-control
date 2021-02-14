import requests
import json
import threading
import time
import math
from SunnyInverter import sma_SolarInverter

# for testing purposes:
import random
def test_power():
    return random.uniform(4000, 8000)
###

class GOE_Charger:
    def __init__(self,address:str):
        self.address = address

    @property
    def data(self):
        r = requests.get(self.address+"/status")
        return json.loads(r.text)

    @property
    def amp(self):
        return self.data.get("amp")

    @property
    def car(self):
        return True if self.data.get("car") > 1 else False

    @property
    def alw(self):
        return True if self.data.get("alw") == "1" else False

    def set_alw(self, value:bool):
        self._set("alw",int(value))

    def set_amp(self, value:int):
        self._set("amp",int(value))

    def _set(self,key:str,value):
        address = self.address +"/mqtt?payload="+key+"="+str(value)
        r = requests.get(address)
        pass

    def power_to_amp(self,power:float):
        """Calculate amps from power.

        Args:
            power (float): power in watts

        Returns:
            float: amps in ampere
        """
        u_eff = 400*math.sqrt(3)
        i = power/u_eff
        return i

    def init_amp_from_power(self,get_power):
        self.get_power = get_power

    # for testing purposes
    def _random(self):
        return random.uniform(4000, 8000)

    def thread_amp_from_power(self,update_period):
        control_active = True
        state = "auto"
        while True:
            power = self.get_power("power")
            if power < 0.0:
                power = 0.0
            power = power * 2.8
            amps = int(self.power_to_amp(power))

            if self.data.get("uby") != "0":
                state = "override"
            else:
                state = "auto"

            if not control_active and self.alw:
                state = "override"
            else:
                state = "auto"

            if state == "auto":
                if amps >= 6:
                    control_active = True
                    self.set_alw(True)
                    self.set_amp(amps)
                else:
                    control_active = False
                    self.set_alw(False)
                    self.set_amp(6)

            time.sleep(update_period)

    def start_controller(self, update_period=120):
        thread = threading.Thread(target=self.thread_amp_from_power, args=(update_period,))
        thread.start()

class Inverter(sma_SolarInverter):
    def __init__(self, ipAddress:str):
        self.ipAddress = ipAddress
        super(Inverter, self).__init__(ipAddress)

def main():
    sunny_inverter = Inverter("192.168.178.128")
    goe_charger = GOE_Charger('http://192.168.178.106')
    print(goe_charger.amp)
    if goe_charger.amp == "16":
        goe_charger._set("amp","6")
    else:
        goe_charger._set("amp","16")
    print(goe_charger.amp)
    print(goe_charger.power_to_amp(4200))
    goe_charger.init_amp_from_power(sunny_inverter.modbus.read_value)
    goe_charger.start_controller(update_period=180)

if __name__ == '__main__':
    main()
