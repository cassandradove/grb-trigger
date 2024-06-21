import json

class GlobalState:
    def __init__(self):
        self.vars = {
            'duration': 100,
            'rate': 30,
            'size_list': 600,
            'running_avg_length': 3,
            'ebe_bin_length': 0.04,
            'enter_significance_constant': 6,
            'tail': 4,
            'enter_look_back_to': 17,
            'trigger_threshold_met': False,
            'triggered_timestamp': -999,
            'exit_timestamp': -999,
            'exit_significance_constant': 3,
            'exit_look_back_to': 15,
            'show_peak_data': True,
            'random_seed': 112,
            'sgrb_A': 20,
            'sgrb_sigma': 0.001,
            'lgrb_A': 2,
            'lgrb_sigma': 5
        }

    def save(self, filename):
        with open(filename, 'w') as file:
            json.dump(self.vars, file, indent=4)
    
    def load(self, filename):
        with open(filename, 'r') as file:
            self.vars = json.load(file)