import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from lifo_queue import FixedLengthLIFOQueue
from grb import *
from collections import deque
import sys
from os import system
from config import *

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

bursts = [lgrb, grb(peak_time=duration/2 + 5, amplitude=3, sigma=5), grb(peak_time=duration/2 + 10, amplitude=2, sigma=5)]

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

        # Logic determining if we trigger threshold has been met
        if current_time > look_back_to :
            look_back_std = np.std(running_average[(-1 * look_back_to) : (-1 * tail)])
            threshold = running_average[-1 * tail] + significance_constant * look_back_std
            
            if (trigger_threshold_met == False and photon_count_data[-1] >= threshold) :
                trigger_threshold_met = True
                global triggered_timestamp
                triggered_timestamp = current_time

        # Filling running average list
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
    system('cls')
    print(burst_info_str())
    press_any_key_to_continue()

def delete_burst() :
    system('cls')
    print(burst_info_str())
    ans = ''
    while ans != 'y' and ans != 'n' :
        ans = input(
            '\nWould you like to delete a burst? (y/n) '
        )
    if ans == 'y' :
        delete_index = int(
            input('\nEnter the number of the burst you\'d like to delete: ')
        )
        del bursts[delete_index]
        print('\nBurst ' + str(delete_index) + ' was sucessfully deleted.')
        press_any_key_to_continue()

def add_burst() :
    system('cls')
    print(burst_info_str())
    ans = ''
    while ans != 'y' and ans != 'n' :
        ans = input(
            '\nWould you like to add a burst? (y/n) '
        )
    if ans == 'y' :
        add_burst_helper()
    else :
        press_any_key_to_continue()

def return_to_burst_menu() :
    press_any_key_to_continue()
    modify_bursts()

def add_burst_helper() :
    system('cls')
    functions_names = [add_sgrb, add_lgrb, return_to_burst_menu]
    menu_items = dict(enumerate(functions_names, start=0))
    while True:
        print(burst_info_str())
        print('\nAdd burst options: ')
        display_menu(menu_items)
        selection = int(
            input("Please enter your selection number: ")
        )
        selected_value = menu_items[selection]
        selected_value()

def add_sgrb() :
    add_grb(grb(sgrb_peak_time, sgrb_A, sgrb_sigma))
def add_lgrb() :
    add_grb(grb(lgrb_peak_time, lgrb_A, lgrb_sigma))

def add_grb(burst) :
    system('cls')
    print(burst_info_str())
    print('\nDefault parameters: ')
    print('\tPeaks at ' + str(burst.peak_time) + '\n\tA = ' + str(burst.amplitude) + '\n\tSigma = ' + str(burst.sigma))
    ans = 99
    while ans != 0 and ans != 1 and ans != 2:
        print('\nWould you like to \n\t0: Add the default burst\n\t1: Modify the burst\n\t2: Return to menu')
        ans = int(input('\nEnter 0, 1, or 2: '))
    if ans == 0 :
        bursts.append(burst)
        i = 99
        while i != 0 and i != 1 :
            i = int(input('Success! Press 0 to add another burst or 1 to return to main menu'))
        if i == 0 :
            add_burst_helper()
        else :
            return_to_menu()
    elif ans == 1 :
        modify(burst)
    else :
        press_any_key_to_continue

def modify(burst) :
    system('cls')
    print(burst_info_str())
    print('\nBurst to add: ')
    print('\tPeaks at ' + str(burst.peak_time) + '\n\tA = ' + str(burst.amplitude) + '\n\tSigma = ' + str(burst.sigma))

    print('\nWould you like to\n\t0: Modify peak time\n\t1: Modify amplitude\n\t2: Modify sigma\n\t3: Confirm burst\n\t4: Cancel')
    ans = 99
    while ans != 0 and ans != 1 and ans != 2 and ans !=3 and ans != 4:
        ans = int (input ('\nEnter your numerical selection: '))
    if ans == 0 :
        modify_peak_time(burst)
        modify(burst)
    if ans == 1 :
        modify_amplitude(burst)
        modify(burst)
    if ans == 2 :
        modify_sigma(burst)
        modify(burst)
    if ans == 3 :
        conf = ''
        while conf != 'y' and conf != 'n' :
            conf = input('Confirm modifications and add to simulation? (y/n) ')
        if conf == 'y' :
            bursts.append(burst)
            i = 99
            while i != 0 and i != 1 :
                i = int(input('Success! Press 0 to add another burst or 1 to return to main menu '))
                if i == 0 :
                    add_burst_helper()
                else :
                    return_to_menu()
        else :
            modify(burst)
    if ans == 4 :
        return_to_burst_menu()

def modify_peak_time(burst) :
    print('Current peak time: ' + str(burst.peak_time))
    new_peak = float(
        input('\nEnter new peak time: ')
    )
    burst.peak_time = new_peak
    print('\nNew peak time: ' + str(burst.peak_time))

def modify_amplitude(burst) : 
    print('Current amplitude: ' + str(burst.amplitude))
    new_A = float(
        input('\nEnter a new amplitude: ')
    )
    burst.amplitude = new_A
    print('\nNew amplitude: ' + str(burst.amplitude))

def modify_sigma(burst) :
    print('Current sigma: ' + str(burst.sigma)) 
    new_sigma = float(
        input('\nEnter new sigma: ')
    )
    burst.sigma = new_sigma
    print('\nNew sigma: ' + str(burst.sigma))

def confirm_burst(burst) :
    print('Burst to be added to simulation: ')
    print(burst)
    ans = ''
    while ans != 'y' and ans != 'n' :
        ans = input('Confirm your selection? (y/n)')
    if ans == 'n' :
        modify(burst)
        bursts.append(burst)
        return_to_burst_menu()

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
    while (x != '0' and x != '1') :
        x = str(
            input('\nEnter 0 to modify variables, or 1 to return to main menu: ')
        )
    if x == '0' :
        modify_variables()
    if x == '1' :
        return_to_menu()

def modify_bursts() :
    functions_names = [display_burst_info, add_burst, delete_burst, return_to_modification_menu, return_to_menu]
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