# plantsensor
A Raspberry Pi Pico plant sensor hub coded in Micropython

I used:
1x Raspberry Pi Pico - microcontroller
1x Waveshare Pico OLED 1.3 - screen for displaying values
1x DHT22 with 10kOhm resistor - air temperature and humidity sensor
1x Thermistor with 10kOhm resistor - for soil temperature
3x Capacitive soil moisture sensor V2.0s - for soil moisture detection
Wires
Heatshrinks
Holder
Nail varnish - for waterproofing soil sensors
Electrical tape - for waterproofing soil sensors
1 Altoid sized tin that I had lying about

DHT22 data pin was linked to the 3V by the resistor and wired to GP2
Thermistor data pin was linked to the 3V by the resistor and wired to GP16
Soil moisture sensors were wired to GP26, GP27 and GP28

All sensors were grounded to ground pins and powered by the 3V3O pin
