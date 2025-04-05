"""
Hardware project simulator
First year hardware project
School of ICT
Metropolia University of Applied Sciences
18.3.2024, Sakari Lukkarinen

This simulator shows all connections for the hardware project
protoboard, except the heart rate sensor. The protoboards contains:
- three LEDs
- three microbuttons
- rotary knob with push button
- 128x64 OLED display, and
- Raspberry Pi Pico
Note that additional library ssd1306.py needs to be installed in
Thonny (Tools > Manage Packages, Search: ssd1306, Install).
"""

import machine
from machine import Pin, I2C, ADC
from ssd1306 import SSD1306_I2C
import utime

# Microbuttons connections to Pico's GPIOs
SW_2 = 7
SW_1 = 8
SW_0 = 9

# Microbuttons
but0 = Pin(SW_0, Pin.IN, Pin.PULL_UP)
but1 = Pin(SW_1, Pin.IN, Pin.PULL_UP)
but2 = Pin(SW_2, Pin.IN, Pin.PULL_UP)

# Rotary coder connections to Pico's GPIOs
C_LEFT = 10
C_RIGHT = 11
C_SWITCH = 12

# Pins for the coder
p1 = Pin(C_LEFT, Pin.IN)
p2 = Pin(C_RIGHT, Pin.IN)
# Connect switch to pin, use pull-up resistor, default value is 1
# When the knob switch is pressed, the value changes to 0
p3 = Pin(C_SWITCH, Pin.IN, Pin.PULL_UP)

# OLED I2C connection to Pico's GPIOS
OLED_SDA = 14
OLED_SCL = 15

# Initialize I2C to control the OLED
i2c = I2C(1, scl=Pin(OLED_SCL), sda=Pin(OLED_SDA), freq=400000)
OLED_WIDTH, OLED_HEIGHT = 128, 64
oled = SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c)

# LED connections to Pico's GPIOs
D3 = 20 # Protoboard's LED3
D2 = 21 # Protoboard's LED2
D1 = 22 # Protoboard's LED1
D0 = 25 # Pico's internal LED

# Analog channel connections to Pico's GPIOs
A0 = 26
A1 = 27

# Heart rate detector is connected to A0
adc = ADC(Pin(A0))


# Pins for LEDs
led0 = Pin(D0, Pin.OUT)
led1 = Pin(D1, Pin.OUT)
led2 = Pin(D2, Pin.OUT)
led3 = Pin(D3, Pin.OUT)

# Turn the LEDs on
led0.value(0)
led1.value(0)
led2.value(0)
led3.value(0)

# Template functions for microbuttons
def button_0(pin):
    print(f'Button 0 pressed, toggle Led 1.')
    led1.toggle()
    
def button_1(pin):
    print(f'Button 1 pressed, toggle Led 2.')
    led2.toggle()
    
def button_2(pin):
    print(f'Button 2 pressed, toggle Led 3.')
    led3.toggle()

# Activate interruptions for microbuttons
but0.irq(button_0, Pin.IRQ_FALLING)
but1.irq(button_1, Pin.IRQ_FALLING)
but2.irq(button_2, Pin.IRQ_FALLING)

# Coder function for rotary knob
counter = 0
def decode(pin):
    global counter
    # Read the pin values
    b = p2.value()
    if b == 1:
        counter += 1
        print(f'Rotated >> {counter}')
    if b == 0:
        counter -= 1
        print(f'Rotated << {counter}')

# Function for rotary knob's button
def switch_pressed(pin):
    global counter
    print('Knob pressed. Counter reset.')
    counter = 0

# Activate interruptions for rotary knob and button
p1.irq(decode, Pin.IRQ_FALLING)
p3.irq(switch_pressed, Pin.IRQ_FALLING)

# Wait for a second
utime.sleep(1)

# Fill the OLED with light
oled.fill(1)
oled.show()

# Wait for a second
utime.sleep(1)

# Clear the display (off)
oled.fill(0)
oled.show()

# Repeat
while True:
    # Write text to OLED
    oled.text('Hardware project', 1, 1)
    oled.text('School of ICT', 1, 11)
    oled.text('Metropolia UAS', 1, 21)
    oled.text('18.3.2024', 1, 31)
    oled.text('123456789-123456', 1, 48)

    # Draw rectangles around the last numbers
    oled.rect(0, 41, 128, 23, 2)
    oled.rect(0, 42, 128, 21, 2)
    oled.show()

    # Wait for 2 seconds
    utime.sleep(2)

    # Clear the display
    oled.fill(0)
    oled.show()

    # Toggle on board led
    led0.toggle()

    # Wait for 0.5 second
    utime.sleep(0.5)