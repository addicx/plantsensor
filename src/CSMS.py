# Copyright(c) 2020 Ashley Morris
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files(the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# This module reads values from Capacitative Soil Moisture Sensors.
#
# Before using the CSMS you must check the max input voltage of the ADC on your
# microcontroller, failure to do so may damage your IC.
#
# ESP32: 0v - 1.0v https://docs.micropython.org/en/latest/esp32/quickref.html#adc-analog-to-digital-conversion
# ESP8266: 0v - 3.6v https://docs.micropython.org/en/latest/esp8266/quickref.html#adc-analog-to-digital-conversion
#
# To use this module, you must first run the calibration. The calibration must be ran
# using the minimum and maximum envrionments your sensor is going to run in. For example
# in air and then in water for the maximum. The calibration function gives you 10 seconds
# to insert your sensor into the min/max environments.
#
# The function will then return the calibrated values.
#
# See calibration_example.py and example.py


from machine import ADC, Pin
import time


class CSMS:

    def __init__(self, adc, min_value=None, max_value=None):
        self.calibrated_min = min_value
        self.calibrated_max = max_value
        self.adc = adc

        if self.calibrated_min is None or self.calibrated_max is None:
            print("Calibrated min/max values not set. Run calibration.")
            return

    # Calibration reads the ADC value from the sensor 100 times and returns an average
    def calibrate(self):
        min_value = None
        max_value = None
        iterations = 100

        print('Calibrate sensor for the minimum environment, for example in air.')
        print('Calibration will start in 10 seconds.')
        time.sleep(10)
        print('Starting minimum calibration')

        min_value = self.read_raw(iterations)

        print('Minimum calibration complete')
        time.sleep(2)
        print('Calibrate sensor for the maximum environment, for example in water')
        print('Calibration will start in 10 seconds.')
        time.sleep(10)
        print('Starting maximum calibration')

        max_value = self.read_raw(iterations)

        print('Maximum calibration complete')
        time.sleep(2)
        print('Calibration complete! Modify your programs variables with the following results:')

        print('min_value = ', round(min_value))
        print('max_value = ', round(max_value))

    # Reads from the ADC for x number of times and then returns the average from all the readings
    # By default read the ADC 25 times with a 100ms pause between readings, this returns a more accurate reading.
    def read_raw(self, iterations):
        readings = []

        while len(readings) < iterations:
            reading = self.adc.read()
            readings.append(reading)
            time.sleep_ms(100)

        return sum(readings) / len(readings)

    # Convert the averaged or single reading to percentage between calibrated min and max values
    def convert_to_percentage(self, reading):
        percent = ((reading - self.calibrated_min) /
                   (self.calibrated_max - self.calibrated_min)) * 100

        # If the percentage returned is lower or higher than the calibrated min/max then return 0%/100% with a warning
        if percent < 0:
            print('Value less than 0%, check calibration')
            return 0

        if percent > 100:
            print('Value greater than 100%, check calibration')
            return 100

        return percent

    # Read the ADC and return the result in percentage
    def read(self, iterations=25):
        reading = self.read_raw(iterations)
        return round(self.convert_to_percentage(reading))
