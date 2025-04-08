import time
from machine import Pin

from fifo import Fifo
from led import Led

import micropython
micropython.alloc_emergency_exception_buf(200)

class Encoder:
    def __init__(self, rot_a, rot_b):
        self.a = Pin(rot_a, mode=Pin.IN, pull=Pin.PULL_UP)
        self.b = Pin(rot_b, mode=Pin.IN, pull=Pin.PULL_UP)

        self.fifo = Fifo(30, typecode='i')
        self.a.irq(handler=self.handler, trigger=Pin.IRQ_RISING, hard=True)

    def handler(self, pin):
        if self.b():
            self.fifo.put(-1)
        else:
            self.fifo.put(1)

rot = Encoder(10, 11)
led = Led(20)
brightness = 10
led.off()
button = Pin(9, mode=Pin.IN, pull=Pin.PULL_UP)


while True:
    if not button():
        led.toggle()
        time.sleep(0.2)

    while rot.fifo.has_data():
        value = rot.fifo.get()
        if led():
            print(value)
            brightness += value
            led.brightness(brightness)
