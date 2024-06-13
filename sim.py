import numpy as np
from collections import deque
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import sys
from os import system

# Default simulation parameters
duration = 100                  # Duration of the simulation in seconds
rate = 30                       # Rate of photon arrival per second
size_list = 600                 # Length of the photon list queue
running_avg_length = 3          # Length of running average

# Default trigger parameters
significance_constant = 6       # Standard deviation multiplier for trigger algorithm
tail = 4                        # Length of recent data to ignore when calculating running avg/variance for trigger
look_back_to = 17               # Length of time we look back through when calculating sigma for trigger threshold
trigger_threshold_met = False   # Flag for trigger algorithm
triggered_timestamp = -999      # Timestamp for when event-by-event is triggered

show_peak_data = True
random_seed = 112               # Seed for reproducibility
np.random.seed(random_seed)     

# Define the power law function - this is used to create random background energy
def power_law(index, min_energy, max_energy):
    random_value = np.random.uniform(0, 1)
    energy = ((max_energy**(index + 1) - min_energy**(index + 1)) * random_value + min_energy**(index + 1))**(1/(index + 1))
    return energy

# Define the Get_Energy function - this is used for random background energy
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
        
# Gamma ray burst class with default values
class grb :
    peak_time = np.random.uniform(0.25 * duration, 0.75 * duration)
    amplitude = 5
    sigma = 1

    # Quick initialization of a GRB with default values that can be overridden if so desired
    def __init__(self, peak_time = np.random.uniform(0.25 * duration, 0.75 * duration), amplitude = 5, sigma = 1):
        self.peak_time = peak_time
        self.amplitude = amplitude
        self.sigma = sigma

    # Returns a Gaussian curve with respect to time that can be added onto background noise to represent a GRB
    def burst_addition(self, curr_time):
        exponent = ((curr_time - self.peak_time) ** 2) / (-2 * self.sigma)
        return self.amplitude * np.exp(exponent)

short_grb = grb(amplitude=20, sigma = 0.001)
long_grb = [grb(peak_time=duration/2, amplitude=2, sigma=5), grb(peak_time=duration/2 + 5, amplitude=3, sigma=5), grb(peak_time=duration/2 + 10, amplitude=2, sigma=5)]

bursts = []
bursts += long_grb

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
    np.random.seed(random_seed)
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

        for burst in bursts :
            photon_count_in_last_second += burst.burst_addition(current_time)

        if current_time > look_back_to :
            look_back_std = np.std(running_average[(-1 * look_back_to) : (-1 * tail)])
            threshold = running_average[-1 * tail] + significance_constant * look_back_std
            
            if (trigger_threshold_met == False and photon_count_data[-1] >= threshold) :
                trigger_threshold_met = True
                global triggered_timestamp
                triggered_timestamp = current_time - tail

        if current_time < duration:
            photon_list_queue.appendleft((current_time, photon_energy))
            photon_count_in_last_second += 1
            
            if accumulated_time >= 1:
                # Push the photon count for the last second into the photon count queues
                photon_count_queue.push(photon_count_in_last_second)
                
                # Calculate the running averages
                running_average.append(photon_count_queue.get_running_average())

                # Store data for plotting
                photon_count_data.append(photon_count_in_last_second)

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

    fig = plt.figure(figsize=(10,6))
    gs = gridspec.GridSpec(2, 2, width_ratios=[3, 1])

    ax1 = fig.add_subplot(gs[0,0])
    ax2 = fig.add_subplot(gs[1,0])

    # # Plotting the results
    # fig, axs = plt.subplots(2, 1, figsize=(12, 10))

    # Plot photon counts with error bars
    ax1.errorbar(range(len(photon_count_data)), photon_count_data, yerr=photon_count_errors, fmt='o', label='Photon Count')
    ax1.set_xlabel('Time (seconds)')
    ax1.set_ylabel('Photon Count')
    ax1.set_title('Photon Count per Second')
    ax1.set_ylim(y_range_min, y_range_max)  # Set the same y-axis range for all plots
    
    # Create labeled dashed lines for each peak
    if show_peak_data :
        i = 1
        for burst in bursts : 
            ax1.vlines(burst.peak_time, y_range_min, y_range_max, label='Burst ' + str(i), color='green', linestyles='dashed')
            i += 1
    ax1.legend()

    # Plot running average
    ax2.plot(running_average, 'o', label='Running Average (' + str(running_avg_length) + ' seconds)', color='orange')
    ax2.vlines(triggered_timestamp, y_range_min, y_range_max, label='Threshold Triggered')
    ax2.annotate(str(round(triggered_timestamp,2)) + 's', (triggered_timestamp + 0.5, y_range_max / 2), xycoords='data', xytext=(-0.5,0), textcoords='offset fontsize', ha='right')
    ax2.set_xlabel('Time (seconds)')
    ax2.set_ylabel('Running Average')
    ax2.set_title('Running Average of Photon Count (' + str(running_avg_length) + ' seconds)')
    ax2.set_ylim(y_range_min, y_range_max)  # Set the same y-axis range for all plots
    ax2.legend()


    # Add textbox with variable information
    #textbox_ax = fig.add_axes([0.85, 0.2, 0.1, 0.6])
    textbox_ax = fig.add_subplot(gs[:, 1])
    textbox_ax.axis('off')
    textbox_ax.text(0.1, 0.5, all_variables_str(), verticalalignment='center', horizontalalignment='left')
    #plt.constrained_
    plt.tight_layout()
    plt.show()

