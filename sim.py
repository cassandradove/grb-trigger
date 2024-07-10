import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from lifo_queue import FixedLengthLIFOQueue
from grb import *
from collections import deque
import sys
import os
from os import system
import fnmatch
from config import *

state = GlobalState()

def init_vars():
    global duration, rate, size_list, running_avg_length, ebe_bin_length, enter_significance_constant, tail
    global enter_look_back_to, trigger_threshold_met, triggered_timestamp, exit_timestamp, exit_significance_constant
    global exit_look_back_to, show_peak_data, random_seed, sgrb_peak_time, sgrb_A, sgrb_sigma, lgrb_peak_time, lgrb_A, lgrb_sigma
    global default_A, default_sigma

    duration = state.vars['duration']                        # Duration of the simulation in seconds
    rate = state.vars['rate']                             # Rate of photon arrival per second
    size_list = state.vars['size_list']                      # Length of the photon list queue
    running_avg_length = state.vars['running_avg_length']               # Length of running average
    ebe_bin_length = state.vars['ebe_bin_length']                  # Event-by-event bin length (in s) --- this should be configured later on to be variable, discuss with science people for how to go about this

    # Default trigger parameters
    enter_significance_constant = state.vars['enter_significance_constant']       # Standard deviation multiplier for trigger algorithm
    tail = state.vars['tail']                              # Length of recent data to ignore when calculating running avg/variance for trigger
    enter_look_back_to = state.vars['enter_look_back_to']              # Length of time we look back through when calculating sigma for trigger threshold
    trigger_threshold_met = state.vars['trigger_threshold_met']         # Flag for trigger algorithm
    triggered_timestamp = state.vars['triggered_timestamp']            # Timestamp for when event-by-event is triggered
    exit_timestamp = state.vars['exit_timestamp']                 # Timestamp for when event-by-event is exited
    exit_significance_constant = state.vars['exit_significance_constant']        # Standard deviation multiplier for exiting event-by-event
    exit_look_back_to = state.vars['exit_look_back_to']                # Length of time we look back when calculating sigma for exiting event-by-event

    show_peak_data = state.vars['show_peak_data']
    random_seed = state.vars['random_seed']                     # Seed for reproducibility

    # Default GRB parameters
    # Short GRB
    sgrb_peak_time = duration / 2
    sgrb_A = state.vars['sgrb_A']
    sgrb_sigma = state.vars['sgrb_sigma']

    # Long GRB - note: to simulate a long grb, multiple of these peaks are required in sucession
    lgrb_peak_time = duration / 2
    lgrb_A = state.vars['lgrb_A']
    lgrb_sigma = state.vars['lgrb_sigma']

    # Default GRB - this will load when the sim runs for the first time
    default_peak_time = duration / 2
    default_A = state.vars['default_A']
    default_sigma = state.vars['default_sigma']

    # Default GRBs
    global sgrb 
    sgrb = grb(peak_time=duration/2, amplitude=sgrb_A, sigma = sgrb_sigma)
    global lgrb 
    lgrb = grb(peak_time=duration/2, amplitude=lgrb_A, sigma=lgrb_sigma)
    global default_burst
    default_burst = grb(peak_time=duration/2, amplitude=default_A, sigma=default_sigma)
    global bursts
    bursts = [default_burst]

init_vars()
np.random.seed(random_seed) 

# Define the power law function - this is used to create random background energy
def power_law(index, min_energy, max_energy):
    random_value = np.random.uniform(0, 1)
    energy = ((max_energy**(index + 1) - min_energy**(index + 1)) * random_value + min_energy**(index + 1))**(1/(index + 1))
    return energy

# Define the Get_Energy function
def Get_Energy():
    index = -0.1                # Index of the spectrum.
    min_energy = 1.0            # Minimum energy.
    max_energy = 1000.0         # Maximum energy.
    energy = power_law(index, min_energy, max_energy)
    return energy

# Function to return the next photon's occurrence time and energy.
def get_photon_next(rate):
    time_to_next_event = np.random.exponential(1 / rate)
    photon_energy = Get_Energy()
    return time_to_next_event, photon_energy

bursts = [default_burst]

# Store data for plotting
photon_count_data = []
running_average = []
light_curve_counts = []
light_curve_timestamps = []

