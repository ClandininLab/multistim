#!/usr/bin/env python3

# Example client program that walks through all available stimuli.

from flystim.stim_server import launch_stim_server
from flystim.screen import Screen

from time import time, sleep


def main():
    manager = launch_stim_server(Screen(fullscreen=False, server_number=0, id=0, vsync=True))
    sleep(5)
    auditory_stims = ['sine_song', 'pulse_song', 'sine_song']
    visual_stims = ['RotatingGrating', 'RandomGrid', 'RotatingGrating']


    for stim1, stim2 in zip(auditory_stims, visual_stims):
        manager.load_stim(stim1, device='speaker')
        manager.load_stim(stim2)
        sleep(500e-3)
        print(stim1)
        print(stim2)

        manager.start_stim(device='speaker')
        print('command sent to speaker at %s' % time())
        manager.start_stim()
        print('command sent to screen at %s' % time())
        sleep(2.5)
        print('played')

        manager.stop_stim(device='speaker')
        manager.stop_stim()
        sleep(500e-3)
    sleep(15)
if __name__ == '__main__':
    main()
