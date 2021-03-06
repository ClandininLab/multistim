"""
Shared analysis tools for visanalysis

https://github.com/ClandininLab/visanalysis
mhturner@stanford.edu
"""
import glob
import h5py
import numpy as np
import matplotlib.pyplot as plt
from visanalysis.util import plot_tools


def matchQuery(epoch_parameters, query):
    """

    params:
        epoch_parameters: single epoch_parameter dict
        query: dict, key-value pairs indicate matching parameter editable_values
            e.g. query = {'current_intensity': 0.75}

    Returns:
        Bool, True if all param values match, false otherwise
    """
    return np.all([epoch_parameters.get(key) == query[key] for key in query])

def filterTrials(epoch_response, ID, query, return_inds=False):
    matching_trials = np.where([matchQuery(ep, query) for ep in ID.getEpochParameters()])[0]
    max_num_trials = epoch_response.shape[1]
    matching_trials = matching_trials[matching_trials < max_num_trials]


    if return_inds:
        return epoch_response[:, matching_trials, :], matching_trials
    else:
        return epoch_response[:, matching_trials, :]

def getUniqueParameterCombinations(param_keys, ID):
    ep_params = [[ep.get(x, None) for x in param_keys]for ep in ID.getEpochParameters()]
    return list({tuple(row) for row in ep_params})

def plotResponseByCondition(ImagingData, roi_name, condition, eg_ind=-1, background_subtraction=False, F_scale=0.1):
    roi_data = ImagingData.getRoiResponses(roi_name, background_subtraction=background_subtraction)

    unique_parameter_values = np.unique([ep.get(condition) for ep in ImagingData.getEpochParameters()])
    fh, ax = plt.subplots(1, len(unique_parameter_values), figsize=(8, 2))
    [x.set_axis_off() for x in ax]
    [x.set_ylim([-0.25, 2*F_scale]) for x in ax]
    for p_ind, param_value in enumerate(unique_parameter_values):
        query = {condition: param_value}
        trials = filterTrials(roi_data.get('epoch_response'), ImagingData, query)
        ax[p_ind].plot(roi_data.get('time_vector'), np.mean(trials[eg_ind, :, :], axis=0), linestyle='-', color=ImagingData.colors[0])

        if p_ind == 0:  # scale bar
            plot_tools.addScaleBars(ax[p_ind], dT=1, dF=F_scale, F_value=-0.25, T_value = -0.2)

def collectResponseByCondition(ImagingData, roi_response, condition, eg_ind=-1, para_ind=0):
    '''
    TODO: make sure the eg_ind is correct here, and add a selection for which parameter to choose
    '''
    unique_parameter_values = np.unique([ep.get(condition) for ep in ImagingData.getEpochParameters()])
    unique_parameter_values.sort()  # ascend
    for p_ind, param_value in enumerate(unique_parameter_values):
        if p_ind == para_ind:
            query = {condition: param_value}
            trials = filterTrials(roi_response, ImagingData, query)
    return trials[eg_ind, :, :]


'''
def plotRoiResponses(ImagingData, roi_name, F_scale=0.1):
    roi_data = ImagingData.getRoiResponses(roi_name)

    fh, ax = plt.subplots(1, int(roi_data.get('epoch_response').shape[0]+1), figsize=(6, 2))
    [x.set_axis_off() for x in ax]
    [x.set_ylim([-0.25, 0.4]) for x in ax]

    for r_ind in range(roi_data.get('epoch_response').shape[0]):
        time_vector = roi_data.get('time_vector')
        no_trials = roi_data.get('epoch_response')[r_ind, :, :].shape[0]
        current_mean = np.mean(roi_data.get('epoch_response')[r_ind,:,:], axis=0)
        current_std = np.std(roi_data.get('epoch_response')[r_ind,:,:], axis=0)
        current_sem = current_std / np.sqrt(no_trials)

        ax[r_ind].plot(time_vector, current_mean, 'k')
        ax[r_ind].fill_between(time_vector,
                            current_mean - current_sem,
                            current_mean + current_sem,
                            alpha=0.5)
        ax[r_ind].set_title(int(r_ind))

        if r_ind == 0: # scale bar
            plot_tools.addScaleBars(ax[r_ind], 1, F_scale, F_value = -0.1, T_value = -0.2)
'''


def filterDataFiles(data_directory, target_fly_metadata={}, target_series_metadata={}, target_roi_series=[]):
    """
    Searches through a directory of visprotocol datafiles and finds datafiles/series that match the search values
    Can search based on any number of fly metadata params or run parameters

    Params
        -data_directory: directory of visprotocol data files to search through
        -target_fly_metadata: (dict) key-value pairs of target parameters to search for in the fly metadata
        -target_series_metadata: (dict) key-value pairs of target parameters to search for in the series run (run parameters)
        -target_roi_series: (list) required roi_series names

    Returns
        -matching_series: List of matching series dicts with all fly & run params as well as file name and series number
    """
    fileNames = glob.glob(data_directory + "/*.hdf5")
    print('Found {} files in {}'.format(len(fileNames), data_directory))

    # collect key/value pairs for all series in data directory
    all_series = []
    for ind, fn in enumerate(fileNames):
        with h5py.File(fn, 'r') as data_file:
            for fly in data_file.get('Flies'):
                fly_metadata = {}
                for f_key in data_file.get('Flies').get(fly).attrs.keys():
                    fly_metadata[f_key] = data_file.get('Flies').get(fly).attrs[f_key]

                for epoch_run in data_file.get('Flies').get(fly).get('epoch_runs'):
                    series_metadata = {}
                    for s_key in data_file.get('Flies').get(fly).get('epoch_runs').get(epoch_run).attrs.keys():
                        series_metadata[s_key] = data_file.get('Flies').get(fly).get('epoch_runs').get(epoch_run).attrs[s_key]

                    new_series = {**fly_metadata, **series_metadata}
                    new_series['series'] = int(epoch_run.split('_')[1])
                    new_series['file_name'] = fn.split('\\')[-1].split('.')[0]

                    existing_roi_sets = list(data_file.get('Flies').get(fly).get('epoch_runs').get(epoch_run).get('rois').keys())
                    new_series['rois'] = existing_roi_sets

                    all_series.append(new_series)


    # search in all series for target key/value pairs
    match_dict = {**target_fly_metadata, **target_series_metadata}
    matching_series = []
    for series in all_series:
        if all(series[key] == match_dict[key] for key in match_dict):
            if np.all([r in series.get('rois') for r in target_roi_series]):
                matching_series.append(series)

    print('Found {} matching series'.format(len(matching_series)))
    return matching_series
