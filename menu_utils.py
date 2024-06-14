from os import system
from config import *

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

def display_menu(menu):
    """
    Display a menu where the key identifies the name of a function.
    :param menu: dictionary, key identifies a value which is a function name
    :return:
    """
    for k, function in menu.items():
        print('\t', k, function.__name__)

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

def return_to_modification_menu() :
    modify_variables()

def return_to_menu() :
    main()

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