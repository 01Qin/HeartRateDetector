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

# Define menu items
menu_items = [
    "Measure HR ",
    "Basic HRV analysis",
    "History",
    "Kubios ",
]


# ADC-converter
adc = ADC(26)

# OLED
i2c = I2C(1, scl = Pin(15), sda = Pin(14))
oled = SSD1306_I2C(128, 64, i2c)

# LEDs
led_onboard = Pin("LED", Pin.OUT)
led21 = PWM(Pin(21))
led21.freq(1000)

# Rotary Encoder Push Button (Assuming rotation inputs would also be connected elsewhere)
rot_push = Pin(12, mode = Pin.IN, pull = Pin.PULL_UP)


# Sample Rate, Buffer
samplerate = 250
samples = Fifo(32)

# Menu selection variables and switch filtering
mode = 0  # 0: Menu, 1: Measure HR, 2: Basic HRV, 3: History, 4: Kubios
count = 0 # For button debouncing
switch_state = 0 # For button debouncing
selected_item_index = 0 # Index of the currently selected menu item


#   Function for reading the signal 

def read_adc(tid):
    x = adc.read_u16()
    samples.put(x)

#   Function to display welcome text 

def welcome_text():
    oled.fill(1)
    i = 0
    horizontal1 = 0
    horizontal2 = 0

    for i in range(6):
        oled.pixel(4+horizontal1, 3, 0)
        oled.pixel(8+horizontal1, 3, 0)
        oled.pixel(4+horizontal1, 54, 0)
        oled.pixel(8+horizontal1, 54, 0)

        oled.line(3+horizontal1, 4, 5+horizontal1, 4, 0)
        oled.line(3+horizontal1, 55, 5+horizontal1, 55, 0)

        oled.line(7+horizontal1, 4, 9+horizontal1, 4, 0)
        oled.line(7+horizontal1, 55, 9+horizontal1, 55, 0)

        oled.line(2+horizontal1, 5, 10+horizontal1, 5, 0)
        oled.line(2+horizontal1, 56, 10+horizontal1, 56, 0)

        oled.line(3+horizontal1, 6, 9+horizontal1, 6, 0)
        oled.line(3+horizontal1, 57, 9+horizontal1, 57, 0)

        oled.line(4+horizontal1, 7, 8+horizontal1, 7, 0)
        oled.line(4+horizontal1, 58, 8+horizontal1, 58, 0)

        oled.line(5+horizontal1, 8, 7+horizontal1, 8, 0)
        oled.line(5+horizontal1, 59, 7+horizontal1, 59, 0)

        oled.pixel(6+horizontal1, 9, 0)
        oled.pixel(6+horizontal1, 60, 0)

        horizontal1 += 23

    for i in range(2):
        oled.pixel(4+horizontal2, 19, 0)
        oled.pixel(8+horizontal2, 19, 0)
        oled.pixel(4+horizontal2, 37, 0)
        oled.pixel(8+horizontal2, 37, 0)

        oled.line(3+horizontal2, 20, 5+horizontal2, 20, 0)
        oled.line(3+horizontal2, 38, 5+horizontal2, 38, 0)

        oled.line(7+horizontal2, 20, 9+horizontal2, 20, 0)
        oled.line(7+horizontal2, 38, 9+horizontal2, 38, 0)

        oled.line(2+horizontal2, 21, 10+horizontal2, 21, 0)
        oled.line(2+horizontal2, 39, 10+horizontal2, 39, 0)

        oled.line(3+horizontal2, 22, 9+horizontal2, 22, 0)
        oled.line(3+horizontal2, 40, 9+horizontal2, 40, 0)

        oled.line(4+horizontal2, 23, 8+horizontal2, 23, 0)
        oled.line(4+horizontal2, 41, 8+horizontal2, 41, 0)

        oled.line(5+horizontal2, 24, 7+horizontal2, 24, 0)
        oled.line(5+horizontal2, 42, 7+horizontal2, 42, 0)

        oled.pixel(6+horizontal2, 25, 0)
        oled.pixel(6+horizontal2, 43, 0)

        horizontal2 += 115

    oled.text("Welcome to", 26, 17, 0)
    oled.text("Group 1's", 29, 27, 0)
    oled.text("project!", 33, 37, 0)
    oled.show()
    utime.sleep_ms(3750)


#      Function to display the menu    #