def change_running_average_length() :
    global running_avg_length
    mod = ''
    while (mod != 'y' and mod != 'n') :
        mod = str(
            input('\nCurrent running average length is ' + str(running_avg_length) + 's. Would you like to modify it? (y/n) ')
        )
    if mod == 'n' :
        modify_variables()
    else :
        running_avg_length = int(
            input('\nEnter the new running average length: ')
        )
        print('\nRunning average length has been changed to ' + str(running_avg_length) + 's!')

def change_rate() :
    global rate
    mod = ''
    while (mod != 'y' and mod != 'n') :
        mod = str(
            input('\nCurrent rate is ' + str(rate) + ' photons/s. Would you like to modify it? (y/n) ')
        )
    if mod == 'n' :
        modify_variables()
    else :
        rate = int(
            input('\nEnter the new rate: ')
        )
        print('\nRate has been changed to ' + str(rate) + ' photons/s!')

def change_duration() :
    global duration
    mod = ''
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
        print('\nDuration has been changed to ' + str(duration) + 's!')

def change_photon_list_length() :
    global size_list
    mod = ''
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
        print('\nPhoton list length has been changed to ' + str(size_list) + ' photons!')

def change_significance_constant() :
    global significance_constant
    mod = ''
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
        print('\nSignificance constant has been changed to ' + str(significance_constant) + '!')

def change_tail_length() :
    global tail
    mod = ''
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
        print('\nTail has been changed to ' + str(tail) + 's!')

def change_look_back_to() :
    global look_back_to
    mod = ''
    while mod != 'y' and mod != 'n' :
        mod = str(
            input('\nCurrent look_back_to is ' + str(look_back_to) + 's. Would you like to modify it? (y/n) ') 
        )
    if mod == 'n' :
        modify_variables()
    else :
        look_back_to = int(
            input('\nEnter the new look_back_to: ')
        )
        print('\nLook_back_to has been changed to ' + str(look_back_to) + 's!')

# tab function (pyplot won't allow \t)
def t() :
    return '     '

def press_any_key_to_continue() :
    i = ''
    while i == '' :
        i = input('Press any key, then ENTER, to continue: ')

def basic_sim_variables_str() : 
    summary = ( '\nBasic simulation variables: ' + 
                '\n' + t() + 'Simulation duration (in seconds) : ' + str(duration) + 
                '\n' + t() + 'Rate of photon arrival per second: ' + str(rate) + 
                '\n' + t() + 'Length of the photon list queue: ' + str(size_list) +
                '\n' + t() + 'Running average length (in seconds): ' + str(running_avg_length))
    return summary

