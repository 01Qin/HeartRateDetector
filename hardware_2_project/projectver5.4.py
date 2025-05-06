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
import os
import MQTTClient


# Define menu items
menu_items = [
    "1.Measure HR ",
    "2.HRV analysis",
    "3.History",
    "4.Kubios ",
]

# ADC-converter
adc = ADC(26)

# OLED
i2c = I2C(1, scl=Pin(15), sda=Pin(14))
oled = SSD1306_I2C(128, 64, i2c)

# LEDs
led_onboard = Pin("LED", Pin.OUT)
led21 = PWM(Pin(21))
led21.freq(1000)

# Rotary Encoder Pins
rotary_A = Pin(10, Pin.IN, Pin.PULL_UP)
rotary_B = Pin(11, Pin.IN, Pin.PULL_UP)
rot_push = Pin(12, Pin.IN, Pin.PULL_UP)

# Sample Rate, Buffer, Menu and debounce variables
samplerate = 250
samples = Fifo(32)
mode = 0  # 0: Menu, 1: Measure HR, 2: Basic HRV, 3: History, 4: Kubios
count = 0  # For button debouncing
switch_state = rot_push.value()  # Initially read the state
selected_item_index = 0  # Index of the currently selected menu item

# Global variable for encoder tracking
last_rotary_A = rotary_A.value()

# --- Encoder Interrupt Handler ---
def encoder_handler(pin):
    global selected_item_index, last_rotary_A
    # Get the current state of rotary_A and the secondary signal from rotary_B:
    new_A = rotary_A.value()
    new_B = rotary_B.value()
    
    if new_A != last_rotary_A:
        # When A goes low, check B to decide the direction.
        if new_A == 0:
            if new_B == 1:
                selected_item_index = (selected_item_index + 1) % len(menu_items)
            else:
                selected_item_index = (selected_item_index - 1) % len(menu_items)
    last_rotary_A = new_A

# Attach the interrupt to rotary_A 
rotary_A.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=encoder_handler)

# Function for reading ADC
def read_adc(tid):
    x = adc.read_u16()
    samples.put(x)

# ---------------------------------------------------------------------
# Display Functions
# ---------------------------------------------------------------------
def welcome_text():
    oled.fill(1)
    horizontal1 = 0
    horizontal2 = 0
    # Draw first group of patterns
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

    # Draw second group of patterns
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

def display_menu(items, selected_index):
    oled.fill(0)
    for i, item in enumerate(items):
        if i == selected_index:
            # Highlight selected item using a filled rectangle
            oled.fill_rect(0, i * 10, 128, 10, 1)
            oled.text(item, 5, i * 10 + 1, 0)
        else:
            oled.text(item, 5, i * 10 + 1, 1)
    oled.show()

def press_to_start():
    oled.fill(0)
    oled.text("Starting the ", 4, 7, 1)
    oled.text("measurement...", 4, 17, 1)
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

# def collect_data():
#     oled.fill(0)
#     oled.text("Collecting", 4, 7, 1)
#     oled.text("Data...", 4, 17, 1)
#     oled.text("(^_-)/", 15, 53, 1)
#     oled.show()
# 
# def send_data():
#     oled.fill(0)
#     oled.text("Sending", 4, 7, 1)
#     oled.text("Data...", 4, 17, 1)
#     oled.text("(>_<)", 15, 53, 1)
#     oled.show()

# ---------------------------------------------------------------------
# Connectivity and HRV calculation functions
# ---------------------------------------------------------------------
ssid = 'KME759_Group_1'
password = 'KME759bql'
broker_ip = "192.168.1.254"

APIKEY = "YP8FLwf7hM80gEoZ4CqEU8H3wP2u2hB9vWAzxScc"
CLIENT_ID = "70qhb6977htoee1u3th2aqf1td"
CLIENT_SECRET = "1skja75f2f2a3pnt9ms6091ego0jbo1i9cp1fnb3ol7pi766b943"

LOGIN_URL = "https://kubioscloud.auth.eu-west-1.amazoncognito.com/login"
TOKEN_URL = "https://kubioscloud.auth.eu-west-1.amazoncognito.com/oauth2/token"
REDIRECT_URI = "https://analysis.kubioscloud.com/v1/portal/login"
ANALYSIS_URL = "https://analysis.kubioscloud.com/v2/analytics/analyze"

def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    ip = wlan.ifconfig()[0]
    print(ip)
    return

