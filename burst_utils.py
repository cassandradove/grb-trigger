from os import system

def burst_info_str() : 
    summary = '\n' + 'Burst information: '
    i = 0
    for burst in bursts :
        summary += ('\n' + t() + 'Peak ' + str(i) + '\n' + t() + t() + 'Peaks at ' + str(round(burst.peak_time, 2)) + 's\n' + t() + t() + 'A = ' + str(burst.amplitude) + '\n' + t() + t() + 'Sigma = ' + str(burst.sigma))
        i += 1
    return summary

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
    functions_names = [return_to_burst_menu]
    menu_items = dict(enumerate(functions_names, start=0))
    while True:
        system('cls')
        print('\nAdd burst options: ')
        display_menu(menu_items)
        selection = int(
            input("Please enter your selection number: ")
        )
        selected_value = menu_items[selection]
        selected_value()