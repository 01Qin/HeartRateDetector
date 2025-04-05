from machine import Pin


class Button_handler:

    def __init__(self, indicator_led):
        self.led = Pin(indicator_led, Pin.OUT)
        self.count = 0

    def handler(self, pin):
        self.count += 1
        self.led.toggle()


button = Pin(9, mode=Pin.IN, pull=Pin.PULL_UP)
my_button = Button_handler(22)

button.irq(handler=my_button.handler, trigger=Pin.IRQ_FALLING, hard=True)

old = 0
while True:
    if old != my_button.count:
        old = my_button.count
        print("Button count:", old)