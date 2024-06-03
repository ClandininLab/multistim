import os
import functools

import h5py
import numpy as np
import pandas as pd
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.signal as signal
from .imaging_data import ImagingDataObject


### DO NOT USE interp1d FUNCTION, MESSED THINGS UP
def interp(tp, p, tq, wid=10):
    '''
    interp uses nearby values for generating a smooth function of time (axis=-1)
    '''
    output_shape = list(p.shape)
    output_shape[-1] = tq.shape[0]
    q = np.zeros(output_shape)
    for i, t in enumerate(tq):
        idx = np.argpartition(np.abs(tp - t), wid)[:wid]
        q[..., i] = np.mean(p[..., idx], axis=-1)
    return q


def getPhotodiodeSignal(image_series_name, data_directory, v_rec_suffix='_Cycle00001_VoltageRecording_001'):
    # image_series_name = 'TSeries-' + experiment_file_name.replace('-', '') + '-' + ('00' + str(series_number))[-3:]
    metadata = ET.parse(os.path.join(data_directory, image_series_name, image_series_name + v_rec_suffix + '.xml'))
    root = metadata.getroot()
    rate_node = root.find('Experiment').find('Rate')
    sample_rate = int(rate_node.text)

    active_channels = []
    signal_list = list(root.find('Experiment').find('SignalList'))
    for signal_node in signal_list:
        is_channel_active = signal_node.find('Enabled').text
        channel_name = signal_node.find('Name').text
        if is_channel_active == 'true':
            active_channels.append(channel_name)

    # Load frame tracker signal and pull frame/epoch timing info
    data_frame = pd.read_csv(os.path.join(data_directory, image_series_name, image_series_name + v_rec_suffix + '.csv'))

    time_vector = data_frame.get('Time(ms)').values / 1e3  # ->sec

    frame_monitor = []  # get responses in all active channels
    for ac in active_channels:
        frame_monitor.append(data_frame.get(' ' + ac).values)
    frame_monitor = np.vstack(frame_monitor)

    return frame_monitor, time_vector, sample_rate


def load_timestamps(image_series_name, data_directory):
    """ Parses a Bruker xml file to get the times of each frame, or loads h5py file if it exists.
    First tries to load from 'timestamps.h5' (h5py file). If this file doesn't exist
    it will load and parse the Bruker xml file, and save the h5py file for quick loading in the future.
    Parameters
    ----------
    directory: full directory that contains xml file (str).
    file: Defaults to 'functional.xml'
    Returns
    -------
    timestamps: [t,z] numpy array of times (in ms) of Bruker imaging frames.
    """
    h5_path = os.path.join(data_directory, image_series_name, 'imaging_timestamps.h5')
    if os.path.exists(h5_path):
        with h5py.File(h5_path, 'r') as hf:
            timestamps = hf['timestamps'][:]

    else:
        xml_file = os.path.join(data_directory, image_series_name, image_series_name + '.xml')
        tree = ET.parse(xml_file)
        root = tree.getroot()
        timestamps = []

        sequences = root.findall('Sequence')
        for sequence in sequences:
            frames = sequence.findall('Frame')
            for frame in frames:
                filename = frame.findall('File')[0].get('filename')
                time = float(frame.get('relativeTime'))
                timestamps.append(time)

        if len(sequences) > 1:
            timestamps = np.reshape(timestamps, (len(sequences), len(frames)))
        else:
            timestamps = np.reshape(timestamps, (len(frames), len(sequences)))

        ### Save h5py file ###
        with h5py.File(os.path.join(data_directory, image_series_name, 'imaging_timestamps.h5'), 'w') as hf:
            hf.create_dataset("timestamps", data=timestamps)

    return timestamps


def find_series(name, obj, series_number):
    """return hdf5 group object if it corresponds to indicated series_number."""
    target_group_name = 'series_{}'.format(str(series_number).zfill(3))
    if target_group_name in name:
        return obj
    return None


