import time
from machine import UART, Pin, I2C, Timer, ADC
from ssd1306 import SSD1306_I2C

i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)


current_line = 0

while True:
    user_input = input("Please enter a word (or ctrl+c to quit): ")

    if current_line == 7:
        oled.scroll(0, -8)
        oled.fill_rect(0,56,128,64,0)
    else:
        current_line += 1
    oled.text(user_input, 0, current_line * 8)
    oled.show()
    
    
    

    #user_input = input("please enter a word (or ctrl+c to quit): ")
    #oled.fill(0)
    