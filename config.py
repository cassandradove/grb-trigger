import json

class GlobalState:

    def __init__(self):
        self.vars = {
            'duration': 100,
            'rate': 57,
            'size_list': 600,
            'running_avg_length': 3,
            'ebe_bin_length': 0.04,
            'enter_significance_constant': 5.5,
            'tail': 5,
            'enter_look_back_to': 17,
            'trigger_threshold_met': False,
            'triggered_timestamp': -999,
            'exit_timestamp': -999,
            'exit_significance_constant': 5,
            'exit_look_back_to': 10,
            'show_peak_data': True,
            'random_seed': 111,
            'sgrb_A': 10,
            'sgrb_sigma': 0.25,
            'lgrb_A': 81217.05,
            'lgrb_sigma': 2.62, 
            'default_A': 90,
            'default_sigma': 5
        }

    def save(self, filename):
        with open(filename, 'w') as file:
            json.dump(self.vars, file, indent=4)
    
    def load(self, filename):
        with open(filename, 'r') as file:
            self.vars = json.load(file)