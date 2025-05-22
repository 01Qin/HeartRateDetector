import time

from machine import Pin, ADC, I2C, PWM
from ssd1306 import SSD1306_I2C
from fifo import Fifo
from piotimer import Piotimer

import micropython
micropython.alloc_emergency_exception_buf(200)

led = Pin("LED", Pin.OUT)
led22 = PWM(Pin(22))
led22.freq(1000)

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


#=========== Heart Rate Pulse Sensor Settings =====


class HeartRateDetector:
    min_hr = 40
    max_hr = 200
    msg_duration = 3
    measurement_msgs =[
        'It starts after',
        f'{msg_duration}s of measuring.',
        'Put your finger',
        'on the sensor',
        'and hold on.',
        'Press the',
        'BUTTON to quit.',
    ]
    def __init__(self):
        self.rot = Encoder(10, 11)
        self.oled = self.get_oled()
        self.ppi_size = 10
        
        #self.pulse = self.get_pulse()
    
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
    
        oled = SSD1306_I2C(self.width_, self.height_, i2c)
        return oled

    def start(self):
        self.greeting()
        self.menu()

    def greeting(self):
        self.oled.fill(1)
        self.oled.text(f'Heart Beating', 5, 1, 0)
        self.oled.text(f'Group 2', 5, 30, 0)
        self.oled.show()
        time.sleep(1)

    def menu(self):
        items = [
            ('1.MEASURE HR', self.measure_hr),
            ('2.HRV ANALYSIS', self.hrv_analyzing),
            ('3.KUBIOS', None),
            ('4.HISTORY', None),
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

    def waiting(self, msgs, next, duration=3):
        self.oled.fill(0)
        for num, lause in enumerate(msgs):
            self.oled.text(lause, 0, num*9, 1)
        self.oled.show()
        time.sleep(duration)
        next()
    
    def measure_hr(self):
        self.waiting(self.measurement_msgs, self._measure_hr, self.msg_duration)

    def _measure_hr(self, countdown=None):
        step = 10
        scale = 3
        left1 = -1
        top1 = int(self.height_/2)
        max_value = 65535
        half_max = max_value/2
        threshold = int(half_max*1.1)

        amount = 0

        section_amount = 0
        section_count = 0

        hrs = 0
        hrs_amount = 0

        ppi_samples = []
        previous = 0

        goingup = False

        start = 0
        num = 0
        
        pulse = self.get_pulse()
        self.oled.fill(0)
        while True:
            if self.rot.fifo.has_data():
                if self.rot.fifo.get() == 0:
                    pulse.timer.deinit()
                    break

            if not pulse.samples.empty():
                data = pulse.samples.get()
                amount += 1
                #===== Plotting Heartbeat PPG Begin =========
                section_amount += data
                section_count += 1
                if section_count >= step:
                    value = section_amount/step
                    self.oled.fill_rect(0, 0, self.width_, 9, 1)
                    self.oled.fill_rect(0, 55, self.width_, 9, 1)
                    self.oled.text(f'Time:  {int(amount/self.sample_rate)}s', 18, 1, 0)
                    if len(ppi_samples) > 0:
                        ave_ppi = int(sum(ppi_samples)/len(ppi_samples))
                        ave_hr = int(60/ave_ppi*1000)
                        self.oled.text(f'PPI:{ave_ppi}', 2, 56, 0)
                        self.oled.text(f'HR:{ave_hr}', 70, 56, 0)
            
                    left2 = left1 + 1
                    top2 = int(scale * self.half_height * (half_max - value)/half_max + self.offset)
                    top2 = max(self.pulse_top, min(self.pulse_bottom, top2))
                    self.oled.line(left2, self.pulse_top, left2, self.pulse_bottom, 0)
                    self.oled.line(left1, top1, left2, top2, 1)
                    self.oled.show()
                    left1 = left2
                    if left1 >= self.width_:
                        left1 = -1
                    top1 = top2
                    section_amount = 0
                    section_count = 0
        
                #===== Plotting Heartbeat PPG End ==========
        
                #===== PPI/HR Detection Begin ==============

                if start:#start to count ppi
                    num += 1

                if data < threshold:
                    continue

                if data >= previous: # found the rising edge
                    goingup = True
                else: # found the falling edge
                    if goingup:
                        # When a falling edge is found,
                        # if it was in a rising state before,
                        # the previous value is the peak
                        if start:
                            # If already started calculating ppi before
                            # then it is not the first peak,
                            # ppi can be saved here.
                            ppi = round(num/250*1000)
                            hr = round(60/ppi*1000)
                            if hr > self.min_hr and hr < self.max_hr:
                                print(f'BPM: {hr}')
                                led22.duty_u16(4000)
                                time.sleep(0.001)
                                led22.duty_u16(0)
                                hrs += 1
                                hrs_amount += hr
                                ppi_samples.append(ppi)
                                if len(ppi_samples) > self.ppi_size:
                                    ppi_samples.pop(0)
                            num = 0
                        else:#found the first peak
                            start = 1 #set start to count ppi
                            num = 0
                        goingup = False # set the status of falling edge.

                previous = data

                #===== PPI/HR Detection End ==============


    def hrv_analyzing(self):
        self.waiting(self.measurement_msgs, self._hrv_analyzing, self.msg_duration)

    def _hrv_analyzing(self):
        self._measure_hr(countdown=30)


#====== Main Menu End =========

detector = HeartRateDetector()
detector.start()
