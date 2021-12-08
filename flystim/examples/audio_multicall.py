#!/usr/bin/env python3

# Example client program that walks through all available stimuli.

from flyrpc.multicall import MyMultiCall
from flystim.stim_server import launch_stim_server
from flystim.screen import Screen

from time import time, sleep


def main():
    manager = launch_stim_server(Screen(fullscreen=False, server_number=0, id=0, vsync=True))
    multicall = MyMultiCall(manager)
    sleep(5)
    auditory_stims = ['sine_song', 'pulse_song', 'sine_song']
    visual_stims = ['RotatingGrating', 'RandomGrid', 'RotatingGrating']


    for stim1, stim2 in zip(auditory_stims, visual_stims):
        multicall.load_stim(stim1, device='speaker')
        multicall.load_stim(stim2)
        multicall()
        sleep(1.0)
        print(stim1)
        print(stim2)

        multicall.start_stim(device='speaker')
        print('command sent to speaker at %s' % time())
        multicall.start_stim()
        print('command sent to screen at %s' % time())
        multicall()
        sleep(4.5)
        print('played')
        # it looks like using multicall does not decrease the jittering of the onset of the two stimuli, however, I do find a potential bug in multicall

        multicall.stop_stim(device='speaker')
        multicall.stop_stim()
        multicall()
        sleep(1.0)
    sleep(15)
if __name__ == '__main__':
    main()
