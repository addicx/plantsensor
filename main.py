from machine import Pin,SPI,ADC #3v3 to humidity1, GP2 to humidity2 GND to humidity 4,  (Link DHT22 pins 1&2 with a 4.7K - 10K resistor)
import framebuf, onewire, ds18x20, rp2, time, random
from src.CSMS import CSMS

DC = 8
RST = 12
MOSI = 11
SCK = 10
CS = 9


class OLED_1inch3(framebuf.FrameBuffer):
    def __init__(self):
        self.width = 128
        self.height = 64
        
        self.cs = Pin(CS,Pin.OUT)
        self.rst = Pin(RST,Pin.OUT)
        
        self.cs(1)
        self.spi = SPI(1)
        self.spi = SPI(1,2000_000)
        self.spi = SPI(1,20000_000,polarity=0, phase=0,sck=Pin(SCK),mosi=Pin(MOSI),miso=None)
        self.dc = Pin(DC,Pin.OUT)
        self.dc(1)
        self.buffer = bytearray(self.height * self.width // 8)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_HMSB)
        self.init_display()
        
        self.white =   0xffff
        self.black =   0x0000
        
    def write_cmd(self, cmd):
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, buf):
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(bytearray([buf]))
        self.cs(1)

    def init_display(self):
        """Initialize dispaly"""  
        self.rst(1)
        time.sleep(0.001)
        self.rst(0)
        time.sleep(0.01)
        self.rst(1)
        
        self.write_cmd(0xAE)#turn off OLED display

        self.write_cmd(0x00)   #set lower column address
        self.write_cmd(0x10)   #set higher column address 

        self.write_cmd(0xB0)   #set page address 
      
        self.write_cmd(0xdc)    #et display start line 
        self.write_cmd(0x00) 
        self.write_cmd(0x81)    #contract control 
        self.write_cmd(0x6f)    #128
        self.write_cmd(0x21)    # Set Memory addressing mode (0x20/0x21) #
    
        self.write_cmd(0xa0)    #set segment remap 
        self.write_cmd(0xc0)    #Com scan direction
        self.write_cmd(0xa4)   #Disable Entire Display On (0xA4/0xA5) 

        self.write_cmd(0xa6)    #normal / reverse
        self.write_cmd(0xa8)    #multiplex ratio 
        self.write_cmd(0x3f)    #duty = 1/64
  
        self.write_cmd(0xd3)    #set display offset 
        self.write_cmd(0x60)

        self.write_cmd(0xd5)    #set osc division 
        self.write_cmd(0x41)
    
        self.write_cmd(0xd9)    #set pre-charge period
        self.write_cmd(0x22)   

        self.write_cmd(0xdb)    #set vcomh 
        self.write_cmd(0x35)  
    
        self.write_cmd(0xad)    #set charge pump enable 
        self.write_cmd(0x8a)    #Set DC-DC enable (a=0:disable; a=1:enable)
        self.write_cmd(0XAF)
    def show(self):
        self.write_cmd(0xb0)
        for page in range(0,64):
            self.column = 63 - page              
            self.write_cmd(0x00 + (self.column & 0x0f))
            self.write_cmd(0x10 + (self.column >> 4))
            for num in range(0,16):
                self.write_data(self.buffer[page*16+num])

# Sensors
    #Onboard Temp
sensor_temp = machine.ADC(4)
conversion_factor = 3.3 / (65535)
reading = sensor_temp.read_u16() * conversion_factor
temperature = 27 - (reading - 0.706)/0.001721
    #External Temp
ds_pin = machine.Pin(16) #GP16 to central pin, 3v3_O to rightmost pin facing the flat side, GND to leftmost pin
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
roms = ds_sensor.scan()

#Soil Moisture (CSMS)
adc0 = machine.ADC(machine.Pin(26)) #CA changed pin to 26 (ADC pins on a Pico are 26, 27 & 28)
adc1 = machine.ADC(machine.Pin(27)) #CA changed pin to 26 (ADC pins on a Pico are 26, 27 & 28)
adc2 = machine.ADC(machine.Pin(28)) #CA changed pin to 26 (ADC pins on a Pico are 26, 27 & 28)

csms0 = CSMS(adc0, min_value=60000, max_value=24854)
csms1 = CSMS(adc1, min_value=60000, max_value=24854)
csms2 = CSMS(adc2, min_value=60000, max_value=24854)

#Humidity
dht = ""
@rp2.asm_pio(set_init=(rp2.PIO.OUT_LOW,rp2.PIO.OUT_LOW),#Pico pin GP2 to DHT22 pin 2 facing the grid, Pico GND to DHT22 pin 4, Pico 3v3_O to DHT22 pin 1 (Link DHT22 pins 1&2 with a 4.7K - 10K resistor)
         autopush=True, in_shiftdir=rp2.PIO.SHIFT_LEFT)