# Initialize the FixedLengthLIFOQueue for photon counts
photon_list_queue = deque(maxlen=size_list)



def sim() : 
    # Start the simulation
    #init_vars()
    
    photon_count_data.clear()
    running_average.clear()
    photon_list_queue.clear()
    light_curve_counts.clear()
    light_curve_timestamps.clear()
    tail_counts = deque(maxlen=int(tail / ebe_bin_length))
    tail_timestamps = deque(maxlen=int(tail / ebe_bin_length))
    
    # Initialize deque for delay ring buffer
    delay_buffer = deque(maxlen=rate)
    delay_buffer_binsize = ebe_bin_length
    
    global bursts
    current_time = 0
    
    ra_accumulated_time = 0         # running average accumulated time (helper)
    ebe_accumulated_time = 0        # event-by-event accumulated time (helper)
    tail_accumulated_time = 0
    
    photon_count_in_last_second = 0
    ebe_binned_photon_count = 0
    tail_count = 0
    
    trigger_threshold_met = False
    already_triggered = False
    get_end_tail = False

    entered_ebe_threshold = -99

    # Initialize the FixedLengthLIFOQueue for running averages
    photon_count_queue = FixedLengthLIFOQueue(running_avg_length)

    while current_time < duration:
        time_to_next_event, photon_energy = get_photon_next(rate)

        current_time += time_to_next_event
        ra_accumulated_time += time_to_next_event
        tail_accumulated_time += time_to_next_event

        # Logic determining if trigger threshold has been met
        if current_time > enter_look_back_to and not already_triggered:
            
            # standard devation of the last n seconds, not including a tail
            look_back_std = np.std(running_average[(-1 * enter_look_back_to) : (-1 * tail)])
            
            # threshold to trigger is last running average count (not including tail) + c * look_back_std       
            #threshold = running_average[-1 * tail] + enter_significance_constant * look_back_std    
            threshold = tail_counts[0] + enter_significance_constant * look_back_std

            #if (trigger_threshold_met == False and running_average[-1] >= threshold) :
            if (trigger_threshold_met == False and tail_counts[-1] >= threshold) :
                entered_ebe_threshold = running_average[-1]
                trigger_threshold_met = True
                
                global triggered_timestamp
                triggered_timestamp = current_time

                light_curve_counts.extend(list(tail_counts))
                light_curve_timestamps.extend(list(tail_timestamps))
        
        # Exit trigger logic
        if trigger_threshold_met :
            ## OLD LOGIC - DOESN'T WORK ALL THAT WELL 
            # look_back_std = np.std(running_average[(-1 * exit_look_back_to) : (-1 * tail)])
            # threshold = running_average[-1 * tail] - exit_significance_constant * look_back_std
            # if running_average[-1] <= threshold  and running_average[-1] < 1.5 * entered_ebe_threshold: 
            #     trigger_threshold_met = False
            #     global exit_timestamp
            #     exit_timestamp = current_time
            #     already_triggered = True
            #     get_end_tail = True
            #     tail_counts.clear()
            #    tail_timestamps.clear()

            der = approximate_derivative(tail_counts[-1], tail_counts[-2], tail_timestamps[-1] - tail_timestamps[-2])
            if (-0.001 < der < 0.001 and tail_counts[-1] < 1.25 * entered_ebe_threshold) :
                trigger_threshold_met = False
                global exit_timestamp
                exit_timestamp = current_time
                already_triggered = True
                get_end_tail = True
                tail_counts.clear()
                tail_timestamps.clear()

        # Filling running average list
        if current_time < duration:
            photon_list_queue.appendleft((current_time, photon_energy))
            photon_count_in_last_second += 1
            # for burst in bursts :
            #     photon_count_in_last_second += burst.burst_addition(current_time)
            tail_count += 1
                
            
            if ra_accumulated_time >= 1:
                for burst in bursts :
                    photon_count_in_last_second += burst.burst_addition(current_time)
                
                # Push the photon count for the last second into the photon count queues
                photon_count_queue.push(photon_count_in_last_second)
                
                # Calculate the running averages
                running_average.append(photon_count_queue.get_running_average())

                # Store data for plotting
                photon_count_data.append(photon_count_in_last_second)

                # Reset for the next second
                photon_count_in_last_second = 0
                ra_accumulated_time = 0
            
            if tail_accumulated_time >= ebe_bin_length :
                for burst in bursts :
                    tail_count += burst.burst_addition(current_time)
                tail_counts.append(tail_count)
                tail_timestamps.append(current_time)
                tail_count = 0
                tail_accumulated_time = 0
                if get_end_tail and tail_counts.__len__() == tail_counts.maxlen :
                    light_curve_counts.extend(tail_counts)
                    light_curve_timestamps.extend(tail_timestamps)
                    get_end_tail = False 

            # Filling lists for light curve
            if trigger_threshold_met :
                # for burst in bursts :
                #     ebe_binned_photon_count += burst.burst_addition(current_time)
                ebe_accumulated_time += time_to_next_event
                ebe_binned_photon_count += 1 
                if ebe_accumulated_time >= ebe_bin_length :
                    for burst in bursts :
                        ebe_binned_photon_count += burst.burst_addition(current_time)
                    light_curve_counts.append(ebe_binned_photon_count)
                    light_curve_timestamps.append(current_time)

                    ebe_accumulated_time = 0
                    ebe_binned_photon_count = 0
    if triggered_timestamp > 0 and exit_timestamp < 0 :
        exit_timestamp = duration

