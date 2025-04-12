
# SSID credentials
ssid = 'KME759_Group_1'
password = 'KME759bql'

def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    ip = wlan.ifconfig()[0]
    return