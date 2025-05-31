import time

from machine import Pin, ADC, I2C
from ssd1306 import SSD1306_I2C
from fifo import Fifo
from piotimer import Piotimer

import micropython
micropython.alloc_emergency_exception_buf(200)

led = Pin("LED", Pin.OUT)


#=============== OLED Screen Settings =============
width_ = 128
height_ = 64
pulse_top = 10
pulse_bottom = 53
half_height = height_/2
black = 0
blue = 1
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled = SSD1306_I2C(width_, height_, i2c)
#=============== OLED Screen Settings =============

#=========== Heart Rate Pulse Sensor Settings =====
class Pulse:
    def __init__(self, adc_pin_nr):
        self.sensor = ADC(adc_pin_nr) # sensor AD channel
        self.samples = Fifo(50) # fifo where ISR will put samples
        self.dbg = Pin(0, Pin.OUT) # debug GPIO pin for measuring timing with oscilloscope

    def handler(self, tid):
        self.samples.put(self.sensor.read_u16())
        self.dbg.toggle()

pulse_pin = 27
sample_rate = 250
pulse = Pulse(pulse_pin)
timer = Piotimer(mode=Piotimer.PERIODIC, freq=sample_rate, callback=pulse.handler)

#=========== Heart Rate Pulse Sensor Settings =====

#========= Heart Rate Detector Begin ==========
class HRDetector:
    left1, top1 = (-1, int(height_/2))
    def __init__
    
#========= Heart Rate Detector End ============
origin = (-1, int(height_/2))#-
left1, top1 = origin#-

step = 10
scale = 4
max_value = 65535
half_max = max_value/2
threshold = int(half_max*1.1)
values = []

amount = 0

section_amount = 0
section_count = 0

min_hr = 40
max_hr = 200
hrs = 0
hrs_amount = 0

ppi_samples = []
previous = 0

goingup = False

start = 0
num = 0

# to read:
while True:
    if not pulse.samples.empty():
        data = pulse.samples.get()
        amount += 1
        #===== Plotting Heartbeat PPG Begin =========
        section_amount += data
        section_count += 1
        if section_count >= step:
            value = section_amount/step
            plot_heartbeat(amount, sample_rate, )
            oled.fill_rect(0, 0, 128, 9, 1)
            oled.fill_rect(0, 55, 128, 64, 1)
            oled.text(f'Time:  {int(amount/sample_rate)}s', 18, 1, 0)
            if len(ppi_samples) > 0:
                ave_ppi = int(sum(ppi_samples)/len(ppi_samples))
                ave_hr = int(60/ave_ppi*1000)
                oled.text(f'PPI:{ave_ppi}', 2, 56, 0)
                oled.text(f'HR:{ave_hr}', 70, 56, 0)
            
            left2 = left1 + 1
            top2 = int(scale * half_height * (half_max - value)/half_max + half_height)
            top2 = max(pulse_top, min(pulse_bottom, top2))
            oled.line(left2, pulse_top, left2, pulse_bottom, black)
            oled.line(left1, top1, left2, top2, blue)
            oled.show()
            left1 = left2
            if left1 >= width_:
                left1 = -1
            top1 = top2
            section_amount = 0
            section_count = 0
        
        #===== Plotting Heartbeat PPG End ==========
        
        #===== PPI/HR Detection Begin ==============

        if start:
            num += 1

        if data < threshold:
            continue

        if data >= previous:
            goingup = True
        else:
            if goingup:
                if start:
                    ppi = round(num/250*1000)
                    hr = round(60/ppi*1000)
                    if hr > min_hr and hr < max_hr:
                        print(f'BPM: {hr}')
                        hrs += 1
                        hrs_amount += hr
                        ppi_samples.append(ppi)
                    num = 0
                else:
                    start = 1
                    num = 0
                goingup = False

        previous = data
        
        
        #===== PPI/HR Detection End ================
        
        