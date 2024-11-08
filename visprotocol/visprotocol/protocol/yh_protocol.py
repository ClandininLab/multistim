#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from functools import partial

import numpy as np
from time import sleep
import os
import flyrpc.multicall
from visprotocol.protocol import clandinin_protocol


class BaseProtocol(clandinin_protocol.BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)  # call the parent class init method

    def getMovingPatchParameters(self, center=None, angle=None, speed=None, width=None, height=None, color=None,
                                 distance_to_travel=None):
        if center is None: center = self.adjustCenter(self.protocol_parameters['center'])
        if angle is None: angle = self.protocol_parameters['angle']
        if speed is None: speed = self.protocol_parameters['speed']
        if width is None: width = self.protocol_parameters['width']
        if height is None: height = self.protocol_parameters['height']
        if color is None: color = self.protocol_parameters['color']

        centerX = center[0]
        centerY = center[1]
        stim_time = self.run_parameters['stim_time']
        if distance_to_travel is None:  # distance_to_travel is set by speed and stim_time
            distance_to_travel = speed * stim_time
            # trajectory just has two points, at time=0 and time=stim_time
            startX = (0, centerX - np.cos(np.radians(angle)) * distance_to_travel / 2)
            endX = (stim_time, centerX + np.cos(np.radians(angle)) * distance_to_travel / 2)
            startY = (0, centerY - np.sin(np.radians(angle)) * distance_to_travel / 2)
            endY = (stim_time, centerY + np.sin(np.radians(angle)) * distance_to_travel / 2)
            x = [startX, endX]
            y = [startY, endY]

        else:  # distance_to_travel is specified, so only go that distance at the defined speed. Hang pre- and post- for any extra stim time
            travel_time = distance_to_travel / speed
            if travel_time > stim_time:
                print('Warning: stim_time is too short to show whole trajectory at this speed!')
                hang_time = 0
            else:
                hang_time = (stim_time - travel_time) / 2

            # split up hang time in pre and post such that trajectory always hits centerX,centerY at stim_time/2
            x_1 = (0, centerX - np.cos(np.radians(angle)) * distance_to_travel / 2)
            x_2 = (hang_time, centerX - np.cos(np.radians(angle)) * distance_to_travel / 2)
            x_3 = (hang_time + travel_time, centerX + np.cos(np.radians(angle)) * distance_to_travel / 2)
            x_4 = (hang_time + travel_time + hang_time, centerX + np.cos(np.radians(angle)) * distance_to_travel / 2)

            y_1 = (0, centerY - np.sin(np.radians(angle)) * distance_to_travel / 2)
            y_2 = (hang_time, centerY - np.sin(np.radians(angle)) * distance_to_travel / 2)
            y_3 = (hang_time + travel_time, centerY + np.sin(np.radians(angle)) * distance_to_travel / 2)
            y_4 = (hang_time + travel_time + hang_time, centerY + np.sin(np.radians(angle)) * distance_to_travel / 2)

            x = [x_1, x_2, x_3, x_4]
            y = [y_1, y_2, y_3, y_4]

        x_trajectory = {'name': 'tv_pairs',
                        'tv_pairs': x,
                        'kind': 'linear'}
        y_trajectory = {'name': 'tv_pairs',
                        'tv_pairs': y,
                        'kind': 'linear'}

        patch_parameters = {'name': 'MovingPatch',
                            'width': width,
                            'height': height,
                            'color': color,
                            'theta': x_trajectory,
                            'phi': y_trajectory,
                            'angle': angle}
        return patch_parameters

    def getExpandingPatchParameters(self, center=None, angle=None, speed=None, width=None, height=None, color=None):
        if center is None: center = self.adjustCenter(self.protocol_parameters['center'])
        if angle is None: angle = self.protocol_parameters['angle']
        if speed is None: speed = self.protocol_parameters['speed']
        if width is None: width = self.protocol_parameters['width']
        if height is None: height = self.protocol_parameters['height']
        if color is None: color = self.protocol_parameters['color']

        centerX = center[0]
        centerY = center[1]
        stim_time = self.run_parameters['stim_time']
        x = []
        y = []
        for tv_pair in height['tv_pairs']:
            x_tv = (tv_pair[0], centerX + np.cos(np.radians(angle+90)) * tv_pair[1] / 2)
            y_tv = (tv_pair[0], centerY + np.sin(np.radians(angle+90)) * tv_pair[1] / 2)
            x.append(x_tv)
            y.append(y_tv)

        x_trajectory = {'name': 'tv_pairs',
                        'tv_pairs': x,
                        'kind': 'linear'}
        y_trajectory = {'name': 'tv_pairs',
                        'tv_pairs': y,
                        'kind': 'linear'}

        patch_parameters = {'name': 'MovingPatch',
                            'width': width,
                            'height': height,
                            'color': color,
                            'theta': x_trajectory,
                            'phi': y_trajectory,
                            'angle': angle}
        return patch_parameters

    def getMovingSpotParameters(self, center=None, angle=None, speed=None, radius=None, color=None,
                                distance_to_travel=None):
        if center is None: center = self.adjustCenter(self.protocol_parameters['center'])
        if angle is None: angle = self.protocol_parameters['angle']
        if speed is None: speed = self.protocol_parameters['speed']
        if radius is None: radius = self.protocol_parameters['radius']
        if color is None: color = self.protocol_parameters['color']

        centerX = center[0]
        centerY = center[1]
        stim_time = self.run_parameters['stim_time']
        if distance_to_travel is None:  # distance_to_travel is set by speed and stim_time
            distance_to_travel = speed * stim_time
            # trajectory just has two points, at time=0 and time=stim_time
            startX = (0, centerX - np.cos(np.radians(angle)) * distance_to_travel / 2)
            endX = (stim_time, centerX + np.cos(np.radians(angle)) * distance_to_travel / 2)
            startY = (0, centerY - np.sin(np.radians(angle)) * distance_to_travel / 2)
            endY = (stim_time, centerY + np.sin(np.radians(angle)) * distance_to_travel / 2)
            x = [startX, endX]
            y = [startY, endY]

        else:  # distance_to_travel is specified, so only go that distance at the defined speed. Hang pre- and post- for any extra stim time
            travel_time = distance_to_travel / speed
            if travel_time > stim_time:
                print('Warning: stim_time is too short to show whole trajectory at this speed!')
                hang_time = 0
            else:
                hang_time = (stim_time - travel_time) / 2

            # split up hang time in pre and post such that trajectory always hits centerX,centerY at stim_time/2
            x_1 = (0, centerX - np.cos(np.radians(angle)) * distance_to_travel / 2)
            x_2 = (hang_time, centerX - np.cos(np.radians(angle)) * distance_to_travel / 2)
            x_3 = (hang_time + travel_time, centerX + np.cos(np.radians(angle)) * distance_to_travel / 2)
            x_4 = (hang_time + travel_time + hang_time, centerX + np.cos(np.radians(angle)) * distance_to_travel / 2)

            y_1 = (0, centerY - np.sin(np.radians(angle)) * distance_to_travel / 2)
            y_2 = (hang_time, centerY - np.sin(np.radians(angle)) * distance_to_travel / 2)
            y_3 = (hang_time + travel_time, centerY + np.sin(np.radians(angle)) * distance_to_travel / 2)
            y_4 = (hang_time + travel_time + hang_time, centerY + np.sin(np.radians(angle)) * distance_to_travel / 2)

            x = [x_1, x_2, x_3, x_4]
            y = [y_1, y_2, y_3, y_4]

        x_trajectory = {'name': 'tv_pairs',
                        'tv_pairs': x,
                        'kind': 'linear'}
        y_trajectory = {'name': 'tv_pairs',
                        'tv_pairs': y,
                        'kind': 'linear'}

        spot_parameters = {'name': 'MovingSpot',
                           'radius': radius,
                           'color': color,
                           'theta': x_trajectory,
                           'phi': y_trajectory}
        return spot_parameters

    def getMovingRingParameters(self, center=None, angle=None, speed=None, inner_radius=None, thickness=None,
                                color=None, distance_to_travel=None):
        if center is None: center = self.adjustCenter(self.protocol_parameters['center'])
        if angle is None: angle = self.protocol_parameters['angle']
        if speed is None: speed = self.protocol_parameters['speed']
        if inner_radius is None: inner_radius = self.protocol_parameters['inner_radius']
        if thickness is None: thickness = self.protocol_parameters['thickness']
        if color is None: color = self.protocol_parameters['color']

        centerX = center[0]
        centerY = center[1]
        stim_time = self.run_parameters['stim_time']
        if distance_to_travel is None:  # distance_to_travel is set by speed and stim_time
            distance_to_travel = speed * stim_time
            # trajectory just has two points, at time=0 and time=stim_time
            startX = (0, centerX - np.cos(np.radians(angle)) * distance_to_travel / 2)
            endX = (stim_time, centerX + np.cos(np.radians(angle)) * distance_to_travel / 2)
            startY = (0, centerY - np.sin(np.radians(angle)) * distance_to_travel / 2)
            endY = (stim_time, centerY + np.sin(np.radians(angle)) * distance_to_travel / 2)
            x = [startX, endX]
            y = [startY, endY]

        else:  # distance_to_travel is specified, so only go that distance at the defined speed. Hang pre- and post- for any extra stim time
            travel_time = distance_to_travel / speed
            if travel_time > stim_time:
                print('Warning: stim_time is too short to show whole trajectory at this speed!')
                hang_time = 0
            else:
                hang_time = (stim_time - travel_time) / 2

            # split up hang time in pre and post such that trajectory always hits centerX,centerY at stim_time/2
            x_1 = (0, centerX - np.cos(np.radians(angle)) * distance_to_travel / 2)
            x_2 = (hang_time, centerX - np.cos(np.radians(angle)) * distance_to_travel / 2)
            x_3 = (hang_time + travel_time, centerX + np.cos(np.radians(angle)) * distance_to_travel / 2)
            x_4 = (hang_time + travel_time + hang_time, centerX + np.cos(np.radians(angle)) * distance_to_travel / 2)

            y_1 = (0, centerY - np.sin(np.radians(angle)) * distance_to_travel / 2)
            y_2 = (hang_time, centerY - np.sin(np.radians(angle)) * distance_to_travel / 2)
            y_3 = (hang_time + travel_time, centerY + np.sin(np.radians(angle)) * distance_to_travel / 2)
            y_4 = (hang_time + travel_time + hang_time, centerY + np.sin(np.radians(angle)) * distance_to_travel / 2)

            x = [x_1, x_2, x_3, x_4]
            y = [y_1, y_2, y_3, y_4]

        x_trajectory = {'name': 'tv_pairs',
                        'tv_pairs': x,
                        'kind': 'linear'}
        y_trajectory = {'name': 'tv_pairs',
                        'tv_pairs': y,
                        'kind': 'linear'}

        ring_parameters = {'name': 'MovingRing',
                           'inner_radius': inner_radius,
                           'thickness': thickness,
                           'color': color,
                           'theta': x_trajectory,
                           'phi': y_trajectory}
        return ring_parameters


