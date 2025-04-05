from machine import Pin

button = Pin(9, mode=Pin.IN, pull=Pin.PULL_UP)
led = Pin("LED", Pin.OUT)
pressed = False


def button_handler(pin):
    global pressed
    pressed = True
    led.toggle()


button.irq(handler=button_handler, trigger=Pin.IRQ_FALLING, hard=True)

while True:
    if pressed:
        pressed = False
        print("Button was pressed")