def display_menu(items, selected_index):
    oled.fill(0)
    for i, item in enumerate(items):
        # Highlight the selected item
        if i == selected_index:
            oled.fill_rect(0, i * 10, 128, 10, 1) # Draw a filled rectangle as background
            oled.text(item, 5, i * 10 + 1, 0)  # Draw text in black on white background
        else:
            oled.text(item, 5, i * 10 + 1, 1)  # Draw text in white on black background
    oled.show()


#   Functions for connecting to WLAN

# SSID credentials
ssid = 'KME759_Group_1'
password = 'KME759bql'
broker_ip = "192.168.1.254"

# Kubios credentials
APIKEY = "pbZRUi49X48I56oL1Lq8y8NDjq6rPfzX3AQeNo3a"
CLIENT_ID = "3pjgjdmamlj759te85icf0lucv"
CLIENT_SECRET = "111fqsli1eo7mejcrlffbklvftcnfl4keoadrdv1o45vt9pndlef"

LOGIN_URL = "https://kubioscloud.auth.eu-west-1.amazoncognito.com/login"
TOKEN_URL = "https://kubioscloud.auth.eu-west-1.amazoncognito.com/oauth2/token"
REDIRECT_URI = "https://analysis.kubioscloud.com/v1/portal/login"
ANALYSIS_URL = "https://analysis.kubioscloud.com/v2/analytics/analyze"


def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    ip = wlan.ifconfig()[0]
    return



# Function to calculate mean PPI
def meanPPI_calculator(data):
    if not data:
        return 0
    sumPPI = 0
    for i in data:
        sumPPI += i
    rounded_PPI = round(sumPPI/len(data), 0)
    return int(rounded_PPI)


# Function to calculate mean HR
def meanHR_calculator(meanPPI):
    if meanPPI == 0:
        return 0
    rounded_HR = round(60*1000/meanPPI, 0)
    return int(rounded_HR)

# Function to calculate SDNN
def SDNN_calculator(data, PPI):
    if len(data) < 2:
        return 0
    summary = 0
    for i in data:
        summary += (i-PPI)**2
    SDNN = (summary/(len(data)-1))**(1/2)
    rounded_SDNN = round(SDNN, 0)
    return int(rounded_SDNN)

# Function to calculate RMSSD
def RMSSD_calculator(data):
    if len(data) < 2:
        return 0
    i = 0
    summary = 0
    while i < len(data)-1:
        summary += (data[i+1]-data[i])**2
        i +=1
    rounded_RMSSD = round((summary/(len(data)-1))**(1/2), 0)
    return int(rounded_RMSSD)

# Function to calculate SDSD
def SDSD_calculator(data):
    if len(data) < 2:
        return 0
    PP_array = array.array('l')
    i = 0
    while i < len(data)-1:
        PP_array.append(int(data[i+1])-int(data[i]))
        i += 1

    if len(PP_array) < 2:
         return 0

    first_value = 0
    second_value = 0
    i = 0
    while i < len(PP_array): # Iterate up to len(PP_array)
        first_value += float(PP_array[i]**2)
        second_value += float(PP_array[i])
        i += 1

    # Corrected calculations based on array size
    first = first_value/len(PP_array) # Sum of squares divided by N
    second = (second_value/len(PP_array))**2 # (Sum of values / N)^2

    # Ensure the value inside sqrt is non-negative
    inside_sqrt = first - second
    if inside_sqrt < 0:
        # This can happen with floating point inaccuracies or if the data is constant
        # In a real scenario, you might want to handle this more robustly
        print("Warning: Negative value inside square root for SDSD calculation. Returning 0.")
        return 0

    rounded_SDSD = round((inside_sqrt)**(1/2), 0)
    return int(rounded_SDSD)

# Function to calculate SD1
def SD1_calculator(SDSD):
    rounded_SD1 = round(((SDSD**2)/2)**(1/2), 0)
    return int(rounded_SD1)

# Function to calculate SD2
def SD2_calculator(SDNN, SDSD):
    # Ensure the value inside sqrt is non-negative
    inside_sqrt = (2*(SDNN**2))-((SDSD**2)/2)
    if inside_sqrt < 0:
         # This can happen with floating point inaccuracies
         print("Warning: Negative value inside square root for SD2 calculation. Returning 0.")
         return 0

    rounded_SD2 = round((inside_sqrt)**(1/2), 0)
    return int(rounded_SD2)

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