def encode_stim(keys, epoch):
    coding_str = ''
    for key in keys:
        coding_str = coding_str + key + '_' + str(epoch[key]).replace('.', 'p') + '#'
    return coding_str


def simple_hour2sec(hour_string):
    hour = [float(num) for num in hour_string.split(':')]
    return hour[0] * 3600 + hour[1] * 60 + hour[2]


def remove_extreme_trace(traces, wid=10, thr=6):
    trace_list = traces.copy()
    bad_inds = []
    for i, trace in enumerate(trace_list):
        #extreme_value = np.max(np.abs(trace))
        extreme_value_point = np.argmax(np.abs(trace))
        extreme_value = np.mean(trace[np.max([extreme_value_point-wid, 0]):extreme_value_point+wid])
        tmp = trace_list.copy()
        _ = tmp.pop(i)
        test_values = [np.mean(t[np.max([extreme_value_point-wid, 0]):extreme_value_point+wid]) for t in tmp]
        test_mean = np.mean(test_values)
        test_std = np.std(test_values)
        if np.abs(extreme_value-test_mean)/test_std > thr:
            print('trace No. {} is bad'.format(i))
            bad_inds.append(i)
    if len(bad_inds) > 0:
        traces = [t for i, t in enumerate(traces) if i not in bad_inds]
    return traces


def getStimulusTypes(ID: ImagingDataObject, para_key=['color'], run_para_key=None):
    stims = []
    epoch_parameters = ID.getEpochParameters()
    run_parameters = ID.getRunParameters()
    for epoch in epoch_parameters:
        if run_para_key is None:
            stims.append(encode_stim(para_key, epoch))
        else:
            stim_ = run_para_key + '_' + str(run_parameters[run_para_key]).replace('.', 'p') + '#' +\
                    encode_stim(para_key, epoch)
            stims.append(stim_)

    stim_types = list(set(stims))
    type2ind = {tp: ind for ind, tp in enumerate(stim_types)}
    return stims, type2ind


def stimulus_triggered_average(ID: ImagingDataObject, timestamps, brain, stimulus_timing, para_key=['color']):
    epoch_parameters = ID.getEpochParameters()
    run_parameters = ID.getRunParameters()
    stims, type2ind = ID.getStimulusTypes(para_key)

    epoch_start_times = stimulus_timing['stimulus_start_times'] - run_parameters['pre_time']
    epoch_end_times = stimulus_timing['stimulus_end_times'] + run_parameters['tail_time']

    epoch_time = 1.00 * (run_parameters['pre_time'] +
                         run_parameters['stim_time'] +
                         run_parameters['tail_time'])  # sec

    ensemble = [[] for _ in type2ind.keys()]
    relative_time = [[] for _ in type2ind.keys()]

    cut_inds = np.empty(0, dtype=int)
    for idx, val in enumerate(epoch_start_times):
        stack_inds = np.where(np.logical_and(timestamps < val + epoch_time + 0.01,
                                             timestamps >= val - 0.01))[0]
        which_type = type2ind[stims[idx]]
        ensemble[which_type].append(brain[:, :, stack_inds])
        stim_time = stimulus_timing['stimulus_start_times'][idx]
        relative_time[which_type].append(timestamps[stack_inds] - stim_time)

    return type2ind, ensemble, relative_time


def get_responses_per_condition(ID: ImagingDataObject, roi_data, para_key=['color'], run_para_key=None, remove_extreme_value=False):
    stims, type2ind = getStimulusTypes(ID, para_key, run_para_key)
    run_parameters = ID.getRunParameters()
    ensemble = [[] for _ in type2ind.keys()]
    relative_time = [[] for _ in type2ind.keys()]
    traces = roi_data['epoch_response'][0, :]
    for idx, trace in enumerate(traces):
        which_type = type2ind[stims[idx]]
        ensemble[which_type].append(trace)
        relative_time = roi_data['time_vector'] - run_parameters['pre_time']

    if remove_extreme_value:
        for ind in type2ind.values():
            ensemble[ind] = remove_extreme_trace(ensemble[ind])

    return type2ind, ensemble, relative_time


