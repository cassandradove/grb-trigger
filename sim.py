import numpy as np
from collections import deque
import matplotlib.pyplot as plt
import sys
from os import system

# Default simulation parameters
duration = 100                  # Duration of the simulation in seconds
rate = 30                       # Rate of photon arrival per second
size_list = 600                 # Length of the photon list queue
significance_constant = 6       # Standard deviation multiplier for trigger algorithm
tail = 4                        # Length of recent data to ignore when calculating running avg/variance for trigger
running_avg_length = 3          # Length of running average

trigger_threshold_met = False   # Flag for trigger algorithm
triggered_timestamp = -999 

np.random.seed(112)             # Seed for reproducibility

# Define the power law function.
def power_law(index, min_energy, max_energy):
    random_value = np.random.uniform(0, 1)
    energy = ((max_energy**(index + 1) - min_energy**(index + 1)) * random_value + min_energy**(index + 1))**(1/(index + 1))
    return energy

# Define the Get_Energy function.
def Get_Energy():
    index = -2.0                # Index of the spectrum.
    min_energy = 1.0            # Minimum energy.
    max_energy = 1000.0         # Maximum energy.
    energy = power_law(index, min_energy, max_energy)
    return energy

# Function to return the next photon's occurrence time and energy.
def get_photon_next(rate):
    time_to_next_event = np.random.exponential(1 / rate)
    photon_energy = Get_Energy()
    return time_to_next_event, photon_energy

# Define the FixedLengthLIFOQueue class for photon counts
class FixedLengthLIFOQueue:
    def __init__(self, length):
        self.queue = deque(maxlen=length)       # Initialize the deque with a fixed length
        self.running_sum = 0                    # Initialize the running sum

    def push(self, item):
        if len(self.queue) == self.queue.maxlen:
            self.running_sum -= self.queue[-1]  # Subtract the rightmost item if the queue is full
        self.queue.appendleft(item)             # Append item to the left end of the queue
        self.running_sum += item                # Add the new item to the running sum

    def pop(self):
        if self.queue:
            item = self.queue.pop()             # Pop the last item from the right end of the queue
            self.running_sum -= item            # Subtract the popped item from the running sum
            return item
        else:
            return None                         # Return None if the queue is empty

    def get_last(self):
        if self.queue:
            return self.queue[-1]               # Return the last item in the queue without removing it
        else:
            return None                         # Return None if the queue is empty

    def get_first(self):
        if self.queue:
            return self.queue[0]                # Return the first item in the queue without removing it
        else:
            return None                         # Return None if the queue is empty

    def size(self):
        return len(self.queue)                  # Return the length of the queue

    def get_item(self, index):
        if 0 <= index < len(self.queue):
            return self.queue[index]            # Return the item at the specified index
        else:
            return None                         # Return None if the index is out of range

    def get_running_average(self):
        if self.queue:
            return self.running_sum / len(self.queue)  # Return the running average
        else:
            return 0                                   # Return 0 if the queue is empty
        
# Gamma ray burst class with default values [Cassie]
class grb :
    peak_time = np.random.uniform(0.25 * duration, 0.75 * duration)
    amplitude = 4
    sigma = 3

    # Quick initialization of a GRB with default values that can be overridden if so desired [Cassie]
    def __init__(self, peak_time = np.random.uniform(0.25 * duration, 0.75 * duration), amplitude = 5, sigma = 1):
        self.peak_time = peak_time
        self.amplitude = amplitude
        self.sigma = sigma

    # Returns a Gaussian curve with respect to time that can be added onto background noise to represent a GRB [Cassie]
    def burst_addition(self, curr_time):
        exponent = ((curr_time - self.peak_time) ** 2) / (-2 * self.sigma)
        return self.amplitude * np.exp(exponent)


default_grb = grb(50,4,0.05)
bursts = [default_grb]

# Store data for plotting
photon_count_data = []
running_average = []

# Initialize the FixedLengthLIFOQueue for photon counts
photon_list_queue = deque(maxlen=size_list)

