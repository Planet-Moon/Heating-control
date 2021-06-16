from datetime import timedelta, datetime
import threading
import time
import logging

logging.basicConfig(level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s')
logger = logging.getLogger(__name__)

class HeizstabElement:
    def __init__(self, leistung=1000,
        min_time_on=0,
        max_time_on=0,
        min_time_off=0,
        max_time_off=0):
        self.leistung = leistung
        self.min_time_on =  timedelta(seconds=min_time_on)
        self.max_time_on =  timedelta(seconds=max_time_on)
        self.min_time_off = timedelta(seconds=min_time_off)
        self.max_time_off =  timedelta(seconds=max_time_off)
        self._on = False
        self.time_turn_on = datetime(1900,1,1)
        self.time_turn_off = datetime(1900,1,1)
        self.active_timer = threading.Timer(1,lambda x:x)

    def __del__(self):
        for thread in self.threads:
            thread.join()
        del self

    @property
    def on(self):
        return self._on

    def turn_on(self):
        if self.time_turn_off + self.min_time_off < datetime.now():
            self.time_turn_on = datetime.now()
            self._on = True
            self.active_timer.cancel()
            logger.info("set to on")
            if self.max_time_on:
                f_on_to_off = threading.Timer(self.max_time_on.total_seconds(),self._turn_off_timer)
                self.active_timer = f_on_to_off
                f_on_to_off.start()
            return True
        logger.info("turn on not allowed")
        return False

    def _turn_on_timer(self):
        self._on = True
        logger.info("set to on by timer")

    def turn_off(self):
        if self.time_turn_on + self.min_time_on < datetime.now():
            self.time_turn_off = datetime.now()
            self._on = False
            self.active_timer.cancel()
            logger.info("set to off")
            if self.max_time_off:
                f_off_to_on = threading.Timer(self.max_time_off.total_seconds(),self._turn_on_timer)
                self.active_timer = f_off_to_on
                f_off_to_on.start()
            return True
        logger.info("turn off not allowed")
        return False

    def _turn_off_timer(self):
        self._on = False
        logger.info("set to off by timer")

if __name__ == "__main__":
    heizstabElement = HeizstabElement(min_time_on=2,min_time_off=2,max_time_on=15,max_time_off=4)
    print("on")
    r = heizstabElement.turn_on()
    print("r: "+str(r),end='\n------\n')
    print("off")
    r = heizstabElement.turn_off()
    print("r: "+str(r),end='\n------\n')

    time.sleep(3)
    print("3s delay",end="\n------\n")

    print("off")
    r = heizstabElement.turn_off()
    print("r: "+str(r),end='\n------\n')

    time.sleep(1.5)
    print("3s delay",end="\n------\n")

    print("on")
    r = heizstabElement.turn_on()
    print("r: "+str(r),end='\n------\n')

    time.sleep(10)


    for i in  heizstabElement.timer:
        i.join()
    print("done")
