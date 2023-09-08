#!/usr/bin/env python3
from time import sleep

import flyrpc.multicall as mc
from flystim.stim_server import launch_stim_server
from flystim.screen import Screen


def main():
    """."""

    screen = Screen(fullscreen=False, server_number=0, id=0, vsync=True)

    # draw_screens(screen)

    manager = launch_stim_server(screen)
    multicall = mc.MyMultiCall(manager)
    # contrast-reversing grating
    period = 10
    rate = 60
    multicall = mc.MyMultiCall(manager)
    loom_trajectory = {'name': 'Loom',
                       'rv_ratio': 0.04,
                       'stim_time': 4,
                       'start_size': 8,
                       'end_size': 90}
    multicall.load_stim(name='MovingSpot', radius=loom_trajectory, sphere_radius=1, color=0.01, theta=-20,
                        phi=0, hold=True)
    rotation_0 = {'name': 'RotatingGrating', 'angle': 0, 'period': period, 'rate': rate, 'color': 1,
                  'phi': 0, 'offset': 180}
    stim = rotation_0.copy()
    multicall.load_stim(**stim, hold=True)
    stim['cylinder_location'] = (.008, 0, 0)
    # stim['cylinder_location'] = (-.008, 0, 0) for front to back flow, or make rate negative
    stim['angle'] -= 180
    multicall.load_stim(**stim, hold=True)
    multicall()
    sleep(1.0)
    multicall.start_stim(append_stim_frames=True)
    multicall()
    sleep(2)


    multicall.stop_stim(print_profile=True)
    multicall()
    sleep(1.5)


if __name__ == '__main__':
    main()