class LoomingSpot(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

        self.getRunParameterDefaults()
        self.getParameterDefaults()

    def getEpochParameters(self):
        stim_time = self.run_parameters['stim_time']
        start_size = self.protocol_parameters['start_size']
        end_size = self.protocol_parameters['end_size']

        # adjust center to screen center
        adj_center = self.adjustCenter(self.protocol_parameters['center'])

        rv_ratio = self.protocol_parameters['rv_ratio']  # msec
        current_rv_ratio = self.selectParametersFromLists(rv_ratio,
                                                          randomize_order=self.protocol_parameters['randomize_order'])

        current_rv_ratio = current_rv_ratio / 1e3  # msec -> sec
        r_traj = {'name': 'Loom',
                  'rv_ratio': current_rv_ratio,
                  'stim_time': stim_time,
                  'start_size': start_size,
                  'end_size': end_size}

        if current_rv_ratio > 0:
            current_radius = start_size / 2
        else:
            current_radius = end_size / 2
        self.pre_epoch_parameters = {'name': 'MovingSpot',
                                     'radius': current_radius,
                                     'sphere_radius': 1,
                                     'color': self.protocol_parameters['intensity'],
                                     'theta': adj_center[0],
                                     'phi': adj_center[1]}

        self.epoch_parameters = {'name': 'MovingSpot',
                                 'radius': r_traj,
                                 'sphere_radius': 1,
                                 'color': self.protocol_parameters['intensity'],
                                 'theta': adj_center[0],
                                 'phi': adj_center[1]}

        self.convenience_parameters = {'current_rv_ratio': current_rv_ratio}

    def getParameterDefaults(self):
        self.protocol_parameters = {'intensity': 0.0,
                                    'center': [0, 0],
                                    'start_size': 2.5,
                                    'end_size': 80.0,
                                    'rv_ratio': [5.0, 10.0, 20.0, 40.0, 80.0],
                                    'randomize_order': True}

    def getRunParameterDefaults(self):
        self.run_parameters = {'protocol_ID': 'LoomingSpot',
                               'num_epochs': 75,
                               'pre_time': 0.5,
                               'stim_time': 1.0,
                               'tail_time': 1.0,
                               'idle_color': 0.5}

    def loadStimuli(self, client):
        # bypassing the load stim here because I loaded it in startStimuli
        pass

    def startStimuli(self, client, append_stim_frames=False, print_profile=True):
        # pre time
        bg = self.run_parameters.get('idle_color')
        multicall = flyrpc.multicall.MyMultiCall(client.manager)
        multicall.load_stim('ConstantBackground', color=[bg, bg, bg, 1.0])
        passedParameters = self.pre_epoch_parameters.copy()
        multicall.load_stim(**passedParameters, hold=True)
        multicall()
        multicall.start_stim(append_stim_frames=append_stim_frames)
        multicall()
        sleep(self.run_parameters['pre_time'])

        # stim time
        bg = self.run_parameters.get('idle_color')
        multicall = flyrpc.multicall.MyMultiCall(client.manager)
        multicall.load_stim('ConstantBackground', color=[bg, bg, bg, 1.0])
        passedParameters = self.epoch_parameters.copy()
        multicall.load_stim(**passedParameters, hold=True)
        multicall()
        multicall = flyrpc.multicall.MyMultiCall(client.manager)
        multicall.start_stim(append_stim_frames=append_stim_frames)
        multicall.start_corner_square()
        multicall()
        sleep(self.run_parameters['stim_time'])

        # tail time
        multicall = flyrpc.multicall.MyMultiCall(client.manager)
        multicall.stop_stim(print_profile=print_profile)
        multicall.black_corner_square()
        multicall()

        sleep(self.run_parameters['tail_time'])


class LinearLoom(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

        self.getRunParameterDefaults()
        self.getParameterDefaults()

    def getEpochParameters(self):
        stim_time = self.run_parameters['stim_time']
        start_size = self.protocol_parameters['start_size']
        end_size = self.protocol_parameters['end_size']

        # adjust center to screen center
        adj_center = self.adjustCenter(self.protocol_parameters['center'])

        loom_speed = self.protocol_parameters['loom_speed']  # deg/sec
        current_loom_speed = self.selectParametersFromLists(loom_speed,
                                                            randomize_order=self.protocol_parameters['randomize_order'])
        startR = (0, start_size / 2)
        final_r = start_size / 2 + stim_time * current_loom_speed / 2
        if final_r < end_size / 2:
            endR = (stim_time, final_r)
            r = [startR, endR]
        else:
            stop_time = (end_size - start_size) / current_loom_speed
            middleR = (stop_time, end_size / 2)
            endR = (stim_time, end_size / 2)
            r = [startR, middleR, endR]

        r_traj = {'name': 'tv_pairs',
                  'tv_pairs': r,
                  'kind': 'linear'}

        self.epoch_parameters = {'name': 'MovingSpot',
                                 'radius': r_traj,
                                 'sphere_radius': 1,
                                 'color': self.protocol_parameters['intensity'],
                                 'theta': adj_center[0],
                                 'phi': adj_center[1]}

        self.convenience_parameters = {'current_rv_ratio': current_loom_speed}

    def getParameterDefaults(self):
        self.protocol_parameters = {'intensity': 0.0,
                                    'center': [0, 0],
                                    'start_size': 2.5,
                                    'end_size': 80.0,
                                    'loom_speed': [50.0, 100.0, 200.0],
                                    'randomize_order': True}

    def getRunParameterDefaults(self):
        self.run_parameters = {'protocol_ID': 'LinearLoom',
                               'num_epochs': 75,
                               'pre_time': 0.5,
                               'stim_time': 1.0,
                               'tail_time': 1.0,
                               'idle_color': 0.5}


class GridLoomingSpot(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

        self.getRunParameterDefaults()
        self.getParameterDefaults()

    def getEpochParameters(self):
        stim_time = self.run_parameters['stim_time']
        start_size = self.protocol_parameters['start_size']
        end_size = self.protocol_parameters['end_size']

        # adjust center to screen center
        theta = self.protocol_parameters['theta']
        phi = self.protocol_parameters['phi']
        current_center = self.selectParametersFromLists((theta, phi), all_combinations=True,
                                                        randomize_order=self.protocol_parameters['randomize_order'])
        adj_center = self.adjustCenter(current_center)

        rv_ratio = self.protocol_parameters['rv_ratio'] / 1e3  # msec -> sec

        r_traj = {'name': 'Loom',
                  'rv_ratio': rv_ratio,
                  'stim_time': stim_time,
                  'start_size': start_size,
                  'end_size': end_size}

        self.epoch_parameters = {'name': 'MovingSpot',
                                 'radius': r_traj,
                                 'sphere_radius': 1,
                                 'color': self.protocol_parameters['intensity'],
                                 'theta': adj_center[0],
                                 'phi': adj_center[1]}

        self.convenience_parameters = {'current_theta': current_center[0],
                                       'current_phi': current_center[1]}

    def getParameterDefaults(self):
        self.protocol_parameters = {'intensity': 0.0,
                                    'theta': [0.0],
                                    'phi': [0.0],
                                    'start_size': 2.5,
                                    'end_size': 80.0,
                                    'rv_ratio': 25,
                                    'randomize_order': True}

    def getRunParameterDefaults(self):
        self.run_parameters = {'protocol_ID': 'GridLoomingSpot',
                               'num_epochs': 75,
                               'pre_time': 0.5,
                               'stim_time': 1.0,
                               'tail_time': 1.0,
                               'idle_color': 0.5}


class LoomingSpotContrast(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

        self.getRunParameterDefaults()
        self.getParameterDefaults()

    def getEpochParameters(self):
        stim_time = self.run_parameters['stim_time']
        start_size = self.protocol_parameters['start_size']
        end_size = self.protocol_parameters['end_size']

        # adjust center to screen center
        adj_center = self.adjustCenter(self.protocol_parameters['center'])

        rv_ratio = self.protocol_parameters['rv_ratio']  # msec
        intensity = self.protocol_parameters['intensity']
        current_intensity = self.selectParametersFromLists(intensity,
                                                           randomize_order=self.protocol_parameters['randomize_order'])

        rv_ratio = rv_ratio / 1e3  # msec -> sec
        r_traj = {'name': 'Loom',
                  'rv_ratio': rv_ratio,
                  'stim_time': stim_time,
                  'start_size': start_size,
                  'end_size': end_size}

        self.epoch_parameters = {'name': 'MovingSpot',
                                 'radius': r_traj,
                                 'sphere_radius': 1,
                                 'color': current_intensity,
                                 'theta': adj_center[0],
                                 'phi': adj_center[1]}

        self.convenience_parameters = {'current_intensity': current_intensity}

    def getParameterDefaults(self):
        self.protocol_parameters = {'intensity': [0.0, 0.1],
                                    'center': [0, 0],
                                    'start_size': 2.5,
                                    'end_size': 80.0,
                                    'rv_ratio': 40.0,
                                    'randomize_order': True}

    def getRunParameterDefaults(self):
        self.run_parameters = {'protocol_ID': 'LoomingSpotContrast',
                               'num_epochs': 75,
                               'pre_time': 0.5,
                               'stim_time': 1.0,
                               'tail_time': 1.0,
                               'idle_color': 0.5}


class ExpandingRing(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)
        self.getRunParameterDefaults()
        self.getParameterDefaults()

    def getEpochParameters(self):
        stim_time = self.run_parameters['stim_time']
        start_size = self.protocol_parameters['start_size']
        end_size = self.protocol_parameters['end_size']

        # adjust center to screen center
        adj_center = self.adjustCenter(self.protocol_parameters['center'])

        loom_speed = self.protocol_parameters['loom_speed']  # deg/sec
        current_loom_speed = self.selectParametersFromLists(loom_speed,
                                                            randomize_order=self.protocol_parameters['randomize_order'])
        startR = (0, start_size / 2)
        final_r = start_size / 2 + stim_time * current_loom_speed / 2
        if final_r < end_size / 2:
            endR = (stim_time, final_r)
            r = [startR, endR]
        else:
            stop_time = np.abs(start_size - end_size) / current_loom_speed
            middleR = (stop_time, end_size / 2)
            endR = (stim_time, end_size / 2)
            r = [startR, middleR, endR]

        r_traj = {'name': 'tv_pairs',
                  'tv_pairs': r,
                  'kind': 'linear'}

        self.epoch_parameters = self.getMovingRingParameters(color=self.protocol_parameters['intensity'],
                                                             inner_radius=r_traj,
                                                             thickness=self.protocol_parameters['thickness'],
                                                             center=adj_center,
                                                             speed=0,
                                                             angle=0)

        self.convenience_parameters = {'current_rv_ratio': current_loom_speed}

    def getParameterDefaults(self):
        self.protocol_parameters = {'intensity': 0.0,
                                    'center': [0, 0],
                                    'start_size': 0,
                                    'end_size': 50,
                                    'thickness': 10,
                                    'loom_speed': [50.0, 100.0],
                                    'randomize_order': True}

    def getRunParameterDefaults(self):
        self.run_parameters = {'protocol_ID': 'LinearExpandRing',
                               'num_epochs': 75,
                               'pre_time': 0.5,
                               'stim_time': 1.0,
                               'tail_time': 1.0,
                               'idle_color': 0.5}


class ClosingRing(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)
        self.getRunParameterDefaults()
        self.getParameterDefaults()

    def getEpochParameters(self):
        stim_time = self.run_parameters['stim_time']
        start_size = self.protocol_parameters['start_size']
        end_size = self.protocol_parameters['end_size']

        # adjust center to screen center
        adj_center = self.adjustCenter(self.protocol_parameters['center'])

        loom_speed = self.protocol_parameters['loom_speed']  # deg/sec
        current_loom_speed = self.selectParametersFromLists(loom_speed,
                                                            randomize_order=self.protocol_parameters['randomize_order'])
        startR = (0, start_size / 2)
        final_r = start_size / 2 + stim_time * current_loom_speed / 2
        if final_r < end_size / 2:
            endR = (stim_time, final_r)
            r = [startR, endR]
        else:
            stop_time = np.abs(start_size - end_size) / current_loom_speed
            middleR = (stop_time, end_size / 2)
            endR = (stim_time, end_size / 2)
            r = [startR, middleR, endR]
        thickness = [(tv[0], start_size / 2 - tv[1]) for tv in r]
        inner_r_traj = {'name': 'tv_pairs',
                        'tv_pairs': r,
                        'kind': 'linear'}
        thickness_traj = {'name': 'tv_pairs',
                          'tv_pairs': thickness,
                          'kind': 'linear'}

        self.epoch_parameters = self.getMovingRingParameters(color=self.protocol_parameters['intensity'],
                                                             inner_radius=inner_r_traj,
                                                             thickness=thickness_traj,
                                                             center=adj_center,
                                                             speed=0,
                                                             angle=0)

        self.convenience_parameters = {'current_rv_ratio': current_loom_speed}

    def getParameterDefaults(self):
        self.protocol_parameters = {'intensity': 0.0,
                                    'center': [0, 0],
                                    'start_size': 50,
                                    'end_size': 0,
                                    'loom_speed': [50.0],
                                    'randomize_order': True}

    def getRunParameterDefaults(self):
        self.run_parameters = {'protocol_ID': 'LinearCloseRing',
                               'num_epochs': 75,
                               'pre_time': 0.5,
                               'stim_time': 1.0,
                               'tail_time': 1.0,
                               'idle_color': 0.5}


class SurroundInhibition(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

        self.getRunParameterDefaults()
        self.getParameterDefaults()

    def getEpochParameters(self):
        thickness = self.protocol_parameters['thickness']
        diameter = self.protocol_parameters['rf_diameter']
        inhibit_time = self.protocol_parameters['inhibit_time']
        # current_thickness = self.selectParametersFromLists(thickness,
        #                                                    randomize_order=self.protocol_parameters['randomize_order'])
        current_paras = self.selectParametersFromLists((thickness, diameter, inhibit_time), all_combinations=True,
                                                       randomize_order=self.protocol_parameters['randomize_order'])
        current_thickness = current_paras[0]
        current_diameter = current_paras[1]
        current_inhibit_time = current_paras[2]

        # adjust center to screen center
        adj_center = self.adjustCenter(self.protocol_parameters['center'])
        bg_color = self.run_parameters.get('idle_color')
        surround_color = self.protocol_parameters['intensity']
        stim_time = self.run_parameters['stim_time']

        color_traj = {'name': 'tv_pairs',
                      'tv_pairs': [(0, bg_color), (current_inhibit_time, bg_color),
                                   (current_inhibit_time, surround_color), (stim_time, surround_color)],
                      'kind': 'linear'}
        ring_parameters = self.getMovingRingParameters(color=color_traj,
                                                       inner_radius=current_diameter / 2,
                                                       thickness=current_thickness,
                                                       center=adj_center,
                                                       speed=0,
                                                       angle=0)

        # stim_time = self.run_parameters['stim_time']
        start_size = self.protocol_parameters['start_size']
        end_size = current_diameter

        # adjust center to screen center
        adj_center = self.adjustCenter(self.protocol_parameters['center'])

        rv_ratio = self.protocol_parameters['rv_ratio']  # msec

        rv_ratio = rv_ratio / 1e3  # msec -> sec
        r_traj = {'name': 'Loom',
                  'rv_ratio': rv_ratio,
                  'stim_time': stim_time,
                  'start_size': start_size,
                  'end_size': end_size}

        spot_parameters = {'name': 'MovingSpot',
                           'radius': r_traj,
                           'sphere_radius': 1,
                           'color': self.protocol_parameters['intensity'],
                           'theta': adj_center[0],
                           'phi': adj_center[1]}

        self.epoch_parameters = (ring_parameters, spot_parameters)

        self.convenience_parameters = {'current_thickness': current_thickness,
                                       'current_diameter': current_diameter,
                                       'current_inhibit_time': current_inhibit_time}

    def loadStimuli(self, client):
        surround_spot_paras = self.epoch_parameters[0].copy()
        looming_spot_paras = self.epoch_parameters[1].copy()

        multicall = flyrpc.multicall.MyMultiCall(client.manager)
        bg = self.run_parameters.get('idle_color')
        multicall.load_stim('ConstantBackground', color=[bg, bg, bg, 1.0])
        multicall.load_stim(**surround_spot_paras, hold=True)
        multicall.load_stim(**looming_spot_paras, hold=True)

        multicall()

    def getParameterDefaults(self):
        self.protocol_parameters = {'thickness': [4.0, 8.0],
                                    'rf_diameter': [40.0],
                                    'start_size': 5,
                                    'rv_ratio': 40.0,
                                    'intensity': 0.0,
                                    'inhibit_time': [0.2],
                                    'center': [0, 0],
                                    'randomize_order': True}

    def getRunParameterDefaults(self):
        self.run_parameters = {'protocol_ID': 'SurroundInhibition',
                               'num_epochs': 40,
                               'pre_time': 0.5,
                               'stim_time': 1.0,
                               'tail_time': 1.5,
                               'idle_color': 0.5}


class SpotSeries(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

        self.getRunParameterDefaults()
        self.getParameterDefaults()

    def getEpochParameters(self):
        stim_time = self.run_parameters['stim_time']
        start_size = self.protocol_parameters['start_size']
        end_size = self.protocol_parameters['end_size']
        # adjust center to screen center
        adj_center = self.adjustCenter(self.protocol_parameters['center'])
        rv_ratio = self.protocol_parameters['rv_ratio']  # msec
        rv_ratio = rv_ratio / 1e3  # msec -> sec
        t_points = self.protocol_parameters['time_points']
        loom_func = partial(get_loom_size, rv_ratio, start_size, end_size)
        t_points2 = t_points.copy()
        t_points2.pop(0)
        t_points2.append(stim_time)
        tr_pairs = []
        for t, t2 in zip(t_points, t_points2):
            tr_pairs.append((t, loom_func(t)))
            tr_pairs.append((t2, loom_func(t)))
        r_traj = {'name': 'tv_pairs',
                  'tv_pairs': tr_pairs,
                  'kind': 'linear'}

        self.epoch_parameters = {'name': 'MovingSpot',
                                 'radius': r_traj,
                                 'sphere_radius': 1,
                                 'color': self.protocol_parameters['intensity'],
                                 'theta': adj_center[0],
                                 'phi': adj_center[1]}

    def getParameterDefaults(self):
        self.protocol_parameters = {'intensity': 0.0,
                                    'center': [0, 0],
                                    'start_size': 2.5,
                                    'end_size': 80.0,
                                    'rv_ratio': 40.0,
                                    'time_points': [0.0, 0.1, 0.2, 0.5],
                                    'randomize_order': True}

    def getRunParameterDefaults(self):
        self.run_parameters = {'protocol_ID': 'SpotSeries',
                               'num_epochs': 75,
                               'pre_time': 0.5,
                               'stim_time': 1.0,
                               'tail_time': 1.0,
                               'idle_color': 0.5}


class DiskFlash(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

        self.getRunParameterDefaults()
        self.getParameterDefaults()

    def getEpochParameters(self):
        stim_time = self.run_parameters['stim_time']
        disk_size = self.protocol_parameters['size']
        # adjust center to screen center
        adj_center = self.adjustCenter(self.protocol_parameters['center'])
        disk_color = self.protocol_parameters['intensity']
        bg_color = self.run_parameters['idle_color']
        color_tv_pairs = []
        time_points = self.protocol_parameters['time_points']
        pulse_duration = self.protocol_parameters['pulse_duration']
        time_points2 = time_points.copy()
        time_points2.pop(0)
        time_points2.append(stim_time)
        for t, t2 in zip(time_points, time_points2):
            color_tv_pairs.append((t, disk_color))
            color_tv_pairs.append((t + pulse_duration, disk_color))
            color_tv_pairs.append((t + pulse_duration, bg_color))
            color_tv_pairs.append((t2, bg_color))

        color_traj = {'name': 'tv_pairs',
                      'tv_pairs': color_tv_pairs,
                      'kind': 'linear'}
        self.epoch_parameters = {'name': 'MovingSpot',
                                 'radius': disk_size,
                                 'sphere_radius': 1,
                                 'color': color_traj,
                                 'theta': adj_center[0],
                                 'phi': adj_center[1]}

    def getParameterDefaults(self):
        self.protocol_parameters = {'intensity': 0.0,
                                    'center': [0, 0],
                                    'size': 20,
                                    'time_points': [0.0, 0.1, 0.2, 0.5],
                                    'pulse_duration': 0.01,
                                    'randomize_order': False}

    def getRunParameterDefaults(self):
        self.run_parameters = {'protocol_ID': 'DiskFlash',
                               'num_epochs': 75,
                               'pre_time': 0.5,
                               'stim_time': 1.0,
                               'tail_time': 1.0,
                               'idle_color': 0.5}


class StillSpots(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

        self.getRunParameterDefaults()
        self.getParameterDefaults()

    def getEpochParameters(self):
        stim_time = self.run_parameters['stim_time']
        # adjust center to screen center
        adj_center = self.adjustCenter(self.protocol_parameters['center'])
        radius = self.protocol_parameters['radius']
        current_radius = self.selectParametersFromLists(radius,
                                                        randomize_order=self.protocol_parameters['randomize_order'])

        self.epoch_parameters = {'name': 'MovingSpot',
                                 'radius': current_radius,
                                 'sphere_radius': 1,
                                 'color': self.protocol_parameters['intensity'],
                                 'theta': adj_center[0],
                                 'phi': adj_center[1]}

        self.convenience_parameters = {'current_radius': current_radius}

    def getParameterDefaults(self):
        self.protocol_parameters = {'intensity': 0.0,
                                    'center': [0, 0],
                                    'radius': [5, 10, 15],
                                    'randomize_order': True}

    def getRunParameterDefaults(self):
        self.run_parameters = {'protocol_ID': 'StillSpots',
                               'num_epochs': 75,
                               'pre_time': 0.5,
                               'stim_time': 1.0,
                               'tail_time': 1.0,
                               'idle_color': 0.5}


class StillRings(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

        self.getRunParameterDefaults()
        self.getParameterDefaults()

    def getEpochParameters(self):
        stim_time = self.run_parameters['stim_time']
        # adjust center to screen center
        adj_center = self.adjustCenter(self.protocol_parameters['center'])
        radius = self.protocol_parameters['radius']
        current_radius = self.selectParametersFromLists(radius,
                                                        randomize_order=self.protocol_parameters['randomize_order'])

        self.epoch_parameters = {'name': 'MovingRing',
                                 'inner_radius': current_radius,
                                 'thickness': self.protocol_parameters['thickness'],
                                 'color': self.protocol_parameters['intensity'],
                                 'theta': adj_center[0],
                                 'phi': adj_center[1]}

        self.convenience_parameters = {'current_radius': current_radius}

    def getParameterDefaults(self):
        self.protocol_parameters = {'intensity': 0.0,
                                    'center': [0, 0],
                                    'radius': [5, 10, 15],
                                    'thickness': 5,
                                    'randomize_order': True}

    def getRunParameterDefaults(self):
        self.run_parameters = {'protocol_ID': 'StillRings',
                               'num_epochs': 75,
                               'pre_time': 0.5,
                               'stim_time': 1.0,
                               'tail_time': 1.0,
                               'idle_color': 0.5}


class OffcenterGrid(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

        self.getRunParameterDefaults()
        self.getParameterDefaults()

    def getEpochParameters(self):
        stim_time = self.run_parameters['stim_time']
        theta = self.protocol_parameters['theta']
        phi = self.protocol_parameters['phi']
        current_offset = self.selectParametersFromLists((theta, phi), all_combinations=True,
                                                        randomize_order=self.protocol_parameters['randomize_order'])
        RFcenter = self.protocol_parameters['center']
        current_center = RFcenter.copy()
        current_center[0] = RFcenter[0] + current_offset[0]
        current_center[1] = RFcenter[1] + current_offset[1]
        # adjust center to screen center
        adj_center = self.adjustCenter(current_center)
        radius = self.protocol_parameters['radius']
        self.epoch_parameters = {'name': 'MovingSpot',
                                 'radius': radius,
                                 'sphere_radius': 1,
                                 'color': self.protocol_parameters['intensity'],
                                 'theta': adj_center[0],
                                 'phi': adj_center[1]}

        self.convenience_parameters = {'current_theta': current_offset[0],
                                      'current_phi': current_offset[1]}

    def getParameterDefaults(self):
        self.protocol_parameters = {'intensity': 0.0,
                                    'center': [0, 0],
                                    'radius': 5,
                                    'theta': [-20, -15, -10, -5, 0, 5, 10, 15, 20],
                                    'phi': [-20, -15, -10, -5, 0, 5, 10, 15, 20],
                                    'randomize_order': True}

    def getRunParameterDefaults(self):
        self.run_parameters = {'protocol_ID': 'OffcenterGrid',
                               'num_epochs': 81,
                               'pre_time': 0.5,
                               'stim_time': 0.2,
                               'tail_time': 0.5,
                               'idle_color': 0.5}


class TwoSpotGrid(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

        self.getRunParameterDefaults()
        self.getParameterDefaults()

    def getEpochParameters(self):
        theta = self.protocol_parameters['theta']
        phi = self.protocol_parameters['phi']
        current_offset = self.selectParametersFromLists((theta, phi), all_combinations=True,
                                                        randomize_order=self.protocol_parameters['randomize_order'])
        RFcenter = self.protocol_parameters['center']
        first_spot_offset = self.protocol_parameters['offset']
        first_spot_center = RFcenter.copy()
        first_spot_center[0] = RFcenter[0] + first_spot_offset[0]
        first_spot_center[1] = RFcenter[1] + first_spot_offset[1]
        current_center = RFcenter.copy()
        current_center[0] = RFcenter[0] + current_offset[0]
        current_center[1] = RFcenter[1] + current_offset[1]
        # adjust center to screen center
        adj_center = self.adjustCenter(current_center)
        adj_first_center = self.adjustCenter(first_spot_center)
        radius = self.protocol_parameters['radius']
        self.first_epoch_parameters = {'name': 'MovingSpot',
                                     'radius': radius,
                                     'sphere_radius': 1,
                                     'color': self.protocol_parameters['intensity'],
                                     'theta': adj_first_center[0],
                                     'phi': adj_first_center[1]}

        self.epoch_parameters = {'name': 'MovingSpot',
                                 'radius': radius,
                                 'sphere_radius': 1,
                                 'color': self.protocol_parameters['intensity'],
                                 'theta': adj_center[0],
                                 'phi': adj_center[1]}

        self.convenience_parameters = {'current_theta': current_offset[0],
                                      'current_phi': current_offset[1]}

    def getParameterDefaults(self):
        self.protocol_parameters = {'intensity': 0.0,
                                    'center': [0, 0],
                                    'offset': [0, 0],  # offset of the first spot to RF center
                                    'first_spot_time': 0.1,  # in second
                                    'radius': 5,
                                    'theta': [-20, -15, -10, -5, 0, 5, 10, 15, 20],
                                    'phi': [-20, -15, -10, -5, 0, 5, 10, 15, 20],
                                    'randomize_order': True}

    def getRunParameterDefaults(self):
        self.run_parameters = {'protocol_ID': 'TwoSpotGrid',
                               'num_epochs': 81,
                               'pre_time': 0.2,
                               'stim_time': 0.2,
                               'tail_time': 0.8,
                               'idle_color': 0.5}

    def loadStimuli(self, client):
        # bypassing the load stim here because I loaded it in startStimuli
        pass

    def startStimuli(self, client, append_stim_frames=False, print_profile=True):
        sleep(self.run_parameters['pre_time'])

        first_spot_time = self.protocol_parameters['first_spot_time']
        two_spot_time = self.run_parameters['stim_time'] - first_spot_time
        bg = self.run_parameters.get('idle_color')
        multicall = flyrpc.multicall.MyMultiCall(client.manager)
        multicall.load_stim('ConstantBackground', color=[bg, bg, bg, 1.0])
        passedParameters = self.first_epoch_parameters.copy()
        multicall.load_stim(**passedParameters, hold=True)
        multicall()
        multicall.start_stim(append_stim_frames=append_stim_frames)
        multicall.start_corner_square()
        multicall()
        sleep(first_spot_time)
        # stim time
        multicall = flyrpc.multicall.MyMultiCall(client.manager)
        multicall.load_stim('ConstantBackground', color=[bg, bg, bg, 1.0])
        passedParameters0 = self.first_epoch_parameters.copy()
        passedParameters = self.epoch_parameters.copy()
        multicall.load_stim(**passedParameters0, hold=True)
        multicall.load_stim(**passedParameters, hold=True)
        multicall()
        multicall = flyrpc.multicall.MyMultiCall(client.manager)
        multicall.start_stim(append_stim_frames=append_stim_frames)
        multicall()
        sleep(two_spot_time)

        # tail time
        multicall = flyrpc.multicall.MyMultiCall(client.manager)
        multicall.stop_stim(print_profile=print_profile)
        multicall.black_corner_square()
        multicall()

        sleep(self.run_parameters['tail_time'])


class ExpandingRectangle(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

        self.getRunParameterDefaults()
        self.getParameterDefaults()

    def getEpochParameters(self):
        angle = self.protocol_parameters['angle']
        current_angle = self.selectParametersFromLists(angle, randomize_order=self.protocol_parameters['randomize_order'])
        stim_time = self.run_parameters['stim_time']
        start_size = 0.0
        end_size = self.protocol_parameters['end_size']
        # adjust center to screen center
        adj_center = self.adjustCenter(self.protocol_parameters['center'])

        speed = self.protocol_parameters['speed']  # deg/sec
        startR = (0, start_size)
        final_r = start_size + stim_time * speed
        if final_r < end_size:
            endR = (stim_time, final_r)
            r = [startR, endR]
        else:
            stop_time = np.abs(start_size - end_size) / speed
            middleR = (stop_time, end_size)
            endR = (stim_time, end_size)
            r = [startR, middleR, endR]

        h_traj = {'name': 'tv_pairs',
                  'tv_pairs': r,
                  'kind': 'linear'}
        self.epoch_parameters = self.getExpandingPatchParameters(center=adj_center,
                                                                 angle=current_angle,
                                                                 height=h_traj,
                                                                 speed=0,
                                                                 color=self.protocol_parameters['intensity'])

        self.convenience_parameters = {'current_angle': current_angle}

    def getParameterDefaults(self):
        self.protocol_parameters = {'width': 5.0,
                                    'end_size': 20.0,
                                    'intensity': 0.0,
                                    'center': [0, 0],
                                    'speed': 100.0,
                                    'angle': [0.0, 90.0],
                                    'randomize_order': True}

    def getRunParameterDefaults(self):
        self.run_parameters = {'protocol_ID': 'ExpandingRectangle',
                               'num_epochs': 40,
                               'pre_time': 0.5,
                               'stim_time': 0.3,
                               'tail_time': 1.0,
                               'idle_color': 0.5}
        

class TwoEpandingBar(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

        self.getRunParameterDefaults()
        self.getParameterDefaults()

    def getEpochParameters(self):
        angle = self.protocol_parameters['angle']
        angle_offset = self.protocol_parameters['angle_offset']
        current_angle, current_offset = self.selectParametersFromLists((angle, angle_offset),
                                                                       randomize_order=self.protocol_parameters['randomize_order'])
        stim_time = self.run_parameters['stim_time']
        start_size = 0.0
        end_size = self.protocol_parameters['end_size']
        # adjust center to screen center
        adj_center = self.adjustCenter(self.protocol_parameters['center'])

        speed = self.protocol_parameters['speed']  # deg/sec
        startR = (0, start_size)
        final_r = start_size + stim_time * speed
        if final_r < end_size:
            endR = (stim_time, final_r)
            r = [startR, endR]
        else:
            stop_time = np.abs(start_size - end_size) / speed
            middleR = (stop_time, end_size)
            endR = (stim_time, end_size)
            r = [startR, middleR, endR]

        h_traj = {'name': 'tv_pairs',
                  'tv_pairs': r,
                  'kind': 'linear'}
        self.first_bar_parameters = self.getExpandingPatchParameters(center=adj_center,
                                                                     angle=current_angle + current_offset,
                                                                     height=h_traj,
                                                                     speed=0,
                                                                     color=self.protocol_parameters['intensity'])
        
        self.epoch_parameters = self.getExpandingPatchParameters(center=adj_center,
                                                                 angle=current_angle,
                                                                 height=h_traj,
                                                                 speed=0,
                                                                 color=self.protocol_parameters['intensity'])

        self.convenience_parameters = {'current_angle': current_angle, 'current_offset': current_offset}

    def getParameterDefaults(self):
        self.protocol_parameters = {'width': 5.0,
                                    'end_size': 20.0,
                                    'intensity': 0.0,
                                    'center': [0, 0],
                                    'speed': 100.0,
                                    'angle': [0.0, 90.0],
                                    'angle_offset': [90.0],
                                    'randomize_order': True}

    def getRunParameterDefaults(self):
        self.run_parameters = {'protocol_ID': 'TwoExpandingBar',
                               'num_epochs': 40,
                               'pre_time': 0.5,
                               'stim_time': 0.3,
                               'tail_time': 1.0,
                               'idle_color': 0.5}

    def loadStimuli(self, client):
        # bypassing the load stim here because I loaded it in startStimuli
        pass

    def startStimuli(self, client, append_stim_frames=False, print_profile=True):
        sleep(self.run_parameters['pre_time'])

        bg = self.run_parameters.get('idle_color')
        multicall = flyrpc.multicall.MyMultiCall(client.manager)
        multicall.load_stim('ConstantBackground', color=[bg, bg, bg, 1.0])
        passedParameters0 = self.first_bar_parameters.copy()
        passedParameters = self.epoch_parameters.copy()
        multicall.load_stim(**passedParameters0, hold=True)
        multicall.load_stim(**passedParameters, hold=True)
        multicall()
        multicall.start_stim(append_stim_frames=append_stim_frames)
        multicall.start_corner_square()
        multicall()
        sleep(self.run_parameters['stim_time'])

        # tail time
        multicall = flyrpc.multicall.MyMultiCall(client.manager)
        multicall.stop_stim(print_profile=print_profile)
        multicall.black_corner_square()
        multicall()

        sleep(self.run_parameters['tail_time'])

class MovingRectangle(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

        self.getRunParameterDefaults()
        self.getParameterDefaults()

    def getEpochParameters(self):
        current_intensity, current_angle = self.selectParametersFromLists(
            (self.protocol_parameters['intensity'], self.protocol_parameters['angle']),
            randomize_order=self.protocol_parameters['randomize_order'])

        self.epoch_parameters = self.getMovingPatchParameters(angle=current_angle, color=current_intensity)

        self.convenience_parameters = {'current_angle': current_angle,
                                       'current_intensity': current_intensity}

    def getParameterDefaults(self):
        self.protocol_parameters = {'width': 5.0,
                                    'height': 50.0,
                                    'intensity': [0.0, 1.0],
                                    'center': [0, 0],
                                    'speed': 80.0,
                                    'angle': [0.0, 180.0],
                                    'randomize_order': True}

    def getRunParameterDefaults(self):
        self.run_parameters = {'protocol_ID': 'MovingRectangle',
                               'num_epochs': 40,
                               'pre_time': 0.5,
                               'stim_time': 3.0,
                               'tail_time': 1.0,
                               'idle_color': 0.5}


class GridRectangle(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

        self.getRunParameterDefaults()
        self.getParameterDefaults()

    def getEpochParameters(self):
        theta = self.protocol_parameters['theta']
        phi = self.protocol_parameters['phi']
        mean_theta = np.mean(theta).item()
        mean_phi = np.mean(phi).item()
        # add zero to the end of theta, and start of phi, so that the grid starts at the center
        augmented_theta = theta + [mean_theta] * len(phi)
        augmented_phi = [mean_phi] * len(theta) + phi
        # make augmented_angle to determine the angle of the bar
        augmented_angle = [0.0] * len(theta) + [90.0] * len(phi)
        current_center = self.selectParametersFromLists((augmented_theta, augmented_phi, augmented_angle), all_combinations=False,
                                                        randomize_order=self.protocol_parameters['randomize_order'])
        adj_center = self.adjustCenter(current_center[0:2])
        self.epoch_parameters = self.getMovingPatchParameters(center=adj_center, angle=current_center[2], speed=0)
        self.convenience_parameters = {'current_theta': current_center[0],
                                       'current_phi': current_center[1]}


    def getParameterDefaults(self):
        self.protocol_parameters = {'width': 5.0,
                                    'height': 80.0,
                                    'color': 0.0,
                                    'theta': [0, 10, -10],
                                    'phi': [0, 10, -10],
                                    'randomize_order': True}

    def getRunParameterDefaults(self):
        self.run_parameters = {'protocol_ID': 'GridRectangle',
                               'num_epochs': 40,
                               'pre_time': 0.5,
                               'stim_time': 0.5,
                               'tail_time': 1.0,
                               'idle_color': 0.5}


class GridSpot(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

        self.getRunParameterDefaults()
        self.getParameterDefaults()

    def getEpochParameters(self):
        # adjust center to screen center
        theta = self.protocol_parameters['theta']
        phi = self.protocol_parameters['phi']
        current_center = self.selectParametersFromLists((theta, phi), all_combinations=True,
                                                        randomize_order=self.protocol_parameters['randomize_order'])
        adj_center = self.adjustCenter(current_center)

        self.epoch_parameters = {'name': 'MovingSpot',
                                 'radius': self.protocol_parameters['radius'],
                                 'sphere_radius': 1,
                                 'color': self.protocol_parameters['intensity'],
                                 'theta': adj_center[0],
                                 'phi': adj_center[1]}

        self.convenience_parameters = {'current_theta': current_center[0],
                                       'current_phi': current_center[1]}

    def getParameterDefaults(self):
        self.protocol_parameters = {'intensity': 0.0,
                                    'theta': [0.0],
                                    'phi': [0.0],
                                    'radius': 2.5,
                                    'randomize_order': True}

    def getRunParameterDefaults(self):
        self.run_parameters = {'protocol_ID': 'GridSpot',
                               'num_epochs': 75,
                               'pre_time': 0.5,
                               'stim_time': 1.0,
                               'tail_time': 1.0,
                               'idle_color': 0.5}


class UniformFlash(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

        self.getRunParameterDefaults()
        self.getParameterDefaults()

    def getEpochParameters(self):
        adj_center = self.adjustCenter(self.protocol_parameters['center'])

        current_intensity = self.selectParametersFromLists(self.protocol_parameters['intensity'],
                                                           randomize_order=self.protocol_parameters['randomize_order'])

        self.epoch_parameters = {'name': 'MovingPatch',
                                 'width': self.protocol_parameters['width'],
                                 'height': self.protocol_parameters['height'],
                                 'sphere_radius': 1,
                                 'color': current_intensity,
                                 'theta': adj_center[0],
                                 'phi': adj_center[1],
                                 'angle': 0}
        self.convenience_parameters = {'current_intensity': current_intensity}

    def getParameterDefaults(self):
        self.protocol_parameters = {'height': 120.0,
                                    'width': 120.0,
                                    'center': [0, 0],
                                    'intensity': [1.0, 0.0],
                                    'randomize_order': True}

    def getRunParameterDefaults(self):
        self.run_parameters = {'protocol_ID': 'UniformFlash',
                               'num_epochs': 10,
                               'pre_time': 1.0,
                               'stim_time': 0.5,
                               'tail_time': 1.0,
                               'idle_color': 0.5}


class DriftingSquareGrating(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

        self.getRunParameterDefaults()
        self.getParameterDefaults()

    def getEpochParameters(self):
        # TODO: center size with aperture (center and center_size)
        current_angle = self.selectParametersFromLists(self.protocol_parameters['angle'],
                                                       randomize_order=self.protocol_parameters['randomize_order'])

        self.epoch_parameters = {'name': 'RotatingGrating',
                                 'period': self.protocol_parameters['period'],
                                 'rate': self.protocol_parameters['rate'],
                                 'color': [1, 1, 1, 1],
                                 'mean': self.protocol_parameters['mean'],
                                 'contrast': self.protocol_parameters['contrast'],
                                 'angle': current_angle,
                                 'offset': 0.0,
                                 'cylinder_radius': 1,
                                 'cylinder_height': 10,
                                 'profile': 'square',
                                 'theta': self.screen_center[0]}

        self.convenience_parameters = {'current_angle': current_angle}

        self.meta_parameters = {'center_size': self.protocol_parameters['center_size'],
                                'center': self.adjustCenter(self.protocol_parameters['center'])}

    def getParameterDefaults(self):
        self.protocol_parameters = {'period': 20.0,
                                    'rate': 20.0,
                                    'contrast': 1.0,
                                    'mean': 0.5,
                                    'angle': [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0],
                                    'center': [0, 0],
                                    'center_size': 180.0,
                                    'randomize_order': True}

    def getRunParameterDefaults(self):
        self.run_parameters = {'protocol_ID': 'DriftingSquareGrating',
                               'num_epochs': 40,
                               'pre_time': 1.0,
                               'stim_time': 4.0,
                               'tail_time': 1.0,
                               'idle_color': 0.5}


class SphericalCheckerboardWhiteNoise(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

        self.getRunParameterDefaults()
        self.getParameterDefaults()

    def getParameterDefaults(self):
        self.protocol_parameters = {'patch_size': 5.0,
                                    'update_rate': 20.0,
                                    'rand_min': 0.0,
                                    'rand_max': 1.0,
                                    'grid_width': 60,
                                    'grid_height': 60,
                                    'center': [0.0, 0.0]}

    def getEpochParameters(self):
        stimulus_ID = 'RandomGridOnSphericalPatch'
        adj_center = self.adjustCenter(self.protocol_parameters['center'])

        start_seed = int(np.random.choice(range(int(1e6))))
        color = [0, 0, 1, 1] # blue only

        distribution_data = {'name': 'Ternary',
                             'args': [],
                             'kwargs': {'rand_min': self.protocol_parameters['rand_min'],
                                        'rand_max': self.protocol_parameters['rand_max']}}

        self.epoch_parameters = {'name': stimulus_ID,
                                 'patch_width': self.protocol_parameters['patch_size'],
                                 'patch_height': self.protocol_parameters['patch_size'],
                                 'width': self.protocol_parameters['grid_width'],
                                 'height': self.protocol_parameters['grid_height'],
                                 'start_seed': start_seed,
                                 'update_rate': self.protocol_parameters['update_rate'],
                                 'distribution_data': distribution_data,
                                 'theta': adj_center[0],
                                 'phi': adj_center[1],
                                 'color': color}

        self.convenience_parameters = {'start_seed': start_seed}

    def getRunParameterDefaults(self):
        self.run_parameters = {'protocol_ID': 'SphericalCheckerboardWhiteNoise',
                               'num_epochs': 10,
                               'pre_time': 2.0,
                               'stim_time': 30.0,
                               'tail_time': 2.0,
                               'idle_color': 0.5}
        

class BTFgrating(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

        self.getRunParameterDefaults()
        self.getParameterDefaults()

    def getEpochParameters(self):
        current_rate = self.selectParametersFromLists(self.protocol_parameters['rate'],
                                                      randomize_order=self.protocol_parameters['randomize_order'])

        self.epoch_parameters = {'name': 'RotatingGrating',
                                 'period': self.protocol_parameters['period'],
                                 'rate': current_rate,
                                 'color': [1, 1, 1, 1],
                                 'mean': self.protocol_parameters['mean'],
                                 'contrast': self.protocol_parameters['contrast'],
                                 'angle': self.protocol_parameters['angle'],
                                 'offset': 0.0,
                                 'cylinder_radius': 1,
                                 'cylinder_height': 10,
                                 'profile': 'square',
                                 'theta': self.screen_center[0]}

        self.pre_epoch_parameters = {'name': 'RotatingGrating',
                                     'period': self.protocol_parameters['period'],
                                     'rate': 0,
                                     'color': [1, 1, 1, 1],
                                     'mean': self.protocol_parameters['mean'],
                                     'contrast': self.protocol_parameters['contrast'],
                                     'angle': self.protocol_parameters['angle'],
                                     'offset': 0.0,
                                     'cylinder_radius': 1,
                                     'cylinder_height': 10,
                                     'profile': 'square',
                                     'theta': self.screen_center[0]}

        self.convenience_parameters = {'current_rate': current_rate}

        self.meta_parameters = {'center_size': self.protocol_parameters['center_size'],
                                'center': self.adjustCenter(self.protocol_parameters['center'])}

    def getParameterDefaults(self):
        self.protocol_parameters = {'period': 20.0,
                                    'rate': 20.0,
                                    'contrast': 1.0,
                                    'mean': 0.5,
                                    'angle': 0.0,
                                    'center': [0, 0],
                                    'center_size': 180.0,
                                    'randomize_order': True}

    def getRunParameterDefaults(self):
        self.run_parameters = {'protocol_ID': 'BTFgrating',
                               'num_epochs': 40,
                               'pre_time': 1.0,
                               'stim_time': 4.0,
                               'tail_time': 1.0,
                               'idle_color': 0.5}

    def loadStimuli(self, client):
        # bypassing the load stim here because I loaded it in startStimuli
        pass

    def startStimuli(self, client, append_stim_frames=False, print_profile=True):
        # pre time
        bg = self.run_parameters.get('idle_color')
        multicall = flyrpc.multicall.MyMultiCall(client.manager)
        multicall.load_stim('ConstantBackground', color=[bg, bg, bg, 1.0])
        stim = self.pre_epoch_parameters.copy()
        multicall.load_stim(**stim, hold=True)
        stim['cylinder_location'] = (.008, 0, 0)
        stim['angle'] -= 180
        multicall.load_stim(**stim, hold=True)
        multicall()
        multicall.start_stim(append_stim_frames=append_stim_frames)
        multicall()
        sleep(self.run_parameters['pre_time'])

        # stim time
        bg = self.run_parameters.get('idle_color')
        multicall = flyrpc.multicall.MyMultiCall(client.manager)
        multicall.load_stim('ConstantBackground', color=[bg, bg, bg, 1.0])
        stim = self.epoch_parameters.copy()
        multicall.load_stim(**stim, hold=True)
        stim['cylinder_location'] = (.008, 0, 0)
        stim['angle'] -= 180
        multicall.load_stim(**stim, hold=True)
        multicall()
        multicall.start_stim(append_stim_frames=append_stim_frames)
        multicall.start_corner_square()
        multicall()
        sleep(self.run_parameters['stim_time'])

        # tail time
        multicall = flyrpc.multicall.MyMultiCall(client.manager)
        multicall.stop_stim(print_profile=print_profile)
        multicall.black_corner_square()
        multicall()

        sleep(self.run_parameters['tail_time'])


class BTFflowLoom(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

        self.getRunParameterDefaults()
        self.getParameterDefaults()

    def getEpochParameters(self):
        current_loom = self.selectParametersFromLists(self.protocol_parameters['loom'],
                                                      randomize_order=self.protocol_parameters['randomize_order'])
        self.epoch_parameters = {'name': 'RotatingGrating',
                                 'period': self.protocol_parameters['period'],
                                 'rate': self.protocol_parameters['rate'],
                                 'color': [1, 1, 1, 1],
                                 'mean': self.protocol_parameters['mean'],
                                 'contrast': self.protocol_parameters['contrast'],
                                 'angle': self.protocol_parameters['angle'],
                                 'offset': 0.0,
                                 'cylinder_radius': 1,
                                 'cylinder_height': 10,
                                 'profile': 'square',
                                 'theta': self.screen_center[0]}

        self.pre_epoch_parameters = {'name': 'RotatingGrating',
                                     'period': self.protocol_parameters['period'],
                                     'rate': 0,
                                     'color': [1, 1, 1, 1],
                                     'mean': self.protocol_parameters['mean'],
                                     'contrast': self.protocol_parameters['contrast'],
                                     'angle': self.protocol_parameters['angle'],
                                     'offset': 0.0,
                                     'cylinder_radius': 1,
                                     'cylinder_height': 10,
                                     'profile': 'square',
                                     'theta': self.screen_center[0]}

        self.convenience_parameters = {'current_loom': current_loom}

        self.meta_parameters = {'center_size': self.protocol_parameters['center_size'],
                                'center': self.adjustCenter(self.protocol_parameters['center'])}

        stim_time = self.run_parameters['stim_time']
        start_size = self.protocol_parameters['start_size']
        end_size = self.protocol_parameters['end_size']
        # adjust center to screen center
        adj_center = self.adjustCenter(self.protocol_parameters['center'])
        rv_ratio = self.protocol_parameters['rv_ratio']  # msec
        rv_ratio = rv_ratio / 1e3  # msec -> sec
        r_traj = {'name': 'Loom',
                  'rv_ratio': rv_ratio,
                  'stim_time': stim_time,
                  'start_size': start_size,
                  'end_size': end_size}
        self.loom_epoch_parameters = {'name': 'MovingSpot',
                                      'loom': current_loom,
                                      'radius': r_traj,
                                      'sphere_radius': 1,
                                      'color': self.protocol_parameters['intensity'],
                                      'theta': adj_center[0],
                                      'phi': adj_center[1]}

    def getParameterDefaults(self):
        self.protocol_parameters = {'period': 20.0,
                                    'rate': 20.0,
                                    'contrast': 1.0,
                                    'mean': 0.5,
                                    'angle': 0.0,
                                    'loom': [0, 1],
                                    'center': [0, 0],
                                    'start_size': 5,
                                    'end_size': 90,
                                    'rv_ratio': 40,
                                    'intensity': 0.0,
                                    'center_size': 180.0,
                                    'randomize_order': True}

    def getRunParameterDefaults(self):
        self.run_parameters = {'protocol_ID': 'BTFflowLoom',
                               'num_epochs': 40,
                               'pre_time': 1.0,
                               'stim_time': 4.0,
                               'tail_time': 1.0,
                               'idle_color': 0.5}

    def loadStimuli(self, client):
        # bypassing the load stim here because I loaded it in startStimuli
        pass

    def startStimuli(self, client, append_stim_frames=False, print_profile=True):
        # pre time
        bg = self.run_parameters.get('idle_color')
        multicall = flyrpc.multicall.MyMultiCall(client.manager)
        multicall.load_stim('ConstantBackground', color=[bg, bg, bg, 1.0])
        stim = self.pre_epoch_parameters.copy()
        multicall.load_stim(**stim, hold=True)
        stim['cylinder_location'] = (.008, 0, 0)
        stim['angle'] -= 180
        multicall.load_stim(**stim, hold=True)
        multicall()
        multicall.start_stim(append_stim_frames=append_stim_frames)
        multicall()
        sleep(self.run_parameters['pre_time'])

        # stim time
        bg = self.run_parameters.get('idle_color')
        multicall = flyrpc.multicall.MyMultiCall(client.manager)
        multicall.load_stim('ConstantBackground', color=[bg, bg, bg, 1.0])
        loom_stim = self.loom_epoch_parameters.copy()
        if loom_stim['loom']:
            loom_stim.pop('loom')
            multicall.load_stim(**loom_stim, hold=True)
        stim = self.epoch_parameters.copy()
        multicall.load_stim(**stim, hold=True)
        stim['cylinder_location'] = (.008, 0, 0)
        stim['angle'] -= 180
        multicall.load_stim(**stim, hold=True)
        multicall()
        multicall.start_stim(append_stim_frames=append_stim_frames)
        multicall.start_corner_square()
        multicall()
        sleep(self.run_parameters['stim_time'])

        # tail time
        multicall = flyrpc.multicall.MyMultiCall(client.manager)
        multicall.stop_stim(print_profile=print_profile)
        multicall.black_corner_square()
        multicall()

        sleep(self.run_parameters['tail_time'])


def get_loom_size(rv_ratio, start_size, end_size, t):
    # calculate angular size at t
    d0 = rv_ratio / np.tan(np.deg2rad(start_size / 2))
    angular_size = 2 * \
                   np.rad2deg(np.arctan(rv_ratio * (1 / (d0 - t))))
    # Cap the curve at end_size and have it just hang there
    if angular_size > end_size or d0 <= t:
        angular_size = end_size
    return angular_size / 2


class PanGlomSuite(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)
        self.cfg = cfg
        self.stim_list = ['FlickeringPatch', 'DriftingSquareGrating', 'LoomingSpot', 'ExpandingMovingSpot',
                          'MovingRectangle', 'UniformFlash']
        n = [3, 2, 3, 12, 6, 4, 2]  # weight each stim draw by how many trial types it has. Total = 32
        avg_per_stim = int(self.run_parameters['num_epochs'] / np.sum(n))
        all_stims = [[self.stim_list[i]] * n[i] * avg_per_stim for i in range(len(n))]

        self.stim_order = np.random.permutation(np.hstack(all_stims))

        # initialize each component class
        self.initComponentClasses()

        self.getRunParameterDefaults()
        self.getParameterDefaults()

    def initComponentClasses(self):
        # pre-populate dict of component classes. Each with its own num_epochs_completed counter etc
        self.component_classes = {}
        for stim_type in self.stim_list:
            if stim_type == 'LoomingSpot':
                new_component_class = LoomingSpot(self.cfg)
                new_component_class.protocol_parameters = {'intensity': 0.0,
                                                           'center': [0, 0],
                                                           'start_size': 2.5,
                                                           'end_size': 80.0,
                                                           'rv_ratio': [5.0, 20.0, 100.0],
                                                           'randomize_order': True}

            elif stim_type == 'DriftingSquareGrating':
                new_component_class = DriftingSquareGrating(self.cfg)
                new_component_class.protocol_parameters = {'period': 20.0,
                                                           'rate': 20.0,
                                                           'contrast': 1.0,
                                                           'mean': 0.5,
                                                           'angle': [0.0, 180.0],
                                                           'center': [0, 0],
                                                           'center_size': 180.0,
                                                           'randomize_order': True}

            elif stim_type == 'ExpandingMovingSpot':
                new_component_class = ExpandingMovingSpot(self.cfg)
                new_component_class.protocol_parameters = {'diameter': [5.0, 15.0, 50.0],
                                                           'intensity': [0.0, 1.0],
                                                           'center': [0, 0],
                                                           'speed': [-80.0, 80.0],
                                                           'angle': 0.0,
                                                           'randomize_order': True}

            elif stim_type == 'UniformFlash':
                new_component_class = UniformFlash(self.cfg)
                new_component_class.protocol_parameters = {'height': 240.0,
                                                           'width': 240.0,
                                                           'center': [0, 0],
                                                           'intensity': [1.0, 0.0],
                                                           'randomize_order': True}

            elif stim_type == 'FlickeringPatch':
                new_component_class = FlickeringPatch(self.cfg)
                new_component_class.protocol_parameters = {'height': 30.0,
                                                           'width': 30.0,
                                                           'center': [0, 0],
                                                           'contrast': 1.0,
                                                           'mean': 0.5,
                                                           'temporal_frequency': [1.0, 2.0, 8.0],
                                                           'randomize_order': True}

            elif stim_type == 'MovingRectangle':
                new_component_class = MovingRectangle(self.cfg)
                new_component_class.protocol_parameters = {'width': 10.0,
                                                           'height': 120.0,
                                                           'intensity': [0.0, 1.0],
                                                           'center': [0, 0],
                                                           'speed': 80.0,
                                                           'angle': [0.0, 180.0],
                                                           'randomize_order': True}

            # Lock component stim timing run params to suite run params
            new_component_class.run_parameters['pre_time'] = self.run_parameters['pre_time']
            new_component_class.run_parameters['stim_time'] = self.run_parameters['stim_time']
            new_component_class.run_parameters['tail_time'] = self.run_parameters['tail_time']
            new_component_class.run_parameters['idle_color'] = self.run_parameters['idle_color']

            self.component_classes[stim_type] = new_component_class

    def getEpochParameters(self):
        stim_type = str(self.stim_order[
                            self.num_epochs_completed])  # note this num_epochs_completed is for the whole suite, not component stim!
        self.convenience_parameters = {'component_stim_type': stim_type}
        self.component_class = self.component_classes[stim_type]

        self.component_class.getEpochParameters()
        self.convenience_parameters.update(self.component_class.convenience_parameters)
        self.epoch_parameters = self.component_class.epoch_parameters

    def loadStimuli(self, client):
        self.component_class.loadStimuli(client)
        self.component_class.advanceEpochCounter()  # up the component class epoch counter

    def getParameterDefaults(self):
        self.protocol_parameters = {}

    def getRunParameterDefaults(self):
        self.run_parameters = {'protocol_ID': 'PanGlomSuite',
                               'num_epochs': 160,  # 160 = 32 * 5 averages each
                               'pre_time': 1.5,
                               'stim_time': 3.0,
                               'tail_time': 1.5,
                               'idle_color': 0.5}


"""
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # OPTO STIMS # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
"""


class OptoStimulus(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)
        self.cfg = cfg

        self.getRunParameterDefaults()
        self.getParameterDefaults()

    def getEpochParameters(self):

        assert self.protocol_parameters['opto_mode'] in ['on', 'off', 'alternating']

        if self.protocol_parameters['opto_mode'] == 'on':
            self.convenience_parameters['opto_stim'] = True

        elif self.protocol_parameters['opto_mode'] == 'off':
            self.convenience_parameters['opto_stim'] = False

        else:
            print('Unrecognized opto_mode string. Allowable: [on, off, alternating]')

    def startStimuli(self, client, append_stim_frames=False, print_profile=True):
        if self.convenience_parameters['opto_stim']:
            client.niusb_device.outputStep(output_channel='ctr1',
                                           low_time=0.001,
                                           high_time=self.protocol_parameters['opto_time'],
                                           initial_delay=0.0)
            sleep(self.run_parameters['pre_time'] - self.protocol_parameters['opto_time'])
        else:
            sleep(self.run_parameters['pre_time'])

    def getParameterDefaults(self):
        self.protocol_parameters = {'opto_mode': 'on',  # 'on', 'off', 'alternating'
                                    'opto_time': 2.0}

    def getRunParameterDefaults(self):
        self.run_parameters = {'protocol_ID': 'MedullaTuningSuite',
                               'num_epochs': 1,  # 96 = 16 stims * 2 opto conditions * 3 averages each
                               'pre_time': 1200.0,
                               'stim_time': 1.0,
                               'tail_time': 1200.0,
                               'idle_color': 0.0}