def getStimulusTime(ID: ImagingDataObject, fs=50):
    run_parameters = ID.getRunParameters()
    epoch_time = 1.00 * (run_parameters['pre_time'] +
                         run_parameters['stim_time'] +
                         run_parameters['tail_time'])
    return np.arange(0, int(fs * epoch_time)) / fs - run_parameters['pre_time']


def get_roi_mean(ID: ImagingDataObject, condition_number=2, run_para_key=None):
    epoch_parameters = ID.getEpochParameters()
    roi_set_names = ID.getRoiSetNames()
    if 'bg' not in roi_set_names:
        return
    elif len(roi_set_names) < 3:
        return
    roi_set_names.remove('bg')

    condition = [k for k in epoch_parameters[0].keys() if 'current' in k][:condition_number]
    stims, type2ind = getStimulusTypes(ID, condition, run_para_key)
    para_set = list(type2ind.keys())
    res_dict = {para:[] for para in para_set}

    for ind, roi in enumerate(roi_set_names):
        roi_data = ID.getRoiResponses(roi, background_subtraction=True)
        type2ind, ensemble, relative_time = get_responses_per_condition(ID, roi_data, para_key=condition, run_para_key=run_para_key)
        if len(para_set) > 1:
            for p_ind, para in enumerate(para_set):
                res = ensemble[type2ind[para]]
                res_dict[para].append(np.mean(res, axis=0))
        else:
            type2ind, ensemble, relative_time = get_responses_per_condition(ID, roi_data, para_key=condition, run_para_key=run_para_key)
            res = ensemble[0]
            res_dict[para_set[0]].append(np.mean(res, axis=0))
    return relative_time, res_dict


def get_roi_response(ID: ImagingDataObject, condition_number=2, run_para_key=None, roi='bg'):
    epoch_parameters = ID.getEpochParameters()
    roi_set_names = ID.getRoiSetNames()
    if 'bg' not in roi_set_names:
        return
    elif len(roi_set_names) < 3:
        return
    roi_set_names.remove('bg')

    condition = [k for k in epoch_parameters[0].keys() if 'current' in k][:condition_number]
    stims, type2ind = getStimulusTypes(ID, condition, run_para_key)
    para_set = list(type2ind.keys())
    res_dict = {para:[] for para in para_set}

    roi_data = ID.getRoiResponses(roi, background_subtraction=True)
    type2ind, ensemble, relative_time = get_responses_per_condition(ID, roi_data, para_key=condition, run_para_key=run_para_key)
    if len(para_set) > 1:
        for p_ind, para in enumerate(para_set):
            res = ensemble[type2ind[para]]
            res_dict[para].append(np.mean(res, axis=0))
    else:
        type2ind, ensemble, relative_time = get_responses_per_condition(ID, roi_data, para_key=condition, run_para_key=run_para_key)
        res = ensemble[0]
        res_dict[para_set[0]].append(np.mean(res, axis=0))
    return relative_time, res_dict