#   Function to display "collect_data" 
def collect_data():
    oled.fill(0)
    oled.text("Collecting", 4, 7, 1)
    oled.text("Data...", 4, 17, 1)
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

#   Function to display "send_data" 
def send_data():
    oled.fill(0)
    oled.text("Sending", 4, 7, 1)
    oled.text("Data...", 4, 17, 1)
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
    
# main programme

welcome_text()
avg_size = 128  # originally: int(samplerate * 0.5)
buffer = array.array('H',[0]*avg_size)

while True:
    if mode == 0:
        # Menu Mode
        display_menu(menu_items, selected_item_index)

        # --- Placeholder for Rotary Encoder Navigation Logic ---
        # Read rotary encoder pins for rotation and update selected_item_index
        # Make sure to handle wrap-around for the index (0 to len(menu_items)-1)
        # Example (requires reading rotary A and B pins, not included in original code):
# #        new_rotation_state = read_rotary_encoder()
#         if new_rotation_state != old_rotation_state:
#             if rotation_is_clockwise:
#                 selected_item_index = (selected_item_index + 1) % len(menu_items)
#             else:
#                 selected_item_index = (selected_item_index - 1) % len(menu_items)
#             old_rotation_state = new_rotation_state
#             time.sleep(0.1) # Debounce rotation

        # --- Button Press for Selection ---
        new_state = rot_push.value()
        if new_state != switch_state:
            count += 1
            if count > 3: # Simple debouncing
                if new_state == 0: # Button is pressed
                    # Transition to the selected mode
                    mode = selected_item_index + 1 # Modes 1-based for menu items
                    led_onboard.value(1)
                    time.sleep(0.15)
                    led_onboard.value(0)
                switch_state = new_state
                count = 0
        else:
            count = 0
        utime.sleep(0.01) # Small delay for debouncing

    elif mode == 1:
        # Measure HR Mode (Existing code from original mode == 1 block)
        
        press_to_start()
        time.sleep(2)
        oled.fill(0)
        oled.show()

        x1 = -1
        y1 = 32
        m0 = 65535 / 2
        a = 1 / 10

        disp_div = samplerate / 25
        disp_count = 0
        capture_length = samplerate * 60  # 60 = 60s, changeable respectively

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

        tmr = Timer(freq = samplerate, callback = read_adc)


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
                    if len(PPI_array) > 0: # Changed from > 3 to > 0 to show latest PPI during measurement
                        # Only show the latest interval during measurement
                        oled.text(f'Last PPI:{interval_ms}', 60, 1, 0)
                        # Optional: Display a rolling average HR during measurement
                        if len(PPI_array) > 3:
                            current_mean_ppi = meanPPI_calculator(PPI_array[-5:]) # Average last few for smoother display
                            current_mean_hr = meanHR_calculator(current_mean_ppi)
                            oled.text(f'HR:{current_mean_hr}', 2, 1, 0)
                    oled.text(f'Timer: {int(capture_count/samplerate)}s', 18, 56, 0)
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
                                if sample_peak >= (previous_peak*0.8):
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

        # Clear remaining samples in the FIFO
        while not samples.empty():
            x = samples.get()


        #   HRV calculation   #


        oled.fill(0)
        if len(PPI_array) >= 3:
            # Basic HRV calculations
            mean_PPI = meanPPI_calculator(PPI_array)
            mean_HR = meanHR_calculator(mean_PPI)
            SDNN = SDNN_calculator(PPI_array, mean_PPI)
            RMSSD = RMSSD_calculator(PPI_array)
            SDSD = SDSD_calculator(PPI_array)
            SD1 = SD1_calculator(SDSD)
            SD2 = SD2_calculator(SDNN, SDSD)

            oled.text('Basic HRV Analysis:', 0, 0, 1)
            oled.text('MeanPPI:'+ str(int(mean_PPI)) +'ms', 0, 10, 1)
            oled.text('MeanHR:'+ str(int(mean_HR)) +'bpm', 0, 20, 1)
            oled.text('SDNN:'+str(int(SDNN)) +'ms', 0, 30, 1)
            oled.text('RMSSD:'+str(int(RMSSD)) +'ms', 0, 40, 1)
            oled.text('SD1:'+str(int(SD1))+' SD2:'+str(int(SD2)), 0, 50, 1)

            # Kubios analysis (using existing logic)

            try:
                 connect() # Attempt to connect to WLAN
                 # Kubios API call - ensure connection is successful before this
                 response = requests.post(...)
                 # process response and display PNS/SNS

                 # Placeholder for Kubios results display
                 oled.text('PNS:'+str(PNS), 0, 45, 1)
                 oled.text('SNS:'+str(SNS), 0, 54, 1)

                 oled.text('Kubios data sent', 0, 55, 1) # Indicate if data was sent

            except Exception as e:
                oled.text('WLAN Error', 0, 55, 1)
                print("WLAN or Kubios Error:", e)

        else:
            oled.text('Measurement Error', 0, 20, 1)
            oled.text('Not enough peaks', 0, 30, 1)
            oled.text('for analysis.', 0, 40, 1)

        oled.show()

        # Stay in this mode until button is pressed to return to menu
        count = 0 # Reset debounce counter
        switch_state = rot_push.value() # Get initial state for debouncing
        while mode == 1:
            new_state = rot_push.value()
            if new_state != switch_state:
                count += 1
                if count > 3: # Debounce
                    if new_state == 0: # Button pressed
                        mode = 0 # Return to menu
                        led_onboard.value(1)
                        time.sleep(0.15)
                        led_onboard.value(0)
                    switch_state = new_state
                    count = 0
            else:
                count = 0
            utime.sleep(0.01) # Small delay for debouncing

    elif mode == 2:
        # Basic HRV Analysis Mode (Placeholder)
        collect_data()
        time.sleep(3)
        send_data()
        time.sleep(3)
        oled.fill(0)
        oled.text("Basic HRV Analysis", 5, 5, 1)
        oled.text("Results Here", 5, 20, 1)
        # Implement your basic HRV display logic here
        # You might need to store the last measurement's PPI_array
        oled.show()

        # Stay in this mode until button is pressed to return to menu
        count = 0 # Reset debounce counter
        switch_state = rot_push.value() # Get initial state for debouncing
        while mode == 2:
            new_state = rot_push.value()
            if new_state != switch_state:
                count += 1
                if count > 3: # Debounce
                    if new_state == 0: # Button pressed
                        mode = 0 # Return to menu
                        led_onboard.value(1)
                        time.sleep(0.15)
                        led_onboard.value(0)
                    switch_state = new_state
                    count = 0
            else:
                count = 0
            utime.sleep(0.01) # Small delay for debouncing


    elif mode == 3:
        # History Mode (Placeholder)
        oled.fill(0)
        oled.text("History", 5, 5, 1)
        oled.text("Display history", 5, 20, 1)
        oled.text("data here", 5, 30, 1)
        # Implement your history display logic here
        oled.show()

        # Stay in this mode until button is pressed to return to menu
        count = 0 # Reset debounce counter
        switch_state = rot_push.value() # Get initial state for debouncing
        while mode == 3:
            new_state = rot_push.value()
            if new_state != switch_state:
                count += 1
                if count > 3: # Debounce
                    if new_state == 0: # Button pressed
                        mode = 0 # Return to menu
                        led_onboard.value(1)
                        time.sleep(0.15)
                        led_onboard.value(0)
                    switch_state = new_state
                    count = 0
            else:
                count = 0
            utime.sleep(0.01) # Small delay for debouncing


    elif mode == 4:
        # Kubios Mode (Placeholder)
        oled.fill(0)
        oled.text("Kubios Analysis", 5, 5, 1)
        oled.text("Integrate Kubios", 5, 20, 1)
        oled.text("API calls here", 5, 30, 1)
         # This part of the logic is already in mode 1 for now,
         # you might want to move it fully here if you want
         # a dedicated "Kubios" menu option that runs the analysis
         # on previously captured data.
        oled.show()

        # Stay in this mode until button is pressed to return to menu
        count = 0 # Reset debounce counter
        switch_state = rot_push.value() # Get initial state for debouncing
        while mode == 4:
            new_state = rot_push.value()
            if new_state != switch_state:
                count += 1
                if count > 3: # Debounce
                    if new_state == 0: # Button pressed
                        mode = 0 # Return to menu
                        led_onboard.value(1)
                        time.sleep(0.15)
                        led_onboard.value(0)
                    switch_state = new_state
                    count = 0
            else:
                count = 0
            utime.sleep(0.01) # Small delay for debouncing