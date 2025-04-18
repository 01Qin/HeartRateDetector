# Peak Detection


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
    x = samples.get()
