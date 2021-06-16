from datetime import timedelta, datetime
import threading
import time
import logging

from PowerSink import PowerSink

logging.basicConfig(level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s')
logger = logging.getLogger(__name__)

class HeizstabElement_Thread(threading.Thread):
    def __init__(self,heizstab,period=30):
        threading.Thread.__init__(self)
        self.heizstab = heizstab
        self.period = period
        self.enabled = True

    def run(self):
        while self.enabled:
            time_now = datetime.now()
            if self.heizstab._on and time_now > self.heizstab.time_turn_on + self.heizstab.max_time_on:
                self.heizstab.turn_off()
            time.sleep(self.period)

class HeizstabElement(PowerSink):
    def __init__(self,
        power=1000,
        min_time_on=0,
        max_time_on=30,
        min_time_off=30,
        max_time_off=0,
        name="HeizstabElement",
        thread_period=30):
        PowerSink.__init__(self, name=name)
        self.request_power = power
        self.min_time_on =  timedelta(seconds=min_time_on)
        self.max_time_on =  timedelta(seconds=max_time_on)
        self.min_time_off = timedelta(seconds=min_time_off)
        self.max_time_off =  timedelta(seconds=max_time_off)
        self._on = False
        self.time_turn_on = datetime(1900,1,1)
        self.time_turn_off = datetime(1900,1,1)
        self.thread = HeizstabElement_Thread(self,period=thread_period)
        self.thread.start()

    def turn_on(self) -> bool:
        time_now = datetime.now()
        if not self._on and self._allowed_power and time_now > self.time_turn_off + self.min_time_off:
            self._on = True
            self.time_turn_on = datetime.now()
            logger.info("Switched on")
            return True
        return False

    def turn_off(self):
        self._on = False
        self.time_turn_off = datetime.now()
        logger.info("Switched off")

    def allow_power(self,power=0.0) -> bool:
        self._allowed_power = power
        if power > 0:
            return self.turn_on()
        return False


def main():
    heizstabElement = HeizstabElement(max_time_on=5,min_time_off=10,thread_period=1)
    while True:
        heizstabElement.allow_power(1000)
        time.sleep(1)

if __name__ == "__main__":
    main()
