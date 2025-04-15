from machine import Pin

button = Pin(9, mode=Pin.IN, pull=Pin.PULL_UP)
led = Pin(22, mode=Pin.OUT)


def button_handler(pin):
    led.toggle()


button.irq(handler=button_handler, trigger=button.IRQ_FALLING, hard=True)
while True:
    # here we have the main program pass
    pass