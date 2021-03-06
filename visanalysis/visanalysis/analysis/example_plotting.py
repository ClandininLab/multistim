from visanalysis.analysis import imaging_data, shared_analysis
import matplotlib.pyplot as plt
import numpy as np
import os


experiment_file_directory = '/Volumes/CLab/voltage_imaging/'
experiment_file_name = '2022-01-27'
series_number = 3

file_path = os.path.join(experiment_file_directory, experiment_file_name + '.hdf5')

# ImagingDataObject wants a path to an hdf5 file and a series number from that file
ID = imaging_data.ImagingDataObject(file_path,
                                    series_number,
                                    quiet=True)

# %% PARAMETERS & METADATA

# run_parameters: dict
run_parameters = ID.getRunParameters()


# epoch_parameters: list of dicts, one for each epoch (trial)
epoch_parameters = ID.getEpochParameters()

# fly_metadata: dict
fly_metadata = ID.getFlyMetadata()

# acquisition_metadata: dict
acquisition_metadata = ID.getAcquisitionMetadata()


# %% ROIS AND RESPONSES

# Get list of rois present in the hdf5 file for this series
roi_set_names = ID.getRoiSetNames()

roi_name = 'cell4'
roi_data = ID.getRoiResponses(roi_name, background_subtraction=True)

# test
shared_analysis.plotResponseByCondition(ID, roi_name='ROI1', condition='color', eg_ind=0)

# getRoiResponses() wants a ROI set name, returns roi_data (dict)
roi_data = ID.getRoiResponses('LC12')
roi_data.keys()

# Plot whole ROI response across entire series
fh0, ax0 = plt.subplots(1, 1, figsize=(12, 4))
ax0.plot(roi_data.get('roi_response')[0].T)
ax0.set_xlabel('Frame')
ax0.set_ylabel('Avg ROI intensity')

# Plot ROI response for trials 10 thru 15
# 'epoch_response' is shape (rois, trials, time)
fh1, ax1 = plt.subplots(1, 1, figsize=(6, 4))
ax1.plot(roi_data.get('time_vector'), roi_data.get('epoch_response')[0, 10:15, :].T)
ax1.set_ylabel('Response (dF/F)')
ax1.set_xlabel('Time (s)')

# %%

ID.generateRoiMap(roi_name='LC12', z=3)

# %%
shared_analysis.plotRoiResponses(ID, roi_name='LC12')

# %%
shared_analysis.plotResponseByCondition(ID, roi_name='LC12', condition='current_diameter', eg_ind=0)
