from ssd1306 import SSD1306_I2C
from machine import Pin, ADC, I2C, PWM
from fifo import Fifo
import utime
import array
import time

# ADC-converter
adc = ADC(26)

# OLED
i2c = I2C(1, scl = Pin(15), sda = Pin(14))
oled = SSD1306_I2C(128, 64, i2c)

# LEDs
led_onboard = Pin("LED", Pin.OUT)
led21 = PWM(Pin(21))
led21.freq(1000)

# Rotary Encoder
rot_push = Pin(12, mode = Pin.IN, pull = Pin.PULL_UP)
rota = Pin(10, mode = Pin.IN, pull = Pin.PULL_UP)
rotb = Pin(11, mode = Pin.IN, pull = Pin.PULL_UP)

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