def display_plots() :
    # Determine the common y-axis range
    y_min = min(photon_count_data)
    y_max = max(photon_count_data)
    y_range_min = y_min * 0.8
    y_range_max = y_max * 1.2

    # Calculate errors for photon count data
    photon_count_errors = [np.sqrt(count) for count in photon_count_data]

    fig = plt.figure(figsize=(10,6))
    gs = gridspec.GridSpec(3, 2, width_ratios=[3, 1])

    ax1 = fig.add_subplot(gs[0,0])  # photon counts
    ax2 = fig.add_subplot(gs[1,0])  # running average
    ax3 = fig.add_subplot(gs[2,0])  # burst light curve

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
    plot_running_avg(ax2, y_range_min, y_range_max, bursts[0].amplitude, bursts[0].sigma)

    # Plot light curve
    try : 
        ax3.stairs(light_curve_counts[1:], light_curve_timestamps, color='red')
    except :
        ax3.text(1,1,'No light curve available')
    ax3.set_xlabel('Time')
    ax3.set_ylabel('Counts')
    ax3.set_title('Light Curve')

    # Add textbox with variable information
    #textbox_ax = fig.add_axes([0.85, 0.2, 0.1, 0.6])
    textbox_ax = fig.add_subplot(gs[:, 1])
    textbox_ax.axis('off')
    textbox_ax.text(0.1, 0.5, all_variables_str(), verticalalignment='center', horizontalalignment='left')
    plt.tight_layout()
    plt.show()

def approximate_derivative(curr_val, prev_value, time_between) :
    return (curr_val - prev_value) / (2 * time_between)

def plot_running_avg(ax, y_min, y_max, A, sigma) :
    ax.plot(running_average, 'o', label='Running Average', color='orange')
    if (triggered_timestamp > 0) :
        ax.vlines(triggered_timestamp, y_min, y_max, label='EBE Entered', colors='red')
    if (exit_timestamp > 0) :
        ax.vlines(exit_timestamp, y_min, y_max, label='EBE Exited')
    ax.annotate(str(round(triggered_timestamp,2)) + 's', (triggered_timestamp + 0.5, y_max * .8), xycoords='data', xytext=(-0.5,0), textcoords='offset fontsize', ha='right')
    ax.annotate(str(round(exit_timestamp,2)) + 's', (exit_timestamp + 0.5, y_max * .8), xycoords='data', xytext=(0.5,0), textcoords='offset fontsize', ha='left')
    ax.set_xlabel('Time (seconds)')
    ax.set_ylabel('Running Average')
    ax.set_title('Running Average of Photon Count (' + str(running_avg_length) + ' seconds)\nA = ' + str(A) + ', sigma = ' + str(sigma))
    ax.set_ylim(y_min, y_max)
    ax.legend(loc='upper left')

def run_tests() : 
    amplitudes = [8.7, 87, 870, 8700]
    photon_count_data.clear()
    running_average.clear()
    plot_tests([0.005, 0.05, 0.5], amplitudes)
    plot_tests([5, 50, 500], amplitudes)

