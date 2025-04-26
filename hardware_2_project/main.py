from piotimer import Piotimer as Timer
from ssd1306 import SSD1306_I2C
from machine import UART, Pin, ADC, I2C, PWM
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
led20 = Pin(20, Pin.OUT)
led21 = Pin(21, Pin.OUT)
led21_pwm = PWM(Pin(21))
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
broker_ip = "194.110.231.250"

# Kubios credentials
APIKEY = "pbZRUi49X48I56oL1Lq8y8NDjq6rPfzX3AQeNo3a"
CLIENT_ID = "3pjgjdmamlj759te85icf0lucv"
CLIENT_SECRET = "111fqsli1eo7mejcrlffbklvftcnfl4keoadrdv1o45vt9pndlef"

LOGIN_URL = "https://kubioscloud.auth.eu-west-1.amazoncognito.com/login"
TOKEN_URL = "https://kubioscloud.auth.eu-west-1.amazoncognito.com/oauth2/token"
REDIRECT_URI = "https://analysis.kubioscloud.com/v1/portal/login"
ANALYSIS_URL = "https://analysis.kubioscloud.com/v2/analytics/analyze"


#   Function for reading the signal
def read_adc(tid):
    x = adc.read_u16()
    samples.put(x)


#   Function to display welcome text
def welcome_text():
    oled.fill(1)
    oled.text("Welcome to", 26, 17, 0)
    oled.text("Group 1's", 29, 27, 0)
    oled.text("project!", 33, 37, 0)
    oled.show()
    utime.sleep_ms(3750)


welcome_text()

# Menu options
menu_items = [
    "Measure HR ",
    "Basic HRV analysis",
    "History",
    "Kubios ",
]
menu_index = 0

# Previous states
prev_a = rota.value()
prev_b = rotb.value()
prev_push = rot_push.value()

# Global list to store history of results
history_results = []


# Function to display menu
def display_menu():
    oled.fill(0)
    for i, item in enumerate(menu_items):
        if i == menu_index:
            oled.text("> " + item, 5, i * 12)
        else:
            oled.text(item, 10, i * 12)
    oled.show()


# Function to read encoder
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


# Function to calculate mean PPI
def meanPPI_calculator(data):
    sumPPI = 0
    for i in data:
        sumPPI += i
    rounded_PPI = round(sumPPI / len(data), 0)
    return int(rounded_PPI)


# Function to calculate mean HR
def meanHR_calculator(meanPPI):
    rounded_HR = round(60 * 1000 / meanPPI, 0)
    return int(rounded_HR)


# Function to calculate SDNN
def SDNN_calculator(data, PPI):
    sum = 0
    for i in data:
        sum += (i - PPI) ** 2
    SDNN = (sum / (len(data) - 1)) ** (1 / 2)
    rounded_SDNN = round(SDNN, 0)
    return int(rounded_SDNN)


# Function to calculate RMSSD
def RMSSD_calculator(data):
    i = 0
    summary = 0
    while i < len(data) - 1:
        summary += (data[i + 1] - data[i]) ** 2
        i += 1
    rounded_RMSSD = round((summary / (len(data) - 1)) ** (1 / 2), 0)
    return int(rounded_RMSSD)


# Function to calculate SDSD
def SDSD_calculator(data):
    PP_array = array.array('l')
    i = 0
    first_value = 0
    second_value = 0
    while i < len(data) - 1:
        PP_array.append(int(data[i + 1]) - int(data[i]))
        i += 1
    i = 0
    while i < len(PP_array) - 1:
        first_value += float(PP_array[i] ** 2)
        second_value += float(PP_array[i])
        i += 1
    first = first_value / (len(PP_array) - 1)
    second = (second_value / (len(PP_array))) ** 2
    rounded_SDSD = round((first - second) ** (1 / 2), 0)
    return int(rounded_SDSD)


# Function to calculate SD1
def SD1_calculator(SDSD):
    rounded_SD1 = round(((SDSD ** 2) / 2) ** (1 / 2), 0)
    return int(rounded_SD1)


# Function to calculate SD2
def SD2_calculator(SDNN, SDSD):
    rounded_SD2 = round(((2 * (SDNN ** 2)) - ((SDSD ** 2) / 2)) ** (1 / 2), 0)
    return int(rounded_SD2)


# Function to measure heart rate
def Measure_HR():
    meanPPI = meanPPI_calculator(data)
    oled.fill(0)
    oled.text("Measuring...", 0, 10)
    oled.show()
    result = meanHR_calculator(meanPPI)
    return result