def connect_mqtt():
    mqtt_client = MQTTClient("", broker_ip)
    mqtt_client.connect(clean_session=True)
    return mqtt_client

def meanPPI_calculator(data):
    if not data:
        return 0
    return int(round(sum(data)/len(data), 0))

def meanHR_calculator(meanPPI):
    if meanPPI == 0:
        return 0
    return int(round(60*1000/meanPPI, 0))

def SDNN_calculator(data, PPI):
    if len(data) < 2:
        return 0
    summary = sum((i - PPI) ** 2 for i in data)
    return int(round((summary/(len(data)-1))**0.5, 0))

def RMSSD_calculator(data):
    if len(data) < 2:
        return 0
    summary = 0
    for i in range(len(data)-1):
        summary += (data[i+1] - data[i])**2
    return int(round((summary/(len(data)-1))**0.5, 0))

def SDSD_calculator(data):
    if len(data) < 2:
        return 0
    PP_array = array.array('l')
    for i in range(len(data)-1):
        PP_array.append(int(data[i+1])-int(data[i]))
    if len(PP_array) < 2:
         return 0
    first_value = sum(float(val**2) for val in PP_array)
    second_value = sum(float(val) for val in PP_array)
    first = first_value/len(PP_array)
    second = (second_value/len(PP_array))**2
    inside_sqrt = first - second
    if inside_sqrt < 0:
        print("Warning: Negative value.")
        return 0
    return int(round((inside_sqrt)**0.5, 0))

def SD1_calculator(SDSD):
    return int(round(((SDSD**2)/2)**0.5, 0))

def SD2_calculator(SDNN, SDSD):
    inside_sqrt = (2*(SDNN**2)) - ((SDSD**2)/2)
    if inside_sqrt < 0:
         print("Warning: Negative value.")
         return 0
    return int(round((inside_sqrt)**0.5, 0))

def print_kubios_summary(response):
    if response.get("status") != "ok":
        print("Analysis failed.")
        return

    analysis = response["analysis"]
    print("\n--- Kubios HRV Summary ---")
    print(f"Timestamp: {analysis.get('create_timestamp')}")
    print(f"Mean HR (bpm): {analysis.get('mean_hr_bpm'):.2f}")
    print(f"Mean RR (ms): {analysis.get('mean_rr_ms'):.2f}")
    print(f"SDNN (ms): {analysis.get('sdnn_ms'):.2f}")
    print(f"RMSSD (ms): {analysis.get('rmssd_ms'):.2f}")
    print(f"PNS Index: {analysis.get('pns_index'):.2f}")
    print(f"SNS Index: {analysis.get('sns_index'):.2f}")
    print(f"Readiness Score: {analysis.get('readiness'):.1f}")
    print(f"Physiological Age: {analysis.get('physiological_age')}")


# ---------------------------------------------------------------------
# Main Program Loop
# ---------------------------------------------------------------------
welcome_text()
avg_size = 128
buffer = array.array('H', [0] * avg_size)

