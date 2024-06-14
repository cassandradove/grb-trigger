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

# Default GRB parameters
# Short GRB
sgrb_peak_time = duration / 2
sgrb_A = 20
sgrb_sigma = 0.001

# Long GRB - note: to simulate a long grb, multiple of these peaks are required in sucession
lgrb_peak_time = duration / 2
lgrb_A = 2
lgrb_sigma = 5