def plot_tests(sigmas, amplitudes) :
    running_avg = plt.figure(constrained_layout=True)
    running_avg.clear()
    gs = gridspec.GridSpec(sigmas.__len__(), amplitudes.__len__(), figure=running_avg)

    light_curve = plt.figure(constrained_layout=True)
    light_curve.clear()
    lc_gs = gridspec.GridSpec(sigmas.__len__(), amplitudes.__len__(), figure=light_curve)

    row = 0
    column = 0
    for sigma in sigmas :
        for amplitude in amplitudes :
            bursts.clear()
            state.vars['default_A'] = amplitude
            state.vars['default_sigma'] = sigma
            
            if (sigma > 100) :
                state.vars['duration'] = 500
            else :
                state.vars['duration'] = 100
            
            init_vars()
            sim()
            ax = running_avg.add_subplot(gs[row, column])
            ax.plot(running_average, 'o', color='blue')
            ax.set_xlabel('time (s)', fontsize='small')
            ax.set_ylabel('running avg\n(counts/s)', fontsize='small')
            ax.set_ylim(top=max(running_average) * 1.2)
            if (triggered_timestamp > 0) :
                ax.axvline(triggered_timestamp, color='orange')
                ax.axvline(triggered_timestamp - tail, color='gray', linestyle='dashed')
            if (exit_timestamp > 0) :
                if exit_timestamp == duration :
                    ax.axvline(exit_timestamp, color='black')
                else :
                    ax.axvline(exit_timestamp, color='orange')
                    ax.axvline(exit_timestamp + tail, color = 'gray', linestyle='dashed')
            ax.set_title('A = ' + str(amplitude) + ', sigma = ' + str(sigma), fontsize='small', loc='left')

            ax2 = light_curve.add_subplot(lc_gs[row, column])
            if (light_curve_counts != [] and light_curve_timestamps != []) :
                lc_counts_per_s = [i / ebe_bin_length for i in light_curve_counts]
                ax2.stairs(lc_counts_per_s[1:], light_curve_timestamps, color='red')
                ax2.set_xlabel('Time')
                ax2.set_ylabel('Counts/s')
                ax2.axhline(rate, color='blue')
            ax2.set_title('A = ' + str(amplitude) + ', sigma = ' + str(sigma), fontsize='small', loc='left')
            column = column + 1
        column = 0
        row = row + 1
    running_avg.suptitle('Running Average of Photon Count (' + str(running_avg_length) + 's)')
    plt.rc('font', size=6)
    #plt.tight_layout()
    plt.show()


#   Variable Modification Methods

#   Default method to change a global var in config.py
def change_var(var, var_name, var_type, var_units) :
    mod = ''
    while (mod != 'y' and mod != 'n') :
        mod = str(
            input('\nCurrent ' + var_name + ' is ' + str(var) + ' ' + var_units + '. Would you like to modify it? (y/n) ')
        )
    if mod == 'n' :
        modify_variables()
    else :
        var = var_type(
            input('\nEnter the new value for ' + var_name + ': ' )
        )
        print('\n' + var_name + ' has been changed to ' + str(var) + ' ' + var_units + '!\n')
        return var

#   Basic simulation variable mod methods
def change_running_average_length() :
    state.vars['running_avg_length'] = change_var(running_avg_length, 'RUNNING AVG LENGTH', int, 's')
    init_vars()

def change_rate() :
    state.vars['rate'] = change_var(rate, 'RATE', int, 'photons/s')
    init_vars()

def change_duration() :
    state.vars['duration'] = change_var(duration, 'DURATION', int, 's')
    init_vars()

def change_photon_list_length() :
    state.vars['size_list'] = change_var(size_list, 'PHOTON LIST SIZE', int, 'photons')
    init_vars()

#   Trigger modification methods
def change_significance_constant() :
    state.vars['enter_significance_constant'] = change_var(enter_significance_constant, 'SIGNIFICANCE CONSTANT (TRIGGER)', float, '')
    init_vars()

def change_exit_significance_constant() :
    state.vars['exit_significance_constant'] = change_var(exit_significance_constant, 'SIGNIFICANCE CONSTANT (EXIT TRIGGER)', float, '')
    init_vars()

