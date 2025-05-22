import time
import network
from umqtt.simple import MQTTClient

import urequests as requests
import ujson
import network
from time import sleep

from machine import Pin, ADC, I2C, PWM
from ssd1306 import SSD1306_I2C
from fifo import Fifo
from piotimer import Piotimer

import micropython
micropython.alloc_emergency_exception_buf(200)

led = Pin("LED", Pin.OUT)
led22 = PWM(Pin(22))
led22.freq(1000)

import logo
import loading

# SSID Settings

SSID = "KMD652_Group_2"
PASSWORD = "Xia0/wan9"
BROKER_IP = "192.168.2.253"

# Kubios Settings

APIKEY = "pbZRUi49X48I56oL1Lq8y8NDjq6rPfzX3AQeNo3a"
CLIENT_ID = "3pjgjdmamlj759te85icf0lucv"
CLIENT_SECRET = "111fqsli1eo7mejcrlffbklvftcnfl4keoadrdv1o45vt9pndlef"

LOGIN_URL = "https://kubioscloud.auth.eu-west-1.amazoncognito.com/login"
TOKEN_URL = "https://kubioscloud.auth.eu-west-1.amazoncognito.com/oauth2/token"
REDIRECT_URI = "https://analysis.kubioscloud.com/v1/portal/login"


class WifiDisconnectedError(Exception):
    """ For some reason the wifi could not be connected"""
    pass

# Function to connect to WLAN
def connect_wlan(detector):
    # Connecting to the group WLAN
    detector.oled.msg('Try to connect the WIFI...')
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    retry_times = 10

    # Attempt to connect once per second
    while wlan.isconnected() == False:
        if retry_times <= 0:
            raise WifiDisconnectedError
        print("Connecting... ")
        time.sleep(1)
        retry_times -= 1

    # Print the IP address of the Pico
    print("Connection successful. Pico IP:", wlan.ifconfig()[0])

def connect_mqtt():
    mqtt_client=MQTTClient("", BROKER_IP)
    mqtt_client.connect(clean_session=True)
    return mqtt_client

#====== OLED Wraper ==============
class OLED(SSD1306_I2C):
    def button(self, text, left, top, bg_color):
        self.fill_rect(max(0, left-5), max(0, top-1), 50, 10, bg_color)
        self.text(text, left, top, bg_color^1)

    def msg_lines(self, text):
        lines = []
        nums = 128/8
        words = text.split()
        line = words.pop(0)
        while len(words) > 0:
            word = words.pop(0)

            if (len(word) + len(line) + 1) <= nums:
                line = ' '.join([line, word])
            else:
                lines.append(line)
                line = word
        else:
            lines.append(line)
        return lines

    def msg(self, text):
        self.fill(0)
        self._msg(text)
        self.show()

    def _msg(self, text):
        lines = self.msg_lines(text)
        for num, line in enumerate(lines):
            self.text(line, 0, num*11, 1)

    def msg_waiting(self, text, duration=3):
        loading.loading(self, msg=text, duration=duration)

    def plot_heart(self, left=0, top=0):
        offsets = [
            (2, 0, 2, 0),
            (6, 0, 6, 0),
            (1, 1, 3, 1),
            (5, 1, 7, 1),
            (0, 2, 8, 2),
            (1, 3, 7, 3),
            (2, 4, 6, 4),
            (3, 5, 5, 5),
            (4, 6, 4, 6),
        ]
        self._plot(left, top, offsets)

    def _plot(self, left, top, offsets, color=0):
        for offset in offsets:
            if len(offset) == 2:
                _left, _top = offset
                self.pixel(_left+left, _top+top, color)
            elif len(offset) == 4:
                _left, _top, _left1, _top1 = offset
                self.line(_left+left, _top+top, _left1+left, _top1+top, color)


