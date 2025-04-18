import math

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

# SSID credentials
ssid = 'KME759_Group_1'
password = 'KME759bql'

# Kubios credentials

# Function for reading the signal
def read_adc(tid):
    x = adc.read_u16()
    samples.put(x)



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

# Function to display welcome text
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

# Function to display "Start menu"   #

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
press_to_start()

# Functions for connecting to WLAN   #

def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    ip = wlan.ifconfig()[0]
    return


# Functions for HRV calculations

# Rotary Encoder setup
rot_push = Pin(12, Pin.IN, Pin.PULL_UP)
rota = Pin(10, Pin.IN, Pin.PULL_UP)
rotb = Pin(11, Pin.IN, Pin.PULL_UP)

# Menu options
menu_items = [
    "Mean HR (bpm) ",
    "Mean PPI(ms)",  # added but still haven't tested with pi pico
    "SDNN (ms) ",
    "RMSSD (ms) ",
    "SDSD (ms) "
]
menu_index = 0

# Previous states
prev_a = rota.value()
prev_b = rotb.value()
prev_push = rot_push.value()


def display_menu():
    oled.fill(0)
    for i, item in enumerate(menu_items):
        if i == menu_index:
            oled.text("> " + item, 5, i * 12)
        else:
            oled.text(item, 10, i * 12)
    oled.show()


def read_encoder():
    global menu_index, prev_a, prev_b
    current_a = rota.value()
    current_b = rotb.value()

    if prev_a == 1 and current_a == 0:
        if current_b == 1:
            menu_index = (menu_index + 1) % len(menu_items)  # Clockwise
        else:
            menu_index = (menu_index - 1) % len(menu_items)  # Anticlockwise

        display_menu()

    prev_a = current_a
    prev_b = current_b

#   Mean HR Calculator
def calculate_mean_hr(rr_intervals):
    if rr_intervals:
        return 60000 / (sum(rr_intervals) / len(rr_intervals))
    else:
        return 0


#   Mean PPI Calculator
def calculate_mean_ppi(rr_intervals):  # haven't tested it yet
    if rr_intervals:
        return sum(rr_intervals) / len(rr_intervals)
    else:
        return 0

#   SDNN Calculator
def calculate_sdnn(rr_intervals):
    if len(rr_intervals) > 1:
        mean_rr = sum(rr_intervals) / len(rr_intervals)
        return math.sqrt(sum((x - mean_rr) ** 2 for x in rr_intervals) / (len(rr_intervals) - 1))
    else:
        return 0

# RMSSD Calculator

def calculate_rmssd(rr_intervals):
    if len(rr_intervals) > 1:
        return math.sqrt(sum((rr_intervals[i] - rr_intervals[i - 1]) ** 2 for i in range(1, len(rr_intervals))) / (
                len(rr_intervals) - 1))
    else:
        return 0

# SDSD Calculator

def calculate_sdsd(rr_intervals):
    if len(rr_intervals) > 1:
        diffs = [rr_intervals[i] - rr_intervals[i - 1] for i in range(1, len(rr_intervals))]
        mean_diff = sum(diffs) / len(diffs)
        return math.sqrt(sum((x - mean_diff) ** 2 for x in diffs) / (len(diffs) - 1))
    else:
        return 0

# SDNN Calculator
def SDNN_calculator(data, PPI):
    summary = 0
    for i in data:
        summary += (i-PPI)**2
    SDNN = (summary/(len(data)-1))**(1/2)
    rounded_SDNN = round(SDNN, 0)
    return int(rounded_SDNN)

def select_option():
    global prev_push
    current_push = rot_push.value()

    if prev_push == 1 and current_push == 0:  # buttonpressed
        oled.fill(0)
        oled.text("Selected:", 10, 10)
        selected_option = menu_items[menu_index].strip()
        oled.text(selected_option, 10, 30)
        oled.show()
        utime.sleep(1)

        rr_intervals = [790, 795, 800, 805, 810, 815, 820]  # eg
        oled.fill(0)
        oled.text("HRV Metric:", 0, 0)
        oled.text(selected_option, 0, 10)

        if selected_option == "Mean HR (bpm)":
            result = calculate_mean_hr(rr_intervals)
        elif selected_option == "Mean PPI (ms)":  # newnewnew
            result = calculate_mean_ppi(rr_intervals)
        elif selected_option == "SDNN (ms)":
            result = calculate_sdnn(rr_intervals)
        elif selected_option == "RMSSD (ms)":
            result = calculate_rmssd(rr_intervals)
        elif selected_option == "SDSD (ms)":
            result = calculate_sdsd(rr_intervals)
        else:
            result = 0

        oled.text("Value: {:.1f}".format(result), 0, 30)
        oled.show()
        utime.sleep(3)

        display_menu()

    prev_push = current_push

# SD1 Calculator
def SD1_calculator(SDSD):
    rounded_SD1 = round(((SDSD**2)/2)**(1/2), 0)
    return int(rounded_SD1)


# SD2 Calculator

def SD2_calculator(SDNN, SDSD):
    rounded_SD2 = round(((2*(SDNN**2))-((SDSD**2)/2))**(1/2), 0)
    return int(rounded_SD2)


# main loop
display_menu()
while True:
    read_encoder()
    select_option()
    utime.sleep_ms(10)


