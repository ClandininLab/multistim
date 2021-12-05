from flystim.stim_server import MultiStimServer
from flystim.screen import Screen
from flystim.util import listify

from flyrpc.launch import launch_server
from flyrpc.util import get_kwargs



def launch_stim_server(screen_or_screens=None):
    # set defaults
    if screen_or_screens is None:
        screen_or_screens = []

    # make list from single screen if necessary
    screens = listify(screen_or_screens, Screen)

    # serialize the Screen objects
    screens = [screen.serialize() for screen in screens]

    # run the server
    return launch_server(__file__, screens=screens)


def run_stim_server(host=None, port=None, auto_stop=None, screens=None):
    # set defaults
    if screens is None:
        screens = []

    # instantiate the server
    server = MultiStimServer(screens=screens, host=host, port=port, auto_stop=auto_stop)

    # launch the server
    server.loop()


def main():
    # get the startup arguments
    kwargs = get_kwargs()

    screens = kwargs['screens']
    if screens is None:
        screens = []
    screens = [Screen.deserialize(screen) for screen in screens]
    # run the server
    run_stim_server(host=kwargs['host'], port=kwargs['port'], auto_stop=kwargs['auto_stop'], screens=screens)

if __name__ == '__main__':
    main()