#====== Rotary Encoder Begin =====
class Encoder:
    def __init__(self, rot_a, rot_b):
        self.a = Pin(rot_a, mode=Pin.IN, pull=Pin.PULL_UP)
        self.b = Pin(rot_b, mode=Pin.IN, pull=Pin.PULL_UP)
        self.button = Pin(12, mode=Pin.IN, pull=Pin.PULL_UP)
        self.last_press = time.ticks_ms()
        self.fifo = Fifo(300, typecode='i')
        self.a.irq(handler=self.handler_turn, trigger=Pin.IRQ_RISING, hard=True)
        self.button.irq(handler=self.handler_press, trigger=Pin.IRQ_RISING, hard=True)

    def handler_turn(self, pin):
        if self.b():
            self.fifo.put(-1)
        else:
            self.fifo.put(1)

    def handler_press(self, pin):
        if time.ticks_diff(time.ticks_ms(), self.last_press) < 300:
            return
        self.fifo.put(0)
        self.last_press = time.ticks_ms()

#====== Rotary Encoder End =======


#=========== Heart Rate Pulse Sensor Settings =====
class Pulse:
    def __init__(self, adc_pin_nr):
        self.sensor = ADC(adc_pin_nr) # sensor AD channel
        self.samples = Fifo(500) # fifo where ISR will put samples
        self.dbg = Pin(0, Pin.OUT) # debug GPIO pin for measuring timing with oscilloscope

    def handler(self, tid):
        self.samples.put(self.sensor.read_u16())
        self.dbg.toggle()