def dht22():
    wrap_target()
    label("again")
    pull(block)
    set(pins, 0)
    mov(x, osr)
    label("loop1")
    jmp(x_dec, "loop1")
    set(pindirs, 0)
    wait(1, pin, 0)
    wait(0, pin, 0)
    wait(1, pin, 0)
    wait(0, pin, 0)
    set(y, 31)
    label("bits")
    wait(1, pin, 0) [25]
    in_(pins, 1)
    wait(0, pin, 0)
    jmp(y_dec, "bits")
      
    set(y, 7)
    label("check")
    wait(1, pin, 0)[25]
    set(pins,2)
    set(pins,0)
    in_(pins, 1)
    wait(0, pin, 0)
    jmp(y_dec, "check")
    push(block)
    wrap()
class DHT22():
    def __init__(self, gpio):
        self.sm = rp2.StateMachine(0, dht22, freq=490196,
            in_base=Pin(gpio), set_base=Pin(gpio),
                                        jmp_pin=Pin(gpio))
        self.sm.active(1)
    def getReading(self):
        self.sm.put(500)
        data=0
        data = self.sm.get()
        byte1 = (data >> 24 & 0xFF)
        byte2 = (data >> 16 & 0xFF)
        byte3 = (data >> 8 & 0xFF)
        byte4 = (data & 0xFF)
        checksum = self.sm.get() & 0xFF
        self.checksum = (checksum == (byte1+byte2+byte3+byte4) & 0xFF)
        self.humidity = ((byte1 << 8) | byte2) / 10.0
        neg = byte3 & 0x80
        byte3 = byte3 & 0x7F
        self.temperature = (byte3 << 8 | byte4) / 10.0
        if neg > 0:
            self.temperature = -self.temperature

# Definitions
i = 0
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

