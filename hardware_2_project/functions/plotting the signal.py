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
            if len(PPI_array) > 3:
                actual_PPI = meanPPI_calculator(PPI_array)
                actual_HR = meanHR_calculator(actual_PPI)
                oled.text(f'HR:{actual_HR}', 2, 1, 0)
                oled.text(f'PPI:{interval_ms}', 60, 1, 0)
            oled.text(f'Timer:  {int(capture_count / samplerate)}s', 18, 56, 0)
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