while True:
    if mode == 0:
        # --- Menu Mode ---
        display_menu(menu_items, selected_item_index)

        # Check for push button press.
        new_state = rot_push.value()
        if new_state != switch_state:
            count += 1
            if count > 3:  # Debounce threshold
                if new_state == 0:  # Button pressed → select the item
                    mode = selected_item_index + 1  # Modes are 1-based for menu actions
                    led_onboard.value(1)
                    time.sleep(0.15)
                    led_onboard.value(0)
                switch_state = new_state
                count = 0
        else:
            count = 0
        utime.sleep(0.01)  # Small delay for debouncing

    elif mode == 1:
        # --- Measure HR Mode ---
        press_to_start()
        time.sleep(2)
        oled.fill(0)
        oled.show()

        # Initial variables for plotting and measurement
        x1 = -1
        y1 = 32
        m0 = 65535 / 2
        a = 1 / 10
        disp_div = samplerate / 25
        disp_count = 0
        capture_length = samplerate * 60  # 60 seconds measurement
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
        
        measurement_aborted= False

        tmr = Timer(freq=samplerate, callback=read_adc)
        

        count = 0
        switch_state = rot_push.value()

        # Sampling and plotting
        while capture_count < capture_length and not measurement_aborted:
            new_state = rot_push.value()
            if new_state != switch_state:
                count += 1
                if count > 3: # Debounce threshold
                    if new_state == 0: # Button pressed (low when pressed due to PULL_UP)
                        # Check if we are still in the measurement mode
                        
                      
                        measurement_aborted = True # Set the flag
                        led_onboard.value(1)
                        time.sleep(0.15)
                        led_onboard.value(0)
                        break # Exit the measurement loop immediately
                    switch_state = new_state
                    count = 0
            else:
                count = 0
            
            
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
                    if len(PPI_array) > 0:
                        oled.text(f'PPI:{interval_ms}', 60, 1, 0)
                        if len(PPI_array) > 3:
                            current_mean_ppi = meanPPI_calculator(PPI_array[-5:])
                            current_mean_hr = meanHR_calculator(current_mean_ppi)
                            print(f'Mean HR is {current_mean_hr}bpm.')
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

                # Peak detection logic
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
            samples.get()
        if measurement_aborted:
            # If aborted, just display a message and go back to the menu
            oled.fill(0)
            oled.text("Measurement", 0, 20, 1)
            oled.text("Stopped.", 0, 30, 1)
            
            oled.show()
            time.sleep(2)
            
            global last_measurement_data
            last_measurement_data = {}
            # Go back to the main menu mode
            mode = 0
            time.sleep(0.5)
        else:
            oled.fill(0)
            if len(PPI_array) >= 3:
                global last_ppi_array
                last_ppi_array = list(PPI_array)
            
                mean_PPI = meanPPI_calculator(PPI_array)
                mean_HR = meanHR_calculator(mean_PPI)
                SDNN = SDNN_calculator(PPI_array, mean_PPI)
                RMSSD = RMSSD_calculator(PPI_array)
                SDSD = SDSD_calculator(PPI_array)
                SD1 = SD1_calculator(SDSD)
                SD2 = SD2_calculator(SDNN, SDSD)
            
                global last_measurement_data
                last_measurement_data = {} # Clear previous data
                last_measurement_data['basic_hrv'] = {
                    'mean_ppi': mean_PPI,
                    'mean_hr': mean_HR,
                    'sdnn': SDNN,
                    'rmssd': RMSSD,
                    'sdsd': SDSD,
                    'sd1': SD1,
                    'sd2': SD2
                }
                last_measurement_data['data'] = list(PPI_array) # Save the raw data too
                last_measurement_data['type'] = "RRI" # Indicate data type

                
                # Add the current time as the timestamp for this measurement
                last_measurement_data['timestamp'] = utime.time() 

                # Save the data to sample.json
               
                try:
                    with open('sample.json', 'w') as outfile:
                        ujson.dump(last_measurement_data, outfile)
                    print("Measurement data saved to sample.json")
                 
                except Exception as save_e:
                    print("Error saving measurement data:", save_e)
                    
           

            
                oled.text('MeanHR:' + str(mean_HR) + 'bpm', 0, 20, 1)
                global last_measurement_data
                last_measurement_data = {}

                try:
                 connect()  # Connect to WLAN
                 response = requests.post(
                     url = TOKEN_URL,
                     data = 'grant_type=client_credentials&client_id={}'.format(CLIENT_ID),
                     headers = {'Content-Type':'application/x-www-form-urlencoded'},
                     auth = (CLIENT_ID, CLIENT_SECRET)
                     )
                 response = response.json()
                 print_kubios_summary(response)
                 access_token = response['access_token']
                 
                 intervals = PPI_array
                 print(intervals)


                    #Create the dataset dictionary 
                 dataset = {
                     "type": "RRI",
                     "data": intervals,
                     "analysis": {"type": "readiness"}
                    }

                 # Make the readiness analysis with the given data
                 token_response = requests.post(
                    url = "https://analysis.kubioscloud.com/v2/analytics/analyze",
                    headers = {
                        "Authorization": "Bearer {}".format(access_token), #use access token toaccess your Kubios Cloud analysis session
                        "X-Api-Key": APIKEY},
                    json = dataset)
                  
                 print(token_response.json())
                 token_response = token_response.json()
        
                
