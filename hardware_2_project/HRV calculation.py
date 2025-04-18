# HRV calculation


oled.fill(0)
if len(PPI_array) >= 3:



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
