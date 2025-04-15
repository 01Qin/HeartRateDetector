from machine import Pin
from fifo import Fifo


class Interrupt_button:
    def __init__(self, button_pin, fifo):
        self.button = Pin(button_pin, mode=Pin.IN, pull=Pin.PULL_UP)
        self.nr = button_pin
        self.fifo = fifo
        self.button.irq(handler=self.handler, trigger=Pin.IRQ_FALLING, hard=True)

    def handler(self, pin):
        self.fifo.put(self.nr)


events = Fifo(30)

sw0 = Interrupt_button(9, events)
sw1 = Interrupt_button(8, events)
sw2 = Interrupt_button(7, events)

while True:
    if events.has_data():
        print(events.get())