import mip
import network
from time import sleep

# Replace these values with your own
SSID = "Xiaomi_C24F"
PASSWORD = "kele453489."
BROKER_IP = "192.168.31.1"

# Function to connect to WLAN
def connect_wlan():
    # Connecting to the group WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    # Attempt to connect once per second
    while wlan.isconnected() == False:
        print("Connecting... ")
        sleep(1)

    # Print the IP address of the Pico
    print("Connection successful. Pico IP:", wlan.ifconfig()[0])

# Function to install MQTT
def install_mqtt():
    try:
        mip.install("umqtt.simple")
    except Exception as e:
        print(f"Could not install MQTT: {e}")

# Main program
connect_wlan()
install_mqtt()