def summary_figure(ID: ImagingDataObject, condition_number=2, figure_size=(4, 4), ylim=None, condition=None,
                   save_dir=None, run_para_key=None):
    if ylim is None:
        ylim = [-0.2, 0.1]
    run_parameters = ID.getRunParameters()
    epoch_parameters = ID.getEpochParameters()
    experiment_date = ID.file_path.split('/')[-1].split('.')[0]
    roi_set_names = ID.getRoiSetNames()
    if 'bg' not in roi_set_names:
        return
    elif len(roi_set_names) < 3:
        return
    roi_set_names.remove('bg')

    if condition is None:
        condition = [k for k in epoch_parameters[0].keys() if 'current' in k][:condition_number]
    stims, type2ind = getStimulusTypes(ID, condition, run_para_key)

    figure_title = run_parameters['protocol_ID'] + '_' + experiment_date + '_trial_' + str(ID.series_number)
    para_set = list(type2ind.keys())
    para_set = list(sorted(para_set))  # for making the parameters consistent across figures
    res_dict = {para:[] for para in para_set}

    big_figure_size = (figure_size[0]*(len(roi_set_names)+2), figure_size[1]*len(para_set))
    fh, ax = plt.subplots(len(para_set), len(roi_set_names)+2, figsize=big_figure_size, tight_layout=True, facecolor='snow')
    fh.suptitle(figure_title)
    [x.set_ylim(ylim) for x in ax.ravel()]
    #[plot_tools.cleanAxes(x) for x in ax.ravel()]

    for ind, roi in enumerate(roi_set_names):
        roi_data = ID.getRoiResponses(roi, background_subtraction=True)
        type2ind, ensemble, relative_time = get_responses_per_condition(ID, roi_data, para_key=condition, run_para_key=run_para_key)
        if len(para_set) > 1:
            for p_ind, para in enumerate(para_set):
                #ax[ind, para].axhline(y=0, color='k', alpha=0.5)
                res = ensemble[type2ind[para]]
                res_dict[para].append(np.mean(res, axis=0))
                #ax[ind, para].fill_betweenx(y=[-1, 1], x1=sac_st, x2=sac_st+0.20, color='y', linewidth=1)
                ax[p_ind, ind].plot(relative_time, np.mean(res, axis=0))

                if p_ind == 0:
                    ax[p_ind, ind].set_title(roi_set_names[ind], color=ID.colors[ind+1], fontsize=12)
                if ind == 0:
                    ax[p_ind, ind].set_ylabel(para_set[p_ind], color='k', fontsize=10)
        else:
            type2ind, ensemble, relative_time = get_responses_per_condition(ID, roi_data, para_key=condition, run_para_key=run_para_key)
            res = ensemble[0]
            res_dict[para_set[0]].append(np.mean(res, axis=0))
            ax[ind].plot(relative_time, np.mean(res, axis=0))
            ax[ind].set_title(roi_set_names[ind], color=ID.colors[ind+1], fontsize=12)
            if ind == 0:
                ax[ind].set_ylabel(para_set[0], color='k', fontsize=10)

    ind = len(roi_set_names)
    if ind > 1:  # check if the average is needed
        if len(para_set) > 1:
            for p_ind, para in enumerate(para_set):
                tmp = np.vstack(res_dict[para])
                ax[p_ind, ind].plot(relative_time, np.mean(tmp, axis=0))
                if p_ind == 0:
                    ax[p_ind, ind].set_title('average', color=ID.colors[ind+1], fontsize=12)
            ID.generateRoiMap(roi_set_names, ax=ax[0, ind + 1])
            ax[0, ind + 1].set_ylim([0, 320])
            for p_ind, para in enumerate(para_set):
                if p_ind > 0:
                    ax[p_ind, ind + 1].remove()
        else:
            tmp = np.vstack(res_dict[para_set[0]])
            ax[ind].plot(relative_time, tmp.mean(0))
            ax[ind].set_title('average', color=ID.colors[ind + 1], fontsize=12)
            ID.generateRoiMap(roi_set_names, ax=ax[ind + 1])
            ax[ind + 1].set_ylim([0, 320])
    else:
        if len(para_set) > 1:
            ID.generateRoiMap(roi_set_names, ax=ax[0, ind])
            ax[0, ind + 1].set_ylim([0, 320])
            for p_ind, para in enumerate(para_set):
                if p_ind > 0:
                    ax[p_ind, ind].remove()
                    ax[p_ind, ind+1].remove()
            ax[0, ind + 1].remove()
        else:
            ID.generateRoiMap(roi_set_names, ax=ax[ind])
            ax[ind].set_ylim([0, 320])
            ax[ind + 1].remove()

    if save_dir:
        save_path = os.path.join(save_dir, figure_title+'.png')
        fh.savefig(save_path, dpi=300)