#======= HR Measure Begin =========================
class HRMeasure:

    step = 10
    scale = 3
    left1 = -1
    top1 = int(64/2)
    max_value = 65535
    half_max = max_value/2
    threshold = int(half_max*1.1)

    amount = 0

    section_amount = 0
    section_count = 0

    hrs = 0
    hrs_amount = 0


    previous = 0

    goingup = False

    start = 0
    num = 0

    meet_error = False
    detection_break = False

    def __init__(self, countdown=None, mode='hr'):
        self.countdown = countdown
        self.ppi_samples = []
        self.mode = mode
        #mode in ['hr', 'hrv', 'kubios']

    def run(self, pulse):
        detector.oled.fill(0)
        while True:
            if detector.rot.fifo.has_data():
                if detector.rot.fifo.get() == 0:
                    pulse.timer.deinit()
                    self.detection_break = True
                    break

            if not pulse.samples.empty():
                data = pulse.samples.get()
                self.plotting_ppi(data)
                self.detect_ppi(data)
                if self.countdown == 0:
                    pulse.timer.deinit()
                    if len(self.ppi_samples) <= 1:
                        self.meet_error = 'Detection Error.'
                    else:
                        try:
                            connect_wlan(detector)
                            if self.mode == 'hrv':
                                self.calculate_hrv()
                                # send to mqtt here
                                self.mqtt_publish()
                            elif self.mode == 'kubios':
                                self.kubios_analyzing()
                        except WifiDisconnectedError:
                            self.meet_error = 'Connection Error.'
                    break

    def plotting_ppi(self, data):
        # Plotting Heartbeat PPI
        self.amount += 1
        self.section_amount += data
        self.section_count += 1
        if self.section_count >= self.step:
            value = self.section_amount/self.step
            seconds = int(self.amount/detector.sample_rate)

            detector.oled.fill_rect(0, 0, detector.width_, 9, 1)
            detector.oled.fill_rect(0, 55, detector.width_, 9, 1)
            if self.countdown:
                detector.oled.fill_rect(68, 2, int(seconds*60/self.countdown), 6, 0)
                seconds = self.countdown-seconds
                if seconds == 0:
                    self.countdown = 0
            detector.oled.text(f'Time:{seconds}s', 0, 1, 0)

            if len(self.ppi_samples) > 0:
                self.ave_ppi = int(sum(self.ppi_samples)/len(self.ppi_samples))
                self.ave_hr = int(60/self.ave_ppi*1000)
                detector.oled.text(f'PPI:{self.ave_ppi}', 2, 56, 0)
                detector.oled.text(f'HR:{self.ave_hr}', 70, 56, 0)

            self.left2 = self.left1 + 1
            self.top2 = int(self.scale * detector.half_height * (self.half_max - value)/self.half_max + detector.offset)
            self.top2 = max(detector.pulse_top, min(detector.pulse_bottom, self.top2))
            detector.oled.line(self.left2, detector.pulse_top, self.left2, detector.pulse_bottom, 0)
            detector.oled.line(self.left1, self.top1, self.left2, self.top2, 1)
            detector.oled.show()
            self.left1 = self.left2
            if self.left1 >= detector.width_:
                self.left1 = -1
            self.top1 = self.top2
            self.section_amount = 0
            self.section_count = 0


    def detect_ppi(self,data):
        # PPI/HR Detection

        if self.start:#start to count ppi
            self.num += 1

        if data < self.threshold:
            return

        if data >= self.previous: # found the rising edge
            self.goingup = True
        else: # found the falling edge
            if self.goingup:
                # When a falling edge is found,
                # if it was in a rising state before, 
                # the previous value is the peak
                if self.start:
                    # If already started calculating ppi before
                    # then it is not the first peak,
                    # ppi can be saved here.
                    ppi = round(self.num/250*1000)
                    hr = round(60/ppi*1000)
                    if hr > detector.min_hr and hr < detector.max_hr:
                        print(f'BPM: {hr}')
                        led22.duty_u16(20000)
                        time.sleep(0.001)
                        led22.duty_u16(0)
                        self.hrs += 1
                        self.hrs_amount += hr
                        self.ppi_samples.append(ppi)
                        if len(self.ppi_samples) > detector.ppi_size:
                            self.ppi_samples.pop(0)
                    self.num = 0
                else:#found the first peak
                    self.start = 1 #set start to count ppi
                    self.num = 0
                self.goingup = False # set the status of falling edge.

        self.previous = data

    def calculate_hrv(self):
        ppi_quantity = len(self.ppi_samples)
        sdnn = 0
        rmssd = 0
        sdsd_2nd = 0
        ppi_prev = None
        for ppi in self.ppi_samples:
            sdnn += (ppi-self.ave_ppi)**2
            if ppi_prev is not None:
                rmssd += (ppi - ppi_prev)**2
                sdsd_2nd += ppi - ppi_prev
            ppi_prev = ppi

        self.sdnn = round((sdnn/(ppi_quantity-1))**(1/2))
        self.rmssd = round((rmssd/(ppi_quantity-1))**(1/2))
        self.sdsd = round((rmssd /(ppi_quantity-1)-(sdsd_2nd/ppi_quantity)**2)**(1/2))
        print(f'sdnn: {self.sdnn}')
        print(f'rmssd: {self.rmssd}')
        print(f'sdsd: {self.sdsd}')
        self.sd1 = round(((self.sdsd**2)/2)**(1/2))
        self.sd2 = round((2*(self.sdnn**2)-(self.sdsd**2)/2)**(1/2))

    def mqtt_publish(self):
        detector.oled.msg_waiting('SENDING TO MQTT...')
        try:
            mqtt_client=connect_mqtt()

        except Exception as e:
            error_msg = f"MQTT ERROR: Failed to connect: {e}"
            self.meet_error = error_msg
            print(error_msg)

        # Send MQTT message
        try:
            measurement = self.outcome_mqtt()
            json_message = ujson.dumps(measurement)
            mqtt_client.publish(detector.mqtt_topic, json_message)
            print(f"Sending to MQTT: {detector.mqtt_topic} -> {json_message}")

        except Exception as e:
            error_msg = f"MQTT ERROR: Failed to publish: {e}"
            self.meet_error = error_msg
            print(error_msg)



    def kubios_analyzing(self):
        #detector.oled.msg('SENDING DATA TO KUBIOS, PLEASE WAIT FOR SEVERAL SECONDS...')
        detector.oled.msg_waiting('SENDING TO KUBIOS...')
        dataset = {
            "type": "RRI",
            "data": self.ppi_samples,
            "analysis": {"type": "readiness"}
        }

        response = requests.post(
            url = TOKEN_URL,
            data = 'grant_type=client_credentials&client_id={}'.format(CLIENT_ID),
            headers = {'Content-Type':'application/x-www-form-urlencoded'},
            auth = (CLIENT_ID, CLIENT_SECRET)
            )
        response = response.json() #Parse JSON response into a python dictionary
        access_token = response["access_token"] #Parse access token

        response = requests.post(
            url = "https://analysis.kubioscloud.com/v2/analytics/analyze",
            headers = {
                "Authorization": "Bearer {}".format(access_token), #use access token to access your Kubios Cloud analysis session
                "X-Api-Key": APIKEY
            },
            json = dataset) #dataset will be automatically converted to JSON by the urequests library
        response = response.json()

        if response['status'] == 'ok':
            res = response['analysis']
            for item, decimal in [
                ('rmssd_ms', 1),
                ('sdnn_ms', 1),
                ('sd1_ms', 1),
                ('sd2_ms', 1),
                ('sns_index', 3),
                ('pns_index', 3)
                ]:

                if decimal:
                    value_ = round(res[item], decimal)
                else:
                    value_ = round(res[item])
                setattr(self, item.split('_')[0], value_)
        elif response['status'] == 'error':
            self.meet_error = 'KUBIOS ERROR: ' + response['error']



    def outcome(self):
        year, month, day, hour, minute = time.localtime()[:5]
        dt = f'{day:0>2d}.{month:0>2d}.{year} {hour:0>2d}:{minute:0>2d}'
        res = [
            f'{dt}',
            f'',
            f'MEAN HR:{self.ave_hr}',
            f'MEAN PPI:{self.ave_ppi}',
            f'RMSSD:{self.rmssd}',
            f'SDNN:{self.sdnn}',
            f'SD1:{self.sd1}',
            f'SD2:{self.sd2}',
        ]
        if self.mode == 'kubios':
            res.extend([
                f'SNS:{self.sns}',
                f'PNS:{self.pns}',
            ])
        res.append('Press to quit:->')
        return res

    def outcome_mqtt(self):
        measurement = {
            "mean_hr": self.ave_hr,
            "mean_ppi": self.ave_ppi,
            "rmssd": self.rmssd,
            "sdnn": self.sdnn,
            "sd1": self.sd1,
            "sd2": self.sd2
        }
        return measurement