def change_tail_length() :
    state.vars['tail'] = change_var(tail, 'TAIL LENGTH', int, 's')
    init_vars()

def change_enter_look_back_to() :
    state.vars['enter_look_back_to'] = change_var(enter_look_back_to, 'LOOK BACK TO (TRIGGER)', int, 's')
    init_vars()

def change_exit_look_back_to() :
    state.vars['exit_look_back_to'] = change_var(exit_look_back_to, 'LOOK BACK TO (EXIT)', int, 's')
    init_vars()

def change_event_by_event_bin_length() :
    state.vars['ebe_bin_length'] = change_var(ebe_bin_length, 'EVENT-BY-EVENT BIN LENGTH', float, 's')
    init_vars()

# tab function (pyplot won't allow \t)
def t() :
    return '     '

#   Used in terminal to transition between menus
def press_enter_to_continue() :
    i = input('Press ENTER to continue: ')

#   String methods
def basic_sim_variables_str() : 
    summary = ( '\nBasic simulation variables: ' + 
                '\n' + t() + 'Simulation duration (in seconds) : ' + str(duration) + 
                '\n' + t() + 'Rate of photon arrival per second: ' + str(rate) + 
                '\n' + t() + 'Length of the photon list queue: ' + str(size_list) +
                '\n' + t() + 'Running average length (in seconds): ' + str(running_avg_length) + 
                '\n' + t() + 'Event-by-event bin duration (in seconds): ' + str(ebe_bin_length))
    return summary

def trigger_variables_str() : 
    summary = ( '\nTrigger Variables: ' + 
                '\n' + t() + 'Trigger significance constant: ' + str(enter_significance_constant) + 
                '\n' + t() + 'Exit trigger significance constant ' + str(exit_significance_constant) + 
                '\n' + t() + 'Tail length (in seconds): ' + str(tail) + 
                '\n' + t() + 'Trigger lookback duration (in seconds): ' + str(enter_look_back_to) +
                '\n' + t() + 'Exit trigger lookback duration (in seconds): ' + str(exit_look_back_to)) 
    return summary

def burst_info_str() : 
    summary = '\n' + 'Burst information: '
    i = 0
    if len(bursts) == 0 :
        summary += '\nThere are no peaks to display.'
    else :
        for burst in bursts :
            summary += ('\n' + t() + 'Peak ' + str(i) + '\n' + t() + t() + 'Peaks at ' + str(round(burst.peak_time, 2)) + 's\n' + t() + t() + 'A = ' + str(burst.amplitude) + '\n' + t() + t() + 'Sigma = ' + str(burst.sigma))
            i += 1
    return summary

def display_burst_info() :
    system('cls')
    print(burst_info_str())

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
        return_to_main_menu()

#   Burst list modification methods
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
        press_enter_to_continue()

def clear_bursts() :
    system('cls')
    print(burst_info_str())
    ans = ''
    while ans != 'y' and ans != 'n' :
        ans = input(
            '\nWould you like to delete all bursts? (y/n) '
        )
    if ans == 'y' :
        global bursts
        bursts.clear()
        print('\nBurst list was successfully cleared.')

def add_burst_helper() :
    system('cls')
    functions_names = [add_sgrb, add_lgrb, return_to_burst_menu]
    menu_items = dict(enumerate(functions_names, start=0))
    selection = -99
    while selection not in range(len(menu_items) + 1):
        print(burst_info_str())
        print('\nAdd burst options: ')
        display_menu(menu_items)
        try:
            selection = int(
                input("Please enter your selection number: ")
            )
        except:
            continue
    selected_value = menu_items[selection]
    selected_value()

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
        press_enter_to_continue()

def add_sgrb() :
    add_grb(grb(peak_time=sgrb_peak_time, amplitude=sgrb_A, sigma=sgrb_sigma))

def add_lgrb() :
    add_grb(grb(lgrb_peak_time, lgrb_A, lgrb_sigma))

