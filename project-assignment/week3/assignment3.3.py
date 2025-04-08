import time
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C

from fifo import Fifo
from led import Led
from filefifo import Filefifo

import micropython
micropython.alloc_emergency_exception_buf(200)


data = Filefifo(10, name = 'capture_250Hz_03.txt')
amount = 1000
values = []

for key in range(amount):
    value = data.get()
    values.append(value)

min_ = min(values)
max_ = max(values)


print(f'Minimum: {min_}, Maximum: {max_}')


i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)
line_h = 8

current = 0

def get_percentage(number):
    res = int((number-min_)/(max_-min_) * (oled_height-1))
    res = max(res, 0)
    res = min(res, (oled_height-1))
    return (oled_height-1) - res

def refresh(values, current=0):
    oled.fill(0)
    for num, value in enumerate(values[current:current+oled_width]):
        #oled.text(f"{line}", 0, num*line_h, 1)
        top = get_percentage(value)
        oled.pixel(num, top, 1)
    oled.show()

refresh(values, current)

class Encoder:
    def __init__(self, rot_a, rot_b):
        self.a = Pin(rot_a, mode=Pin.IN, pull=Pin.PULL_UP)
        self.b = Pin(rot_b, mode=Pin.IN, pull=Pin.PULL_UP)
        self.fifo = Fifo(300, typecode='i')
        self.a.irq(handler=self.handler_turn, trigger=Pin.IRQ_RISING, hard=True)

    def handler_turn(self, pin):
        if self.b():
            self.fifo.put(-1)
        else:
            self.fifo.put(1)

rot = Encoder(10, 11)


while True:
    if rot.fifo.has_data():
        value = rot.fifo.get()
        current += value
        print(current)
        current = max(0, min(current, len(values)-oled_width))
        refresh(values, current)

