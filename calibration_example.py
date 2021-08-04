import machine
from src.CSMS import CSMS

adc = machine.ADC(machine.Pin(36))

csms = CSMS(adc)
csms.calibrate()
