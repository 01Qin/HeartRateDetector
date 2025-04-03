from piotimer import Piotimer as Timer
from ssd1306 import SSD1306_I2C
from machine import Pin, ADC, I2C, PWM
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
i2c = I2C(1, scl=Pin(15), sda=Pin(14))
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
def welcome_text():
    oled.fill(1)
    i = 0
    horizontal1 = 0
    horizontal2 = 0

    for i in range(6):
        oled.pixel(4 + horizontal1, 3, 0)
        oled.pixel(8 + horizontal1, 3, 0)
        oled.pixel(4 + horizontal1, 54, 0)
        oled.pixel(8 + horizontal1, 54, 0)

        oled.line(3 + horizontal1, 4, 5 + horizontal1, 4, 0)
        oled.line(3 + horizontal1, 55, 5 + horizontal1, 55, 0)

        oled.line(7 + horizontal1, 4, 9 + horizontal1, 4, 0)
        oled.line(7 + horizontal1, 55, 9 + horizontal1, 55, 0)

        oled.line(2 + horizontal1, 5, 10 + horizontal1, 5, 0)
        oled.line(2 + horizontal1, 56, 10 + horizontal1, 56, 0)

        oled.line(3 + horizontal1, 6, 9 + horizontal1, 6, 0)
        oled.line(3 + horizontal1, 57, 9 + horizontal1, 57, 0)

        oled.line(4 + horizontal1, 7, 8 + horizontal1, 7, 0)
        oled.line(4 + horizontal1, 58, 8 + horizontal1, 58, 0)

        oled.line(5 + horizontal1, 8, 7 + horizontal1, 8, 0)
        oled.line(5 + horizontal1, 59, 7 + horizontal1, 59, 0)

        oled.pixel(6 + horizontal1, 9, 0)
        oled.pixel(6 + horizontal1, 60, 0)

        horizontal1 += 23

    for i in range(2):
        oled.pixel(4 + horizontal2, 19, 0)
        oled.pixel(8 + horizontal2, 19, 0)
        oled.pixel(4 + horizontal2, 37, 0)
        oled.pixel(8 + horizontal2, 37, 0)

        oled.line(3 + horizontal2, 20, 5 + horizontal2, 20, 0)
        oled.line(3 + horizontal2, 38, 5 + horizontal2, 38, 0)

        oled.line(7 + horizontal2, 20, 9 + horizontal2, 20, 0)
        oled.line(7 + horizontal2, 38, 9 + horizontal2, 38, 0)

        oled.line(2 + horizontal2, 21, 10 + horizontal2, 21, 0)
        oled.line(2 + horizontal2, 39, 10 + horizontal2, 39, 0)

        oled.line(3 + horizontal2, 22, 9 + horizontal2, 22, 0)
        oled.line(3 + horizontal2, 40, 9 + horizontal2, 40, 0)

        oled.line(4 + horizontal2, 23, 8 + horizontal2, 23, 0)
        oled.line(4 + horizontal2, 41, 8 + horizontal2, 41, 0)

        oled.line(5 + horizontal2, 24, 7 + horizontal2, 24, 0)
        oled.line(5 + horizontal2, 42, 7 + horizontal2, 42, 0)

        oled.pixel(6 + horizontal2, 25, 0)
        oled.pixel(6 + horizontal2, 43, 0)

        horizontal2 += 115

    oled.text("Welcome to", 26, 17, 0)
    oled.text("Group 1's", 29, 27, 0)
    oled.text("project!", 33, 37, 0)
    oled.show()
    utime.sleep_ms(3750)


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