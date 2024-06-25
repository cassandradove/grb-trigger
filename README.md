<h1>GRB Detection Algorithm for Background and Transient Observer</h1>
<p>This code contains a work in progress of a simulation to test different algorithms for detecting gamma-ray bursts on BTO.</p>
<p>Currently, you can run sim.py in command line to see a customizable simulation of gamma ray bursts with a simple terminal user interface</p>
<p>Functionality currently includes:</p>
<ul>
  <li>Run simulation and plot</li>
  <li>Update simulation variables such as simulation duration, photon rate in terminal</li>
  <li>Update trigger algorithm constants such as significance constant, "tail" length, amount of time to consider for background rate</li>
  <li>Add and delete bursts within the simulation</li>
  <li>Default lgrb and sgrb objects</li>
  <li>Exit trigger funtionality, with customizable variables</li>
  <li>Light curve graph using simulated trigger timeline</li>
  <li>Functionality to export/import data to simulate</li>
  <li>Script to fit a gaussian curve to real data from a .dat file to help refine simulation model</li>
</ul>

<p>To Do:</p>
<ul>
  <li>Create basic flares that look like the ones BTO will see</li>
  <li>Expand save/load to include the customized bursts</li>
</ul>
