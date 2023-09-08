#!/usr/bin/env python3
from time import sleep, time
from datetime import datetime

from flystim.stim_server import launch_stim_server
from flystim.screen import Screen


def main():
    manager = launch_stim_server(Screen(fullscreen=False, server_number=0, id=0, vsync=False))

    bg =1.0  # background brightness
    n_trials = 100
    ILI = 1.0  # inter-looming interval (s)
    contrast = 10
    patch_brightness = bg / contrast
    rv_ratio = 0.08
    stim_time = 1  # loom duration (s)
    start_size = 5
    end_size = 90

    loom_trajectory = {'name': 'Loom',
                       'rv_ratio': rv_ratio,
                       'stim_time': stim_time,
                       'start_size': start_size,
                       'end_size': end_size}
    
    fileName='looming'+datetime.now().strftime('%Y%m%d%H%M%S')+'.txt' # for saving the time when looming starts
    F=open(fileName,'w')

    for i in range(n_trials):
        manager.load_stim(name='ConstantBackground', color=[1.0, 1.0, 1.0, bg], side_length=100)
        manager.load_stim(name='MovingSpot', radius=loom_trajectory, sphere_radius=1, color=patch_brightness, theta=0, phi=0, hold=True)
        F.write(str(time()) +'\n') #write the time in file just before start stimulating
        F.flush()
        manager.start_stim()
        sleep(stim_time)
        manager.stop_stim(print_profile=True)
        sleep(ILI)

    F.close()
if __name__ == '__main__':
    main()
