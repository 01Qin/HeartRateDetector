import ssd1306
import fifo
import time
from machine import Pin

import micropython
micropython.alloc_emergency_exception_buf(200)


rb = fifo.Fifo(50)
print('I am test.py')

if rb.empty():
    print('Fifo is empty')

led = Pin("LED", Pin.OUT)

while True:
    led.toggle()
    time.sleep(1)

