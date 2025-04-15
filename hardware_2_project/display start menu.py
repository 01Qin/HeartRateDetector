from ssd1306 import SSD1306_I2C
from machine import Pin, I2C
import math
import utime

# OLED setup
i2c = I2C(1, scl=Pin(15), sda=Pin(14))
oled = SSD1306_I2C(128, 64, i2c)

# Rotary Encoder setup
rot_push = Pin(12, Pin.IN, Pin.PULL_UP)
rota = Pin(10, Pin.IN, Pin.PULL_UP)
rotb = Pin(11, Pin.IN, Pin.PULL_UP)

# Menu options
menu_items = [
    "Mean HR (bpm) ",
    "Mean PPI(ms)", # added but still haven't tested with pi pico
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


def calculate_mean_hr(rr_intervals):
    if rr_intervals:
        return 60000 / (sum(rr_intervals) / len(rr_intervals))
    else:
        return 0

def calculate_mean_ppi(rr_intervals): # haven't tested it yet
    if rr_intervals:
        return sum(rr_intervals) / len(rr_intervals)
    else:
        return 0

def calculate_sdnn(rr_intervals):
    if len(rr_intervals) > 1:
        mean_rr = sum(rr_intervals) / len(rr_intervals)
        return math.sqrt(sum((x - mean_rr) ** 2 for x in rr_intervals) / (len(rr_intervals) - 1))
    else:
        return 0


def calculate_rmssd(rr_intervals):
    if len(rr_intervals) > 1:
        return math.sqrt(sum((rr_intervals[i] - rr_intervals[i - 1]) ** 2 for i in range(1, len(rr_intervals))) / (
                    len(rr_intervals) - 1))
    else:
        return 0


def calculate_sdsd(rr_intervals):
    if len(rr_intervals) > 1:
        diffs = [rr_intervals[i] - rr_intervals[i - 1] for i in range(1, len(rr_intervals))]
        mean_diff = sum(diffs) / len(diffs)
        return math.sqrt(sum((x - mean_diff) ** 2 for x in diffs) / (len(diffs) - 1))
    else:
        return 0


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
        elif selected_option == "Mean PPI (ms)": #newnewnew
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

# main loop
display_menu()
while True:
    read_encoder()
    select_option()
    utime.sleep_ms(10)