#                  oled.text('Kubios Results:', 0, 55, 1) # Indicate start of Kubios results
#                  oled.show()
                 # Process Kubios results
                 if 'analysis' in token_response and 'sns_index' in token_response['analysis'] and 'pns_index' in token_response['analysis']:
                     #SNS = round(response_json['analysis']['sns_index'], 2)
                     #PNS = round(analysis_response_json['analysis']['pns_index'], 2)
                    # Display the actual values
                     #print(str(PNS))
                     #print(str(SNS))
                     #oled.text('PNS:'+str(PNS), 0, 45, 1) # Adjust y-coordinate if needed to not overlap Basic HRV
                     print('analysis')
                     #oled.text('SNS:'+str(SNS), 60, 45, 1) # Display SNS next to PNS
                 else:
                     print('Kubios: No results')
            
                except Exception as e:
                    print("WLAN or Kubios Error:", e)
            else:
                print('Measurement Error')
 

        oled.show()

        # Wait until button is pressed to return to the main menu.
        count = 0
        switch_state = rot_push.value()
        while mode == 1:
            new_state = rot_push.value()
            if new_state != switch_state:
                count += 1
                if count > 3:
                    if new_state == 0:
                        mode = 0
                        led_onboard.value(1)
                        time.sleep(0.15)
                        led_onboard.value(0)
                    switch_state = new_state
                    count = 0
            else:
                count = 0
            utime.sleep(0.01)

    elif mode == 2:
        # --- Basic HRV Analysis Mode ---

        oled.fill(0)
        oled.text(" HRV Analysis", 0, 0, 1)
        
            
        oled.text('MeanPPI:' + str(mean_PPI) + 'ms', 0, 10, 1)
        oled.text('MeanHR:' + str(mean_HR) + 'bpm', 0, 20, 1)
        oled.text('SDNN:' + str(SDNN) + 'ms', 0, 30, 1)
        oled.text('RMSSD:' + str(RMSSD) + 'ms', 0, 40, 1)
        oled.text('SD1:' + str(SD1) + ' SD2:' + str(SD2), 0, 50, 1)
        
        
        oled.show()
        
        count = 0
        switch_state = rot_push.value()
        while mode == 2:
            new_state = rot_push.value()
            if new_state != switch_state:
                count += 1
                if count > 3:
                    if new_state == 0:
                        mode = 0
                        led_onboard.value(1)
                        time.sleep(0.15)
                        led_onboard.value(0)
                    switch_state = new_state
                    count = 0
            else:
                count = 0
            utime.sleep(0.01)

    elif mode == 3:
        # --- History Mode ---
        oled.fill(0)
        oled.text("Measurement 1", 0, 10, 1)
        oled.show()
        time.sleep(2)
        oled.fill(0)
        oled.text("History", 5, 0, 1) 

        json_object = None
        history_loaded = False

        try:
            if 'sample.json' in os.listdir('/'): # Check if file exists
                with open('sample.json', 'r') as openfile:
                    json_object = ujson.load(openfile)
                history_loaded = True
                print("History file loaded successfully.") # Debugging
            else:
                 print("History file not found.")

        except Exception as e:
             print(f"Error loading history file: {e}")



        if history_loaded and json_object and isinstance(json_object, dict):
            # Display Timestamp
            timestamp = json_object.get("timestamp")
            if timestamp:
                try:
                    t = utime.localtime(timestamp)
                    timestamp_str = f"{t[0]:04d}{t[1]:02d}{t[2]:02d} {t[3]:02d}:{t[4]:02d}"
                    oled.text(timestamp_str, 5, 10, 1) 
                    
                except Exception as ts_e:
                    print(f"Error formatting timestamp: {ts_e}")
            


            # Display Basic HRV Data (Left side)
            basic_hrv_data = json_object.get("basic_hrv")
            if basic_hrv_data and isinstance(basic_hrv_data, dict):
                oled.text(f"RMSSD:{basic_hrv_data.get('rmssd', 'N/A')}ms", 5, 20, 1)
                oled.text(f"PPI:{basic_hrv_data.get('mean_ppi', 'N/A')}ms", 5, 30, 1)        
                oled.text(f"HR:{basic_hrv_data.get('mean_hr', 'N/A')}bpm", 5, 40, 1)
                oled.text(f"SDNN:{basic_hrv_data.get('sdnn', 'N/A')}ms", 5, 50, 1)

            # Display Kubios Analysis Data 
            kubios_analysis_data = json_object.get("analysis")
            if kubios_analysis_data and isinstance(kubios_analysis_data, dict):
                 oled.text("Kubios:", 65, 25, 1) # Adjusted position
                 oled.text(f"PNS:{kubios_analysis_data.get('pns_index', 'N/A'):.2f}", 65, 35, 1)
                 oled.text(f"SNS:{kubios_analysis_data.get('sns_index', 'N/A'):.2f}", 65, 45, 1)
                 oled.text(f"Readiness: {kubios_analysis_data.get('readiness', 'N/A')}", 65, 55, 1)


            # Check if any analysis data was found (Basic or Kubios)
            if not basic_hrv_data and not kubios_analysis_data:
                 # Only display this if the file was loaded but contained no analysis data
                 if history_loaded:
                     print("No analysis data.")
                    


        oled.show()

        # Wait until button is pressed to return to the main menu.
        count = 0
        switch_state = rot_push.value()
        while mode == 3:
            new_state = rot_push.value()
            if new_state != switch_state:
                count += 1
                if count > 3:
                    if new_state == 0:
                        mode = 0
                        led_onboard.value(1)
                        time.sleep(0.15)
                        led_onboard.value(0)
                    switch_state = new_state
                    count = 0
            else:
                count = 0
            utime.sleep(0.01)

    elif mode == 4:
        # --- Kubios Mode ---
        oled.fill(0)
        oled.text("Kubios Analysis", 5, 5, 1)

        if 'last_ppi_array' in globals() and len(last_ppi_array) >= 3:
            oled.text("Connecting...", 5, 20, 1)
            oled.show()
            try:
                connect()  

                # Get Access Token
                oled.text("Getting Token...", 5, 30, 1)
                oled.show()
                token_response = requests.post(
                    url = TOKEN_URL,
                    data = 'grant_type=client_credentials&client_id={}'.format(CLIENT_ID),
                    headers = {'Content-Type':'application/x-www-form-urlencoded'},
                    auth = (CLIENT_ID, CLIENT_SECRET)
                )
                token_data = token_response.json()
                print("Token Response:", token_data) # For debugging
                access_token = token_data.get('access_token')

                if access_token:
                    oled.text("Sending Data...", 5, 40, 1)
                    oled.show()
                    intervals = last_ppi_array

                    dataset = {
                        "type": "RRI",
                        "data": intervals,
                        "analysis": {"type": "readiness"}
                    }

                    # Make the readiness analysis with the given data
                    analysis_response = requests.post(
                        url = ANALYSIS_URL,
                        headers = {
                            "Authorization": "Bearer {}".format(access_token),
                            "X-Api-Key": APIKEY
                        },
                        json = dataset
                    )

                    analysis_data = analysis_response.json()
                    print("Analysis Response:", analysis_data) # For debugging

                    oled.fill(0) 
                

                    if analysis_data.get("status") == "ok" and "analysis" in analysis_data:
                        analysis = analysis_data["analysis"]
                        
                        oled.text(f"MeanHR:{analysis.get('mean_hr_bpm', 0.0):.1f}bpm", 5, 0, 1)
                        oled.text(f"MeanPPI:{analysis.get('mean_rr_ms', 0.0):.1f}ms", 5, 10, 1)
                        oled.text(f"SDNN:{analysis.get('sdnn_ms', 0.0):.1f}ms", 5, 20, 1)
                        oled.text(f"RMSSD:{analysis.get('rmssd_ms', 0.0):.1f}ms", 5, 30, 1)          
                        oled.text(f"PNS:{analysis.get('pns_index', 0.0):.2f}",5, 40, 1)
                        oled.text(f"SNS:{analysis.get('sns_index', 0.0):.2f}", 5, 50, 1)
                    else:
                        print("Analysis Failed.")

                else:
                    print("Failed to get token.")
               


            except Exception as e:
                
                print("Kubios Error.")
                
                error_str = str(e)
                oled.text(error_str[:16], 5, 20, 1) # Display first part
                if len(error_str) > 16:
                    oled.text(error_str[16:32], 5, 30, 1) # Display second part
                
                print("Kubios Analysis Error:", e) # Print full error to console for debugging

        else:
            print("No data.")


        oled.show()

        # Wait until button is pressed to return to the main menu.
        count = 0
        switch_state = rot_push.value()
        while mode == 4:
            new_state = rot_push.value()
            if new_state != switch_state:
                count += 1
                if count > 3:
                    if new_state == 0:
                        mode = 0
                        led_onboard.value(1)
                        time.sleep(0.15)
                        led_onboard.value(0)
                    switch_state = new_state
                    count = 0
            else:
                count = 0
            utime.sleep(0.01)
        

