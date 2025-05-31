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
        self.samples = Fifo(500) # fifo where ISR will put samples
        self.dbg = Pin(0, Pin.OUT) # debug GPIO pin for measuring timing with oscilloscope

    def handler(self, tid):
        self.samples.put(self.sensor.read_u16())
        self.dbg.toggle()
        
pulse_pin = 27
sample_rate = 250
pulse = Pulse(pulse_pin)
timer = Piotimer(mode=Piotimer.PERIODIC, freq=sample_rate, callback=pulse.handler)

#=========== Heart Rate Pulse Sensor Settings =====

pulse_line = []
origin = (-1, int(height_/2))
left1, top1 = origin

step = 10
scale = 4
max_value = 65535
half_max = max_value/2

values = []
section = []
samples_amount = 500
min_hr = 40
max_hr = 200
hrs = 0
hrs_amount = 0

previous = 0

goingup = False

start = 0
num = 0

# to read:
while True:
    if not pulse.samples.empty():
        #===== Plotting Heartbeat PPG Begin =========
        section = []
        while True:
            if pulse.samples.empty():
                continue
            section.append(pulse.samples.get())
            if len(section) >= step:
                break

        value = sum(section)/step
        left2 = left1 + 1
        top2 = int(scale*half_height*(half_max - value)/half_max + half_height)
        top2 = max(pulse_top, min(pulse_bottom, top2))
        oled.line(left2, pulse_top, left2, pulse_bottom, black)
        oled.line(left1, top1, left2, top2, blue)
        oled.show()
        left1 = left2
        if left1 >= width_:
            left1 = -1
        top1 = top2
        
        #===== Plotting Heartbeat PPG End ==========
        
        #===== PPI/HR Detection Begin ==============
        values.extend(section)
        if len(values) > samples_amount:
            values = values[len(values)-samples_amount:]
        else:
            continue
        
        threshold = (min(values)+max(values))/2
        for data in section:
            if start:
            num += 1

        if data < threshold:
            continue

        if data >= previous:
            goingup = True
        else:
            if goingup:
                if start:
                    ppi = num/250
                    hr = round(60/ppi)
                    if hr > min_hr and hr < max_hr:
                        print(f'BPM: {hr}')
                        hrs += 1
                        hrs_amount += hr
                    num = 0
                else:
                    start = 1
                    num = 0
                goingup = False

        previous = data
        
        
        #===== PPI/HR Detection End ================
        
        