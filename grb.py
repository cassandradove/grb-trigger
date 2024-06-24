import numpy as np
from config import *
# Gamma ray burst class with default values

class grb :
    # Quick initialization of a GRB with default values that can be overridden if so desired
    def __init__(self, peak_time = 50, amplitude = 5, sigma = 1):
        self.peak_time = peak_time
        self.amplitude = amplitude
        self.sigma = sigma

    # Returns a Gaussian curve with respect to time that can be added onto background noise to represent a GRB
    def burst_addition(self, curr_time):
        exponent = ((curr_time - self.peak_time) ** 2) / (-2 * self.sigma)
        return self.amplitude * np.exp(exponent)
    
    def __str__(self) :
        return 'Peak time: ' + str(round(self.peak_time, 2)) + 's, A=' + str(self.amplitude) + ', sigma=' + str(self.sigma)