def sim() : 
    # Start the simulation
    photon_count_data.clear()
    running_average.clear()
    photon_list_queue.clear()
    current_time = 0
    accumulated_time = 0
    photon_count_in_last_second = 0
    trigger_threshold_met = False

    # Initialize the FixedLengthLIFOQueue for running averages
    photon_count_queue = FixedLengthLIFOQueue(running_avg_length)

    while current_time < duration:
        time_to_next_event, photon_energy = get_photon_next(rate)

        current_time += time_to_next_event
        accumulated_time += time_to_next_event

        if current_time < duration:
            photon_list_queue.appendleft((current_time, photon_energy))
            photon_count_in_last_second += 1

            for burst in bursts :
                photon_count_in_last_second += burst.burst_addition(current_time)
            
            if accumulated_time >= 1:
                # Push the photon count for the last second into the photon count queues
                photon_count_queue.push(photon_count_in_last_second)
                
                # Calculate the running averages
                running_average.append(photon_count_queue.get_running_average())

                # Store data for plotting
                photon_count_data.append(photon_count_in_last_second)

                look_back_to = 17
                if current_time > look_back_to :
                    # 3s test
                    look_back_std = np.std(running_average[-1 * look_back_to : -1 * tail])

                    if (trigger_threshold_met == False and photon_count_data[-1] >= (running_average[-1 * tail] + (significance_constant * look_back_std))) :
                        trigger_threshold_met = True
                        global triggered_timestamp
                        triggered_timestamp = current_time - tail

                # Reset for the next second
                photon_count_in_last_second = 0
                accumulated_time -= 1

def display_plots() :
    # Determine the common y-axis range
    y_min = min(photon_count_data)
    y_max = max(photon_count_data)
    y_range_min = y_min * 0.8
    y_range_max = y_max * 1.2

    # Calculate errors for photon count data
    photon_count_errors = [np.sqrt(count) for count in photon_count_data]

    # Plotting the results
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))

    # Plot photon counts with error bars
    ax1.errorbar(range(len(photon_count_data)), photon_count_data, yerr=photon_count_errors, fmt='o', label='Photon Count')
    ax1.set_xlabel('Time (seconds)')
    ax1.set_ylabel('Photon Count')
    ax1.set_title('Photon Count per Second')
    ax1.set_ylim(y_range_min, y_range_max)  # Set the same y-axis range for all plots
    ax1.legend()

    # Plot running average
    ax2.plot(running_average, 'o', label='Running Average (' + str(running_avg_length) + ' seconds)', color='orange')
    ax2.vlines(triggered_timestamp, y_range_min, y_range_max, label='Threshold Triggered')
    ax2.set_xlabel('Time (seconds)')
    ax2.set_ylabel('Running Average')
    ax2.set_title('Running Average of Photon Count (' + str(running_avg_length) + ' seconds)')
    ax2.set_ylim(y_range_min, y_range_max)  # Set the same y-axis range for all plots
    ax2.legend()

    for burst in bursts :
        print("GRB at " + str(burst.peak_time) + " seconds with amplitude " + str(burst.amplitude) + " and sigma value " + str(burst.sigma))

    print("Event-by-event triggered at " + str(triggered_timestamp))
    plt.tight_layout(pad=3)
    plt.show()

def change_running_average_length() :
    global running_avg_length
    mod = str(
        input('\nCurrent running average length is ' + str(running_avg_length) + 's. Would you like to modify it? (y/n) ')
    )
    while (mod != 'y' and mod != 'n') :
        mod = str(
            input('\nCurrent running average length is ' + str(running_avg_length) + 's. Would you like to modify it? (y/n) ')
        )
    if mod == 'n' :
        modify_variables()
    else :
        new_running_avg = int(
            input('\nEnter the new running average length: ')
        )
        running_avg_length = new_running_avg

def change_rate() :
    global rate
    mod = str(
        input('\nCurrent rate is ' + str(rate) + ' photons/s. Would you like to modify it? (y/n) ')
    )
    while (mod != 'y' and mod != 'n') :
        mod = str(
            input('\nCurrent rate is ' + str(rate) + ' photons/s. Would you like to modify it? (y/n) ')
        )
    if mod == 'n' :
        modify_variables()
    else :
        new_rate = int(
            input('\nEnter the new rate: ')
        )
        rate = new_rate

