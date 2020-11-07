import os
import time
import RPi.GPIO as GPIO
from time import sleep

def measure_temp():
        temp = os.popen("vcgencmd measure_temp").readline()
        temp = temp.replace("temp=","")
        temp = temp.replace("'C","")
        return (float(temp))

Info = GPIO.RPI_INFO
version = GPIO.VERSION

ledpin = 12
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
func = GPIO.gpio_function(ledpin)
GPIO.setup(ledpin,GPIO.OUT)
pi_pwm = GPIO.PWM(ledpin,500) #ca. 500 Hz PWM
pi_pwm.start(0)

for i in range(0,2,1):
    for duty in range(0,101,1):
        pi_pwm.ChangeDutyCycle(duty)
        print("Duty Cycle: " + str(duty))
        print("CPU Temperatur: " + str(measure_temp()) + "°C")
        sleep(0.05)
    sleep(0.5)

GPIO.cleanup()