def add_grb(burst) :
    system('cls')
 
    ans = 99
    while ans != 0 and ans != 1 and ans != 2:
        print(burst_info_str())
        print('\nDefault parameters: ')
        print('\tPeaks at ' + str(burst.peak_time) + '\n\tA = ' + str(burst.amplitude) + '\n\tSigma = ' + str(burst.sigma))
        print('\nWould you like to \n\t0: Add the default burst\n\t1: Modify the burst\n\t2: Return to menu')
        try : 
            ans = int(input('\nEnter 0, 1, or 2: '))
        except :
            continue
    if ans == 0 :
        global bursts
        bursts.append(burst)
        i = 99
        while i != 0 and i != 1 :
            try:
                i = int(input('Success! Press 0 to add another burst or 1 to return to main menu'))
            except:
                continue
        if i == 0 :
            add_burst_helper()
        else :
            return_to_main_menu()
    if ans == 1 :
        modify(burst)
    if ans == 2 :
        press_enter_to_continue()

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
            global bursts
            bursts.append(burst)
            i = 99
            while i != 0 and i != 1 :
                i = int(input('Success! Press 0 to add another burst or 1 to return to main menu '))
                if i == 0 :
                    add_burst_helper()
                else :
                    return_to_main_menu()
        else :
            modify(burst)
    if ans == 4 :
        return_to_burst_menu()

def return_to_burst_menu() :
    press_enter_to_continue()
    modify_bursts()

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

#   Save / Load methods
def save_current_settings() :
    ans = ''
    while ans != 'y' and ans != 'n' :
        ans = input('Would you like to save the current settings? (y/n) ')
    if ans == 'y' : 
        filename = input('Enter your desired filename: ')
        state.save(filename + '.json')
        print('The simulation was saved as ' + filename + '.json')

def load_settings() :
    ans = ''
    while ans != 'y' and ans != 'n' :
        ans = input('Would you like to load settings from a file? (y/n) ')
    if ans == 'y' :
        files = list_json_files()
        file_options = dict(enumerate(files, start=0))
        for k, file in file_options.items():
            print('\t', k, file)
        selection = -99
        while selection not in range(0,len(files) + 1) :
            try:
                selection = int(
                    input('\nPlease enter your selection number: ')
                )
            except:
                continue
        bursts.clear()
        state.load(file_options[selection])
        init_vars()
        
        
def list_json_files():
    curr_dir = os.getcwd()
    json_files = []
    for filename in os.listdir(curr_dir) :
        if fnmatch.fnmatch(filename, '*.json'):
            json_files.append(filename)
    return json_files

#   Menu methods
def return_to_modification_menu() :
    modify_variables()

#   Return to previous menu methods
def exit() : 
    system('cls')  # clears stdout
    print("Goodbye")
    sys.exit()

def return_to_main_menu() :
    main()

#   Modify variables menu
def modify_variables() :
    functions_names = [modify_basic_simulation_variables, modify_trigger_variables, modify_bursts, return_to_main_menu]
    menu('VARIABLE MODIFICATION MENU', functions_names)

def modify_basic_simulation_variables() :
    functions_names = [display_all_variables, change_duration, change_rate, change_photon_list_length, change_running_average_length, 
                       change_event_by_event_bin_length, return_to_modification_menu, return_to_main_menu]
    menu('SIMULATION VARIABLE MODIFICATION MENU', functions_names)

def modify_trigger_variables() :
    functions_names = [display_all_variables, change_significance_constant, change_exit_significance_constant, change_tail_length, change_enter_look_back_to, 
                       change_exit_look_back_to, return_to_modification_menu, return_to_main_menu]
    menu('TRIGGER VARIABLE MODIFICATION MENU', functions_names)

def modify_bursts() :
    functions_names = [display_burst_info, add_burst, delete_burst, clear_bursts, return_to_modification_menu, return_to_main_menu]
    menu('BURST MODIFICATION MENU', functions_names)

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
    init_vars()
    functions_names = [run_simulation_and_plot, display_all_variables, modify_variables, run_tests, save_current_settings, load_settings, exit]
    menu('MAIN MENU', functions_names)

def menu(name, functions):
    # Create a menu dictionary where the key is an integer number and the
    # value is a function name.
    menu_items = dict(enumerate(functions, start=1))
    
    while True: 
        system('cls')
        selection = 0
        print(name)
        display_menu(menu_items)
        while selection not in range(1,len(functions) + 1) :
            try:
                selection = int(
                    input('\nPlease enter your selection number: ')
                )
            except:
                continue
        
        selected_value = menu_items[selection]
        selected_value()
        press_enter_to_continue()

if __name__ == "__main__":
    main()