from filefifo import Filefifo
import time


def scale_data(data, min_val, max_val):
    """Scales data to the range 0-100."""
    if max_val == min_val:  # Handle the case where min and max are equal
        return [50] * len(data) # Return 50 for all values to avoid division by zero
    scaled_data = [float(100 * (x - min_val) / (max_val - min_val)) for x in data]
    return scaled_data


# --- Main program ---
#sample_rate = 250  
#duration = 10 
#num_samples = sample_rate * duration

data = Filefifo(10, name='capture_250Hz_01.txt') 

# Initial data for min/max calculation (first 2 seconds)
initial_data = [data.get() for _ in range(500)]


if not initial_data: # Handle the case where the file is empty or cannot be read
    print("No data found in the file.")
else:
    min_val = min(initial_data)
    max_val = max(initial_data)

    # Collect and scale the data for plotting
    plot_data = []
    for _ in range(2500):
        sample = data.get()
        scaled_sample = scale_data([sample], min_val, max_val)[0]  
        plot_data.append(scaled_sample)
        print(scaled_sample)  