# Function to perform basic HRV analysis
def Basic_HRV_analysis():
        meanPPI = meanPPI_calculator(data)

    result = RMSSD_calculator(data)
    return result


# Function to display history
def History():
    global history_results

    meanPPI = meanPPI_calculator(data)
    result = SDNN_calculator(data, meanPPI)
    history_results.append(result)
   
    oled.fill(0)
    oled.text("History:", 0, 0)
    for i, res in enumerate(history_results):
            oled.text(f"{i + 1}: {res}", 0, (i + 1) * 10)
    oled.show()
    return result


def Kubios():
    return


meanPPI = meanPPI_calculator(data)
Measure_HR()
Basic_HRV_analysis()
RMSSD_calculator(data)
SDNN_calculator(data, meanPPI)
SDSD_calculator(data)
SD2_calculator(SDNN_calculator(data, meanPPI), SDSD_calculator(data))
SD1_calculator(SDSD_calculator(data))


#   Function to display "Start menu"
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


def select_option():
    global prev_push
    global menu_index
    current_push = rot_push.value()
    global measure_stop

    if prev_push == 1 and current_push == 0:  # buttonpressed
        oled.fill(0)
        oled.text("Selected:", 10, 10)
        selected_option = menu_items[menu_index].strip()
        oled.text(selected_option, 10, 30)
        oled.show()
        utime.sleep(1)

        oled.fill(0)

        oled.text(selected_option, 0, 10)

        if selected_option == "Measure HR ":
            press_to_start()
            utime.sleep(2)  # Give time to read the screen
            result = meanHR_calculator(meanPPI)
            oled.fill(0)
            oled.text("Heart Rate:", 0, 10)
            oled.text("Value: {:.1f}".format(result), 0, 30)
            oled.show()
            utime.sleep(3)
            measure_stop = False

        elif selected_option == "Basic HRV analysis":
            result = Basic_HRV_analysis(rr_intervals)
        elif selected_option == "History":
            result = History(rr_intervals)
        elif selected_option == "Kubios":
            result = Kubios(rr_intervals)
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


#   Functions for connecting to WLAN   #
def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    ip = wlan.ifconfig()[0]
    return ip


# main programmme

avg_size = 128  # originally: int(samplerate * 0.5)
buffer = array.array('H', [0] * avg_size)

