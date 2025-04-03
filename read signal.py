from piotimer import Piotimer as Timer
from ssd1306 import SSD1306_I2C
from machine import UART,Pin, ADC, I2C, PWM, Timer
from fifo import Fifo
import utime
import array
import time
import network
import socket
import urequests as requests
import ujson

# ADC-converter
adc = ADC(26)

# OLED
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)

# LEDs
led_onboard = Pin("LED", Pin.OUT)
led21 = PWM(Pin(21))
led21.freq(1000)

# Rotary Encoder
rot_push = Pin(12, mode=Pin.IN, pull=Pin.PULL_UP)

# Sample Rate, Buffer
samplerate = 250
samples = Fifo(32)

# Sample Rate, Buffer
samplerate = 250
samples = Fifo(32)

# Menu selection variables and switch filtering
mode = 0
count = 0
switch_state = 0


def read_adc(tid):
    x = adc.read_u16()
    samples.put(x)


########################################
def draw_heart(oled, x, y, size):
    top_r = size // 2
    bottom_point = y + size
    bottom_r = size // 3

    for i in range(-top_r, top_r + 1):
        oled.pixel(x + top_r + i, y + int((top_r ** 2 - i ** 2) ** 0.5), 0)
        oled.pixel(x + 2 * top_r + i, y + int((top_r ** 2 - i ** 2) ** 0.5), 0)

    oled.pixel(x + size * 3 // 2, bottom_point, 0)

    for i in range(-bottom_r, bottom_r + 1):
        oled.pixel(x + size * 3 // 2 - i, bottom_point + i, 0)
        oled.pixel(x + size * 3 // 2 - i, bottom_point + i, 0)


def welcome_text():
    oled.fill(1)

    for i in range(6):
        draw_heart(oled, i * 23 + 2, 2, 10)

    for i in range(2):
        draw_heart(oled, i * 60 + 30, 25, 20)

    oled.text("Welcome to", 26, 17, 0)
    oled.text("Group 1's", 29, 27, 0)
    oled.text("project!", 33, 37, 0)
    oled.show()
    utime.sleep_ms(3750)


welcome_text()

#   Function to display "Start menu"   #

def press_to_start():
    oled.fill(0)
    oled.text("Press to start", 4, 7, 1)
    oled.text("the measurement", 4, 17, 1)
    oled.line(10, 53, 15, 53, 1)
    oled.line(93, 53, 124, 53, 1)
    oled.line(118, 48, 124, 53, 1)
    oled.line(118, 58, 124, 53, 1)
    oled.line(118, 48, 124, 53, 1)
    oled.line(118, 58, 124, 53, 1)
    oled.line(93, 53, 124, 53, 1)
    oled.line(48, 53, 60, 53, 1)
    horizontal = 0

    for i in range(2):
        oled.line(60 - horizontal, 53, 63 - horizontal, 50, 1)
        oled.line(63 - horizontal, 50, 66 - horizontal, 53, 1)
        oled.line(66 - horizontal, 53, 68 - horizontal, 53, 1)
        oled.line(68 - horizontal, 53, 70 - horizontal, 57, 1)
        oled.line(70 - horizontal, 57, 73 - horizontal, 31, 1)
        oled.line(73 - horizontal, 31, 76 - horizontal, 64, 1)
        oled.line(76 - horizontal, 64, 78 - horizontal, 53, 1)
        oled.line(78 - horizontal, 53, 80 - horizontal, 53, 1)
        oled.line(80 - horizontal, 53, 84 - horizontal, 47, 1)
        oled.line(84 - horizontal, 47, 88 - horizontal, 53, 1)
        oled.line(88 - horizontal, 53, 89 - horizontal, 53, 1)
        oled.line(89 - horizontal, 53, 91 - horizontal, 51, 1)
        oled.line(91 - horizontal, 51, 93 - horizontal, 53, 1)

        horizontal += 45

    oled.show()