def change_duration() :
    global duration
    mod = str(
        input('\nCurrent duration is ' + str(duration) + 's. Would you like to modify it? (y/n) ')
    )
    while (mod != 'y' and mod != 'n') :
        mod = str(
            input('\nCurrent duration is ' + str(duration) + 's. Would you like to modify it? (y/n) ')
        )
    if mod == 'n' :
        modify_variables()
    else :
        duration = int(
            input('\nEnter the new duration: ')
        )

def change_photon_list_length() :
    global size_list
    mod = str(
        input('\nCurrent size of photon list is ' + str(size_list) + ' photons. Would you like to modify it? (y/n) ')
    )
    while (mod != 'y' and mod != 'n') :
        mod = str(
            input('\nCurrent size of photon list is ' + str(size_list) + ' photons. Would you like to modify it? (y/n) ')
        )
    if mod == 'n' :
        modify_variables()
    else :
        size_list = int(
            input('\nEnter the new photon list length: ')
        )

def change_significance_constant() :
    global significance_constant
    mod = str(
        input('\nCurrent significance constant is ' + str(significance_constant) + '. Would you like to modify it? (y/n) ')
    )
    while (mod != 'y' and mod != 'n') :
        mod = str(
            input('\nCurrent significance constant is ' + str(significance_constant) + '. Would you like to modify it? (y/n) ')
        )
    if mod == 'n' :
        modify_variables()
    else :
        significance_constant = int(
            input('\nEnter the new significance constant: ')
        )

def change_tail_length() :
    global tail
    mod = str(
        input('\nCurrent tail is ' + str(tail) + 's. Would you like to modify it? (y/n) ')
    )
    while (mod != 'y' and mod != 'n') :
        mod = str(
            input('\nCurrent tail is ' + str(tail) + 's. Would you like to modify it? (y/n) ')
        )
    if mod == 'n' :
        modify_variables()
    else :
        tail = int(
            input('\nEnter the new tail: ')
        )

def display_all_variables() : 
    print('\nCurrent settings:')
    print('\t1. Simulation duration (in seconds) : ' + str(duration))
    print('\t2. Rate of photon arrival per second: ' + str(rate))
    print('\t3. Length of the photon list queue: ' + str(size_list))
    print('\t4. Significance constant: ' + str(significance_constant))
    print('\t5. Tail length (in seconds): ' + str(tail))
    print('\t6. Running average length (in seconds): ' + str(running_avg_length))
    print('\t7. Number of peaks: ' + str(len(bursts)))

def exit() : 
    system('cls')  # clears stdout
    print("Goodbye")
    sys.exit()

def return_to_menu() :
    main()

def modify_variables() : 
    functions_names = [display_all_variables, change_duration, change_rate, change_photon_list_length, change_significance_constant, 
                       change_tail_length, change_running_average_length, return_to_menu]
    menu_items = dict(enumerate(functions_names, start=0))
    while True:
        print('\nMENU')
        print('\nModification options: ')
        display_menu(menu_items)
        selection = int(
            input("Please enter your selection number: "))      # Get function key
        selected_value = menu_items[selection]                  # Gets the function name
        selected_value()                                        # add parentheses to call the function

def display_menu(menu):
    """
    Display a menu where the key identifies the name of a function.
    :param menu: dictionary, key identifies a value which is a function name
    :return:
    """
    for k, function in menu.items():
        print('\t', k, function.__name__)

def main():
    # Create a menu dictionary where the key is an integer number and the
    # value is a function name.
    functions_names = [sim, display_plots, display_all_variables, modify_variables, exit]
    menu_items = dict(enumerate(functions_names, start=1))

    while True:
        print('\nMENU')
        display_menu(menu_items)
        selection = int(
            input("Please enter your selection number: "))      # Get function key
        selected_value = menu_items[selection]                  # Gets the function name
        selected_value()                                        # add parentheses to call the function

if __name__ == "__main__":
    main()