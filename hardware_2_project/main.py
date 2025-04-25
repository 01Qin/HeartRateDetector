from piotimer import Piotimer as Timer
from ssd1306 import SSD1306_I2C
from machine import UART, Pin, ADC, I2C, PWM, Timer
from fifo import Fifo
import utime
import array
import time
import network
import socket
import urequests as requests
import ujson
import math

# ADC-converter
adc = ADC(26)

# OLED
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)

# LEDs
led_onboard = Pin("LED", Pin.OUT)
led20 = Pin(20, Pin.OUT)  # Define LED pins for ASM_test
led21 = Pin(21, Pin.OUT)
led21_pwm = PWM(led21)
led21_pwm.freq(1000)

# Rotary Encoder
rot_push = Pin(12, mode=Pin.IN, pull=Pin.PULL_UP)
rota = Pin(10, Pin.IN, Pin.PULL_UP)
rotb = Pin(11, Pin.IN, Pin.PULL_UP)

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


class ASM_test:
    def __init__(self, delay, led1_pin, led2_pin):
        self.delay = delay
        self.led1 = Pin(led1_pin, Pin.OUT)
        self.led2 = Pin(led2_pin, Pin.OUT)
        self.state = self.on1

    def execute(self):
        self.state()

    def on1(self):
        self.led1.on()
        self.led2.off()
        time.sleep(self.delay)
        self.state = self.on2

    def on2(self):
        self.led1.off()
        self.led2.on()
        time.sleep(self.delay)
        self.state = self.on1


#    Function for reading the signal
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


#    Function to display welcome text
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


#    Function to display "Start menu"    #

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


# Menu options
menu_items = [
    "Measure heart rate ",
    "Basic HRV analysis",
    "History",
    "Kubios ",
]
menu_index = 0

# Previous states
prev_a = rota.value()
prev_b = rotb.value()
prev_push = rot_push.value()

# --- LED Blinking Instance ---
blinker = ASM_test(0.2, 20, 21)  # Faster blink for indication


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



def Measure_heart_rate(rr_intervals):
    print("Measuring Heart Rate...")
    blink_start_time = utime.time()  # Start time for blinking

    # Keep blinking the LEDs for 5 seconds
    while utime.time() - blink_start_time < 5:
        blinker.execute()
        utime.sleep(0.01)

    # Simulate the actual measurement process.  Replace this with your real measurement
    # code.  This part should take the time the actual measurement would take.
    utime.sleep(2)

    # Calculate the result
    if rr_intervals:
        result = 60000 / (sum(rr_intervals) / len(rr_intervals))
    else:
        result = 0

    return result  # Return the calculated heart rate



def Basic_HRV_analysis(rr_intervals):
    print("Performing Basic HRV Analysis")
    utime.sleep(2)
    if rr_intervals:
        return sum(rr_intervals) / len(rr_intervals)
    else:
        return 0


def History(rr_intervals):
    utime.sleep(2)
    if len(rr_intervals) > 1:
        mean_rr = sum(rr_intervals) / len(rr_intervals)
        return math.sqrt(sum((x - mean_rr) ** 2 for x in rr_intervals) / (len(rr_intervals) - 1))
    else:
        return 0


def Kubios(rr_intervals):
    utime.sleep(2)
    if len(rr_intervals) > 1:
        return math.sqrt(sum((rr_intervals[i] - rr_intervals[i - 1]) ** 2 for i in range(1, len(rr_intervals))) / (
                    len(rr_intervals) - 1))
    else:
        return 0


def display_menu():
    oled.fill(0)
    for i, item in enumerate(menu_items):
        if i == menu_index:
            oled.text("> " + item, 5, i * 12)
        else:
            oled.text(item, 10, i * 12)
    oled.show()



def select_option():
    global prev_push
    global menu_index
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
        oled.text(selected_option, 0, 10)

        if selected_option == "Measure heart rate":
            result = Measure_heart_rate(rr_intervals)  # Call the function, which now includes blinking
            oled.fill(0) # Clear the OLED before displaying result.
            oled.text("Heart Rate:", 0, 10)
            oled.text("Value: {:.1f}".format(result), 0, 30)
            oled.show()
            utime.sleep(3)

        elif selected_option == "Basic HRV analysis":
            result = Basic_HRV_analysis(rr_intervals)
            oled.fill(0)
            oled.text("Basic HRV:", 0, 10)
            oled.text("Value: {:.1f}".format(result), 0, 30)
            oled.show()
            utime.sleep(3)
        elif selected_option == "History":
            result = History(rr_intervals)
            oled.fill(0)
            oled.text("History:", 0, 10)
            oled.text("Value: {:.1f}".format(result), 0, 30)
            oled.show()
            utime.sleep(3)
        elif selected_option == "Kubios":
            result = Kubios(rr_intervals)
            oled.fill(0)
            oled.text("Kubios:", 0, 10)
            oled.text("Value: {:.1f}".format(result), 0, 30)
            oled.show()
            utime.sleep(3)
        else:
            result = 0

        display_menu()

    prev_push = current_push



# main loop
display_menu()
while True:
    read_encoder()
    select_option()
    utime.sleep_ms(10)

#    Functions for connecting to WLAN    #

def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    ip = wlan.ifconfig()[0]
    return ip