while True:

    filename = ("data" + str(random.getrandbits(16)) + ".csv") #log given a random name to minimise risk of overwriting data upon power loss
    file = open(filename, "w")
    file.close()

    #It begins
    while True:
        #empty cache and assess memory strain
        csvdata = []
        with open(filename,'r') as file:
            for line in file:
                csvdata.append(line.rstrip('\n').rstrip('\r').split(','))
        if len(csvdata) > 300:
            break
        #set time parameters
        t_end = time.time() + 60 #time ~between reads - 3600 in final
        
            #zfill date parameters
        if len(str(abs(time.localtime()[4]))) == 1:
            zmin = ("0" + str(abs(time.localtime()[4])))
        else:
            zmin = str(abs(time.localtime()[4]))
        if len(str(abs(time.localtime()[3]))) == 1:
            zhr = ("0" + str(abs(time.localtime()[3])))
        else:
            zhr = str(abs(time.localtime()[3]))
        if len(str(abs(time.localtime()[2]))) == 1:
            zday = ("0" + str(abs(time.localtime()[2])))
        else:
            zday = str(abs(time.localtime()[2]))

        date = (zhr + ":" + zmin + " " + zday + months[abs(time.localtime()[1])] + "'" + str(abs(time.localtime()[0]) % 100))
        #iterate lognum
        i += 1
        if len(str(i)) == 1:
            lognum = ("Log0000" + str(i))
        elif len(str(i)) == 2:
            lognum = ("Log000" + str(i))
        elif len(str(i)) == 3:
            lognum =  ("Log00" + str(i))
        elif len(str(i)) == 4:
            lognum =  ("Log0" + str(i))
        else:
            lognum =  ("Log" + str(i))
        # MinMax values
        sm1set = [x[5] for x in csvdata]
        sm2set = [x[6] for x in csvdata]
        sm3set = [x[7] for x in csvdata]
        csvdata = []
        if sm1set ==[]:
            row3 = "High " + "N/A" + " " + "N/A" + " " + "N/A"
            row5 = "Low  " + "N/A" + " " + "N/A" + " " + "N/A"
        else:
            row3 = "High " + max(sm1set) + " " + max(sm2set) + " " + max(sm3set)
            row5 = "Low  " + min(sm1set) + " " + min(sm2set) + " " + min(sm3set)
        sm1set = []
        sm2set = []
        sm3set = []
        #update sensors
        ds_sensor.convert_temp()
        time.sleep_ms(750) #need to wait 750 ms between convert and read
        for rom in roms:
            stemp = ds_sensor.read_temp(rom)
        if len(str(round(stemp))) ==1:
            zstemp = "0" + str(round(stemp))
        else:
            zstemp = str(round(stemp))
        dht = DHT22(2)
        dht.getReading()
        sensor_temp = machine.ADC(4)
        conversion_factor = 3.3 / (65535)
        reading = sensor_temp.read_u16() * conversion_factor
        temperature = 27 - (reading - 0.706)/0.001721
        soilz1 = csms0.read(25)
        soilz2 = csms1.read(25)
        soilz3 = csms2.read(25)
        if len(str(soilz1)) == 1:#normalises the length of the values
            soil1 = ("0" + str(soilz1) + "%")
        elif len(str(soilz1)) == 2:
            soil1 = (str(soilz1) + "%")
        else:
            soil1 = ("Max")
        if len(str(soilz2)) == 1:#normalises the length of the values
            soil2 = ("0" + str(soilz2) + "%")
        elif len(str(soilz2)) == 2:
            soil2 = (str(soilz2) + "%")
        else:
            soil2 = ("Max")
        if len(str(soilz3)) == 1:#normalises the length of the values
            soil3 = ("0" + str(soilz3) + "%")
        elif len(str(soilz1)) == 2:
            soil3 = (str(soilz3) + "%")
        else:
            soil3 = ("Max")
        if len(str(round(dht.temperature))) ==1:
            ztemp = "0" + str(round(dht.temperature))
        else:
            ztemp = str(round(dht.temperature))
        if len(str(round(dht.humidity))) ==1:
            zhum = "0" + str(round(dht.humidity))
        else:
            zhum = str(round(dht.humidity))
        row0 = (date)
        row1 = "A " + ztemp + "C " + zhum + "%h S " + zstemp + "C"
        row2 = " Soil  Moisture "
        row4 = "Now  " + str(soil1) + " " + str(soil2) + " " + str(soil3)
            #write to screen
        OLED = OLED_1inch3() #Fills the screen with the defined row strings
        OLED.fill(0x0000)
        OLED.text(row0,6,1)
        OLED.text(row1,1,11)
        OLED.text(row2,1,23)
        OLED.line(9,31,120,31,OLED.white)
        OLED.text(row3,1,34)
        OLED.text(row4,1,44)
        OLED.text(row5,1,54)
        OLED.show()
        #write to log
        file = open(filename, "a+")
        file.write(str(lognum) + "," + str(time.time()) + "," + str(dht.temperature) + "," + str(dht.humidity) + "," + str(stemp) + "," + str(soil1) + "," + str(soil2) + "," + str(soil3) + "\n")
        file.close()
        #buttons
        keyA = Pin(15,Pin.IN,Pin.PULL_UP)
        keyB = Pin(17,Pin.IN,Pin.PULL_UP)
        
        import micropython
        micropython.mem_info()#memory check DEBUG
        
        keyA = Pin(15,Pin.IN,Pin.PULL_UP)
        keyB = Pin(17,Pin.IN,Pin.PULL_UP)
        with open(filename,'r') as file:
            for line in file:
                csvdata.append(line.rstrip('\n').rstrip('\r').split(','))
        t_end = time.time() + 60
        activeline = len(csvdata)
        numlines = len(csvdata)
        while time.time() < t_end:

            if keyA.value() == 0:
                OLED.fill(0x0000)
                OLED.text(str(csvdata[activeline-1][0]),1,1)
                OLED.line(9,11,120,11,OLED.white)
                OLED.text("Air Temp: " + str(csvdata[activeline-1][2]) + "C",1,14)
                OLED.text("Humidity: " + str(csvdata[activeline-1][3]) + "%",1,24)
                OLED.text("Soil Temp: " + str(csvdata[activeline-1][4]) + "C",1,34)
                OLED.text("CSMS:" + str(csvdata[activeline-1][5]) + " " + str(csvdata[activeline-1][6]) + " " + str(csvdata[activeline-1][7]),1,44)
                OLED.text(str(time.time() - t_end),1,54)
                OLED.show()
                activeline += 1
                if activeline > numlines:
                    csvdata = []
                    break
              
                
            if keyB.value() == 0:
                OLED.fill(0x0000)
                OLED.text(str(csvdata[activeline-1][0]),1,1)
                OLED.line(9,11,120,11,OLED.white)
                OLED.text("Air Temp: " + str(csvdata[activeline-1][2]) + "C",1,14)
                OLED.text("Humidity: " + str(csvdata[activeline-1][3]) + "%",1,24)
                OLED.text("Soil Temp: " + str(csvdata[activeline-1][4]) + "C",1,34)
                OLED.text("CSMS:" + str(csvdata[activeline-1][5]) + " " + str(csvdata[activeline-1][6]) + " " + str(csvdata[activeline-1][7]),1,44)
                OLED.text(str(time.time() - t_end),1,54)
                OLED.show()
                activeline -= 1
                if activeline < 0:
                    activeline += 1

            OLED.show()
