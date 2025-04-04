from ssd1306 import SSD1306_I2C
from machine import Pin, I2C
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
    "Mean HR ",
    "SDNN ",
    "RMSSD ",
    "SDSD "
]
menu_index = 0

# previvous
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


def select_option():
    global prev_push
    current_push = rot_push.value()

    if prev_push == 1 and current_push == 0:  # Buttonpressed
        oled.fill(0)
        oled.text("Selected:", 10, 10)
        oled.text(menu_items[menu_index], 10, 30)
        oled.show()
        utime.sleep(1)
        display_menu()

    prev_push = current_push


# Main loop
display_menu()
while True:
    read_encoder()
    select_option()
    utime.sleep_ms(10)  # Small delay
