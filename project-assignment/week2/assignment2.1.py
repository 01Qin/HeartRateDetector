from filefifo import Filefifo
import math

def find_peaks(data_stream, sample_rate):
    peaks = []
    prev_sample = None
    prev_slope = None
    for i, sample in enumerate(data_stream):
        if prev_sample is not None:
            slope = sample - prev_sample
            if prev_slope is not None and prev_slope > 0 and slope <= 0:
                peaks.append(i - 1)
            prev_slope = slope
        prev_sample = sample
    return peaks


def calculate_frequency(peak_indices, sample_rate):
    if len(peak_indices) < 2:
        return 0
    peak_intervals = [peak_indices[i+1] - peak_indices[i]
                      for i in range(len(peak_indices) - 1)]
    avg_interval = sum(peak_intervals) / len(peak_intervals) if peak_intervals else 0
    return sample_rate / avg_interval if avg_interval else 0



# --- Main program ---
#sample_rate = 250
data = Filefifo(10, name='capture_250Hz_01.txt')  



data_samples = [data.get()
for _ in range(2500)]

peak_indices = find_peaks(data_samples, 250)
frequency = calculate_frequency(peak_indices, 250)

print(peak_indices)

if len(peak_indices) >= 4:
    for i in range(3):  # Print 3 intervals
        interval_samples = peak_indices[i+1] - peak_indices[i]
        interval_seconds = interval_samples / 250
        print(f"Interval {i+1}: {interval_samples} samples, {interval_seconds:.4f}s")

print(f"Frequency: {frequency:.2f} Hz")





if len(peak_indices) >= 4:
    for i in range(3):  # Print 3 intervals
        interval_samples = peak_indices[i+1] - peak_indices[i]
        interval_seconds = interval_samples / 250
        print(f"Interval {i+1}: {interval_samples} samples, {interval_seconds:.4f}s")

print(f"Frequency: {frequency:.2f} Hz")
    
