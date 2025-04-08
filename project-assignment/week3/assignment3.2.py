import time
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C

from fifo import Fifo
from led import Led

import micropython
micropython.alloc_emergency_exception_buf(200)


leds = []
pins = [20, 21, 22]
for pin in pins:
    led = Led(pin)
    led.off()
    leds.append(led)

i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)
line_h = 8
current = 0

def refresh(leds, current=0):
    oled.fill(0)
    for num, led in enumerate(leds):
        status = led() and 'ON ' or 'OFF'
        current_left = current==num and '<' or ' '
        current_right = current==num and '>' or ' ' 
        oled.text(f"{current_left}LED{num+1} - {status}{current_right}", 8, num*line_h, 1)
    oled.show()

refresh(leds, current)

class Encoder:
    def __init__(self, rot_a, rot_b):
        self.a = Pin(rot_a, mode=Pin.IN, pull=Pin.PULL_UP)
        self.b = Pin(rot_b, mode=Pin.IN, pull=Pin.PULL_UP)
        self.button = Pin(12, mode=Pin.IN, pull=Pin.PULL_UP)
        self.last_press = time.ticks_ms()
        self.fifo = Fifo(300, typecode='i')
        self.a.irq(handler=self.handler_turn, trigger=Pin.IRQ_RISING, hard=True)
        self.button.irq(handler=self.handler_press, trigger=Pin.IRQ_RISING, hard=True)

    def handler_turn(self, pin):
        if self.b():
            self.fifo.put(-1)
        else:
            self.fifo.put(1)

    def handler_press(self, pin):
        if time.ticks_diff(time.ticks_ms(), self.last_press) < 300:
            return
        self.fifo.put(0)
        self.last_press = time.ticks_ms()

rot = Encoder(10, 11)


while True:
    while rot.fifo.has_data():
        value = rot.fifo.get()
        print(value)
        if value == 0:
            leds[current].toggle()
        else:
            current += value
            current = current % len(leds)
        refresh(leds, current)
