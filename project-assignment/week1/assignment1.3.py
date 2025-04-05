import time
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C

# Microbuttons connections to Pico's GPIOs
SW_2 = 7
SW_1 = 8
SW_0 = 9


but0 = Pin(SW_0, Pin.IN, Pin.PULL_UP)
but1 = Pin(SW_1, Pin.IN, Pin.PULL_UP)
but2 = Pin(SW_2, Pin.IN, Pin.PULL_UP)

i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)

x = 0
y = oled_height // 2
pic_x = x
pic_y = y

oled.fill(0)
oled.show()

while True:
    if not but1.value():  # Reset
        oled.fill(0)
        oled.show()
        x = 0
        y = oled_height // 2
        pic_x = x
        pic_y = y
        time.sleep(0.5)
    elif not but0.value() and y > 0:
        y -= 1
    elif not but2.value() and y < oled_height - 1:
        y += 1

    oled.line(pic_x, pic_y, x, y, 1)
    oled.show()
    pic_x = x
    pic_y = y
    x += 1
    if x >= oled_width:
        x = 0
        pic_x = 0
    time.sleep(0.01)