#=========== Heart Rate Pulse Sensor Settings =====


class HeartRateDetector:
    min_hr = 40
    max_hr = 200
    msg_duration = 3
    detection_duration = 35
    mqtt_topic = "CardioWave-Pro"
    measurement_msgs = 'Loading...'
    (
        f'It starts after {msg_duration}s '
        'of measuring. Put your finger on '
        'the sensor and hold on. Press the '
        'BUTTON to quit.'
    )
    def __init__(self):
        self.rot = Encoder(10, 11)
        self.oled = self.get_oled()
        self.ppi_size = 20
        self.histories = []
        self.histories_count = 5

    def get_pulse(self):
        pulse_pin = 27
        self.sample_rate = 250
        pulse = Pulse(pulse_pin)
        pulse.timer = Piotimer(mode=Piotimer.PERIODIC, freq=self.sample_rate, callback=pulse.handler)
        return pulse

    def get_oled(self):
        # OLED Screen Settings
        if hasattr(self, 'oled'):
            return self.oled
        self.width_ = 128
        self.height_ = 64
        self.line_h = 8
        self.pulse_top = 10+2
        self.pulse_bottom = 53-2
        self.half_height = self.height_/2
        self.offset = 40
        i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)

        oled = OLED(self.width_, self.height_, i2c)
        return oled

    def start(self):
        while True:
            try:
                self.greeting()
                self.menu()
            except Exception as e:
                error_msg = f"UNKNOWN ERROR: {e}"
                waiting = 3
                error_msg += f' Restart in {waiting} seconds.'
                self.oled.msg_waiting(error_msg, waiting)
                self.oled.msg_waiting('Restarting...', waiting)
                print(error_msg)

    def greeting(self):
        logo.plot_greeting(self.oled)
        time.sleep(3)

    def menu(self):
        items = [
            ('1.MEASURE HR', self.measure_hr),
            ('2.HRV ANALYSIS', self.hrv_analyzing),
            ('3.KUBIOS', self.kubios_analyzing),
            ('4.HISTORY', self.show_histories),
        ]
        current = 0
        self._menu(items, current)
        while True:
            while self.rot.fifo.has_data():
                value = self.rot.fifo.get()
                if value == 0:
                    method = items[current][1]
                    method()
                else:
                    current += value
                    current = current % len(items)
                self._menu(items, current)

    def _menu(self, items, current=0):
        self.oled.fill(0)
        for num, item in enumerate(items):
            text_color = 1
            left = 0
            top = num * 16 + 4
            left2 = self.width_
            top2 = 12

            if current==num:
                text_color = 0
                self.oled.fill_rect(0, top-2, left2, top2, 1)
            self.oled.text(item[0], 0, top, text_color)
        self.oled.show()

    def measure_hr(self):
        self.oled.msg_waiting(self.measurement_msgs, self.msg_duration)
        self._measure_hr()

    def _measure_hr(self, countdown=None, mode='hr'):
        pulse = self.get_pulse()
        hr_measure = HRMeasure(countdown=countdown, mode=mode)
        hr_measure.run(pulse)
        return hr_measure

    def hrv_analyzing(self):
        self.oled.msg_waiting(self.measurement_msgs, self.msg_duration)
        self._hrv_analyzing()

    def _hrv_analyzing(self, mode='hrv'):
        current = 0
        left_bg = 1
        right_bg = 0
        while True:
            hr_measure = self._measure_hr(countdown=self.detection_duration, mode=mode)
            if hr_measure.meet_error:
                while True:
                    if self.rot.fifo.has_data():
                        value = self.rot.fifo.get()
                        if value == 0:
                            if current == 0:
                                break
                            else:
                                return
                        else:
                            current += value
                            current = current % 2
                            left_bg, right_bg = right_bg, left_bg

                    self.oled.fill(0)
                    self.oled._msg(hr_measure.meet_error)
                    self.oled.button('Retry', 5, 55, left_bg)
                    self.oled.button('Back', 90, 55, right_bg)
                    self.oled.show()
            elif hr_measure.detection_break:
                return
            else:
                break

        items = hr_measure.outcome()
        self.histories.append(items)
        if len(self.histories) > self.histories_count:
            self.histories.pop(0)
        self.show_outcome(items)

    def show_outcome(self, items):
        pointer = 0
        while True:
            self.oled.fill(0)
            for num, prop in enumerate(items[pointer:pointer+6]):
                self.oled.text(prop, 0, 10*num, 1)
            self.oled.show()

            if self.rot.fifo.has_data():
                value = self.rot.fifo.get()
                if value == 0:
                    break
                else:
                    pointer += value
                    pointer = min(len(items)-6, max(0, pointer))

    def kubios_analyzing(self):
        self.oled.msg_waiting(self.measurement_msgs, self.msg_duration)
        self._kubios_analyzing()

    def _kubios_analyzing(self):
        self._hrv_analyzing(mode='kubios')

    def show_histories(self):
        current = 0
        items = [f'MEASUREMENT {i+1}' for i in range(len(self.histories))]
        items.append('Back')
        self._show_histories(items, current)
        while True:
            if self.rot.fifo.has_data():
                value = self.rot.fifo.get()
                if value == 0:
                    if current == len(items) - 1:
                        break
                    self.show_outcome(self.histories[current])
                else:
                    current += value
                    current = current % len(items)
                self._show_histories(items, current)

    def _show_histories(self, items, current=0):
        self.oled.fill(0)
        for num, item in enumerate(items):
            text_color = 1
            left = 0
            top = num * 10 + 4
            left2 = self.width_
            top2 = 10

            if current==num:
                text_color = 0
                self.oled.fill_rect(0, top-2, left2, top2, 1)
            self.oled.text(item, 0, top, text_color)
        self.oled.show()

#====== Main Menu End =========

detector = HeartRateDetector()
detector.start()
