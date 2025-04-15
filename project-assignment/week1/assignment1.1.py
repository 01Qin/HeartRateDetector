import time
from machine import UART, Pin, I2C, Timer, ADC
from ssd1306 import SSD1306_I2C

# Microbuttons connections to Pico's GPIOs
SW_2 = 7
SW_1 = 8
SW_0 = 9


but0 = Pin(SW_0, Pin.IN, Pin.PULL_UP)
but2 = Pin(SW_2, Pin.IN, Pin.PULL_UP)

i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)


ufo_x = (oled_width - 3) // 2
ufo_y = 56
ufo_width = 3

#Template functions for microbuttons

def button_0(pin):
    global ufo_x
    if ufo_x > 0:
        ufo_x -= 10
    ufo_x = max(0, ufo_x)
    oled.fill(0)
    oled.text('<=>', ufo_x, ufo_y, 1)
    oled.show()
    
      
def button_2(pin):
    global ufo_x
    if ufo_x < oled_width - ufo_width:
        ufo_x += 10
    ufo_x = min(oled_width - ufo_width, ufo_x)
    oled.fill(0)
    oled.text('<=>', ufo_x, ufo_y, 1)
    oled.show()
    

#Activate interruptions for microbuttons
but0.irq(trigger=Pin.IRQ_FALLING, handler=button_0)
but2.irq(trigger=Pin.IRQ_FALLING, handler=button_2)

oled.fill(0)
print(f"{ufo_x} {ufo_y}")
oled.text('<=>', ufo_x, ufo_y, 1)
oled.show()

while True:
    time.sleep(0.05)