def trigger_variables_str() : 
    summary = ( '\nTrigger Variables: ' + 
                '\n' + t() + 'Significance constant: ' + str(significance_constant) + 
                '\n' + t() + 'Tail length (in seconds): ' + str(tail) + 
                '\n' + t() + 'Lookback duration (in seconds): ' + str(look_back_to))
    return summary

def burst_info_str() : 
    summary = '\n' + 'Burst information: '
    i = 0
    for burst in bursts :
        summary += ('\n' + t() + 'Peak ' + str(i) + '\n' + t() + t() + 'Peaks at ' + str(round(burst.peak_time, 2)) + 's\n' + t() + t() + 'A = ' + str(burst.amplitude) + '\n' + t() + t() + 'Sigma = ' + str(burst.sigma))
        i += 1
    return summary

def display_burst_info() :
    print(burst_info_str())

def delete_burst_helper(i) :
    del bursts[i]

def delete_burst() :
    system('cls')
    display_burst_info()
    ans = ''
    while ans != 'y' and ans != 'n' :
        ans = input(
            '\nWould you like to delete a burst? (y/n) '
        )
    if ans == 'y' :
        delete_index = int(
            input('\nEnter the number of the burst you\'d like to delete: ')
        )
        delete_burst_helper(delete_index)
        print('\nBurst ' + str(delete_index) + ' was sucessfully deleted.')
        press_any_key_to_continue()
    

def all_variables_str() : 
    summary = basic_sim_variables_str() + '\n' + trigger_variables_str()
    if show_peak_data :
        summary += '\n' + burst_info_str()
    return summary

def display_all_variables() :
    system('cls')
    print('\nCurrent settings: ')
    print(all_variables_str())
    x = 999
    while x != '0' and x != 1 :
        x = str(
            input('\nEnter 0 to modify variables, or 1 to return to main menu: ')
        )
    if x == '0' :
        modify_variables()
    else :
        main()

def modify_bursts() :
    functions_names = [display_burst_info, delete_burst, return_to_modification_menu, return_to_menu]
    menu_items = dict(enumerate(functions_names, start=0))
    while True:
        system('cls')
        print('\nBurst Modification Menu: ')
        display_menu(menu_items)
        selection = int(
            input("Please enter your selection number: ")
        )
        selected_value = menu_items[selection]
        selected_value()

def return_to_modification_menu() :
    modify_variables()

def exit() : 
    system('cls')  # clears stdout
    print("Goodbye")
    sys.exit()

def return_to_menu() :
    main()

def modify_variables() :
    system('cls')
    functions_names = [display_all_variables, change_duration, change_rate, change_photon_list_length, change_running_average_length, 
                       change_significance_constant, change_tail_length, change_look_back_to, modify_bursts, return_to_menu]
    menu_items = dict(enumerate(functions_names, start=0))
    while True:
        print('\nModification options: ')
        display_menu(menu_items)
        selection = int(
            input("Please enter your selection number: "))      # Get function key
        selected_value = menu_items[selection]                  # Gets the function name
        selected_value()                                        # add parentheses to call the function

def run_simulation_and_plot() :
    global show_peak_data
    selection = ''
    while selection != 'y' and selection != 'n' :
        selection = str(
            input('Show peak data? (y/n) ')
        )
    if selection == 'y' :
        show_peak_data = True
    else :
        show_peak_data = False
    system('cls')
    sim()
    display_plots()

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
    functions_names = [run_simulation_and_plot, display_all_variables, modify_variables, exit]
    menu_items = dict(enumerate(functions_names, start=1))
    system('cls')

    while True:
        print('MENU')
        display_menu(menu_items)
        selection = int(
            input("\nPlease enter your selection number: "))      # Get function key
        selected_value = menu_items[selection]                  # Gets the function name
        selected_value()                                        # add parentheses to call the function

if __name__ == "__main__":
    main()