while True:
    press_to_start()
    new_state = rot_push.value()

    if new_state != switch_state:
        count += 1
        if count > 3:
            if new_state == 0:
                if mode == 0:
                    mode = 1
                else:
                    mode = 0
                led_onboard.value(1)
                time.sleep(0.15)
                led_onboard.value(0)
            switch_state = new_state
            count = 0
    else:
        count = 0
    utime.sleep(0.01)

    if mode == 1:
        count = 0
        switch_state = 0

        oled.fill(0)
        oled.show()

        x1 = -1
        y1 = 32
        m0 = 65535 / 2
        a = 1 / 10

        disp_div = samplerate / 25
        disp_count = 0
        capture_length = samplerate * 60  # 60 = 60s, changable respectively

        index = 0
        capture_count = 0
        subtract_old_sample = 0
        sample_sum = 0

        min_bpm = 30
        max_bpm = 200
        sample_peak = 0
        sample_index = 0
        previous_peak = 0
        previous_index = 0
        interval_ms = 0
        PPI_array = []

        brightness = 0

        tmr = Timer(freq=samplerate, callback=read_adc)

        # Plotting the signal, Sampling
        while capture_count < capture_length:
            if not samples.empty():
                x = samples.get()
                disp_count += 1

                if disp_count >= disp_div:
                    disp_count = 0
                    m0 = (1 - a) * m0 + a * x
                    y2 = int(32 * (m0 - x) / 14000 + 35)
                    y2 = max(10, min(53, y2))
                    x2 = x1 + 1
                    oled.fill_rect(0, 0, 128, 9, 1)
                    oled.fill_rect(0, 55, 128, 64, 1)
                    if len(PPI_array) > 3:
                        actual_PPI = meanPPI_calculator(PPI_array)
                        actual_HR = meanHR_calculator(actual_PPI)
                        oled.text(f'HR:{actual_HR}', 2, 1, 0)
                        oled.text(f'PPI:{interval_ms}', 60, 1, 0)
                    oled.text(f'Timer:  {int(capture_count / samplerate)}s', 18, 56, 0)
                    oled.line(x2, 10, x2, 53, 0)
                    oled.line(x1, y1, x2, y2, 1)
                    oled.show()
                    x1 = x2
                    if x1 > 127:
                        x1 = -1
                    y1 = y2

                if subtract_old_sample:
                    old_sample = buffer[index]
                else:
                    old_sample = 0
                sample_sum = sample_sum + x - old_sample

                # Peak Detection
                if subtract_old_sample:
                    sample_avg = sample_sum / avg_size
                    sample_val = x
                    if sample_val > (sample_avg * 1.05):
                        if sample_val > sample_peak:
                            sample_peak = sample_val
                            sample_index = capture_count

                    else:
                        if sample_peak > 0:
                            if (sample_index - previous_index) > (60 * samplerate / min_bpm):
                                previous_peak = 0
                                previous_index = sample_index
                            else:
                                if sample_peak >= (previous_peak * 0.8):
                                    if (sample_index - previous_index) > (60 * samplerate / max_bpm):
                                        if previous_peak > 0:
                                            interval = sample_index - previous_index
                                            interval_ms = int(interval * 1000 / samplerate)
                                            PPI_array.append(interval_ms)
                                            brightness = 5
                                            led21.duty_u16(4000)
                                        previous_peak = sample_peak
                                        previous_index = sample_index
                        sample_peak = 0

                    if brightness > 0:
                        brightness -= 1
                    else:
                        led21.duty_u16(0)

                buffer[index] = x
                capture_count += 1
                index += 1
                if index >= avg_size:
                    index = 0
                    subtract_old_sample = 1

        tmr.deinit()

        while not samples.empty():
            x = samples.get()

        #   HRV calculation

        oled.fill(0)
        if len(PPI_array) >= 3:
            try:
                connect()
            except KeyboardInterrupt:
                machine.reset()

            try:
                response = requests.post(
                    url=TOKEN_URL,
                    data='grant_type=client_credentials&client_id={}'.format(CLIENT_ID),
                    headers={'Content-Type': 'application/x-www-form-urlencoded'},
                    auth=(CLIENT_ID, CLIENT_SECRET))

                response = response.json()
                access_token = response["access_token"]

                data_set = {
                    "type": "RRI",
                    "data": PPI_array,
                    "analysis": {"type": "readiness"}
                }

                response = requests.post(
                    url="https://analysis.kubioscloud.com/v2/analytics/analyze",
                    headers={"Authorization": "Bearer {}".format(access_token),
                             "X-Api-Key": APIKEY},
                    json=data_set)

                response = response.json()

                SNS = round(response['analysis']['sns_index'], 2)
                PNS = round(response['analysis']['pns_index'], 2)
                oled.text('PNS:' + str(PNS), 0, 45, 1)
                oled.text('SNS:' + str(SNS), 0, 54, 1)

            except KeyboardInterrupt:
                machine.reset()

            mean_PPI = meanPPI_calculator(PPI_array)
            mean_HR = meanHR_calculator(mean_PPI)
            SDNN = SDNN_calculator(PPI_array, mean_PPI)
            RMSSD = RMSSD_calculator(PPI_array)
            SDSD = SDSD_calculator(PPI_array)
            SD1 = SD1_calculator(SDSD)
            SD2 = SD2_calculator(SDNN, SDSD)

            oled.text('MeanPPI:' + str(int(mean_PPI)) + 'ms', 0, 0, 1)
            oled.text('MeanHR:' + str(int(mean_HR)) + 'bpm', 0, 9, 1)
            oled.text('SDNN:' + str(int(SDNN)) + 'ms', 0, 18, 1)
            oled.text('RMSSD:' + str(int(RMSSD)) + 'ms', 0, 27, 1)
            oled.text('SD1:' + str(int(SD1)) + ' SD2:' + str(int(SD2)), 0, 36, 1)
        else:
            oled.text('Error', 45, 10, 1)
            oled.text('Please restart', 8, 30, 1)
            oled.text('measurement', 20, 40, 1)
        oled.show()

        while mode == 1:
            new_state = rot_push.value()
            if new_state != switch_state:
                count += 1
                if count > 3:
                    if new_state == 0:
                        if mode == 0:
                            mode = 1
                        else:
                            mode = 0
                        led_onboard.value(1)
                        time.sleep(0.15)
                        led_onboard.value(0)
                    switch_state = new_state
                    count = 0
            else:
                count = 0
                utime.sleep(0.01)