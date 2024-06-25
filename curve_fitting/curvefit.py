import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Read the .dat file, skipping the first two lines and ignoring invalid data
data = np.genfromtxt('lgrb.dat', skip_header=2, delimiter=' ', invalid_raise=False)

# Extract columns (skip the first column)
x_data = data[:, 1]  # Select the second column
y_data = data[:, 2]  # Select the third column

# Step 2: Define the Gaussian function
def gaussian(x, amp, mean, stddev):
    return amp * np.exp(-((x - mean) ** 2) / (2 * stddev ** 2))

# Initial guess for the parameters [amplitude, mean, standard deviation]
initial_guess = [np.max(y_data), np.mean(x_data), np.std(x_data)]

# Bound amplitude to be between 0 and max(y_data)
bounds = ([0, -np.inf, 0], [np.max(y_data), np.inf, np.inf])

# Perform the curve fitting
popt, pcov = curve_fit(gaussian, x_data, y_data, p0=initial_guess, bounds=bounds)

# Extract the fitted parameters
amp, mean, stddev = popt

# Step 3: Plot the data and the fit
plt.figure()
plt.scatter(x_data, y_data, label='Data')
x_fit = np.linspace(min(x_data), max(x_data), 1000)
y_fit = gaussian(x_fit, *popt)
plt.plot(x_fit, y_fit, color='red', label='Gaussian Fit')

# Annotate the plot with the Gaussian formula
formula = f'$y = {amp:.2f} \exp\\left(-\\frac{{(x - {mean:.2f})^2}}{{2 \\times {stddev:.2f}^2}}\\right)$'
plt.text(0.55, 0.5, formula, transform=plt.gca().transAxes, fontsize=10,
         verticalalignment='center', horizontalalignment='left', bbox=dict(boxstyle='round,pad=0.5', edgecolor='black', facecolor='white'))

plt.legend()
plt.xlabel('Time')
plt.ylabel('Counts')
plt.title('Gaussian Fit for LGRB Burst')
plt.show()